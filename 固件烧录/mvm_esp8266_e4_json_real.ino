#include <Arduino.h>
#include <DHT.h>

/*
 * Firmware: mvm_esp8266_e4_json_real.ino
 * Purpose: E4+ real JSON/text parsing baseline on MCU.
 *
 * Serial protocol:
 *   Request:  [4-byte LE length][UTF-8 JSON object bytes]
 *   Response: [4-byte LE length][payload]
 *     OK payload:    [result zigzag-varint][steps varint][0x01]
 *     FAULT payload: [fault varint][pc varint][0x00]
 *
 * Supported commands:
 *   {"dev":5,"op":"set","val":1}
 *   {"dev":5,"op":"get"}
 *   {"op":"wait","ms":10}
 */

// Pins
static const int PIN_WATER_A0 = A0;
static const int PIN_DHT = D4;    // GPIO2
static const int PIN_RELAY1 = D1; // GPIO5
static const int PIN_RELAY2 = D2; // GPIO4

// DHT
static const int DHTTYPE = DHT11;
static DHT dht(PIN_DHT, DHTTYPE);

// Simple fault codes aligned with host-side meaning where possible.
static const uint32_t FAULT_NONE = 0;
static const uint32_t FAULT_BAD_ENCODING = 13;
static const uint32_t FAULT_BAD_ARG = 17;

static bool read_exact(uint8_t *dst, int n) {
  int got = 0;
  unsigned long start = millis();
  while (got < n) {
    if (Serial.available()) {
      dst[got++] = (uint8_t)Serial.read();
      start = millis();
    } else {
      if (millis() - start > 2000) return false;
      delay(1);
    }
  }
  return true;
}

static int encode_uvarint(uint64_t v, uint8_t *out) {
  int i = 0;
  while (v > 0x7FULL) {
    out[i++] = (uint8_t)(v & 0x7F) | 0x80;
    v >>= 7;
  }
  out[i++] = (uint8_t)v;
  return i;
}

static uint64_t encode_zigzag64(int64_t n) {
  return ((uint64_t)n << 1) ^ (uint64_t)(n >> 63);
}

static void send_ok(int64_t result, uint32_t steps) {
  uint8_t out[24];
  int pos = 0;
  pos += encode_uvarint(encode_zigzag64(result), out + pos);
  pos += encode_uvarint((uint64_t)steps, out + pos);
  out[pos++] = 0x01;
  uint32_t len = (uint32_t)pos;
  Serial.write((uint8_t *)&len, 4);
  Serial.write(out, pos);
}

static void send_fault(uint32_t fault, uint32_t pc) {
  uint8_t out[24];
  int pos = 0;
  pos += encode_uvarint((uint64_t)fault, out + pos);
  pos += encode_uvarint((uint64_t)pc, out + pos);
  out[pos++] = 0x00;
  uint32_t len = (uint32_t)pos;
  Serial.write((uint8_t *)&len, 4);
  Serial.write(out, pos);
}

static int64_t read_sensor(uint32_t dev) {
  if (dev == 1) {
    return (int64_t)analogRead(PIN_WATER_A0);
  }
  if (dev == 2) {
    float t = dht.readTemperature();
    if (isnan(t)) return -127;
    return (int64_t)t;
  }
  if (dev == 3) {
    float h = dht.readHumidity();
    if (isnan(h)) return -1;
    return (int64_t)h;
  }
  if (dev == 5) {
    return digitalRead(PIN_RELAY1) == HIGH ? 1 : 0;
  }
  if (dev == 6) {
    return digitalRead(PIN_RELAY2) == HIGH ? 1 : 0;
  }
  return 0;
}

static void write_actuator(uint32_t dev, int64_t val) {
  int on = (val != 0) ? HIGH : LOW;
  if (dev == 5) {
    digitalWrite(PIN_RELAY1, on);
  } else if (dev == 6) {
    digitalWrite(PIN_RELAY2, on);
  }
}

static int skip_spaces(const String &s, int p) {
  while (p < s.length() && (s[p] == ' ' || s[p] == '\t' || s[p] == '\r' || s[p] == '\n')) p++;
  return p;
}

static bool parse_string_field(const String &s, const char *key, String &out) {
  String k = "\"" + String(key) + "\"";
  int i = s.indexOf(k);
  if (i < 0) return false;
  i = s.indexOf(':', i + (int)k.length());
  if (i < 0) return false;
  i = skip_spaces(s, i + 1);
  if (i >= s.length() || s[i] != '"') return false;
  int j = s.indexOf('"', i + 1);
  if (j < 0) return false;
  out = s.substring(i + 1, j);
  return true;
}

static bool parse_int_field(const String &s, const char *key, int &out) {
  String k = "\"" + String(key) + "\"";
  int i = s.indexOf(k);
  if (i < 0) return false;
  i = s.indexOf(':', i + (int)k.length());
  if (i < 0) return false;
  i = skip_spaces(s, i + 1);
  bool neg = false;
  if (i < s.length() && s[i] == '-') {
    neg = true;
    i++;
  }
  if (i >= s.length() || s[i] < '0' || s[i] > '9') return false;
  long v = 0;
  while (i < s.length() && s[i] >= '0' && s[i] <= '9') {
    v = v * 10 + (long)(s[i] - '0');
    i++;
  }
  if (neg) v = -v;
  out = (int)v;
  return true;
}

static bool execute_cmd(const uint8_t *buf, int len, int64_t *result, uint32_t *steps, uint32_t *fault_code) {
  String s;
  s.reserve(len + 1);
  for (int i = 0; i < len; i++) s += (char)buf[i];

  String op;
  if (!parse_string_field(s, "op", op)) {
    *fault_code = FAULT_BAD_ENCODING;
    return false;
  }

  if (op == "set") {
    int dev = 0;
    int val = 0;
    if (!parse_int_field(s, "dev", dev) || !parse_int_field(s, "val", val)) {
      *fault_code = FAULT_BAD_ARG;
      return false;
    }
    write_actuator((uint32_t)dev, (int64_t)val);
    *result = (int64_t)(val != 0 ? 1 : 0);
    *steps = 3;
    return true;
  }

  if (op == "get") {
    int dev = 0;
    if (!parse_int_field(s, "dev", dev)) {
      *fault_code = FAULT_BAD_ARG;
      return false;
    }
    *result = read_sensor((uint32_t)dev);
    *steps = 3;
    return true;
  }

  if (op == "wait") {
    int ms = 0;
    if (!parse_int_field(s, "ms", ms)) {
      *fault_code = FAULT_BAD_ARG;
      return false;
    }
    if (ms < 0) ms = 0;
    delay((unsigned long)ms);
    *result = 0;
    *steps = 2;
    return true;
  }

  *fault_code = FAULT_BAD_ARG;
  return false;
}

void setup() {
  Serial.begin(115200);
  pinMode(PIN_RELAY1, OUTPUT);
  pinMode(PIN_RELAY2, OUTPUT);
  digitalWrite(PIN_RELAY1, LOW);
  digitalWrite(PIN_RELAY2, LOW);
  pinMode(PIN_WATER_A0, INPUT);
  dht.begin();
}

void loop() {
  if (Serial.available() < 4) {
    delay(1);
    return;
  }
  uint8_t lenbuf[4];
  if (!read_exact(lenbuf, 4)) return;
  uint32_t len = (uint32_t)lenbuf[0] |
                 ((uint32_t)lenbuf[1] << 8) |
                 ((uint32_t)lenbuf[2] << 16) |
                 ((uint32_t)lenbuf[3] << 24);
  if (len == 0 || len > 384) {
    send_fault(FAULT_BAD_ARG, 0);
    return;
  }
  static uint8_t buf[384];
  if (!read_exact(buf, (int)len)) return;

  int64_t result = 0;
  uint32_t steps = 0;
  uint32_t fault = FAULT_NONE;
  bool ok = execute_cmd(buf, (int)len, &result, &steps, &fault);
  if (ok) {
    send_ok(result, steps);
  } else {
    send_fault(fault, 0);
  }
}
