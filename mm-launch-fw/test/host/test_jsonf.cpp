// Host tests for the @json number/string helpers.
#include <cmath>
#include <cstdio>
#include <limits>

#include "jsonf.hpp"

static int failures = 0;
#define CHECK(cond)                                                                                \
  do {                                                                                             \
    if (!(cond)) {                                                                                 \
      std::printf("FAIL %s:%d  %s\n", __FILE__, __LINE__, #cond);                                  \
      failures++;                                                                                  \
    }                                                                                              \
  } while (0)

int main() {
  CHECK(jsonf::num(NAN) == "null");
  CHECK(jsonf::num(std::numeric_limits<float>::infinity()) == "null");
  CHECK(jsonf::num(-std::numeric_limits<float>::infinity(), 1) == "null");
  CHECK(jsonf::num(12.345f, 1) == "12.3");
  CHECK(jsonf::num(-7.25f, 2) == "-7.25");
  CHECK(jsonf::num(3.0f, 0) == "3");
  CHECK(jsonf::num(-0.0001f, 1) == "0.0"); // no "-0.0"
  CHECK(jsonf::num(-0.04f, 1) == "0.0");
  CHECK(jsonf::num(-0.06f, 1) == "-0.1");
  CHECK(jsonf::str("FEED_JAM (open err 9.1)") == "\"FEED_JAM (open err 9.1)\"");
  CHECK(jsonf::str("say \"hi\" \\ there") == "\"say \\\"hi\\\" \\\\ there\"");
  CHECK(jsonf::str("a\nb") == "\"a b\"");
  std::printf("%s: jsonf (%d failures)\n", failures ? "FAIL" : "PASS", failures);
  return failures ? 1 : 0;
}
