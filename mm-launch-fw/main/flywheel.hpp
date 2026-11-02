#pragma once

// Flywheel: the XTEAM XTI-3674 on MotorGo Axis motor channel 1, Plink MT6701
// on encoder port 1, voltage-mode FOC with espp::BldcMotor.
//
// What comes from espp unchanged: the MotorGo Axis BSP's 6-PWM driver
// (MotorGoAxis::initialize_motors / motor_driver), its pin map and SPI clock,
// espp::Mt6701<SSI>, espp::BldcMotor (SVPWM, velocity PID, sensor alignment),
// espp::HighResolutionTimer.
//
// Why the BSP's initialize_motor() is not used as-is: it runs the encoder on
// its own 1 kHz task. At 6000 rpm with 2 pole pairs that is 72 electrical
// degrees between angle samples, so the commutation angle lags by up to a
// fifth of a cycle. Here the encoder is read and FOC runs in the same 4 kHz
// tick (CONFIG_MM_FOC_HZ), 18 electrical degrees per sample at 6000 rpm. The
// encoder is the BSP's (same bus pins, chip select, clock), just updated from
// this loop.
//
// FocMotor is a thin subclass that exposes what BldcMotor keeps protected:
// live gains and voltage limits, the q voltage, and the calibration result
// (electrical zero + sensor direction) so it can be stored in NVS and the
// boot skips the alignment twitch.
//
// Threads and locking:
//   - tick() runs on the esp_timer task at CONFIG_MM_FOC_HZ. It never blocks:
//     it try-locks `mutex_` and skips the FOC step for that tick if the lock
//     is busy (counted in lock_skips()).
//   - Every mode change and every call into motor_ happens under `mutex_`,
//     so a mode transition and the bridge enable/disable that goes with it
//     are one step for every other task.
//   - Calibration runs on its own task ("fw_cal") WITHOUT holding `mutex_`
//     (BldcMotor's alignment sleeps for about 3 s). While mode_ is
//     Calibrating nothing else touches motor_; stop()/coast()/fault() abort it
//     by disabling the driver directly, which BldcDriver::set_pwm honours
//     (it refuses to write while disabled).
//   - Settings are never read here outside the console task: apply_settings()
//     (console task) copies what the tick needs into atomics, and calibration
//     results go back through take_calibration_result().
//   - The tick never prints, formats or allocates: a fault it raises is a code
//     plus two numbers in atomics, turned into text by fault_reason() on the
//     reader's task, and announced by the console task (take_fault_notice()).

#include <algorithm>
#include <atomic>
#include <chrono>
#include <cmath>
#include <condition_variable>
#include <memory>
#include <mutex>
#include <optional>
#include <string>
#include <thread>

#include "esp_timer.h"
#include "sdkconfig.h"

#include "bldc_motor.hpp"
#include "high_resolution_timer.hpp"
#include "logger.hpp"
#include "motorgo-axis.hpp"
#include "mt6701.hpp"
#include "spi.hpp"
#include "task.hpp"

#include "settings.hpp"
#include "stop_rule.hpp"

namespace mml {

using Encoder = espp::MotorGoAxis::Encoder;
using Driver = espp::MotorGoAxis::MotorDriver;

class FocMotor : public espp::BldcMotor<Driver, Encoder> {
public:
  using Base = espp::BldcMotor<Driver, Encoder>;
  using Base::Base;

  /// q-axis voltage cap for closed loop and the open-loop drive voltage.
  void set_voltage_limit(float v) {
    voltage_limit_ = v;
    apply_velocity_pid();
  }
  float voltage_limit() const { return voltage_limit_; }
  void set_align_voltage(float v) { voltage_sensor_align_ = v; }
  void set_velocity_gains(float kp, float ki) {
    kp_ = kp;
    ki_ = ki;
    apply_velocity_pid();
  }
  /// Drop the PI state (call before a fresh spin-up: the espp Pid integrates
  /// over the wall time since its last update, which includes the idle time).
  void reset_velocity_pid() { pid_velocity_.clear(); }
  float uq() const { return voltage_.q; }
  float zero_electric_angle() const { return zero_electrical_angle_; }
  int sensor_direction() const { return static_cast<int>(sensor_direction_); }
  bool ready() const { return status_ == Status::READY; }
  /// Put back a known calibration without BldcMotor::initialize(), which
  /// would enable() the bridge with the comparators still at the last
  /// alignment vector (review R2-04).
  void restore_calibration(float zero, int dir) {
    zero_electrical_angle_ = zero == 0.0f ? 1e-6f : zero;
    sensor_direction_ = static_cast<espp::detail::SensorDirection>(dir);
    status_ = Status::READY;
  }
  /// Forget the calibration so the next initialize() measures both values.
  void forget_calibration() {
    zero_electrical_angle_ = 0;
    sensor_direction_ = espp::detail::SensorDirection::UNKNOWN;
    status_ = Status::UNCALIBRATED;
  }

private:
  void apply_velocity_pid() {
    // phase_resistance is 0, so the PID output is the q voltage directly
    // (SimpleFOC "voltage mode, no R"): the gains are V per rad/s and V per rad.
    pid_velocity_.change_gains({.kp = kp_,
                                .ki = ki_,
                                .kd = 0,
                                .integrator_min = -voltage_limit_,
                                .integrator_max = voltage_limit_,
                                .output_min = -voltage_limit_,
                                .output_max = voltage_limit_},
                               false);
  }
  float kp_{0}, ki_{0};
};

class Flywheel {
public:
  enum class Mode : int { Off = 0, Calibrating = 1, OpenLoop = 2, Closed = 3, Fault = 6 };
  enum class FaultCode : int { None = 0, Encoder, Overspeed, Stall, External };

  /// Result of a calibration run, handed to the console task.
  struct CalResult {
    bool ok{false};
    bool aborted{false};
    bool kept_previous{false}; ///< failed/aborted, previous calibration still in force
    float zero_electric{0};
    int sensor_dir{0};
    std::string why;
  };

  Flywheel()
      : logger_({.tag = "flywheel", .level = espp::Logger::Verbosity::INFO}) {}

  /// Bring up the driver, the encoder and the motor. Never moves the motor:
  /// without a stored calibration the wheel stays off until `fw cal`.
  bool init(const Settings &s) {
    auto &board = espp::MotorGoAxis::get();
    // The driver's limit is the full supply: the motor-level voltage_limit_
    // (FocMotor::set_voltage_limit) is what actually caps the phase voltage.
    if (!board.initialize_motors(CONFIG_MM_SUPPLY_MV / 1000.0f, CONFIG_MM_SUPPLY_MV / 1000.0f)) {
      logger_.error("motor driver init failed");
      return false;
    }
    driver_ = board.motor_driver(0);
    // BldcDriver::disable() logs "Disabling" at INFO; the tick disables the
    // bridge at the end of every ramp-down, so keep that off the esp_timer task.
    driver_->set_log_level(espp::Logger::Verbosity::WARN);

    const auto pins = board.encoder_bus_pins();
    spi_ = std::make_unique<espp::Spi>(espp::Spi::Config{
        .host = SPI2_HOST,
        .sclk_io_num = pins.sclk,
        .mosi_io_num = GPIO_NUM_NC,
        .miso_io_num = pins.miso,
        .max_transfer_sz = 32,
    });
    std::error_code ec;
    spi_dev_ = spi_->add_device({.mode = 0,
                                 .clock_speed_hz = static_cast<int>(board.encoder_spi_clock_speed_hz()),
                                 .cs_io_num = board.encoder_cs_pin(0),
                                 .queue_size = 1},
                                ec);
    if (ec || !spi_dev_) {
      logger_.error("encoder SPI device failed: {}", ec.message());
      return false;
    }
    // the tick reads through this device; a transmit error must not print there
    spi_dev_->set_log_level(espp::Logger::Verbosity::NONE);
    encoder_ = std::make_shared<Encoder>(Encoder::Config{
        .read = [this](uint8_t *data, size_t size) -> bool {
          std::error_code e;
          return spi_dev_->read(std::span<uint8_t>(data, size), {}, e);
        },
        .velocity_filter = [this](float raw_rpm) { return filter_rpm(raw_rpm); },
        .update_period = std::chrono::duration<float>(1.0f / CONFIG_MM_FOC_HZ),
        .auto_init = false,
        .run_task = false,
        // a failed SPI read would log on every tick; enc_errors_ counts them
        .log_level = espp::Logger::Verbosity::NONE,
    });
    encoder_->initialize(false, ec);
    if (ec) {
      logger_.error("encoder init failed: {}", ec.message());
      return false;
    }

    motor_ = std::make_shared<FocMotor>(FocMotor::Config{
        .num_pole_pairs = static_cast<size_t>(s.pole_pairs),
        .phase_resistance = 0.0f, // voltage mode: PID output is volts
        .kv_rating = s.kv,
        .current_limit = 0.0f,
        .velocity_limit = s.max_rpm * espp::RPM_TO_RADS,
        .driver = driver_,
        .sensor = encoder_,
        .run_sensor_update = false, // the timer below updates the encoder
        .auto_init = false,
        .log_level = espp::Logger::Verbosity::INFO,
    });
    apply_settings(s);

    if (s.calibrated) {
      // Both values known: BldcMotor::align_sensor skips every motion. espp
      // treats an electrical zero of exactly 0 as "unknown" and would align,
      // so a stored 0 is nudged off it.
      const float zero = s.zero_electric == 0.0f ? 1e-6f : s.zero_electric;
      std::lock_guard<std::mutex> lk(mutex_);
      motor_->initialize(zero, static_cast<espp::detail::SensorDirection>(s.sensor_dir));
      sdir_ = s.sensor_dir == 0 ? 1 : s.sensor_dir;
      calibrated_ = motor_->ready();
      logger_.info("calibration from NVS: zero {:.4f} rad, dir {}", zero, s.sensor_dir);
    } else {
      logger_.warn("not calibrated: run 'fw cal' on a current-limited supply");
    }

    cal_task_ = espp::Task::make_unique({
        .callback = [this](std::mutex &m, std::condition_variable &cv) { return cal_loop(m, cv); },
        .task_config = {.name = "fw_cal", .stack_size_bytes = 6 * 1024, .priority = 3},
    });
    cal_task_->start();

    timer_ = std::make_unique<espp::HighResolutionTimer>(espp::HighResolutionTimer::Config{
        .name = "foc", .callback = [this]() { tick(); }});
    timer_->start(1000000ULL / CONFIG_MM_FOC_HZ);
    ok_ = true;
    return true;
  }

  /// False if init() failed: every command refuses, stop/coast are no-ops.
  bool ok() const { return ok_; }

  /// Copy gains and limits from Settings (console task only).
  void apply_settings(const Settings &s) {
    kp_ = s.kp;
    ki_ = s.ki;
    tf_ = s.vel_tf;
    ramp_ = s.ramp_rpm_s;
    tol_ = s.at_speed_tol;
    max_rpm_ = s.max_rpm;
    sign_ = s.sign;
    vlim_ = s.vlim;
    vopen_ = s.vopen;
    valign_ = s.valign;
    if (!motor_)
      return;
    std::lock_guard<std::mutex> lk(mutex_);
    if (cal_running_)
      return; // the calibration task owns the motor; values apply next time
    motor_->set_velocity_gains(s.kp, s.ki);
    motor_->set_align_voltage(s.valign);
    motor_->set_voltage_limit(mode_ == Mode::OpenLoop ? s.vopen : s.vlim);
  }

  /// B3: start a sensor-direction / pole-pair / electrical-zero calibration
  /// on the fw_cal task. Returns at once; the result comes back through
  /// take_calibration_result(). `stop` aborts it.
  bool start_calibration(std::string &why) {
    if (!ok_) {
      why = "flywheel not initialized (see the boot log)";
      return false;
    }
    std::lock_guard<std::mutex> lk(mutex_);
    if (mode_ != Mode::Off) {
      why = fmt::format("flywheel must be off (it is {})", mode_name());
      return false;
    }
    cal_abort_ = false;
    mode_ = Mode::Calibrating;
    cal_running_ = true;
    cal_requested_ = true;
    cal_cv_.notify_all();
    return true;
  }

  /// The finished calibration, once (console task polls this).
  std::optional<CalResult> take_calibration_result() {
    std::lock_guard<std::mutex> lk(result_m_);
    auto r = std::move(cal_result_);
    cal_result_.reset();
    return r;
  }

  bool forget_calibration(std::string &why) {
    if (!ok_) {
      why = "flywheel not initialized";
      return false;
    }
    std::lock_guard<std::mutex> lk(mutex_);
    if (cal_running_) {
      why = "a calibration is still finishing";
      return false;
    }
    if (mode_ != Mode::Off && mode_ != Mode::Fault) {
      why = fmt::format("flywheel must be off (it is {})", mode_name());
      return false;
    }
    motor_->forget_calibration();
    calibrated_ = false;
    return true;
  }

  /// B5: closed-loop velocity to `rpm` (signed), ramped.
  bool spin(float rpm, std::string &why) {
    if (!ok_) {
      why = "flywheel not initialized";
      return false;
    }
    std::lock_guard<std::mutex> lk(mutex_);
    switch (mode_.load()) {
    case Mode::Fault:
      why = "fault latched: " + fault_reason() + " ('clear' first)";
      return false;
    case Mode::Calibrating:
      why = "calibrating";
      return false;
    case Mode::OpenLoop:
      why = "in open loop: 'fw stop' first";
      return false;
    default:
      break;
    }
    if (!calibrated_ || !motor_->ready()) {
      why = "not calibrated ('fw cal')";
      return false;
    }
    const float m = max_rpm_.load();
    target_rpm_ = std::clamp(rpm, -m, m);
    if (mode_ != Mode::Closed) {
      set_rpm_ = 0;
      stall_us_ = 0;
      stop_elapsed_s_ = 0;
      in_band_ticks_ = 0;
      at_speed_ = false;
      motor_->set_voltage_limit(vlim_);
      motor_->set_motion_control_type(espp::detail::MotionControlType::VELOCITY);
      motor_->reset_velocity_pid();
      motor_->enable();
      mode_ = Mode::Closed;
    }
    return true;
  }

  /// B4: open loop at `vopen`, no encoder in the loop.
  bool open_loop(float rpm, std::string &why) {
    if (!ok_) {
      why = "flywheel not initialized";
      return false;
    }
    std::lock_guard<std::mutex> lk(mutex_);
    if (mode_ != Mode::Off && mode_ != Mode::OpenLoop) {
      why = fmt::format("not available while {} ('fw stop' / 'clear' first)", mode_name());
      return false;
    }
    const float m = max_rpm_.load();
    target_rpm_ = std::clamp(rpm, -m, m);
    if (mode_ != Mode::OpenLoop) {
      set_rpm_ = 0;
      stop_elapsed_s_ = 0;
      at_speed_ = false;
      motor_->set_voltage_limit(vopen_);
      motor_->set_motion_control_type(espp::detail::MotionControlType::VELOCITY_OPENLOOP);
      motor_->enable();
      mode_ = Mode::OpenLoop;
    }
    return true;
  }

  /// Ramp to zero, then disable the bridge (the tick does the disable). A
  /// running calibration is aborted at once. Lock-free: callable from any task
  /// (watchdog, OTA, tip guard) even while the console task is busy.
  void stop() {
    target_rpm_ = 0;
    at_speed_ = false;
    if (cal_running_)
      abort_calibration();
  }

  /// Immediate coast: bridge off now, mode Off (unless faulted).
  void coast() {
    target_rpm_ = 0;
    at_speed_ = false;
    if (!ok_)
      return;
    if (cal_running_) { // the calibration task owns motor_: abort, don't touch it
      abort_calibration();
      return;
    }
    std::lock_guard<std::mutex> lk(mutex_);
    coast_locked();
  }

  /// Latch a fault: bridge off now. Callable from any task except the tick
  /// (which uses fault_locked under its own lock). During a calibration the
  /// calibration task owns motor_, so this aborts it (driver off) and only
  /// latches the fault; cal_loop leaves a Fault mode alone when it finishes.
  void fault(const std::string &why) {
    target_rpm_ = 0;
    at_speed_ = false;
    {
      std::lock_guard<std::mutex> fl(fault_m_);
      fault_text_ = why;
    }
    if (!ok_) {
      fault_code_ = static_cast<int>(FaultCode::External);
      fault_notice_ = true;
      return;
    }
    std::lock_guard<std::mutex> lk(mutex_);
    if (mode_ == Mode::Calibrating || cal_running_) {
      abort_calibration();
      set_fault_state(FaultCode::External, 0, 0);
      return;
    }
    fault_locked(FaultCode::External, 0, 0);
  }

  /// False (and nothing cleared) while a calibration is still finishing: a
  /// fault latched mid-calibration stays until the calibration task has handed
  /// motor_ back (at most ~3 s), so nothing can enable it meanwhile.
  bool clear_fault() {
    std::lock_guard<std::mutex> lk(mutex_);
    if (cal_running_)
      return false;
    if (mode_ == Mode::Fault)
      mode_ = Mode::Off;
    fault_code_ = static_cast<int>(FaultCode::None); // also the !ok_ path (review R2-03)
    return true;
  }

  /// The text of a fault latched since the last call, once (console task
  /// prints it: the tick itself never prints).
  std::optional<std::string> take_fault_notice() {
    if (!fault_notice_.exchange(false))
      return std::nullopt;
    return fault_reason();
  }

  /// B2: raw encoder angle statistics over `seconds`.
  struct EncStats {
    float deg, std_deg, rpm;
    int samples;
  };
  EncStats encoder_stats(float seconds) {
    if (!encoder_)
      return {NAN, NAN, NAN, 0};
    double sum = 0, sum2 = 0;
    int n = 0;
    const auto end = std::chrono::steady_clock::now() + std::chrono::duration<float>(seconds);
    const float first = encoder_->get_mechanical_degrees();
    while (std::chrono::steady_clock::now() < end) {
      // unwrap around the first reading so 359.9 / 0.1 does not inflate std
      float d = encoder_->get_mechanical_degrees() - first;
      d -= 360.0f * std::floor(d / 360.0f + 0.5f);
      sum += d;
      sum2 += d * d;
      n++;
      std::this_thread::sleep_for(std::chrono::milliseconds(2));
    }
    const double mean = n ? sum / n : 0;
    const double var = n ? std::max(0.0, sum2 / n - mean * mean) : 0;
    float deg = first + static_cast<float>(mean);
    deg -= 360.0f * std::floor(deg / 360.0f);
    return {deg, static_cast<float>(std::sqrt(var)), rpm(), n};
  }

  // ---- readouts (any task)
  Mode mode() const { return mode_; }
  std::string fault_reason() const {
    const float v1 = fault_v1_.load(), v2 = fault_v2_.load();
    switch (static_cast<FaultCode>(fault_code_.load())) {
    case FaultCode::None:
      return {};
    case FaultCode::Encoder:
      return "ENCODER (no reads for 50 ms)";
    case FaultCode::Overspeed:
      return fmt::format("OVERSPEED ({:.0f} rpm)", v1);
    case FaultCode::Stall:
      return fmt::format("STALL (set {:.0f}, wheel {:.0f} rpm)", v1, v2);
    case FaultCode::External: {
      std::lock_guard<std::mutex> lk(fault_m_);
      return fault_text_;
    }
    }
    return "?";
  }
  float rpm() const { return sign_.load() * encoder_rpm_.load(); }
  float setpoint() const { return set_rpm_.load(); }
  float target() const { return target_rpm_.load(); }
  float uq() const { return uq_.load(); }
  bool calibrated() const { return calibrated_.load(); }
  /// Closed loop, setpoint reached and the wheel within tolerance for 300 ms.
  bool at_speed() const { return at_speed_.load() && mode_ == Mode::Closed; }
  uint32_t encoder_errors() const { return enc_errors_.load(); }
  uint32_t overruns() const { return overruns_.load(); }
  uint32_t lock_skips() const { return lock_skips_.load(); }
  const char *mode_name() const {
    switch (mode_.load()) {
    case Mode::Off:
      return "off";
    case Mode::Calibrating:
      return "calibrating";
    case Mode::OpenLoop:
      return "open_loop";
    case Mode::Closed:
      return at_speed_ ? "at_speed" : "spin_up";
    case Mode::Fault:
      return "fault";
    }
    return "?";
  }

private:
  // "Coast" in this file means "release the drive". On the MotorGo Axis that
  // is a short brake, not a float: espp's BldcDriver::disable() stops the
  // MCPWM timer without forcing gate levels and the BSP has no enable pin, so
  // the three low-side FETs stay on and the windings are shorted (review
  // R2-05). Braking current is about back-EMF / winding impedance, no more
  // than what vlim already allows at stall, and the energy goes into the
  // windings rather than the supply. A true float needs an upstream espp
  // change (force the generators low on disable).
  void coast_locked() {
    if (motor_)
      motor_->disable();
    target_rpm_ = 0;
    set_rpm_ = 0;
    at_speed_ = false;
    uq_ = 0;
    if (mode_ != Mode::Fault)
      mode_ = Mode::Off;
  }

  // No allocation, no printing: safe on the tick.
  void set_fault_state(FaultCode code, float v1, float v2) {
    fault_v1_ = v1;
    fault_v2_ = v2;
    fault_code_ = static_cast<int>(code);
    mode_ = Mode::Fault;
    fault_notice_ = true;
  }
  void fault_locked(FaultCode code, float v1, float v2) {
    coast_locked();
    set_fault_state(code, v1, v2);
  }

  // Called without mutex_ (the calibration task may be inside BldcMotor's
  // alignment). Disabling the driver makes every further set_pwm a no-op.
  void abort_calibration() {
    cal_abort_ = true;
    if (driver_)
      driver_->disable();
  }

  bool cal_loop(std::mutex &, std::condition_variable &) {
    {
      std::unique_lock<std::mutex> lk(cal_m_);
      cal_cv_.wait_for(lk, std::chrono::milliseconds(200), [this] { return cal_requested_.load(); });
    }
    if (!cal_requested_)
      return false;
    cal_requested_ = false;
    cal_running_ = true;

    CalResult r;
    // A failed or aborted run puts back the calibration that was in force.
    const bool had_cal = calibrated_;
    const float prev_zero = motor_->zero_electric_angle();
    const int prev_dir = motor_->sensor_direction();
    // mode_ is Calibrating (set under mutex_ by start_calibration), so neither
    // the tick nor spin/open_loop touch motor_ until this task hands it back.
    if (!cal_abort_) {
      // set_pwm warns on every call once a stop has disabled the driver
      // mid-alignment; keep that from flooding the console.
      driver_->set_log_level(espp::Logger::Verbosity::ERROR);
      motor_->set_align_voltage(valign_);
      motor_->forget_calibration();
      motor_->initialize(); // enable, align (prints the PP check), disable
      driver_->set_log_level(espp::Logger::Verbosity::WARN);
    }
    {
      std::lock_guard<std::mutex> lk(mutex_);
      motor_->disable();
      auto restore = [&]() {
        motor_->forget_calibration();
        calibrated_ = false;
        if (had_cal) {
          motor_->restore_calibration(prev_zero, prev_dir);
          calibrated_ = true;
        }
      };
      if (cal_abort_) {
        r.aborted = true;
        r.why = "aborted by stop";
        restore();
      } else if (motor_->ready()) {
        r.ok = true;
        r.zero_electric = motor_->zero_electric_angle();
        r.sensor_dir = motor_->sensor_direction();
        sdir_ = r.sensor_dir == 0 ? 1 : r.sensor_dir;
        calibrated_ = true;
      } else {
        r.why = "alignment failed (no movement seen: check phases, encoder gap, valign)";
        restore();
      }
      r.kept_previous = !r.ok && calibrated_;
      // hand back with every value the console set meanwhile (apply_settings
      // skipped the motor while this task owned it; review R2-06)
      motor_->set_velocity_gains(kp_, ki_);
      motor_->set_align_voltage(valign_);
      motor_->set_voltage_limit(vlim_);
      if (mode_ != Mode::Fault) // a fault latched during the run stays latched
        mode_ = Mode::Off;
      cal_running_ = false;
    }
    {
      std::lock_guard<std::mutex> lk(result_m_);
      cal_result_ = std::move(r);
    }
    return false;
  }

  float filter_rpm(float raw) {
    // First-order low pass, Tf seconds (SimpleFOC LowPassFilter equivalent).
    const float dt = 1.0f / CONFIG_MM_FOC_HZ;
    const float tf = tf_.load();
    const float a = tf > 0 ? dt / (tf + dt) : 1.0f;
    rpm_lp_ += a * (raw - rpm_lp_);
    return rpm_lp_;
  }

  void tick() {
    const int64_t t0 = esp_timer_get_time();
    const float dt = 1.0f / CONFIG_MM_FOC_HZ;
    std::error_code ec;
    encoder_->update(ec);
    const bool enc_ok = !ec;
    if (!enc_ok)
      enc_errors_++;
    enc_err_run_ = enc_ok ? 0 : enc_err_run_ + 1;
    // motor frame: the encoder's rpm times the calibrated sensor direction
    encoder_rpm_ = sdir_.load() * encoder_->get_rpm();

    // A stop that lands between cal_loop's abort check and BldcDriver::enable()
    // finds the driver not yet enabled, so its disable() is a no-op. Re-assert
    // it here: a missed abort lasts at most one tick (review R1-01). Keyed on
    // cal_running_, not the mode: a fault latched mid-run sets mode Fault while
    // the calibration task is still inside BldcMotor::initialize().
    if (cal_running_ && cal_abort_ && driver_->is_enabled()) {
      driver_->disable();
      return;
    }
    if (mode_ != Mode::Closed && mode_ != Mode::OpenLoop)
      return;

    std::unique_lock<std::mutex> lk(mutex_, std::try_to_lock);
    if (!lk.owns_lock()) {
      lock_skips_++;
      return;
    }
    const Mode m = mode_.load(); // re-read under the lock
    if (m != Mode::Closed && m != Mode::OpenLoop)
      return;

    if (m == Mode::Closed && enc_err_run_ > CONFIG_MM_FOC_HZ / 20) {
      fault_locked(FaultCode::Encoder, 0, 0);
      return;
    }

    // slew the setpoint toward the target; a stop (target 0) uses the stop
    // band and deadline from stop_rule.hpp, never the operator's `fw ramp`
    float set = set_rpm_.load();
    const float tgt = target_rpm_.load();
    const bool stopping = tgt == 0.0f;
    stop_elapsed_s_ = stopping ? stop_elapsed_s_ + dt : 0.0f;
    set = stoprule::slew(set, tgt, stoprule::rate(ramp_.load(), stopping), dt);
    set_rpm_ = set;

    motor_->move(sign_.load() * set * espp::RPM_TO_RADS);
    motor_->loop_foc();
    uq_ = motor_->uq();

    const float rpm_now = rpm();
    const float tol = tol_.load();
    // at-speed: setpoint has arrived and the wheel holds the band for 300 ms
    if (m == Mode::Closed && set == tgt && tgt != 0 && std::fabs(rpm_now - set) < tol) {
      if (in_band_ticks_ < CONFIG_MM_FOC_HZ * 3 / 10)
        in_band_ticks_++;
      else
        at_speed_ = true;
    } else if (std::fabs(rpm_now - set) > 2 * tol || set != tgt || tgt == 0) {
      in_band_ticks_ = 0;
      at_speed_ = false;
    }

    // guards (closed loop only: open loop has no trustworthy speed)
    if (m == Mode::Closed) {
      if (std::fabs(rpm_now) > max_rpm_.load() * 1.2f) {
        fault_locked(FaultCode::Overspeed, rpm_now, 0);
        return;
      }
      // stall / wrong direction: commanded >= 1000 rpm, wheel under 20 % of it for 1.5 s
      if (std::fabs(set) >= 1000 && rpm_now * set < 0.2f * set * set) {
        stall_us_ += static_cast<int64_t>(dt * 1e6f);
        if (stall_us_ > 1500000) {
          fault_locked(FaultCode::Stall, set, rpm_now);
          return;
        }
      } else {
        stall_us_ = 0;
      }
    }

    // release the bridge once the wheel has nearly stopped, or at the stop
    // deadline whatever it is doing (review R2-01)
    if (stoprule::release(stopping, stop_elapsed_s_, set, rpm_now, m == Mode::OpenLoop))
      coast_locked();

    if (esp_timer_get_time() - t0 > static_cast<int64_t>(dt * 1e6f * 0.8f))
      overruns_++;
  }

  espp::Logger logger_;
  std::shared_ptr<Driver> driver_;
  std::unique_ptr<espp::Spi> spi_;
  std::shared_ptr<espp::Spi::Device> spi_dev_;
  std::shared_ptr<Encoder> encoder_;
  std::shared_ptr<FocMotor> motor_;
  std::unique_ptr<espp::HighResolutionTimer> timer_;
  std::unique_ptr<espp::Task> cal_task_;
  std::mutex mutex_; ///< motor_ calls and mode transitions

  std::atomic<bool> ok_{false};
  std::atomic<Mode> mode_{Mode::Off};
  mutable std::mutex fault_m_;
  std::string fault_text_; ///< FaultCode::External only
  std::atomic<int> fault_code_{0};
  std::atomic<float> fault_v1_{0}, fault_v2_{0};
  std::atomic<bool> fault_notice_{false};

  // calibration hand-off
  std::mutex cal_m_;
  std::condition_variable cal_cv_;
  std::atomic<bool> cal_requested_{false}, cal_abort_{false};
  std::atomic<bool> cal_running_{false}; ///< cal task owns motor_ (from request to hand-back)
  std::mutex result_m_;
  std::optional<CalResult> cal_result_;

  // settings cached for the tick (written by apply_settings on the console task)
  std::atomic<float> tf_{0.01f}, ramp_{1500.0f}, tol_{200.0f}, max_rpm_{7000.0f};
  std::atomic<float> kp_{0.1f}, ki_{2.0f};
  std::atomic<float> vlim_{4.0f}, vopen_{2.0f}, valign_{1.0f};
  std::atomic<int> sign_{1}, sdir_{1};
  std::atomic<bool> calibrated_{false};

  // state shared with readers
  std::atomic<float> target_rpm_{0}, set_rpm_{0}, uq_{0};
  std::atomic<float> encoder_rpm_{0}; ///< motor frame (sensor direction applied), before `sign`
  std::atomic<bool> at_speed_{false};
  std::atomic<uint32_t> enc_errors_{0}, overruns_{0}, lock_skips_{0};

  // tick-only state
  float rpm_lp_{0};
  int enc_err_run_{0};
  int in_band_ticks_{0};
  int64_t stall_us_{0};
  float stop_elapsed_s_{0}; ///< time with target 0 while driving
};

} // namespace mml
