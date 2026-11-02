#pragma once

// How the flywheel stops. Pure, host-tested (test/host/test_stop_rule.cpp).
//
// A stop is any time the target is 0: `stop` / `fw stop` (panel Stop, Esc,
// gamepad B), the host watchdog, a FEED_JAM, `fw spin 0`. Its duration must
// not depend on `fw ramp`, which the operator tunes for setpoint changes and
// may set as low as 50 rpm/s (review R2-01). So a stop:
//
//   1. slews the setpoint down at a decel held inside [kStopDecelMin,
//      kStopDecelMax], whatever `fw ramp` says; and
//   2. releases the drive when the wheel is nearly stopped, or at the latest
//      kStopDeadlineS after the stop began, whatever the wheel is doing.
//
// Choosing the numbers (review R2-05 asked to weigh regeneration):
//   - A driven decel returns the wheel's energy to the 12 V bus. The PLA
//     flywheel is roughly 50 g at r 30 mm, I ~ 4.5e-5 kg m^2, so at 6000 rpm
//     (628 rad/s) it holds E = I w^2 / 2 ~ 9 J. Spread over 2-3 s that is
//     3-4.5 W on average, about 0.3-0.4 A back into 12 V, less the board's
//     own draw (MotorGo, servo board and buck idle about 0.2-0.5 A). A bench
//     supply that cannot sink current sees at most a small rise. Decelerating
//     faster than 3000 rpm/s doubles the return current for little gain, so
//     a fast `fw ramp` (up to 20000) is capped to 3000 for stops.
//   - 2000 rpm/s as the floor: from 6000 rpm (the top of the design range)
//     the setpoint reaches 0 in 3.0 s, and from max_rpm 7000 in 3.5 s.
//   - kStopDeadlineS 4 s: 3.5 s worst-case ramp plus 0.5 s for the wheel to
//     follow. After it the drive is released no matter what (PI saturated,
//     encoder lying, open loop with no feedback). On the MotorGo Axis a
//     released bridge is a three-phase short brake (BldcDriver::disable()
//     leaves the low-side FETs on), so the remaining energy goes into the
//     windings, not the supply. If the decel worked, little energy is left
//     by then.
//   - kReleaseRpm 150: below this the wheel is effectively stopped, and the
//     short brake does the rest.

#include <algorithm>
#include <cmath>

namespace stoprule {

inline constexpr float kStopDecelMin = 2000.0f; ///< rpm/s, stop decel floor
inline constexpr float kStopDecelMax = 3000.0f; ///< rpm/s, stop decel ceiling (regen)
inline constexpr float kStopDeadlineS = 4.0f;   ///< s, drive released at the latest
inline constexpr float kReleaseRpm = 150.0f;    ///< rpm, "stopped"

/// Slew rate for this tick: `fw ramp` for setpoint changes, the stop band for stops.
inline float rate(float ramp_rpm_s, bool stopping) {
  return stopping ? std::clamp(ramp_rpm_s, kStopDecelMin, kStopDecelMax) : ramp_rpm_s;
}

/// Move `set` toward `tgt` by at most `rate * dt`.
inline float slew(float set, float tgt, float rate_rpm_s, float dt) {
  const float step = rate_rpm_s * dt;
  return tgt > set ? std::min(tgt, set + step) : std::max(tgt, set - step);
}

/// Release the drive this tick? `elapsed_s` is the time since the target went
/// to 0 (ignored when not stopping). Open loop has no trustworthy speed, so it
/// releases as soon as the setpoint is down.
inline bool release(bool stopping, float elapsed_s, float set, float rpm, bool open_loop) {
  if (!stopping)
    return false;
  if (elapsed_s >= kStopDeadlineS)
    return true;
  return set == 0.0f && (open_loop || std::fabs(rpm) < kReleaseRpm);
}

} // namespace stoprule
