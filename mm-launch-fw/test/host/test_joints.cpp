// Host tests for the joint <-> servo-count mapping.
#include <cmath>
#include <cstdio>

#include "joint_map.hpp"

using joints::JointMap;

static int failures = 0;
#define CHECK(cond)                                                                                \
  do {                                                                                             \
    if (!(cond)) {                                                                                 \
      std::printf("FAIL %s:%d  %s\n", __FILE__, __LINE__, #cond);                                  \
      failures++;                                                                                  \
    }                                                                                              \
  } while (0)

static bool near(float a, float b, float tol = 0.25f) { return std::fabs(a - b) <= tol; }

int main() {
  // Pan: 1:1 external mesh, +/-90.
  JointMap pan{.ratio = 1.0f, .dir = -1, .zero = 500, .min_deg = -90, .max_deg = 90};
  CHECK(pan.to_counts(0) == 500);
  CHECK(pan.to_counts(90) == 125);  // 500 - 90 / 0.24
  CHECK(pan.to_counts(-90) == 875);
  CHECK(pan.to_counts(200) == 125); // clamped to the soft limit
  CHECK(near(pan.to_deg(125), 90));
  CHECK(pan.range_fits());

  // Feeder: disc +/-60 = servo -/+88 (DESIGN_LOG).
  JointMap feed{.ratio = 44.0f / 30.0f, .dir = -1, .zero = 500, .min_deg = -60, .max_deg = 60};
  const float servo_deg = (feed.to_counts(60) - 500) * joints::kDegPerCount;
  CHECK(near(servo_deg, -88.0f, 0.3f));
  CHECK(near(feed.to_deg(feed.to_counts(60)), 60.0f));
  CHECK(feed.range_fits());

  // A zero set too close to the end of travel no longer fits the range.
  JointMap shifted = feed;
  shifted.zero = 200;
  CHECK(!shifted.range_fits());

  // Tilt 0..45, direct.
  JointMap tilt{.ratio = 1.0f, .dir = 1, .zero = 450, .min_deg = 0, .max_deg = 45};
  CHECK(tilt.to_counts(-10) == 450); // below the stop clamps to 0 deg
  CHECK(tilt.to_counts(45) == 638);  // 450 + 187.5 rounds to 638
  CHECK(near(tilt.to_deg(638), 45.12f, 0.01f));

  // Move time.
  CHECK(joints::move_time_ms(0, 90, 180) == 500);
  CHECK(joints::move_time_ms(0, 1, 180) == 40); // floor
  CHECK(joints::move_time_ms(0, 10, 0) == 40);

  std::printf("%s: joint map (%d failures)\n", failures ? "FAIL" : "PASS", failures);
  return failures ? 1 : 0;
}
