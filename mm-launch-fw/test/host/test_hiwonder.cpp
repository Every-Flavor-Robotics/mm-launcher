// Host tests for the Hiwonder controller-board protocol. Every expected byte
// string below is copied from the examples in the vendor PDF.
#include <cassert>
#include <cstdio>
#include <deque>
#include <vector>

#include "hiwonder_bus_board.hpp"

using namespace hiwonder;
using Bytes = std::vector<uint8_t>;

static int failures = 0;
#define CHECK(cond)                                                                                \
  do {                                                                                             \
    if (!(cond)) {                                                                                 \
      std::printf("FAIL %s:%d  %s\n", __FILE__, __LINE__, #cond);                                  \
      failures++;                                                                                  \
    }                                                                                              \
  } while (0)

static void test_builders_match_pdf() {
  // I.1 example 1: servo 1 to position 800 within 1000 ms.
  const ServoTarget one[] = {{1, 800}};
  CHECK(build_servo_move(one, 1000) == (Bytes{0x55, 0x55, 0x08, 0x03, 0x01, 0xE8, 0x03, 0x01, 0x20, 0x03}));
  // I.1 example 2: servos 2 and 9 to 800 within 800 ms.
  const ServoTarget two[] = {{2, 800}, {9, 800}};
  CHECK(build_servo_move(two, 800) ==
        (Bytes{0x55, 0x55, 0x0B, 0x03, 0x02, 0x20, 0x03, 0x02, 0x20, 0x03, 0x09, 0x20, 0x03}));
  // I.2: run action group 8 once; group 2 forever.
  CHECK(build_action_group_run(8, 1) == (Bytes{0x55, 0x55, 0x05, 0x06, 0x08, 0x01, 0x00}));
  CHECK(build_action_group_run(2, 0) == (Bytes{0x55, 0x55, 0x05, 0x06, 0x02, 0x00, 0x00}));
  // I.3 stop.
  CHECK(build_action_group_stop() == (Bytes{0x55, 0x55, 0x02, 0x07}));
  // I.5 battery.
  CHECK(build_get_battery() == (Bytes{0x55, 0x55, 0x02, 0x0F}));
  // I.6 unload 1,2,3.
  const uint8_t ids3[] = {1, 2, 3};
  CHECK(build_unload(ids3) == (Bytes{0x55, 0x55, 0x06, 0x14, 0x03, 0x01, 0x02, 0x03}));
  // I.7 read 1..6.
  const uint8_t ids6[] = {1, 2, 3, 4, 5, 6};
  CHECK(build_read_positions(ids6) ==
        (Bytes{0x55, 0x55, 0x09, 0x15, 0x06, 0x01, 0x02, 0x03, 0x04, 0x05, 0x06}));
  // Positions above 1000 clamp.
  const ServoTarget hi[] = {{1, 4000}};
  auto b = build_servo_move(hi, 0);
  CHECK(b[8] == (1000 & 0xff) && b[9] == (1000 >> 8));
}

static std::vector<Packet> parse_all(const Bytes &bytes) {
  Parser p;
  std::vector<Packet> out;
  for (auto c : bytes)
    if (auto pkt = p.push(c))
      out.push_back(*pkt);
  return out;
}

static void test_parser_and_decoders() {
  // I.5 reply: 7500 mV.
  auto pk = parse_all({0x55, 0x55, 0x04, 0x0F, 0x4C, 0x1D});
  CHECK(pk.size() == 1);
  CHECK(decode_battery(pk[0]) == 7500);

  // I.7 reply: six servos all at 500.
  Bytes reply = {0x55, 0x55, 0x15, 0x15, 0x06};
  for (uint8_t id = 1; id <= 6; id++) {
    reply.push_back(id);
    reply.push_back(0xF4);
    reply.push_back(0x01);
  }
  pk = parse_all(reply);
  CHECK(pk.size() == 1);
  auto pos = decode_positions(pk[0]);
  CHECK(pos && pos->size() == 6);
  if (pos)
    for (size_t i = 0; i < pos->size(); i++)
      CHECK((*pos)[i].id == i + 1 && (*pos)[i].position == 500);

  // Garbage, a truncated header, an impossible length, then a valid packet.
  pk = parse_all({0x00, 0x55, 0x13, 0x55, 0x55, 0x01, 0x55, 0x55, 0x02, 0x07});
  CHECK(pk.size() == 1 && pk[0].cmd == 7 && pk[0].params.empty());

  // II.3 action group complete followed immediately by a battery reply.
  pk = parse_all({0x55, 0x55, 0x05, 0x08, 0x08, 0x01, 0x00, 0x55, 0x55, 0x04, 0x0F, 0x4C, 0x1D});
  CHECK(pk.size() == 2 && pk[0].cmd == 8 && pk[1].cmd == 15);

  // Short position payload is rejected, not over-read.
  Packet bad{21, {3, 1, 0xF4}};
  CHECK(!decode_positions(bad));
}

// Fake board: records writes, serves queued RX bytes.
struct FakeUart {
  std::vector<Bytes> writes;
  std::deque<uint8_t> rx;
  bool write(std::span<const uint8_t> d) {
    writes.emplace_back(d.begin(), d.end());
    return true;
  }
  size_t read(std::span<uint8_t> d, std::chrono::milliseconds) {
    size_t n = 0;
    while (n < d.size() && !rx.empty()) {
      d[n++] = rx.front();
      rx.pop_front();
    }
    return n;
  }
};

static void test_driver() {
  FakeUart uart;
  std::vector<Packet> unsolicited;
  BusServoBoard board({.write = [&](auto d) { return uart.write(d); },
                       .read = [&](auto d, auto t) { return uart.read(d, t); },
                       .timeout = std::chrono::milliseconds(5),
                       .on_unsolicited = [&](const Packet &p) { unsolicited.push_back(p); }});

  // A stale "action group stopped" sits in the buffer; then the reply.
  for (uint8_t c : {0x55, 0x55, 0x02, 0x07, 0x55, 0x55, 0x04, 0x0F, 0x4C, 0x1D})
    uart.rx.push_back(c);
  // drain() runs first and eats both, so the battery reply is "unsolicited":
  // the reply to OUR request has not arrived and the call times out.
  CHECK(!board.battery_mv());
  CHECK(unsolicited.size() == 2);
  CHECK(board.timeouts() == 1);

  // Now a well-ordered exchange: the reply arrives after the request.
  unsolicited.clear();
  uart.writes.clear();
  BusServoBoard board2({.write =
                            [&](auto d) {
                              uart.write(d);
                              // the board answers a 3-servo read
                              for (uint8_t c : {0x55, 0x55, 0x0C, 0x15, 0x03, 0x01, 0xF4, 0x01, 0x02,
                                                0x2C, 0x01, 0x03, 0xFF, 0xFF})
                                uart.rx.push_back(c);
                              return true;
                            },
                        .read = [&](auto d, auto t) { return uart.read(d, t); },
                        .timeout = std::chrono::milliseconds(5)});
  const uint8_t ids[] = {1, 2, 3};
  auto pos = board2.read_positions(ids);
  CHECK(pos && pos->size() == 3);
  if (pos && pos->size() == 3) {
    CHECK((*pos)[0].position == 500);
    CHECK((*pos)[1].position == 300);
    CHECK((*pos)[2].position == -1); // signed 16-bit
  }
  CHECK(uart.writes.size() == 1 && uart.writes[0] == (Bytes{0x55, 0x55, 0x06, 0x15, 0x03, 1, 2, 3}));
}

int main() {
  test_builders_match_pdf();
  test_parser_and_decoders();
  test_driver();
  std::printf("%s: hiwonder protocol (%d failures)\n", failures ? "FAIL" : "PASS", failures);
  return failures ? 1 : 0;
}
