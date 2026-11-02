#pragma once

// JSON number formatting for the `@kind {json}` lines. fmt prints a NaN or
// infinity as `nan` / `inf`, which is not JSON, so one bad float would make
// the panel drop the whole line. Unset values (an unloaded servo, no IMU)
// are NaN on purpose, so they print as `null`.
// Pure, host-tested (test/host/test_jsonf.cpp).

#include <cmath>
#include <cstdio>
#include <string>

namespace jsonf {

/// `v` with `digits` decimals, or `null` if it is not finite.
inline std::string num(float v, int digits = 2) {
  if (!std::isfinite(v))
    return "null";
  char buf[48];
  std::snprintf(buf, sizeof(buf), "%.*f", digits, static_cast<double>(v));
  // "-0.0" reads oddly in a readout; JSON allows it, but print 0.
  std::string s(buf);
  if (s.size() > 1 && s[0] == '-' && s.find_first_not_of("-0.") == std::string::npos)
    s.erase(0, 1);
  return s;
}

/// JSON string body with quotes and backslashes escaped (fault reasons and
/// error text are free-form).
inline std::string str(const std::string &in) {
  std::string out;
  out.reserve(in.size() + 2);
  out.push_back('"');
  for (char c : in) {
    if (c == '"' || c == '\\') {
      out.push_back('\\');
      out.push_back(c);
    } else if (static_cast<unsigned char>(c) < 0x20) {
      out.push_back(' ');
    } else {
      out.push_back(c);
    }
  }
  out.push_back('"');
  return out;
}

} // namespace jsonf
