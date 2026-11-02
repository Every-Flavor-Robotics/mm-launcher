#pragma once

// Turret: pan, tilt and feeder Hiwonder bus servos behind the Hiwonder
// controller board (UART 9600 8N1), plus the fire sequence.
//
// Joint conventions (match the CAD joints in mm-launch-hw/v2/DESIGN_LOG.md):
//   pan   +/-90 deg, 0 = forward, positive = counter-clockwise seen from above
//   tilt  0..45 deg, 0 = level, positive = muzzle up (hard stops at -3 / +46)
//   feed  disc angle +/-60, 0 = park (solid over the outlet). One shot is
//         park -> +/-60 -> park, alternating sides, so each stroke passes
//         exactly one pocket over the outlet (DESIGN_LOG "Index").
//
// Each fire stroke is verified by reading the feeder back at the open
// position and again at park. A miss larger than `feed_tol_deg` is a jam:
// the feeder is unloaded (so it stops pushing on the candy), the flywheel
// spins down, and the turret latches FEED_JAM until `clear`.
//
// Threads: console calls (aim/move/fire/zero...) on the console task, the
// position poll on "servo_poll", the fire sequence on "fire". The bus driver
// serializes transactions. The joint maps and servo IDs live in a locked copy
// here (set_joint), never read from Settings off the console task; a fire
// sequence runs on a FireParams snapshot taken when `fire` is accepted.

#include <algorithm>
#include <array>
#include <atomic>
#include <chrono>
#include <cmath>
#include <condition_variable>
#include <mutex>
#include <optional>
#include <string>
#include <thread>

#include "driver/uart.h"
#include "esp_timer.h"
#include "sdkconfig.h"

#include "format.hpp"
#include "logger.hpp"
#include "motorgo-axis.hpp"
#include "task.hpp"

#include "flywheel.hpp"
#include "hiwonder_bus_board.hpp"
#include "joint_map.hpp"
#include "jsonf.hpp"
#include "settings.hpp"

namespace mml {

enum class Joint : int { Pan = 0, Tilt = 1, Feed = 2 };

inline const char *joint_name(Joint j) {
  return j == Joint::Pan ? "pan" : j == Joint::Tilt ? "tilt" : "feed";
}

inline std::optional<Joint> parse_joint(std::string_view s) {
  if (s == "pan")
    return Joint::Pan;
  if (s == "tilt")
    return Joint::Tilt;
  if (s == "feed" || s == "feeder")
    return Joint::Feed;
  return std::nullopt;
}

/// Manual `feed` moves beyond this disc angle can put a pocket over the
/// outlet and drop a candy, so they need the wheel at speed (S2). Calibration
/// uses `servo unload` + hand placement, and `servo raw` stays the explicit
/// bypass.
inline constexpr float kFeedFreeDeg = 15.0f;

class Turret {
public:
  /// What a fire sequence needs from Settings, copied when it starts.
  struct FireParams {
    float open_deg{60};
    int stroke_ms{300};
    int dwell_ms{150};
    float tol_deg{8};
    int gap_ms{400};
    float rpm_tol{200};
  };

  explicit Turret(Flywheel &fw)
      : fw_(fw)
      , logger_({.tag = "turret", .level = espp::Logger::Verbosity::INFO}) {
    for (auto &c : cmd_deg_)
      c.store(NAN);
    for (auto &r : read_deg_)
      r.store(NAN);
  }

  /// Console task, before anything else runs.
  bool init(const Settings &s) {
    ids_ = {static_cast<uint8_t>(s.id_pan), static_cast<uint8_t>(s.id_tilt),
            static_cast<uint8_t>(s.id_feed)};
    maps_ = {s.pan, s.tilt, s.feed};

    // The servo UART defaults to the Qwiic pins. The BSP brings the Qwiic I2C
    // bus up when the board singleton is constructed, so release it first.
    auto &board = espp::MotorGoAxis::get();
    const auto q = board.qwiic_pins();
    if (CONFIG_MM_SERVO_UART_TX == q.sda || CONFIG_MM_SERVO_UART_TX == q.scl ||
        CONFIG_MM_SERVO_UART_RX == q.sda || CONFIG_MM_SERVO_UART_RX == q.scl) {
      std::error_code ec;
      board.qwiic_i2c().deinit(ec);
      logger_.info("Qwiic I2C released for the servo UART");
    }

    const uart_config_t cfg = {
        .baud_rate = 9600,
        .data_bits = UART_DATA_8_BITS,
        .parity = UART_PARITY_DISABLE,
        .stop_bits = UART_STOP_BITS_1,
        .flow_ctrl = UART_HW_FLOWCTRL_DISABLE,
        .rx_flow_ctrl_thresh = 0,
        .source_clk = UART_SCLK_DEFAULT,
    };
    if (uart_driver_install(kPort, 512, 0, 0, nullptr, 0) != ESP_OK ||
        uart_param_config(kPort, &cfg) != ESP_OK ||
        uart_set_pin(kPort, CONFIG_MM_SERVO_UART_TX, CONFIG_MM_SERVO_UART_RX, UART_PIN_NO_CHANGE,
                     UART_PIN_NO_CHANGE) != ESP_OK) {
      logger_.error("servo UART init failed");
      return false;
    }

    bus_ = std::make_unique<hiwonder::BusServoBoard>(hiwonder::BusServoBoard::Config{
        .write = [](std::span<const uint8_t> d) {
          return uart_write_bytes(kPort, d.data(), d.size()) == static_cast<int>(d.size());
        },
        .read = [](std::span<uint8_t> d, std::chrono::milliseconds t) { return uart_read(d, t); },
        .timeout = std::chrono::milliseconds(CONFIG_MM_SERVO_REPLY_TIMEOUT_MS),
        .on_unsolicited =
            [](const hiwonder::Packet &p) {
              fmt::print("# servo board sent cmd {} ({} param bytes)\n", p.cmd, p.params.size());
            },
    });

    poll_task_ = espp::Task::make_unique({
        .callback = [this](std::mutex &m, std::condition_variable &cv) { return poll(m, cv); },
        .task_config = {.name = "servo_poll", .stack_size_bytes = 6 * 1024, .priority = 3},
    });
    poll_task_->start();
    fire_task_ = espp::Task::make_unique({
        .callback = [this](std::mutex &m, std::condition_variable &cv) { return fire_loop(m, cv); },
        .task_config = {.name = "fire", .stack_size_bytes = 8 * 1024, .priority = 4},
    });
    fire_task_->start();
    return true;
  }

  // ---------------------------------------------------------------- joint maps

  joints::JointMap joint(Joint j) const {
    std::lock_guard<std::mutex> lk(maps_m_);
    return maps_[static_cast<int>(j)];
  }
  /// Console task: after changing Settings' copy, push it here.
  void set_joint(Joint j, const joints::JointMap &m) {
    std::lock_guard<std::mutex> lk(maps_m_);
    maps_[static_cast<int>(j)] = m;
  }
  uint8_t id(Joint j) const { return ids_[static_cast<int>(j)]; }

  // ---------------------------------------------------------------- motion

  /// Move pan and tilt together. ms < 0: derive the time from `deg_per_s`.
  /// Allowed while firing (walk the shots across a target).
  bool aim(float pan_deg, float tilt_deg, int ms, float deg_per_s, std::string &why) {
    if (!bus_) {
      why = "servo UART not initialized";
      return false;
    }
    const auto pm = joint(Joint::Pan), tm = joint(Joint::Tilt);
    pan_deg = pm.clamp(pan_deg);
    tilt_deg = tm.clamp(tilt_deg);
    if (ms < 0)
      ms = std::max(auto_ms(Joint::Pan, pan_deg, deg_per_s), auto_ms(Joint::Tilt, tilt_deg, deg_per_s));
    const hiwonder::ServoTarget t[] = {{id(Joint::Pan), pm.to_counts(pan_deg)},
                                       {id(Joint::Tilt), tm.to_counts(tilt_deg)}};
    if (!bus_->move(t, static_cast<uint16_t>(ms))) {
      why = "UART write failed";
      return false;
    }
    cmd_deg_[0] = pan_deg;
    cmd_deg_[1] = tilt_deg;
    return true;
  }

  bool move(Joint j, float deg, int ms, float deg_per_s, std::string &why) {
    if (!bus_) {
      why = "servo UART not initialized";
      return false;
    }
    const auto m = joint(j);
    deg = m.clamp(deg);
    if (j == Joint::Feed) {
      if (firing_) {
        why = "firing";
        return false;
      }
      if (std::fabs(deg) > kFeedFreeDeg && !fw_.at_speed()) {
        why = fmt::format("|feed| > {:.0f} deg can drop a candy: spin the flywheel up first "
                          "(or use 'servo raw')",
                          kFeedFreeDeg);
        return false;
      }
    }
    if (ms < 0)
      ms = auto_ms(j, deg, deg_per_s);
    const hiwonder::ServoTarget t[] = {{id(j), m.to_counts(deg)}};
    if (!bus_->move(t, static_cast<uint16_t>(ms))) {
      why = "UART write failed";
      return false;
    }
    cmd_deg_[static_cast<int>(j)] = deg;
    return true;
  }

  bool raw(uint8_t servo_id, uint16_t counts, uint16_t ms) {
    if (!bus_)
      return false;
    const hiwonder::ServoTarget t[] = {{servo_id, counts}};
    return bus_->move(t, ms);
  }

  bool unload(std::span<const Joint> js) {
    if (!bus_)
      return false;
    std::array<uint8_t, 3> ids{};
    size_t n = 0;
    for (auto j : js) {
      if (n >= ids.size())
        break;
      ids[n++] = id(j);
      cmd_deg_[static_cast<int>(j)] = NAN; // limp: no command in force
    }
    return bus_->unload(std::span<const uint8_t>(ids.data(), n));
  }

  /// Read all three. Updates the read-back state. nullopt on a timeout.
  struct Reading {
    std::array<int, 3> counts;
    std::array<float, 3> deg;
    std::array<bool, 3> valid;
  };
  std::optional<Reading> read() {
    if (!bus_)
      return std::nullopt;
    const uint8_t ids[] = {id(Joint::Pan), id(Joint::Tilt), id(Joint::Feed)};
    auto pos = bus_->read_positions(ids);
    if (!pos)
      return std::nullopt;
    std::array<joints::JointMap, 3> maps;
    {
      std::lock_guard<std::mutex> lk(maps_m_);
      maps = maps_;
    }
    Reading r{};
    for (const auto &p : *pos)
      for (int j = 0; j < 3; j++)
        if (p.id == ids[j]) {
          r.counts[j] = p.position;
          r.deg[j] = maps[j].to_deg(p.position);
          r.valid[j] = true;
          read_counts_[j] = p.position;
          read_deg_[j] = r.deg[j];
        }
    last_read_us_ = esp_timer_get_time();
    return r;
  }

  /// Read the current position of `j` (hand-placed, unloaded) as its new
  /// zero. Returns the counts; the caller stores them in Settings and calls
  /// set_joint().
  std::optional<int> read_zero(Joint j, std::string &why) {
    auto r = read();
    const int k = static_cast<int>(j);
    if (!r || !r->valid[k]) {
      why = "no reply from the servo";
      return std::nullopt;
    }
    return r->counts[k];
  }

  std::optional<uint16_t> battery_mv() {
    if (!bus_)
      return std::nullopt;
    auto mv = bus_->battery_mv();
    if (mv)
      servo_mv_ = *mv;
    return mv;
  }

  // ---------------------------------------------------------------- fire

  bool fire(int n, const FireParams &p, std::string &why) {
    if (!bus_) {
      why = "servo UART not initialized";
      return false;
    }
    if (has_fault_) {
      why = "turret fault latched: " + fault() + " ('clear' first)";
      return false;
    }
    if (fw_.mode() == Flywheel::Mode::Fault) {
      why = "flywheel fault latched: " + fw_.fault_reason();
      return false;
    }
    if (firing_) {
      why = "already firing";
      return false;
    }
    if (!fw_.at_speed()) {
      why = fmt::format("flywheel not at speed ({}, {:.0f} of {:.0f} rpm)", fw_.mode_name(), fw_.rpm(),
                        fw_.target());
      return false;
    }
    {
      std::lock_guard<std::mutex> lk(fire_m_);
      params_ = p;
      abort_ = false;
      pending_ = std::clamp(n, 1, 20);
      requested_ = pending_.load();
      firing_ = true;
    }
    fire_cv_.notify_all();
    return true;
  }

  void abort_fire() {
    abort_ = true;
    pending_ = 0;
  }

  void clear_fault() {
    std::lock_guard<std::mutex> lk(fault_m_);
    fault_.clear();
    has_fault_ = false;
  }

  // ---- readouts (any task)
  float cmd_deg(Joint j) const { return cmd_deg_[static_cast<int>(j)].load(); }
  float read_deg(Joint j) const { return read_deg_[static_cast<int>(j)].load(); }
  int read_counts(Joint j) const { return read_counts_[static_cast<int>(j)].load(); }
  float servo_volts() const { return servo_mv_.load() / 1000.0f; }
  bool firing() const { return firing_; }
  uint32_t shots() const { return shots_; }
  bool has_fault() const { return has_fault_; }
  std::string fault() const {
    std::lock_guard<std::mutex> lk(fault_m_);
    return fault_;
  }
  size_t bus_timeouts() const { return bus_ ? bus_->timeouts() : 0; }
  bool bus_alive() const { return esp_timer_get_time() - last_read_us_ < 2000000; }

  std::string servo_json() const {
    auto j = [&](Joint jt) {
      const int k = static_cast<int>(jt);
      const bool seen = std::isfinite(read_deg_[k].load());
      return fmt::format("\"{}\":{{\"id\":{},\"counts\":{},\"deg\":{},\"cmd\":{},\"zero\":{}}}",
                         joint_name(jt), id(jt), seen ? std::to_string(read_counts_[k].load()) : "null",
                         jsonf::num(read_deg_[k].load(), 1), jsonf::num(cmd_deg_[k].load(), 1),
                         joint(jt).zero);
    };
    return fmt::format("{{{},{},{},\"servo_v\":{},\"timeouts\":{}}}", j(Joint::Pan), j(Joint::Tilt),
                       j(Joint::Feed), jsonf::num(servo_volts(), 2), bus_timeouts());
  }

private:
  static constexpr uart_port_t kPort = static_cast<uart_port_t>(CONFIG_MM_SERVO_UART_NUM);

  // Wait up to `timeout` for the first byte, then take whatever else is
  // already buffered (uart_read_bytes alone would sit out the whole timeout
  // unless the buffer filled).
  static size_t uart_read(std::span<uint8_t> d, std::chrono::milliseconds timeout) {
    size_t avail = 0;
    uart_get_buffered_data_len(kPort, &avail);
    if (avail == 0) {
      if (timeout.count() == 0)
        return 0;
      const int got = uart_read_bytes(kPort, d.data(), 1, pdMS_TO_TICKS(timeout.count()));
      if (got <= 0)
        return 0;
      uart_get_buffered_data_len(kPort, &avail);
      const size_t more = std::min(avail, d.size() - 1);
      const int rest = more ? uart_read_bytes(kPort, d.data() + 1, more, 0) : 0;
      return 1 + std::max(rest, 0);
    }
    const int got = uart_read_bytes(kPort, d.data(), std::min(avail, d.size()), 0);
    return got > 0 ? static_cast<size_t>(got) : 0;
  }

  int auto_ms(Joint j, float to_deg, float deg_per_s) const {
    float from = read_deg_[static_cast<int>(j)].load();
    if (std::isnan(from))
      from = cmd_deg_[static_cast<int>(j)].load();
    if (std::isnan(from))
      return 1000; // unknown start: move gently
    return joints::move_time_ms(from, to_deg, deg_per_s);
  }

  void latch_fault(const std::string &why) {
    {
      std::lock_guard<std::mutex> lk(fault_m_);
      fault_ = why;
    }
    has_fault_ = true;
  }

  // ~8 Hz position read-back, battery every 2 s. Paused while firing (the fire
  // sequence reads the feeder itself and needs the bus).
  bool poll(std::mutex &m, std::condition_variable &cv) {
    if (!firing_ && bus_) {
      read();
      if (++poll_n_ % 16 == 0)
        battery_mv();
      bus_->poll();
    }
    std::unique_lock<std::mutex> lk(m);
    cv.wait_for(lk, std::chrono::milliseconds(125));
    return false;
  }

  /// Anything that should end a stroke early: a stop, a latched turret fault,
  /// or a flywheel fault raised by the tick (overspeed, stall, encoder, tip).
  bool cut() const { return abort_ || has_fault_ || fw_.mode() == Flywheel::Mode::Fault; }

  void sleep_sampling(int ms, float &rpm_min, int64_t &t_min) {
    const int64_t end = esp_timer_get_time() + ms * 1000LL;
    while (esp_timer_get_time() < end && !cut()) {
      const float r = std::fabs(fw_.rpm());
      if (r < rpm_min) {
        rpm_min = r;
        t_min = esp_timer_get_time();
      }
      std::this_thread::sleep_for(std::chrono::milliseconds(5));
    }
  }

  void park_feeder(const joints::JointMap &fm, int ms) {
    const hiwonder::ServoTarget park[] = {{id(Joint::Feed), fm.to_counts(0)}};
    bus_->move(park, static_cast<uint16_t>(ms));
    cmd_deg_[2] = 0;
  }

  bool fire_loop(std::mutex &, std::condition_variable &) {
    FireParams p;
    {
      std::unique_lock<std::mutex> lk(fire_m_);
      fire_cv_.wait_for(lk, std::chrono::milliseconds(100), [this] { return pending_ > 0; });
      if (pending_ <= 0) {
        // an abort between fire() and this wake-up: nothing to do, and the
        // firing flag fire() set must not stay up (review R1-05)
        if (firing_.exchange(false))
          fmt::print("# fire done: 0 of {} shots, ended by stop\n", requested_);
        return false;
      }
      p = params_;
    }
    const int requested = requested_;
    int fired = 0;
    const char *why_end = nullptr;
    const auto fm = joint(Joint::Feed);

    // The feeder may never have been commanded since boot: park it first.
    if (std::isnan(cmd_deg_[2].load())) {
      park_feeder(fm, p.stroke_ms * 2);
      std::this_thread::sleep_for(std::chrono::milliseconds(p.stroke_ms * 2 + 100));
    }

    while (pending_ > 0 && !abort_) {
      if (!fw_.at_speed() || has_fault_) {
        fmt::print("! fire stopped: flywheel left speed ({}, {:.0f} rpm)\n", fw_.mode_name(), fw_.rpm());
        why_end = "flywheel left speed";
        break;
      }
      const int64_t t_start = esp_timer_get_time();
      const float rpm_set = std::fabs(fw_.setpoint());
      const float rpm_before = std::fabs(fw_.rpm());
      float rpm_min = rpm_before;
      int64_t t_min = t_start;
      const int dir = next_dir_;
      next_dir_ = -next_dir_;
      const float open = dir * std::fabs(p.open_deg);

      // park -> open
      const hiwonder::ServoTarget to_open[] = {{id(Joint::Feed), fm.to_counts(open)}};
      bus_->move(to_open, static_cast<uint16_t>(p.stroke_ms));
      cmd_deg_[2] = open;
      sleep_sampling(p.stroke_ms + p.dwell_ms, rpm_min, t_min);
      if (cut()) {
        // stopped or faulted mid-stroke: close the outlet, no jam verdict on a
        // cut-short move
        park_feeder(fm, p.stroke_ms);
        fmt::print("# fire cut short mid-stroke ({}): feeder parking\n", abort_ ? "stop" : "fault");
        why_end = abort_ ? "stop" : "fault";
        break;
      }
      float err_open = NAN;
      if (auto r = read(); r && r->valid[2])
        err_open = std::fabs(r->deg[2] - open);

      // open -> park
      park_feeder(fm, p.stroke_ms);
      sleep_sampling(p.stroke_ms + 60, rpm_min, t_min);
      if (cut()) {
        fmt::print("# fire cut short ({}): feeder parking\n", abort_ ? "stop" : "fault");
        why_end = abort_ ? "stop" : "fault";
        break;
      }
      float err_park = NAN;
      if (auto r = read(); r && r->valid[2])
        err_park = std::fabs(r->deg[2]);

      const float err = std::max(std::isnan(err_open) ? 999.0f : err_open,
                                 std::isnan(err_park) ? 999.0f : err_park);
      if (err > p.tol_deg) {
        const Joint fj[] = {Joint::Feed};
        unload(fj);
        fw_.stop();
        const std::string why =
            std::isnan(err_open) || std::isnan(err_park)
                ? std::string("FEED_JAM (no read-back from the feeder)")
                : fmt::format("FEED_JAM (open err {:.1f}, park err {:.1f} deg)", err_open, err_park);
        latch_fault(why);
        fmt::print("! {}: feeder unloaded, flywheel stopping\n", why);
        pending_ = 0;
        print_shot(dir, rpm_set, rpm_before, rpm_before - rpm_min, -1, err);
        why_end = "FEED_JAM";
        break;
      }

      // rpm recovery: back within the at-speed band, measured from the dip
      int recover_ms = -1;
      const int64_t recover_deadline = esp_timer_get_time() + 1500000;
      while (esp_timer_get_time() < recover_deadline && !cut()) {
        const float r = std::fabs(fw_.rpm());
        if (r < rpm_min) {
          rpm_min = r;
          t_min = esp_timer_get_time();
        }
        if (std::fabs(r - rpm_set) < p.rpm_tol && esp_timer_get_time() > t_min + 20000) {
          recover_ms = static_cast<int>((esp_timer_get_time() - t_min) / 1000);
          break;
        }
        std::this_thread::sleep_for(std::chrono::milliseconds(5));
      }
      shots_++;
      fired++;
      if (pending_ > 0)
        pending_--;
      print_shot(dir, rpm_set, rpm_before, rpm_before - rpm_min, recover_ms, err);

      const int64_t elapsed_ms = (esp_timer_get_time() - t_start) / 1000;
      if (pending_ > 0 && elapsed_ms < p.gap_ms)
        std::this_thread::sleep_for(std::chrono::milliseconds(p.gap_ms - elapsed_ms));
    }
    if (!why_end && abort_)
      why_end = "stop"; // stopped in the gap between shots (review R2-02)
    {
      std::lock_guard<std::mutex> lk(fire_m_);
      pending_ = 0;
      firing_ = false;
    }
    // Every sequence ends with exactly one closing line, so the panel's Fire
    // button never waits for a timeout.
    fmt::print("# fire done: {} of {} shots{}{}\n", fired, requested, why_end ? ", ended by " : "",
               why_end ? why_end : "");
    return false;
  }

  void print_shot(int dir, float rpm_set, float rpm_before, float dip, int recover_ms, float err) {
    fmt::print("@shot {{\"n\":{},\"dir\":{},\"rpm_set\":{:.0f},\"rpm_before\":{:.0f},\"dip_rpm\":{:.0f},"
               "\"recover_ms\":{},\"feed_err_deg\":{:.1f}}}\n",
               shots_.load(), dir, rpm_set, rpm_before, dip, recover_ms, err);
  }

  Flywheel &fw_;
  espp::Logger logger_;
  std::unique_ptr<hiwonder::BusServoBoard> bus_;
  std::unique_ptr<espp::Task> poll_task_, fire_task_;

  std::array<uint8_t, 3> ids_{1, 2, 3}; ///< set once in init, read-only after
  mutable std::mutex maps_m_;
  std::array<joints::JointMap, 3> maps_{};

  std::array<std::atomic<float>, 3> cmd_deg_;
  std::array<std::atomic<float>, 3> read_deg_;
  std::array<std::atomic<int>, 3> read_counts_{};
  std::atomic<uint16_t> servo_mv_{0};
  std::atomic<int64_t> last_read_us_{0};
  uint32_t poll_n_{0};

  std::mutex fire_m_;
  std::condition_variable fire_cv_;
  FireParams params_;
  std::atomic<int> pending_{0};
  int requested_{0}; ///< shots asked for by the last accepted fire (under fire_m_)
  std::atomic<bool> firing_{false}, abort_{false};
  std::atomic<uint32_t> shots_{0};
  int next_dir_{1}; ///< fire task only

  mutable std::mutex fault_m_;
  std::string fault_;
  std::atomic<bool> has_fault_{false};
};

} // namespace mml
