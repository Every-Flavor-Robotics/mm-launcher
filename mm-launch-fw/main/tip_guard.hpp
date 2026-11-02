#pragma once

// Tip guard: is the base still standing the way it stood when it was levelled?
// Pure math, host-tested (test/host/test_tip_guard.cpp).
//
// The MotorGo's IMU is screwed to the base floor in some orientation nobody
// has measured, so there is no "down" axis to compare against. Instead the
// guard stores a reference gravity vector (`imu level`, or the average of the
// first samples after boot) and measures the angle between it and the current
// accelerometer reading. The CG analysis puts the static tip angle at about
// 30 deg with the jar full (v2 BOM, "stability"), so the default trip is 20.
//
// Samples whose magnitude is far from 1 g (an impact, the robot in free fall,
// a shot's recoil spike) say nothing about which way is down, so they neither
// trip nor clear the guard.

#include <algorithm>
#include <cmath>

namespace tip {

struct Vec3 {
  float x{0}, y{0}, z{0};
  float norm() const { return std::sqrt(x * x + y * y + z * z); }
};

/// Angle between two vectors in degrees; 0 if either is (near) zero.
inline float angle_deg(const Vec3 &a, const Vec3 &b) {
  const float na = a.norm(), nb = b.norm();
  if (na < 1e-6f || nb < 1e-6f)
    return 0.0f;
  const float c = std::clamp((a.x * b.x + a.y * b.y + a.z * b.z) / (na * nb), -1.0f, 1.0f);
  return std::acos(c) * 180.0f / 3.14159265f;
}

class TipGuard {
public:
  enum class Event { None, Tripped, Cleared };

  struct Config {
    float trip_deg{20.0f};  ///< tilt from the reference that trips
    float clear_deg{8.0f};  ///< tilt below which a trip clears (hysteresis)
    float hold_s{0.15f};    ///< tilt must persist this long to trip
    float min_g{0.7f};      ///< samples outside [min_g, max_g] are ignored
    float max_g{1.3f};
    float settle_s{0.5f};   ///< auto-reference: average this long after start...
    float settle_max_deg{3.0f}; ///< ...with every sample within this of the first (steady)
  };

  TipGuard() = default;
  explicit TipGuard(const Config &c)
      : cfg_(c) {}

  void set_config(const Config &c) { cfg_ = c; }
  const Config &config() const { return cfg_; }

  /// Use a stored reference (from NVS). A zero vector means "auto-level".
  void set_reference(const Vec3 &r) {
    if (r.norm() > 0.5f) {
      ref_ = r;
      have_ref_ = true;
    } else {
      have_ref_ = false;
      acc_ = {};
      acc_s_ = 0;
    }
  }
  bool has_reference() const { return have_ref_; }
  Vec3 reference() const { return ref_; }

  /// Feed one accelerometer sample (g) taken `dt` seconds after the last.
  Event update(const Vec3 &a, float dt) {
    const float g = a.norm();
    last_ = a;
    if (g < cfg_.min_g || g > cfg_.max_g)
      return Event::None; // not a gravity reading: hold state
    if (!have_ref_) {
      // Auto-level only from a steady pose: if the robot is being handled at
      // power-up, restart the window instead of averaging the motion into
      // "level" (review R1-11b). The guard does nothing until a reference exists.
      if (acc_s_ == 0.0f)
        acc_first_ = a;
      else if (angle_deg(a, acc_first_) > cfg_.settle_max_deg) {
        acc_ = {};
        acc_s_ = 0;
        acc_first_ = a;
      }
      acc_.x += a.x * dt;
      acc_.y += a.y * dt;
      acc_.z += a.z * dt;
      acc_s_ += dt;
      if (acc_s_ >= cfg_.settle_s) {
        ref_ = {acc_.x / acc_s_, acc_.y / acc_s_, acc_.z / acc_s_};
        have_ref_ = true;
      }
      return Event::None;
    }
    tilt_ = angle_deg(a, ref_);
    if (!tipped_) {
      over_s_ = tilt_ > cfg_.trip_deg ? over_s_ + dt : 0.0f;
      if (over_s_ >= cfg_.hold_s) {
        tipped_ = true;
        return Event::Tripped;
      }
    } else if (tilt_ < cfg_.clear_deg) {
      tipped_ = false;
      over_s_ = 0;
      return Event::Cleared;
    }
    return Event::None;
  }

  /// Make the latest sample the new reference ("this is level").
  bool level_here() {
    const float g = last_.norm();
    if (g < cfg_.min_g || g > cfg_.max_g)
      return false;
    ref_ = last_;
    have_ref_ = true;
    tipped_ = false;
    over_s_ = 0;
    tilt_ = 0;
    return true;
  }

  float tilt_deg() const { return tilt_; }
  bool tipped() const { return tipped_; }
  Vec3 last() const { return last_; }

private:
  Config cfg_{};
  Vec3 ref_{0, 0, 1};
  bool have_ref_{false};
  Vec3 acc_{};
  Vec3 acc_first_{};
  float acc_s_{0};
  Vec3 last_{};
  float tilt_{0};
  float over_s_{0};
  bool tipped_{false};
};

/// What the firmware does with the guard's state. Level-based rather than
/// edge-based, so every way the guard's `tipped()` can change is covered:
///   - the base tips past the trip angle            -> Trip
///   - it is stood back up (hysteresis clears)      -> Clear
///   - `imu level` re-references while tipped       -> Clear  (review R1-02)
///   - `imu guard on` while already tipped          -> Trip   (review R1-11)
///   - `imu guard off`                              -> Clear
/// Trip is where the caller latches the TIPPED flywheel fault; Clear only
/// lifts the refusal of spin/fire/clear, the fault itself still needs `clear`.
class TipLatch {
public:
  enum class Action { None, Trip, Clear };

  Action step(bool guard_on, bool guard_tipped) {
    const bool want = guard_on && guard_tipped;
    if (want == latched_)
      return Action::None;
    latched_ = want;
    return want ? Action::Trip : Action::Clear;
  }

  bool latched() const { return latched_; }

private:
  bool latched_{false};
};

} // namespace tip
