// Host tests for the base tip guard.
#include <cmath>
#include <cstdio>

#include "tip_guard.hpp"

using tip::TipGuard;
using tip::Vec3;

static int failures = 0;
#define CHECK(cond)                                                                                \
  do {                                                                                             \
    if (!(cond)) {                                                                                 \
      std::printf("FAIL %s:%d  %s\n", __FILE__, __LINE__, #cond);                                  \
      failures++;                                                                                  \
    }                                                                                              \
  } while (0)

static Vec3 tilted(float deg) {
  const float r = deg * 3.14159265f / 180.0f;
  return {std::sin(r), 0.0f, std::cos(r)};
}

static TipGuard::Event run(TipGuard &g, Vec3 a, float secs, float dt = 0.02f) {
  TipGuard::Event last = TipGuard::Event::None;
  for (float t = 0; t < secs - 1e-6f; t += dt) {
    auto e = g.update(a, dt);
    if (e != TipGuard::Event::None)
      last = e;
  }
  return last;
}

int main() {
  CHECK(std::fabs(tip::angle_deg({0, 0, 1}, {1, 0, 0}) - 90.0f) < 0.01f);
  CHECK(std::fabs(tip::angle_deg({0, 0, 1}, tilted(30)) - 30.0f) < 0.01f);
  CHECK(tip::angle_deg({0, 0, 0}, {1, 0, 0}) == 0.0f);

  // Auto-reference: the board is mounted sideways (gravity on -y). After the
  // settle time the reference is -y, so "sideways" reads as level.
  TipGuard g;
  CHECK(!g.has_reference());
  CHECK(run(g, {0, -1, 0}, 0.6f) == TipGuard::Event::None);
  CHECK(g.has_reference());
  CHECK(run(g, {0, -1, 0}, 0.2f) == TipGuard::Event::None);
  CHECK(g.tilt_deg() < 0.5f);

  // R1-11b: handled at power-up. A swinging pose never becomes the reference;
  // once it is held steady for 0.5 s, that pose does.
  TipGuard hb;
  for (int k = 0; k < 100; k++) // 2 s of being waved about +/-20 deg
    hb.update(tilted((k % 10 < 5) ? 20.0f : -20.0f), 0.02f);
  CHECK(!hb.has_reference());
  CHECK(run(hb, tilted(5), 0.3f) == TipGuard::Event::None);
  CHECK(!hb.has_reference()); // 0.3 s steady is not enough
  CHECK(run(hb, tilted(5), 0.3f) == TipGuard::Event::None);
  CHECK(hb.has_reference());
  CHECK(run(hb, tilted(5), 0.1f) == TipGuard::Event::None);
  CHECK(hb.tilt_deg() < 0.5f);

  // Stored reference +z; a 10 deg lean is fine, 25 deg held trips.
  TipGuard h;
  h.set_reference({0, 0, 1});
  CHECK(run(h, tilted(10), 1.0f) == TipGuard::Event::None);
  CHECK(!h.tipped());
  // 25 deg for less than hold_s: no trip.
  CHECK(run(h, tilted(25), 0.10f) == TipGuard::Event::None);
  CHECK(run(h, tilted(0), 0.1f) == TipGuard::Event::None);
  // 25 deg held: trips once.
  CHECK(run(h, tilted(25), 0.3f) == TipGuard::Event::Tripped);
  CHECK(h.tipped());
  // Hysteresis: back to 12 deg is still tipped; under 8 clears.
  CHECK(run(h, tilted(12), 0.3f) == TipGuard::Event::None);
  CHECK(h.tipped());
  CHECK(run(h, tilted(3), 0.1f) == TipGuard::Event::Cleared);
  CHECK(!h.tipped());

  // Impacts and free fall (|a| far from 1 g) neither trip nor clear.
  CHECK(run(h, {3.0f, 0, 0}, 1.0f) == TipGuard::Event::None);
  CHECK(run(h, {0.05f, 0, 0.05f}, 1.0f) == TipGuard::Event::None);
  CHECK(!h.tipped());

  // level_here: the current pose becomes the reference.
  CHECK(run(h, tilted(40), 0.3f) == TipGuard::Event::Tripped);
  CHECK(h.level_here());
  CHECK(!h.tipped());
  CHECK(run(h, tilted(40), 0.5f) == TipGuard::Event::None);
  CHECK(h.tilt_deg() < 0.5f);
  // ...and refuses a non-gravity sample.
  h.update({2.5f, 0, 0}, 0.02f);
  CHECK(!h.level_here());

  // A zero stored reference means auto-level.
  TipGuard k;
  k.set_reference({0, 0, 0});
  CHECK(!k.has_reference());

  // ---- TipLatch: the firmware's view of the guard (review R1-02, R1-11)
  {
    using A = tip::TipLatch::Action;
    TipGuard g2;
    g2.set_reference({0, 0, 1});
    tip::TipLatch latch;
    auto feed = [&](Vec3 a, float secs, bool on) {
      A last = A::None;
      for (float t = 0; t < secs - 1e-6f; t += 0.02f) {
        g2.update(a, 0.02f);
        auto act = latch.step(on, g2.tipped());
        if (act != A::None)
          last = act;
      }
      return last;
    };
    CHECK(feed(tilted(30), 0.3f, true) == A::Trip);
    CHECK(latch.latched());
    // R1-02: 'imu level' while tipped re-references; the latch must clear.
    CHECK(g2.level_here());
    CHECK(latch.step(true, g2.tipped()) == A::Clear);
    CHECK(!latch.latched());
    CHECK(feed(tilted(30), 0.5f, true) == A::None); // 30 deg is the new level
    // R1-11: guard off while tipped, then on: trips on enable.
    TipGuard g3;
    g3.set_reference({0, 0, 1});
    tip::TipLatch l3;
    for (int k = 0; k < 20; k++) {
      g3.update(tilted(35), 0.02f);
      CHECK(l3.step(false, g3.tipped()) == A::None);
    }
    CHECK(g3.tipped());
    CHECK(!l3.latched());
    CHECK(l3.step(true, g3.tipped()) == A::Trip);
    // guard off clears the refusal
    CHECK(l3.step(false, g3.tipped()) == A::Clear);
    CHECK(l3.step(false, g3.tipped()) == A::None);
  }

  std::printf("%s: tip guard (%d failures)\n", failures ? "FAIL" : "PASS", failures);
  return failures ? 1 : 0;
}
