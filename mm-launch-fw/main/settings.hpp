#pragma once

// Every tunable in one struct, persisted in NVS namespace "mml" by `save`.
// Defaults come from the design docs and the launch-rig bring-up plan
// (mm-launch-hw/test-prints/launch-rig/README.md, steps B3-B5). Floats are
// stored as their bit pattern in a u32, because NVS has no float type.
//
// Threading rule: a Settings object is read and written ONLY on the console
// task (app_main's loop). Other tasks never touch it: the flywheel tick reads
// atomics cached by Flywheel::apply_settings(), the turret keeps its own
// locked copy of the joint maps, a fire sequence runs on a snapshot taken when
// `fire` is accepted, and calibration results come back through
// Flywheel::take_calibration_result(), which the console task polls.

#include <algorithm>
#include <cmath>
#include <cstdint>
#include <cstring>
#include <string>
#include <system_error>

#include "format.hpp"
#include "sdkconfig.h"
#include "nvs_handle_espp.hpp"

#include "joint_map.hpp"

namespace mml {

struct Settings {
  // ---- flywheel (XTEAM XTI-3674 1900KV, Plink MT6701 on the rear shaft)
  int pole_pairs{2};          ///< 36xx inrunners are usually 4-pole; B3 measures it
  float kv{1900.0f};
  float vlim{4.0f};           ///< closed-loop q-voltage cap. 6000 rpm / 1900 KV ~ 3.2 V of back-EMF
  float vopen{2.0f};          ///< B4: open loop at 2 V
  float valign{1.0f};         ///< B3: align at 1-2 V, on a current-limited supply
  float kp{0.1f};             ///< B5 start: P 0.1 V per rad/s
  float ki{2.0f};             ///< B5 start: I 2 V per rad
  float vel_tf{0.01f};        ///< B5 start: velocity low-pass Tf 0.01 s
  float ramp_rpm_s{1500.0f};  ///< "a gentle ramp"
  float max_rpm{7000.0f};     ///< hard ceiling on any setpoint
  float at_speed_tol{200.0f}; ///< |rpm - setpoint| for fire permission
  int sign{1};                ///< +1: positive rpm is clockwise seen from +X (B3)
  bool calibrated{false};
  float zero_electric{0.0f};
  int sensor_dir{0};          ///< espp SensorDirection: 1 CW, -1 CCW, 0 unknown

  // ---- turret (Hiwonder bus servos behind the controller board)
  int id_pan{1}, id_tilt{2}, id_feed{3};
  joints::JointMap pan{.ratio = 1.0f, .dir = -1, .zero = 500, .min_deg = -90, .max_deg = 90};
  joints::JointMap tilt{.ratio = 1.0f, .dir = 1, .zero = 500, .min_deg = 0, .max_deg = 45};
  joints::JointMap feed{.ratio = 44.0f / 30.0f, .dir = -1, .zero = 500, .min_deg = -60, .max_deg = 60};
  float aim_speed{90.0f};     ///< deg/s for aim moves without an explicit time
  float feed_open_deg{60.0f}; ///< disc angle of a fire stroke (pockets sit at +/-60, DESIGN_LOG "Index")
  int stroke_ms{300};         ///< park -> open, and open -> park (servo moves ~88 deg each way)
  int dwell_ms{150};          ///< time at the open position for the candy to drop
  float feed_tol_deg{8.0f};   ///< read-back error that counts as a jam
  int shot_gap_ms{400};       ///< minimum time between strokes in a burst (rpm recovery)

  // ---- base tip guard (onboard IMU, tip_guard.hpp)
  bool imu_guard{true};
  float imu_trip_deg{20.0f};
  float imu_ref_x{0}, imu_ref_y{0}, imu_ref_z{0}; ///< 0,0,0 = auto-level at boot

  static constexpr const char *kNamespace = "mml";

  void load() {
    std::error_code ec;
    espp::NvsHandle h(kNamespace, ec);
    if (ec)
      return;
    auto gi = [&](const char *k, int &v) {
      int32_t x = v;
      std::error_code e;
      h.get(k, x, x, e);
      v = x;
    };
    auto gf = [&](const char *k, float &v) {
      uint32_t bits;
      std::memcpy(&bits, &v, 4);
      std::error_code e;
      h.get(k, bits, bits, e);
      std::memcpy(&v, &bits, 4);
    };
    auto gb = [&](const char *k, bool &v) {
      int x = v ? 1 : 0;
      gi(k, x);
      v = x != 0;
    };
    gi("pp", pole_pairs);
    gf("kv", kv);
    gf("vlim", vlim);
    gf("vopen", vopen);
    gf("valign", valign);
    gf("kp", kp);
    gf("ki", ki);
    gf("vtf", vel_tf);
    gf("ramp", ramp_rpm_s);
    gf("maxrpm", max_rpm);
    gf("tol", at_speed_tol);
    gi("sign", sign);
    gb("cal", calibrated);
    gf("zel", zero_electric);
    gi("sdir", sensor_dir);
    gi("idp", id_pan);
    gi("idt", id_tilt);
    gi("idf", id_feed);
    gi("pz", pan.zero);
    gi("pd", pan.dir);
    gi("tz", tilt.zero);
    gi("td", tilt.dir);
    gi("fz", feed.zero);
    gi("fd", feed.dir);
    gf("aspd", aim_speed);
    gf("fopen", feed_open_deg);
    gi("strk", stroke_ms);
    gi("dwel", dwell_ms);
    gf("ftol", feed_tol_deg);
    gi("sgap", shot_gap_ms);
    gb("imug", imu_guard);
    gf("imut", imu_trip_deg);
    gf("imux", imu_ref_x);
    gf("imuy", imu_ref_y);
    gf("imuz", imu_ref_z);
    sanitize();
  }

  /// Hold every limit to the same hard ceilings the console enforces, so a
  /// stale or corrupt NVS value cannot exceed them (S5; review R1-12).
  void sanitize() {
    auto fin = [](float v, float lo, float hi, float dflt) {
      return std::isfinite(v) ? std::clamp(v, lo, hi) : dflt;
    };
    const float supply = CONFIG_MM_SUPPLY_MV / 1000.0f;
    pole_pairs = std::clamp(pole_pairs, 1, 20);
    kv = fin(kv, 100.0f, 10000.0f, 1900.0f);
    vlim = fin(vlim, 0.2f, supply * 0.5f, 4.0f);
    vopen = fin(vopen, 0.2f, 4.0f, 2.0f);
    valign = fin(valign, 0.2f, 3.0f, 1.0f);
    kp = fin(kp, 0.0f, 10.0f, 0.1f);
    ki = fin(ki, 0.0f, 100.0f, 2.0f);
    vel_tf = fin(vel_tf, 0.0f, 0.5f, 0.01f);
    ramp_rpm_s = fin(ramp_rpm_s, 50.0f, 20000.0f, 1500.0f);
    max_rpm = fin(max_rpm, 500.0f, 7000.0f, 7000.0f);
    at_speed_tol = fin(at_speed_tol, 20.0f, 2000.0f, 200.0f);
    sign = sign < 0 ? -1 : 1;
    sensor_dir = sensor_dir < 0 ? -1 : sensor_dir > 0 ? 1 : 0;
    if (calibrated && (sensor_dir == 0 || !std::isfinite(zero_electric)))
      calibrated = false; // never let a half calibration run the direction sweep at boot
    for (auto *m : {&pan, &tilt, &feed}) {
      m->zero = std::clamp(m->zero, 0, 1000);
      m->dir = m->dir < 0 ? -1 : 1;
    }
    aim_speed = fin(aim_speed, 5.0f, 600.0f, 90.0f);
    feed_open_deg = fin(feed_open_deg, 20.0f, 60.0f, 60.0f);
    stroke_ms = std::clamp(stroke_ms, 50, 3000);
    dwell_ms = std::clamp(dwell_ms, 0, 3000);
    feed_tol_deg = fin(feed_tol_deg, 1.0f, 60.0f, 8.0f);
    shot_gap_ms = std::clamp(shot_gap_ms, 0, 10000);
    imu_trip_deg = fin(imu_trip_deg, 5.0f, 45.0f, 20.0f);
    for (float *r : {&imu_ref_x, &imu_ref_y, &imu_ref_z})
      if (!std::isfinite(*r))
        *r = 0;
  }

  /// Persist only the flywheel calibration (the auto-save after `fw cal` must
  /// not also commit unrelated unsaved tweaks; review R1-08).
  bool save_calibration(std::error_code &ec) const {
    espp::NvsHandle h(kNamespace, ec);
    if (ec)
      return false;
    uint32_t bits;
    std::memcpy(&bits, &zero_electric, 4);
    h.set("cal", static_cast<int32_t>(calibrated ? 1 : 0), ec);
    if (!ec)
      h.set("zel", bits, ec);
    if (!ec)
      h.set("sdir", static_cast<int32_t>(sensor_dir), ec);
    if (!ec)
      h.commit(ec);
    return !ec;
  }

  bool save(std::error_code &ec) const {
    espp::NvsHandle h(kNamespace, ec);
    if (ec)
      return false;
    auto si = [&](const char *k, int v) {
      if (!ec)
        h.set(k, static_cast<int32_t>(v), ec);
    };
    auto sf = [&](const char *k, float v) {
      uint32_t bits;
      std::memcpy(&bits, &v, 4);
      if (!ec)
        h.set(k, bits, ec);
    };
    si("pp", pole_pairs);
    sf("kv", kv);
    sf("vlim", vlim);
    sf("vopen", vopen);
    sf("valign", valign);
    sf("kp", kp);
    sf("ki", ki);
    sf("vtf", vel_tf);
    sf("ramp", ramp_rpm_s);
    sf("maxrpm", max_rpm);
    sf("tol", at_speed_tol);
    si("sign", sign);
    si("cal", calibrated ? 1 : 0);
    sf("zel", zero_electric);
    si("sdir", sensor_dir);
    si("idp", id_pan);
    si("idt", id_tilt);
    si("idf", id_feed);
    si("pz", pan.zero);
    si("pd", pan.dir);
    si("tz", tilt.zero);
    si("td", tilt.dir);
    si("fz", feed.zero);
    si("fd", feed.dir);
    sf("aspd", aim_speed);
    sf("fopen", feed_open_deg);
    si("strk", stroke_ms);
    si("dwel", dwell_ms);
    sf("ftol", feed_tol_deg);
    si("sgap", shot_gap_ms);
    si("imug", imu_guard ? 1 : 0);
    sf("imut", imu_trip_deg);
    sf("imux", imu_ref_x);
    sf("imuy", imu_ref_y);
    sf("imuz", imu_ref_z);
    if (!ec)
      h.commit(ec);
    return !ec;
  }

  std::string to_json(uint32_t watchdog_ms) const {
    return fmt::format(
        "{{\"pole_pairs\":{},\"kv\":{:.0f},\"vlim\":{:.2f},\"vopen\":{:.2f},\"valign\":{:.2f},"
        "\"kp\":{:.4g},\"ki\":{:.4g},\"tf\":{:.4g},\"ramp\":{:.0f},\"max_rpm\":{:.0f},"
        "\"tol\":{:.0f},\"sign\":{},\"calibrated\":{},\"zero_electric\":{:.4f},\"sensor_dir\":{},"
        "\"ids\":[{},{},{}],"
        "\"pan\":{{\"zero\":{},\"dir\":{},\"min\":{:.0f},\"max\":{:.0f},\"fits\":{}}},"
        "\"tilt\":{{\"zero\":{},\"dir\":{},\"min\":{:.0f},\"max\":{:.0f},\"fits\":{}}},"
        "\"feed\":{{\"zero\":{},\"dir\":{},\"min\":{:.0f},\"max\":{:.0f},\"fits\":{}}},"
        "\"aim_speed\":{:.0f},\"feed_open\":{:.0f},\"stroke_ms\":{},\"dwell_ms\":{},"
        "\"feed_tol\":{:.1f},\"shot_gap_ms\":{},\"wd_ms\":{},"
        "\"imu\":{{\"guard\":{},\"trip_deg\":{:.1f},\"ref\":[{:.3f},{:.3f},{:.3f}]}}}}",
        pole_pairs, kv, vlim, vopen, valign, kp, ki, vel_tf, ramp_rpm_s, max_rpm, at_speed_tol,
        sign, calibrated, zero_electric, sensor_dir, id_pan, id_tilt, id_feed, pan.zero, pan.dir,
        pan.min_deg, pan.max_deg, pan.range_fits(), tilt.zero, tilt.dir, tilt.min_deg,
        tilt.max_deg, tilt.range_fits(), feed.zero, feed.dir, feed.min_deg, feed.max_deg,
        feed.range_fits(), aim_speed, feed_open_deg, stroke_ms, dwell_ms, feed_tol_deg,
        shot_gap_ms, watchdog_ms, imu_guard, imu_trip_deg, imu_ref_x, imu_ref_y, imu_ref_z);
  }
};

} // namespace mml
