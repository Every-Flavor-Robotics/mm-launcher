#pragma once

// Hiwonder bus-servo CONTROLLER BOARD protocol ("Bus Servo Controller
// Communication Protocol", 7 pages). This is the board's own UART protocol,
// not the servos' 115200-baud half-duplex bus protocol: the board speaks
// 9600 8N1 on its GND/TX/RX/5V header and relays to the servos itself.
//
//   [0x55 0x55][length][cmd][params...]      length = params + 2
//
// No checksum. A malformed packet makes the board beep twice and hold LED2.
// The board also sends packets on its own (action group started / stopped /
// completed), so a reader must resync on 0x55 0x55 and skip what it did not
// ask for.
//
// Dependency-free (standard library only) so it builds and unit-tests on a
// host; the transport (UART read/write) is injected, the espp way
// (cf. espp::Basicmicro).

#include <algorithm>
#include <array>
#include <chrono>
#include <cstddef>
#include <cstdint>
#include <functional>
#include <mutex>
#include <optional>
#include <span>
#include <vector>

namespace hiwonder {

/// Command bytes (protocol section I and II).
enum class Cmd : uint8_t {
  ServoMove = 3,          ///< host->board: [n][time lo][time hi]{[id][pos lo][pos hi]} x n
  ActionGroupRun = 6,     ///< both ways: [group][count lo][count hi]
  ActionGroupStop = 7,    ///< both ways: no params
  ActionGroupComplete = 8,///< board->host: [group][count lo][count hi]
  ActionGroupSpeed = 11,  ///< host->board: [group][pct lo][pct hi]
  GetBatteryVoltage = 15, ///< host->board: none; reply [mv lo][mv hi]
  MultServoUnload = 20,   ///< host->board: [n]{[id]} x n
  MultServoPosRead = 21,  ///< host->board: [n]{[id]} x n; reply [n]{[id][pos lo][pos hi]} x n
};

inline constexpr uint8_t kHeader = 0x55;
inline constexpr size_t kMaxParams = 253; ///< length is one byte and counts itself + cmd
inline constexpr uint16_t kMaxPosition = 1000; ///< 0..1000 counts = 0..240 deg
inline constexpr float kDegPerCount = 240.0f / 1000.0f;

struct Packet {
  uint8_t cmd{0};
  std::vector<uint8_t> params;
};

struct ServoTarget {
  uint8_t id;
  uint16_t position; ///< 0..1000 counts (clamped when built)
};

struct ServoPosition {
  uint8_t id;
  int16_t position; ///< as reported; the board sends it as a signed 16-bit value
};

// ---------------------------------------------------------------- builders

inline std::vector<uint8_t> build(Cmd cmd, std::span<const uint8_t> params) {
  std::vector<uint8_t> out;
  out.reserve(params.size() + 4);
  out.push_back(kHeader);
  out.push_back(kHeader);
  out.push_back(static_cast<uint8_t>(params.size() + 2));
  out.push_back(static_cast<uint8_t>(cmd));
  out.insert(out.end(), params.begin(), params.end());
  return out;
}

/// CMD_SERVO_MOVE: move every target to its position over `time_ms`.
inline std::vector<uint8_t> build_servo_move(std::span<const ServoTarget> targets,
                                             uint16_t time_ms) {
  std::vector<uint8_t> p;
  p.reserve(3 + targets.size() * 3);
  p.push_back(static_cast<uint8_t>(targets.size()));
  p.push_back(time_ms & 0xff);
  p.push_back(time_ms >> 8);
  for (const auto &t : targets) {
    const uint16_t pos = t.position > kMaxPosition ? kMaxPosition : t.position;
    p.push_back(t.id);
    p.push_back(pos & 0xff);
    p.push_back(pos >> 8);
  }
  return build(Cmd::ServoMove, p);
}

inline std::vector<uint8_t> build_id_list(Cmd cmd, std::span<const uint8_t> ids) {
  std::vector<uint8_t> p;
  p.reserve(1 + ids.size());
  p.push_back(static_cast<uint8_t>(ids.size()));
  p.insert(p.end(), ids.begin(), ids.end());
  return build(cmd, p);
}

/// CMD_MULT_SERVO_UNLOAD: the servos lose holding torque.
inline std::vector<uint8_t> build_unload(std::span<const uint8_t> ids) {
  return build_id_list(Cmd::MultServoUnload, ids);
}

/// CMD_MULT_SERVO_POS_READ.
inline std::vector<uint8_t> build_read_positions(std::span<const uint8_t> ids) {
  return build_id_list(Cmd::MultServoPosRead, ids);
}

/// CMD_GET_BATTERY_VOLTAGE (the board's input, in mV).
inline std::vector<uint8_t> build_get_battery() { return build(Cmd::GetBatteryVoltage, {}); }

inline std::vector<uint8_t> build_action_group_run(uint8_t group, uint16_t count) {
  const uint8_t p[] = {group, static_cast<uint8_t>(count & 0xff), static_cast<uint8_t>(count >> 8)};
  return build(Cmd::ActionGroupRun, p);
}
inline std::vector<uint8_t> build_action_group_stop() { return build(Cmd::ActionGroupStop, {}); }

// ---------------------------------------------------------------- reply decoding

inline std::optional<uint16_t> decode_battery(const Packet &p) {
  if (p.cmd != static_cast<uint8_t>(Cmd::GetBatteryVoltage) || p.params.size() < 2)
    return std::nullopt;
  return static_cast<uint16_t>(p.params[0] | (p.params[1] << 8));
}

inline std::optional<std::vector<ServoPosition>> decode_positions(const Packet &p) {
  if (p.cmd != static_cast<uint8_t>(Cmd::MultServoPosRead) || p.params.empty())
    return std::nullopt;
  const size_t n = p.params[0];
  if (p.params.size() < 1 + 3 * n)
    return std::nullopt;
  std::vector<ServoPosition> out;
  out.reserve(n);
  for (size_t i = 0; i < n; i++) {
    const uint8_t *r = &p.params[1 + 3 * i];
    out.push_back({r[0], static_cast<int16_t>(r[1] | (r[2] << 8))});
  }
  return out;
}

// ---------------------------------------------------------------- stream parser

/// Byte-at-a-time parser that resyncs on 0x55 0x55. A length below 2 is
/// impossible (it counts itself and the command), so it drops the header and
/// rescans; this is what keeps a lost byte from desynchronizing it forever.
class Parser {
public:
  /// Feed one byte. Returns a packet when one completes.
  std::optional<Packet> push(uint8_t b) {
    switch (state_) {
    case State::H1:
      if (b == kHeader)
        state_ = State::H2;
      break;
    case State::H2:
      state_ = (b == kHeader) ? State::Len : State::H1;
      break;
    case State::Len:
      if (b == kHeader) {
        // 0x55 0x55 0x55: treat the extra header byte as a new start.
        state_ = State::Len;
      } else if (b < 2) {
        state_ = State::H1;
      } else {
        remaining_ = b - 1; // cmd + params
        pkt_ = Packet{};
        state_ = State::Cmd;
      }
      break;
    case State::Cmd:
      pkt_.cmd = b;
      remaining_--;
      if (remaining_ == 0) {
        state_ = State::H1;
        return std::move(pkt_);
      }
      state_ = State::Params;
      break;
    case State::Params:
      pkt_.params.push_back(b);
      if (--remaining_ == 0) {
        state_ = State::H1;
        return std::move(pkt_);
      }
      break;
    }
    return std::nullopt;
  }

  void reset() { state_ = State::H1; }

private:
  enum class State { H1, H2, Len, Cmd, Params };
  State state_{State::H1};
  size_t remaining_{0};
  Packet pkt_;
};

// ---------------------------------------------------------------- driver

/// Request/reply driver over an injected byte transport. One transaction at a
/// time (internal mutex). Unsolicited board packets that arrive while waiting
/// for a reply go to `on_unsolicited` and do not end the wait.
class BusServoBoard {
public:
  using write_fn = std::function<bool(std::span<const uint8_t>)>;
  /// Read up to data.size() bytes, waiting at most `timeout`; return the count.
  using read_fn = std::function<size_t(std::span<uint8_t>, std::chrono::milliseconds)>;
  using packet_fn = std::function<void(const Packet &)>;

  struct Config {
    write_fn write;
    read_fn read;
    /// Reply deadline. At 9600 baud a 3-servo position reply is 14 bytes
    /// (~15 ms on the wire) plus the board's own servo-bus round trips.
    std::chrono::milliseconds timeout{120};
    packet_fn on_unsolicited{nullptr};
  };

  explicit BusServoBoard(const Config &config)
      : config_(config) {}

  bool move(std::span<const ServoTarget> targets, uint16_t time_ms) {
    std::lock_guard<std::mutex> lk(mutex_);
    return send(build_servo_move(targets, time_ms));
  }

  bool unload(std::span<const uint8_t> ids) {
    std::lock_guard<std::mutex> lk(mutex_);
    return send(build_unload(ids));
  }

  std::optional<std::vector<ServoPosition>> read_positions(std::span<const uint8_t> ids) {
    std::lock_guard<std::mutex> lk(mutex_);
    drain();
    if (!send(build_read_positions(ids)))
      return std::nullopt;
    auto p = await(Cmd::MultServoPosRead);
    return p ? decode_positions(*p) : std::nullopt;
  }

  std::optional<uint16_t> battery_mv() {
    std::lock_guard<std::mutex> lk(mutex_);
    drain();
    if (!send(build_get_battery()))
      return std::nullopt;
    auto p = await(Cmd::GetBatteryVoltage);
    return p ? decode_battery(*p) : std::nullopt;
  }

  /// Process any unsolicited bytes that have arrived (call when idle).
  void poll() {
    std::lock_guard<std::mutex> lk(mutex_);
    drain();
  }

  size_t timeouts() const { return timeouts_; }

private:
  bool send(const std::vector<uint8_t> &bytes) {
    return config_.write && config_.write(std::span<const uint8_t>(bytes.data(), bytes.size()));
  }

  // Hand everything already buffered to on_unsolicited, so a stale packet is
  // never mistaken for the reply to the next request.
  void drain() {
    std::array<uint8_t, 64> buf;
    for (;;) {
      const size_t n = config_.read ? config_.read(buf, std::chrono::milliseconds(0)) : 0;
      if (n == 0)
        return;
      for (size_t i = 0; i < n; i++)
        if (auto p = parser_.push(buf[i]); p && config_.on_unsolicited)
          config_.on_unsolicited(*p);
    }
  }

  std::optional<Packet> await(Cmd want) {
    using clock = std::chrono::steady_clock;
    const auto deadline = clock::now() + config_.timeout;
    std::array<uint8_t, 32> buf;
    while (true) {
      const auto now = clock::now();
      if (now >= deadline)
        break;
      const auto left = std::chrono::duration_cast<std::chrono::milliseconds>(deadline - now);
      const size_t n = config_.read(buf, std::max(left, std::chrono::milliseconds(1)));
      for (size_t i = 0; i < n; i++) {
        auto p = parser_.push(buf[i]);
        if (!p)
          continue;
        if (p->cmd == static_cast<uint8_t>(want))
          return p;
        if (config_.on_unsolicited)
          config_.on_unsolicited(*p);
      }
    }
    timeouts_++;
    parser_.reset();
    return std::nullopt;
  }

  Config config_;
  Parser parser_;
  std::mutex mutex_;
  size_t timeouts_{0};
};

} // namespace hiwonder
