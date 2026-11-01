// Executa o sketch real com GPIO, relógio e serial simulados no computador.
#include <cassert>
#include <cstdint>
#include <deque>
#include <string>
#include <vector>

using byte = uint8_t;
constexpr int LOW = 0, HIGH = 1, OUTPUT = 1, LED_BUILTIN = 13;
int pins[20] = {};
unsigned long clockMs = 0;
void digitalWrite(int pin, int value) { pins[pin] = value; }
void pinMode(int, int) {}
unsigned long millis() { return clockMs; }
struct SerialStub {
  std::deque<char> input;
  std::vector<std::string> output;
  void begin(int) {}
  int available() { return input.size(); }
  char read() { char c = input.front(); input.pop_front(); return c; }
  void println(const char* value) { output.emplace_back(value); }
  void send(const std::string& value) { for (char c : value) input.push_back(c); }
} Serial;

#include "../arduino/face_lamp/face_lamp.ino"

int main() {
  setup();
  assert(!lampOn && pins[RELAY_PIN] == HIGH);
  Serial.send("ON\n"); loop();
  assert(lampOn && pins[RELAY_PIN] == LOW && Serial.output.back() == "ACK ON");
  clockMs = 2999; loop(); assert(lampOn);
  clockMs = 3000; loop(); assert(!lampOn && pins[RELAY_PIN] == HIGH);
  Serial.send("ON\r\n"); loop(); assert(lampOn);
  Serial.send("OFF\n"); loop();
  assert(!lampOn && Serial.output.back() == "ACK OFF");
  Serial.send("ON TOO LONG\n"); loop();
  assert(!lampOn && Serial.output.back() == "ERR");
  Serial.send("ON\n"); loop(); assert(lampOn);
  clockMs += 2000;
  Serial.send("INVALID\n"); loop();
  clockMs += 1000; loop(); assert(!lampOn);
  return 0;
}
