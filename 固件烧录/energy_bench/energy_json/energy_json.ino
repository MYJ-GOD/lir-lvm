/*
 * P0-2 Energy benchmark - GROUP 2: MCU-side JSON interpreter
 *
 * The V3_006 task execution plan is stored as a JSON string in flash.
 * A minimal JSON interpreter walks the plan and executes each step.
 * Same REPORT_EVERY / TICK protocol as energy_bytecode.ino.
 * Real relay writes are skipped (sim_relay[]) to isolate interpretation cost.
 *
 * Intentionally uses no third-party library — a minimal recursive-descent
 * scanner matches the "~80 lines of C, jsmn library" baseline described in
 * the paper (E4 JSON baseline, §m9), reproduced here without jsmn for flash
 * size fairness (jsmn itself is <200 bytes of code).
 */

#include <Arduino.h>

static const uint32_t REPORT_EVERY = 10000; // JSON parsing is slower; fewer reps per window

// V3_006 execution plan as a compact JSON string (stored in flash via PROGMEM)
static const char TASK_JSON[] PROGMEM =
  "{\"task\":\"v3_006\","
   "\"require\":[{\"device\":\"relay1\",\"id\":5}],"
   "\"steps\":["
     "{\"op\":\"retry\",\"times\":3,\"body\":["
       "{\"op\":\"iow\",\"dev\":5,\"val\":0},"
       "{\"op\":\"ior\",\"dev\":5,\"expect\":0}"
     "]},"
     "{\"op\":\"halt\"}"
   "]}";

// Simulated relay state (not driven to real pins)
static int sim_relay[8] = {0,0,0,0,0,0,0,0};
static uint8_t caps[32];
static int exec_fault = 0;

static void caps_clear(){ memset(caps,0,sizeof(caps)); }
static void caps_add(int id){ if(id>=0&&id<256) caps[id>>3]|=(1u<<(id&7)); }
static bool caps_has(int id){ if(id<0||id>=256) return false; return (caps[id>>3]&(1u<<(id&7)))!=0; }

// Minimal JSON helpers: find the nth occurrence of key in src, return pointer after ':'
// src is RAM buffer (copied from PROGMEM each run).
static char json_buf[512];

static const char* json_find(const char* src, const char* key) {
  // Find "key": in src
  size_t kl = strlen(key);
  const char* p = src;
  while (*p) {
    if (*p == '"') {
      p++;
      size_t i = 0;
      while (p[i] && p[i] != '"') i++;
      if (i == kl && strncmp(p, key, kl) == 0) {
        p += i + 1; // skip closing "
        while (*p == ' ' || *p == ':') p++;
        return p;
      }
      p += i + 1;
    } else p++;
  }
  return nullptr;
}

static int json_int(const char* p) {
  if (!p) return 0;
  bool neg = (*p == '-'); if (neg) p++;
  int v = 0; while (*p >= '0' && *p <= '9') v = v*10 + (*p++ - '0');
  return neg ? -v : v;
}

// Execute one retry block with its body array.
// body_ptr points to the '[' of the body array.
static void exec_body(const char* body_ptr, int times) {
  for (int t = 0; t < times && !exec_fault; t++) {
    const char* p = body_ptr;
    // Walk each step object in the array
    while (*p && *p != ']' && !exec_fault) {
      if (*p == '{') {
        // find op
        const char* op_p = json_find(p, "op");
        if (!op_p) { exec_fault = 1; break; }
        if (strncmp(op_p, "\"iow\"", 5) == 0) {
          const char* dev_p = json_find(p, "dev");
          const char* val_p = json_find(p, "val");
          int dev = json_int(dev_p), val = json_int(val_p);
          if (!caps_has(dev)) { exec_fault = 14; break; }
          if (dev >= 0 && dev < 8) sim_relay[dev] = val;
        } else if (strncmp(op_p, "\"ior\"", 5) == 0) {
          const char* dev_p = json_find(p, "dev");
          const char* exp_p = json_find(p, "expect");
          int dev = json_int(dev_p), expect = json_int(exp_p);
          if (!caps_has(dev)) { exec_fault = 14; break; }
          int actual = (dev >= 0 && dev < 8) ? sim_relay[dev] : 0;
          if (actual != expect) { /* readback mismatch: retry logic would trigger, ignored for benchmark */ }
        }
        // skip to end of this object
        int depth = 0;
        while (*p) { if (*p=='{') depth++; else if (*p=='}') { depth--; if(depth==0){p++;break;} } p++; }
      } else p++;
    }
  }
}

static void run_json() {
  exec_fault = 0; caps_clear();
  strcpy_P(json_buf, TASK_JSON); // copy from flash to RAM each run
  // Grant capability for relay1 (id=5) from require section
  caps_add(5);
  // Execute steps
  const char* steps_p = json_find(json_buf, "steps");
  if (!steps_p) { exec_fault = 1; return; }
  // steps_p -> '['
  const char* p = steps_p;
  while (*p && *p != ']' && !exec_fault) {
    if (*p == '{') {
      const char* op_p = json_find(p, "op");
      if (!op_p) { exec_fault = 1; break; }
      if (strncmp(op_p, "\"retry\"", 7) == 0) {
        const char* times_p = json_find(p, "times");
        int times = json_int(times_p);
        const char* body_p = json_find(p, "body");
        if (body_p) exec_body(body_p, times);
      }
      // skip to end of object
      int depth = 0;
      while (*p) { if(*p=='{') depth++; else if(*p=='}'){depth--;if(depth==0){p++;break;}} p++; }
    } else p++;
  }
}

static uint32_t reps = 0;
static unsigned long t0 = 0;

void setup() {
  Serial.begin(115200);
  Serial.print("BANNER json v3_006 json_bytes=");
  Serial.print((int)strlen_P(TASK_JSON));
  Serial.print(" reps=");
  Serial.println(REPORT_EVERY);
  t0 = micros();
}

void loop() {
  run_json();
  reps++;
  if (reps % REPORT_EVERY == 0) {
    unsigned long elapsed = micros() - t0;
    Serial.print("TICK ");
    Serial.print(reps);
    Serial.print(" ");
    Serial.print(elapsed);
    Serial.print(" 0 ");
    Serial.println(exec_fault);
  }
}
