#pragma once

// Joint angle <-> bus-servo count mapping. Pure math, host-tested
// (test/host/test_joints.cpp).
//
//   counts = zero + dir * joint_deg * ratio / 0.24
//
// `ratio` is servo degrees per joint degree, from the gearing in
// mm-launch-hw/v2/blender/params.py:
//   pan    pinion 36T : hub 36T             -> 1.0   (external mesh: dir -1)
//   tilt   horn on the tilt axis            -> 1.0   (dir +1)
//   feed   pinion 30T : disc ring 44T       -> 44/30 (external mesh: dir -1;
//          disc +/-60 = servo -/+88, DESIGN_LOG "Pinion")
// `zero` is the count read with the joint at its 0 (set by hand with
// `servo zero`), and `dir` can be flipped with `servo dir` if the horn went on
// the other way.

#include <algorithm>
#include <cmath>
#include <cstdint>

namespace joints {

inline constexpr float kDegPerCount = 240.0f / 1000.0f;

struct JointMap {
  float ratio{1.0f};  ///< servo deg per joint deg
  int dir{1};         ///< +1 or -1
  int zero{500};      ///< servo counts at joint 0
  float min_deg{-90}; ///< joint soft limits
  float max_deg{90};

  float clamp(float joint_deg) const { return std::clamp(joint_deg, min_deg, max_deg); }

  /// Joint degrees (clamped to the soft limits) to servo counts (clamped to 0..1000).
  uint16_t to_counts(float joint_deg) const {
    const float c = zero + dir * clamp(joint_deg) * ratio / kDegPerCount;
    return static_cast<uint16_t>(std::clamp(std::lround(c), 0L, 1000L));
  }

  /// Servo counts to joint degrees (not clamped: a read-back may sit outside).
  float to_deg(int counts) const {
    return static_cast<float>(counts - zero) * kDegPerCount / (static_cast<float>(dir) * ratio);
  }

  /// True if both soft limits map inside the servo's 0..1000 travel, i.e. the
  /// zero leaves room for the whole joint range.
  bool range_fits() const {
    const float a = zero + dir * min_deg * ratio / kDegPerCount;
    const float b = zero + dir * max_deg * ratio / kDegPerCount;
    return std::min(a, b) >= 0.0f && std::max(a, b) <= 1000.0f;
  }
};

/// Move time for a joint step at `deg_per_s`, floored so the board always
/// gets a non-zero interpolation window.
inline uint16_t move_time_ms(float from_deg, float to_deg, float deg_per_s, uint16_t floor_ms = 40) {
  if (deg_per_s <= 0)
    return floor_ms;
  const float ms = std::fabs(to_deg - from_deg) / deg_per_s * 1000.0f;
  return static_cast<uint16_t>(std::clamp(ms, static_cast<float>(floor_ms), 30000.0f));
}

} // namespace joints
