// M&M launcher firmware. MotorGo Axis (ESP32-S3).
//
//   flywheel  XTEAM 3674 + Plink MT6701, voltage-mode FOC     (flywheel.hpp)
//   turret    pan / tilt / feeder Hiwonder bus servos          (turret.hpp)
//   tip guard onboard IMU: stop everything if the base tips    (tip_guard.hpp)
//   link      WebUSB + CDC: console, telemetry, OTA, core dump (demo_link.hpp)
//
// Every console command answers with exactly one `ok ...` or `! ...` line
// (the panel uses that to know a command finished), optionally preceded by
// `# ...` info and `@kind {json}` state lines. See README.md for the table.
//
// Threads: g_settings belongs to the console task (this file's main loop).
// Everything another task needs is an atomic below or a copy held by the
// Flywheel / Turret objects (see settings.hpp).

#include <algorithm>
#include <atomic>
#include <charconv>
#include <cmath>
#include <chrono>
#include <cstdio>
#include <cstdlib>
#include <string>
#include <string_view>
#include <thread>
#include <vector>

#include "esp_timer.h"
#include "sdkconfig.h"

#include "format.hpp"
#include "logger.hpp"
#include "motorgo-axis.hpp"
#include "nvs.hpp"
#include "task.hpp"

#include "demo_link.hpp"
#include "flywheel.hpp"
#include "jsonf.hpp"
#include "settings.hpp"
#include "tip_guard.hpp"
#include "turret.hpp"

using namespace std::chrono_literals;

namespace {

mml::Settings g_settings; // console task only
std::unique_ptr<mml::Flywheel> g_fw;
std::unique_ptr<mml::Turret> g_turret;
std::unique_ptr<demo::DemoLink> g_link;
std::atomic<int64_t> g_last_line_us{0};
std::atomic<uint32_t> g_wd_ms{0};
std::atomic<bool> g_wd_tripped{false};

// ---- IMU tip guard state (imu task writes, everyone reads)
std::atomic<bool> g_imu_ok{false};
std::atomic<bool> g_tipped{false};
std::atomic<float> g_base_tilt{NAN};
// console -> imu task
std::atomic<bool> g_imu_guard_on{true};
std::atomic<float> g_imu_trip_deg{20.0f};
std::atomic<int> g_imu_level_req{0}; ///< 1 = requested, 2 = done ok, 3 = refused
std::atomic<float> g_imu_ref[3] = {0, 0, 0};

// ---------------------------------------------------------------- helpers

std::vector<std::string_view> split(std::string_view s) {
  std::vector<std::string_view> out;
  size_t i = 0;
  while (i < s.size()) {
    while (i < s.size() && (s[i] == ' ' || s[i] == '\t'))
      i++;
    size_t j = i;
    while (j < s.size() && s[j] != ' ' && s[j] != '\t')
      j++;
    if (j > i)
      out.push_back(s.substr(i, j - i));
    i = j;
  }
  return out;
}

bool to_f(std::string_view s, float &v) {
  std::string tmp(s);
  char *end = nullptr;
  v = std::strtof(tmp.c_str(), &end);
  return !tmp.empty() && end && *end == '\0' && std::isfinite(v);
}

bool to_i(std::string_view s, int &v) {
  auto r = std::from_chars(s.data(), s.data() + s.size(), v);
  return r.ec == std::errc() && r.ptr == s.data() + s.size();
}

void ok(std::string_view what) { fmt::print("ok {}\n", what); }
void err(std::string_view why) { fmt::print("! {}\n", why); }

int state_code() {
  if (g_fw->mode() == mml::Flywheel::Mode::Fault || g_turret->has_fault())
    return 6;
  if (g_turret->firing())
    return 5;
  switch (g_fw->mode()) {
  case mml::Flywheel::Mode::Off:
    return 0;
  case mml::Flywheel::Mode::Calibrating:
    return 1;
  case mml::Flywheel::Mode::OpenLoop:
    return 2;
  case mml::Flywheel::Mode::Closed:
    return g_fw->at_speed() ? 4 : 3;
  default:
    return 6;
  }
}

void print_status() {
  using jsonf::num;
  fmt::print("@status {{\"state\":{},\"flywheel\":\"{}\",\"rpm\":{},\"rpm_set\":{},\"target\":{},"
             "\"uq\":{},\"at_speed\":{},\"calibrated\":{},\"fw_ok\":{},\"fw_fault\":{},\"turret_fault\":{},"
             "\"firing\":{},\"shots\":{},\"servo_v\":{},\"bus_ok\":{},\"enc_errors\":{},"
             "\"foc_overruns\":{},\"foc_lock_skips\":{},\"wd_ms\":{},\"foc_hz\":{},"
             "\"imu\":{},\"base_tilt\":{},\"tipped\":{},\"tip_guard\":{}}}\n",
             state_code(), g_fw->mode_name(), num(g_fw->rpm(), 0), num(g_fw->setpoint(), 0),
             num(g_fw->target(), 0), num(g_fw->uq(), 2), g_fw->at_speed(), g_fw->calibrated(), g_fw->ok(),
             jsonf::str(g_fw->fault_reason()), jsonf::str(g_turret->fault()), g_turret->firing(),
             g_turret->shots(), num(g_turret->servo_volts(), 2), g_turret->bus_alive(),
             g_fw->encoder_errors(), g_fw->overruns(), g_fw->lock_skips(), g_wd_ms.load(),
             CONFIG_MM_FOC_HZ, g_imu_ok.load(), num(g_base_tilt.load(), 1), g_tipped.load(),
             g_imu_guard_on.load());
}

/// Stop everything that moves on its own. Lock-free on the flywheel side, so
/// the watchdog, the tip guard and OTA can call it from any task.
void stop_all() {
  g_turret->abort_fire();
  g_fw->stop();
}

/// Refuse anything that spins the wheel or feeds while the base is tipped.
bool tipped_refuse(std::string_view what) {
  if (!g_tipped)
    return false;
  err(fmt::format("{}: base is tipped {:.0f} deg (stand it up, then 'clear')", what, g_base_tilt.load()));
  return true;
}

constexpr const char *kHelp =
    "# system: help | status | stop | clear | wd <ms> | ping | save | cfg\n"
    "# flywheel: fw enc [s] | fw cal | fw cal clear | fw open <rpm> | fw spin <rpm> | fw stop\n"
    "#   fw gains <kp> <ki> [tf_s] | fw vlim <V> | fw vopen <V> | fw valign <V> | fw ramp <rpm_s>\n"
    "#   fw pp <n> | fw sign <1|-1> | fw tol <rpm>\n"
    "# turret: aim <pan> <tilt> [ms] | pan|tilt|feed <deg> [ms] | servo read\n"
    "#   servo unload [pan|tilt|feed|all] | servo zero <joint> | servo dir <joint> <1|-1>\n"
    "#   servo raw <id> <counts> [ms] | turret speed <deg_s> | vbat\n"
    "# fire: fire [n] | feed timing <stroke_ms> <dwell_ms> | feed tol <deg>\n"
    "# imu: imu | imu level | imu guard <on|off> | imu trip <deg>\n";

// ---------------------------------------------------------------- commands

void cmd_fw(const std::vector<std::string_view> &a) {
  auto &s = g_settings;
  std::string why;
  float f = 0, f2 = 0, f3 = 0;
  int i = 0;
  const auto sub = a.size() > 1 ? a[1] : std::string_view{};

  if (sub == "enc") {
    float secs = 1.0f;
    if (a.size() > 2 && !to_f(a[2], secs))
      return err("usage: fw enc [seconds]");
    secs = std::clamp(secs, 0.1f, 5.0f);
    auto st = g_fw->encoder_stats(secs);
    if (!g_fw->ok())
      return err("fw enc: flywheel not initialized");
    fmt::print("@enc {{\"deg\":{},\"std_deg\":{},\"rpm\":{},\"samples\":{},\"errors\":{}}}\n",
               jsonf::num(st.deg, 3), jsonf::num(st.std_deg, 4), jsonf::num(st.rpm, 1), st.samples,
               g_fw->encoder_errors());
    return ok("fw enc");
  }
  if (sub == "cal") {
    if (a.size() > 2 && a[2] == "clear") {
      if (!g_fw->forget_calibration(why))
        return err("fw cal clear: " + why);
      s.calibrated = false;
      s.zero_electric = 0;
      s.sensor_dir = 0;
      return ok("fw cal clear (run 'save' to keep it cleared)");
    }
    if (tipped_refuse("fw cal"))
      return;
    if (!g_fw->start_calibration(why))
      return err("fw cal: " + why);
    fmt::print("# aligning at {:.2f} V: the shaft turns about one electrical revolution each way. "
               "'stop' aborts.\n",
               s.valign);
    return ok("fw cal started (result follows as @cal)");
  }
  if (sub == "open" && a.size() > 2 && to_f(a[2], f)) {
    if (tipped_refuse("fw open"))
      return;
    g_wd_tripped = false;
    if (!g_fw->open_loop(f, why))
      return err("fw open: " + why);
    return ok(fmt::format("fw open {:.0f} rpm at {:.2f} V", std::clamp(f, -s.max_rpm, s.max_rpm), s.vopen));
  }
  if (sub == "spin" && a.size() > 2 && to_f(a[2], f)) {
    if (tipped_refuse("fw spin"))
      return;
    g_wd_tripped = false;
    if (!g_fw->spin(f, why))
      return err("fw spin: " + why);
    return ok(fmt::format("fw spin {:.0f} rpm", std::clamp(f, -s.max_rpm, s.max_rpm)));
  }
  if (sub == "stop") {
    stop_all();
    return ok("fw stop");
  }
  if (sub == "gains" && a.size() > 3 && to_f(a[2], f) && to_f(a[3], f2)) {
    s.kp = std::clamp(f, 0.0f, 10.0f);
    s.ki = std::clamp(f2, 0.0f, 100.0f);
    if (a.size() > 4 && to_f(a[4], f3))
      s.vel_tf = std::clamp(f3, 0.0f, 0.5f);
    g_fw->apply_settings(s);
    return ok(fmt::format("fw gains kp {:.4g} ki {:.4g} tf {:.4g}", s.kp, s.ki, s.vel_tf));
  }
  if (sub == "vlim" && a.size() > 2 && to_f(a[2], f)) {
    s.vlim = std::clamp(f, 0.2f, CONFIG_MM_SUPPLY_MV / 1000.0f * 0.5f);
    g_fw->apply_settings(s);
    return ok(fmt::format("fw vlim {:.2f} V", s.vlim));
  }
  if (sub == "vopen" && a.size() > 2 && to_f(a[2], f)) {
    s.vopen = std::clamp(f, 0.2f, 4.0f);
    g_fw->apply_settings(s);
    return ok(fmt::format("fw vopen {:.2f} V", s.vopen));
  }
  if (sub == "valign" && a.size() > 2 && to_f(a[2], f)) {
    s.valign = std::clamp(f, 0.2f, 3.0f);
    g_fw->apply_settings(s);
    return ok(fmt::format("fw valign {:.2f} V", s.valign));
  }
  if (sub == "ramp" && a.size() > 2 && to_f(a[2], f)) {
    s.ramp_rpm_s = std::clamp(f, 50.0f, 20000.0f);
    g_fw->apply_settings(s);
    return ok(fmt::format("fw ramp {:.0f} rpm/s", s.ramp_rpm_s));
  }
  if (sub == "tol" && a.size() > 2 && to_f(a[2], f)) {
    s.at_speed_tol = std::clamp(f, 20.0f, 2000.0f);
    g_fw->apply_settings(s);
    return ok(fmt::format("fw tol {:.0f} rpm", s.at_speed_tol));
  }
  if (sub == "pp" && a.size() > 2 && to_i(a[2], i) && i >= 1 && i <= 20) {
    s.pole_pairs = i;
    return ok(fmt::format("fw pp {} ('save' and reboot to apply, then 'fw cal')", i));
  }
  if (sub == "sign" && a.size() > 2 && to_i(a[2], i) && (i == 1 || i == -1)) {
    if (g_fw->mode() != mml::Flywheel::Mode::Off)
      return err("fw sign: flywheel must be off");
    s.sign = i;
    g_fw->apply_settings(s);
    return ok(fmt::format("fw sign {}", i));
  }
  err("usage: fw enc|cal|open|spin|stop|gains|vlim|vopen|valign|ramp|tol|pp|sign (see 'help')");
}

joints::JointMap &settings_map(mml::Joint j) {
  auto &s = g_settings;
  return j == mml::Joint::Pan ? s.pan : j == mml::Joint::Tilt ? s.tilt : s.feed;
}

void cmd_servo(const std::vector<std::string_view> &a) {
  std::string why;
  const auto sub = a.size() > 1 ? a[1] : std::string_view{};
  int i = 0, i2 = 0, i3 = 0;

  if (sub == "read") {
    if (!g_turret->read())
      return err("servo read: no reply from the controller board (wiring, baud, TX level?)");
    fmt::print("@servo {}\n", g_turret->servo_json());
    return ok("servo read");
  }
  if (sub == "unload") {
    std::vector<mml::Joint> js;
    if (a.size() < 3 || a[2] == "all")
      js = {mml::Joint::Pan, mml::Joint::Tilt, mml::Joint::Feed};
    else if (auto j = mml::parse_joint(a[2]))
      js = {*j};
    else
      return err("usage: servo unload [pan|tilt|feed|all]");
    if (!g_turret->unload(js))
      return err("servo unload: UART write failed");
    return ok("servo unload");
  }
  if (sub == "zero" && a.size() > 2) {
    auto j = mml::parse_joint(a[2]);
    if (!j)
      return err("usage: servo zero <pan|tilt|feed>");
    auto counts = g_turret->read_zero(*j, why);
    if (!counts)
      return err("servo zero: " + why);
    auto &m = settings_map(*j);
    m.zero = *counts;
    g_turret->set_joint(*j, m);
    if (!m.range_fits())
      fmt::print("# warning: with zero {} the {} range {:.0f}..{:.0f} runs past the servo's travel; "
                 "re-seat the horn one spline tooth\n",
                 m.zero, mml::joint_name(*j), m.min_deg, m.max_deg);
    return ok(fmt::format("servo zero {} = {} counts ('save' to keep)", mml::joint_name(*j), m.zero));
  }
  if (sub == "dir" && a.size() > 3) {
    auto j = mml::parse_joint(a[2]);
    if (!j || !to_i(a[3], i) || (i != 1 && i != -1))
      return err("usage: servo dir <pan|tilt|feed> <1|-1>");
    auto &m = settings_map(*j);
    m.dir = i;
    g_turret->set_joint(*j, m);
    return ok(fmt::format("servo dir {} {}", mml::joint_name(*j), i));
  }
  if (sub == "raw" && a.size() > 3 && to_i(a[2], i) && to_i(a[3], i2)) {
    if (a.size() > 4 && !to_i(a[4], i3))
      return err("usage: servo raw <id> <counts> [ms]");
    if (a.size() <= 4)
      i3 = 1000;
    if (i < 0 || i > 253 || i2 < 0 || i2 > 1000 || i3 < 0 || i3 > 30000)
      return err("servo raw: id 0..253, counts 0..1000, ms 0..30000");
    if (!g_turret->raw(static_cast<uint8_t>(i), static_cast<uint16_t>(i2), static_cast<uint16_t>(i3)))
      return err("servo raw: UART write failed");
    return ok(fmt::format("servo raw {} {} {}", i, i2, i3));
  }
  err("usage: servo read|unload|zero|dir|raw (see 'help')");
}

void cmd_imu(const std::vector<std::string_view> &a) {
  auto &s = g_settings;
  float f = 0;
  const auto sub = a.size() > 1 ? a[1] : std::string_view{};
  if (sub.empty()) {
    using jsonf::num;
    fmt::print("@imu {{\"ok\":{},\"base_tilt\":{},\"tipped\":{},\"guard\":{},\"trip_deg\":{},"
               "\"ref\":[{},{},{}]}}\n",
               g_imu_ok.load(), num(g_base_tilt.load(), 2), g_tipped.load(), g_imu_guard_on.load(),
               num(g_imu_trip_deg.load(), 1), num(g_imu_ref[0].load(), 3), num(g_imu_ref[1].load(), 3),
               num(g_imu_ref[2].load(), 3));
    return ok("imu");
  }
  if (sub == "level") {
    if (!g_imu_ok)
      return err("imu level: no IMU");
    g_imu_level_req = 1;
    for (int k = 0; k < 50 && g_imu_level_req == 1; k++)
      std::this_thread::sleep_for(10ms);
    const int r = g_imu_level_req.exchange(0);
    if (r != 2)
      return err("imu level: no steady gravity reading (hold the robot still)");
    s.imu_ref_x = g_imu_ref[0];
    s.imu_ref_y = g_imu_ref[1];
    s.imu_ref_z = g_imu_ref[2];
    return ok(fmt::format("imu level: reference ({:.3f}, {:.3f}, {:.3f}) g ('save' to keep)", s.imu_ref_x,
                          s.imu_ref_y, s.imu_ref_z));
  }
  if (sub == "guard" && a.size() > 2 && (a[2] == "on" || a[2] == "off")) {
    s.imu_guard = a[2] == "on";
    g_imu_guard_on = s.imu_guard; // the imu task's TipLatch trips or clears on its next sample
    return ok(fmt::format("imu guard {}", a[2]));
  }
  if (sub == "trip" && a.size() > 2 && to_f(a[2], f)) {
    s.imu_trip_deg = std::clamp(f, 5.0f, 45.0f);
    g_imu_trip_deg = s.imu_trip_deg;
    return ok(fmt::format("imu trip {:.1f} deg", s.imu_trip_deg));
  }
  err("usage: imu | imu level | imu guard <on|off> | imu trip <deg>");
}

void handle_line(std::string_view line) {
  const auto a = split(line);
  if (a.empty())
    return;
  const auto c = a[0];
  auto &s = g_settings;
  std::string why;
  float f = 0, f2 = 0;
  int i = 0, i2 = 0;

  if (c == "help") {
    fmt::print("{}", kHelp);
    return ok("help");
  }
  if (c == "ping")
    return ok("ping");
  if (c == "status") {
    print_status();
    return ok("status");
  }
  if (c == "cfg") {
    fmt::print("@cfg {}\n", s.to_json(g_wd_ms));
    return ok("cfg");
  }
  if (c == "stop") {
    stop_all();
    return ok("stop");
  }
  if (c == "clear") {
    if (tipped_refuse("clear"))
      return;
    if (!g_fw->clear_fault())
      return err("clear: a calibration is still finishing (about 3 s), try again");
    g_turret->clear_fault();
    g_wd_tripped = false;
    return ok("clear");
  }
  if (c == "wd" && a.size() > 1 && to_i(a[1], i) && i >= 0) {
    g_wd_ms = static_cast<uint32_t>(std::min(i, 60000));
    g_wd_tripped = false;
    return ok(fmt::format("wd {} ms", g_wd_ms.load()));
  }
  if (c == "save") {
    std::error_code ec;
    if (!s.save(ec))
      return err("save: NVS write failed: " + ec.message());
    return ok("save");
  }
  if (c == "fw")
    return cmd_fw(a);
  if (c == "servo")
    return cmd_servo(a);
  if (c == "imu")
    return cmd_imu(a);
  if (c == "vbat") {
    auto mv = g_turret->battery_mv();
    if (!mv)
      return err("vbat: no reply from the controller board");
    return ok(fmt::format("vbat {:.2f} V", *mv / 1000.0f));
  }
  if (c == "aim" && a.size() > 2 && to_f(a[1], f) && to_f(a[2], f2)) {
    if (a.size() > 3 && !to_i(a[3], i))
      return err("usage: aim <pan> <tilt> [ms]");
    if (!g_turret->aim(f, f2, a.size() > 3 ? std::clamp(i, 0, 30000) : -1, s.aim_speed, why))
      return err("aim: " + why);
    return ok(fmt::format("aim {:.1f} {:.1f}", s.pan.clamp(f), s.tilt.clamp(f2)));
  }
  if (auto j = mml::parse_joint(c); j && a.size() > 1 && to_f(a[1], f)) {
    if (a.size() > 2 && !to_i(a[2], i))
      return err(fmt::format("usage: {} <deg> [ms]", c));
    if (*j == mml::Joint::Feed && tipped_refuse("feed"))
      return;
    if (!g_turret->move(*j, f, a.size() > 2 ? std::clamp(i, 0, 30000) : -1, s.aim_speed, why))
      return err(fmt::format("{}: {}", c, why));
    return ok(fmt::format("{} {:.1f}", c, settings_map(*j).clamp(f)));
  }
  if (c == "turret" && a.size() > 2 && a[1] == "speed" && to_f(a[2], f)) {
    s.aim_speed = std::clamp(f, 5.0f, 600.0f);
    return ok(fmt::format("turret speed {:.0f} deg/s", s.aim_speed));
  }
  if (c == "fire") {
    i = 1;
    if (a.size() > 1 && !to_i(a[1], i))
      return err("usage: fire [n]");
    if (tipped_refuse("fire"))
      return;
    const mml::Turret::FireParams p{.open_deg = s.feed_open_deg,
                                    .stroke_ms = s.stroke_ms,
                                    .dwell_ms = s.dwell_ms,
                                    .tol_deg = s.feed_tol_deg,
                                    .gap_ms = s.shot_gap_ms,
                                    .rpm_tol = s.at_speed_tol};
    if (!g_turret->fire(i, p, why))
      return err("fire: " + why);
    return ok(fmt::format("fire {}", std::clamp(i, 1, 20)));
  }
  if (c == "feed" && a.size() > 3 && a[1] == "timing" && to_i(a[2], i) && to_i(a[3], i2)) {
    s.stroke_ms = std::clamp(i, 50, 3000);
    s.dwell_ms = std::clamp(i2, 0, 3000);
    return ok(fmt::format("feed timing {} {}", s.stroke_ms, s.dwell_ms));
  }
  if (c == "feed" && a.size() > 2 && a[1] == "tol" && to_f(a[2], f)) {
    s.feed_tol_deg = std::clamp(f, 1.0f, 60.0f);
    return ok(fmt::format("feed tol {:.1f}", s.feed_tol_deg));
  }
  err(fmt::format("unknown command '{}' (try 'help')", line));
}

/// Console task, idle path: pick up a finished calibration.
void poll_calibration() {
  auto r = g_fw->take_calibration_result();
  if (!r)
    return;
  auto &s = g_settings;
  bool saved = false;
  if (r->ok) {
    s.calibrated = true;
    s.zero_electric = r->zero_electric;
    s.sensor_dir = r->sensor_dir;
    std::error_code ec;
    saved = s.save_calibration(ec);
    fmt::print("# fw cal done: zero {:.4f} rad, dir {} ({})\n", r->zero_electric, r->sensor_dir,
               saved ? "saved" : "NVS write FAILED");
  } else {
    // A failed or aborted run leaves the previous calibration in force (and in
    // Settings / NVS) if there was one.
    if (!r->kept_previous)
      s.calibrated = false;
    // "! cal:" rather than "! fw cal:": this arrives asynchronously, and must
    // not complete some other pending `fw ...` command in the panel (R2-02)
    fmt::print("! cal: {}{}\n", r->why, r->kept_previous ? " (previous calibration kept)" : "");
  }
  fmt::print("@cal {{\"ok\":{},\"aborted\":{},\"kept_previous\":{},\"zero_electric\":{},"
             "\"sensor_dir\":{},\"saved\":{},\"why\":{}}}\n",
             r->ok, r->aborted, r->kept_previous, jsonf::num(r->zero_electric, 4), r->sensor_dir, saved,
             jsonf::str(r->why));
}

/// Console task, idle path: announce a flywheel fault (the FOC tick that
/// raises most of them must not print).
void poll_faults() {
  if (auto why = g_fw->take_fault_notice())
    fmt::print("! flywheel fault: {}\n", *why);
}

/// 50 Hz on the hidden I2C bus: base tilt from the onboard IMU.
bool imu_step(std::mutex &m, std::condition_variable &cv, tip::TipGuard &guard, tip::TipLatch &latch) {
  auto imu = espp::MotorGoAxis::get().imu();
  std::error_code ec;
  const auto a = imu->read_accelerometer(ec);
  if (!ec) {
    auto c = guard.config();
    if (c.trip_deg != g_imu_trip_deg) {
      c.trip_deg = g_imu_trip_deg;
      c.clear_deg = std::min(8.0f, c.trip_deg * 0.5f);
      guard.set_config(c);
    }
    const auto ev = guard.update({a.x, a.y, a.z}, 0.02f);
    if (guard.has_reference()) {
      g_base_tilt = guard.tilt_deg();
      const auto r = guard.reference();
      g_imu_ref[0] = r.x;
      g_imu_ref[1] = r.y;
      g_imu_ref[2] = r.z;
    }
    (void)ev; // the latch below is level-based: it sees every way tipped() changes
    if (g_imu_level_req == 1)
      g_imu_level_req = guard.level_here() ? 2 : 3;
    switch (latch.step(g_imu_guard_on, guard.tipped())) {
    case tip::TipLatch::Action::Trip:
      g_tipped = true;
      g_turret->abort_fire();
      g_fw->fault(fmt::format("TIPPED (base {:.0f} deg from level)", guard.tilt_deg()));
      fmt::print("! TIPPED: base {:.0f} deg from level, flywheel off\n", guard.tilt_deg());
      break;
    case tip::TipLatch::Action::Clear:
      g_tipped = false;
      fmt::print("# base level again ({:.0f} deg); 'clear' to re-arm\n", guard.tilt_deg());
      break;
    case tip::TipLatch::Action::None:
      break;
    }
  }
  std::unique_lock<std::mutex> lk(m);
  cv.wait_for(lk, 20ms);
  return false;
}

} // namespace

extern "C" void app_main(void) {
  espp::Logger logger({.tag = "mml", .level = espp::Logger::Verbosity::INFO});

  {
    std::error_code ec;
    espp::Nvs nvs;
    nvs.init(ec);
    if (ec)
      logger.error("NVS init failed: {}", ec.message());
  }
  g_settings.load();
  g_imu_guard_on = g_settings.imu_guard;
  g_imu_trip_deg = g_settings.imu_trip_deg;

  // USB first, so the console and OTA work even if the hardware below is not
  // connected yet. before_ota: flash writes stall anything running from flash,
  // so the bridge goes off first.
  g_link = std::make_unique<demo::DemoLink>(demo::DemoLink::Config{
      .product = "MM Launcher",
      .manufacturer = "assistivetech.dev",
      .serial = "mm-launcher-1",
      .pid = 0x0d50,
      .channels = {"rpm_set", "rpm", "uq", "pan_cmd", "pan", "tilt_cmd", "tilt", "feed_cmd", "feed",
                   "servo_v", "state", "shots", "base_tilt"},
      .before_ota =
          []() {
            if (g_turret)
              g_turret->abort_fire();
            if (g_fw)
              g_fw->coast();
            fmt::print("#ota: flywheel off\n");
          },
      .self_verify_after_s = 30,
      // Act on a WebUSB `stop` on the USB worker task, before it queues behind
      // whatever the console task is doing (review R1-14). stop_all() is
      // lock-free; the console still answers the queued line with `ok stop`.
      .on_console_line =
          [](std::string_view l) {
            while (!l.empty() && (l.back() == ' ' || l.back() == '\r' || l.back() == '\n'))
              l.remove_suffix(1);
            if ((l == "stop" || l == "fw stop") && g_fw && g_turret)
              stop_all();
          },
  });
  if (std::error_code ec; !g_link->start(ec))
    logger.error("USB link failed: {}", ec.message());

  g_fw = std::make_unique<mml::Flywheel>();
  if (!g_fw->init(g_settings))
    logger.error("flywheel init failed; turret and console still run");
  g_turret = std::make_unique<mml::Turret>(*g_fw);
  if (!g_turret->init(g_settings))
    logger.error("turret init failed");

  // Tip guard on the onboard IMU. Optional: without it everything else runs.
  static tip::TipGuard guard({.trip_deg = g_settings.imu_trip_deg,
                              .clear_deg = std::min(8.0f, g_settings.imu_trip_deg * 0.5f)});
  guard.set_reference({g_settings.imu_ref_x, g_settings.imu_ref_y, g_settings.imu_ref_z});
  static tip::TipLatch latch;
  std::unique_ptr<espp::Task> imu_task;
  if (espp::MotorGoAxis::get().initialize_imu()) {
    g_imu_ok = true;
    imu_task = espp::Task::make_unique({
        .callback = [](std::mutex &m, std::condition_variable &cv) { return imu_step(m, cv, guard, latch); },
        .task_config = {.name = "imu", .stack_size_bytes = 4 * 1024, .priority = 3},
    });
    imu_task->start();
  } else {
    logger.warn("IMU init failed: tip guard off");
  }

  // 50 Hz: telemetry samples and the host watchdog.
  auto stream = espp::Task::make_unique({
      .callback =
          [](std::mutex &m, std::condition_variable &cv) {
            using mml::Joint;
            const std::array<float, 13> sample{
                g_fw->setpoint(),
                g_fw->rpm(),
                g_fw->uq(),
                g_turret->cmd_deg(Joint::Pan),
                g_turret->read_deg(Joint::Pan),
                g_turret->cmd_deg(Joint::Tilt),
                g_turret->read_deg(Joint::Tilt),
                g_turret->cmd_deg(Joint::Feed),
                g_turret->read_deg(Joint::Feed),
                g_turret->servo_volts(),
                static_cast<float>(state_code()),
                static_cast<float>(g_turret->shots()),
                g_base_tilt.load(),
            };
            g_link->emit(sample);

            const uint32_t wd = g_wd_ms;
            const auto md = g_fw->mode();
            const bool moving = md == mml::Flywheel::Mode::Closed || md == mml::Flywheel::Mode::OpenLoop ||
                                md == mml::Flywheel::Mode::Calibrating || g_turret->firing();
            if (wd > 0 && moving && !g_wd_tripped &&
                esp_timer_get_time() - g_last_line_us.load() > static_cast<int64_t>(wd) * 1000) {
              g_wd_tripped = true;
              stop_all();
              fmt::print("! watchdog: no host line for {} ms, flywheel stopping\n", wd);
            }
            std::unique_lock<std::mutex> lk(m);
            cv.wait_for(lk, 20ms);
            return false;
          },
      .task_config = {.name = "stream", .stack_size_bytes = 6 * 1024, .priority = 2},
  });
  stream->start();

  fmt::print("#ready: MM launcher fw, FOC {} Hz, servo UART{} TX {} RX {}, IMU {}. 'help' for commands.\n",
             CONFIG_MM_FOC_HZ, CONFIG_MM_SERVO_UART_NUM, CONFIG_MM_SERVO_UART_TX,
             CONFIG_MM_SERVO_UART_RX, g_imu_ok ? "on" : "absent");

  std::string line;
  bool overflow = false;
  while (true) {
    const int ch = g_link->getc();
    if (ch < 0) {
      poll_calibration();
      poll_faults();
      std::this_thread::sleep_for(10ms);
      continue;
    }
    if (ch != '\n' && ch != '\r') {
      if (line.size() < 160)
        line.push_back(static_cast<char>(ch));
      else
        overflow = true;
      continue;
    }
    if (line.empty())
      continue;
    g_last_line_us = esp_timer_get_time();
    if (overflow)
      err("line too long (160 characters max)");
    else
      handle_line(line);
    line.clear();
    overflow = false;
  }
}
