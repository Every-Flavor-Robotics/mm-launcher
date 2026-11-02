// Host tests for the flywheel stop rule (review R2-01).
#include <cmath>
#include <cstdio>

#include "stop_rule.hpp"

using namespace stoprule;

static int failures = 0;
#define CHECK(cond)                                                                                \
  do {                                                                                             \
    if (!(cond)) {                                                                                 \
      std::printf("FAIL %s:%d  %s\n", __FILE__, __LINE__, #cond);                                  \
      failures++;                                                                                  \
    }                                                                                              \
  } while (0)

// Simulate the 4 kHz tick from `rpm0` with a stop at t=0. The wheel follows
// the setpoint with `lag` (0 = perfectly, 1 = not at all: PI saturated or no
// feedback). Returns the time at which the drive is released.
static float stop_time(float rpm0, float ramp, float lag, bool open_loop = false) {
  const float dt = 1.0f / 4000.0f;
  float set = rpm0, rpm = rpm0, t = 0;
  while (t < 60.0f) {
    set = slew(set, 0.0f, rate(ramp, true), dt);
    rpm = lag * rpm + (1.0f - lag) * set;
    t += dt;
    if (release(true, t, set, rpm, open_loop))
      return t;
  }
  return 1e9f;
}

int main() {
  // The stop decel is held in [2000, 3000] whatever fw ramp says.
  CHECK(rate(50, true) == kStopDecelMin);
  CHECK(rate(200, true) == kStopDecelMin);
  CHECK(rate(2500, true) == 2500);
  CHECK(rate(20000, true) == kStopDecelMax);
  // ...but setpoint changes keep the operator's ramp.
  CHECK(rate(50, false) == 50);
  CHECK(rate(20000, false) == 20000);

  // Review R2-01 scenario: fw ramp 200, 6000 rpm, Esc. Was 30 s; now about 3 s.
  const float t200 = stop_time(6000, 200, 0.0f);
  CHECK(t200 <= 3.05f);
  // Worst ramp (50 rpm/s) from max_rpm 7000: bounded by the 3.5 s ramp.
  CHECK(stop_time(7000, 50, 0.0f) <= 3.55f);
  // A fast ramp is capped for stops: 6000 rpm at 3000 rpm/s takes 2 s, not 0.3 s.
  const float tfast = stop_time(6000, 20000, 0.0f);
  CHECK(tfast >= 1.95f && tfast <= 2.05f);
  // A wheel that does not follow (PI saturated, bad encoder) is released at the deadline.
  const float tstuck = stop_time(6000, 1500, 1.0f);
  CHECK(std::fabs(tstuck - kStopDeadlineS) < 0.001f);
  // Open loop releases as soon as the setpoint reaches 0.
  CHECK(stop_time(3000, 50, 1.0f, true) <= 1.55f);
  // Every stop, any ramp, any wheel: released within the deadline.
  for (float ramp : {50.0f, 200.0f, 1500.0f, 20000.0f})
    for (float lag : {0.0f, 0.5f, 0.999f, 1.0f})
      CHECK(stop_time(7000, ramp, lag) <= kStopDeadlineS + 0.001f);

  // No release while there is a target, however long.
  CHECK(!release(false, 100.0f, 0.0f, 0.0f, false));
  // Not released at set 0 while the wheel still turns fast (closed loop)...
  CHECK(!release(true, 1.0f, 0.0f, 800.0f, false));
  // ...released once it is slow.
  CHECK(release(true, 1.0f, 0.0f, 100.0f, false));

  // slew basics
  CHECK(slew(0, 1000, 1000, 0.5f) == 500);
  CHECK(slew(1000, 0, 1000, 2.0f) == 0);
  CHECK(slew(-1000, 0, 1000, 0.25f) == -750);

  std::printf("%s: stop rule (%d failures)\n", failures ? "FAIL" : "PASS", failures);
  return failures ? 1 : 0;
}
