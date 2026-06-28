/*
 * P0-2 Energy benchmark - GROUP 3: Arduino C native (no interpretation layer)
 *
 * The V3_006 task (require relay1; retry 3 { set relay1=0; readback relay1 expect 0 })
 * is compiled directly to C — no bytecode, no JSON, no interpreter.
 * This is the energy LOWER BOUND: it measures only the work the task actually does.
 * Difference (bytecode - native) = cost of carrying and interpreting the LIR representation.
 * Same REPORT_EVERY / TICK protocol.
 */

#include <Arduino.h>

static const uint32_t REPORT_EVERY = 200000; // native is fast; more reps per window

static int sim_relay[8] = {0,0,0,0,0,0,0,0};

// Direct C translation of V3_006: retry 3 times { sim_relay[5]=0; readback=sim_relay[5]; }
static inline void run_native() {
  for (int i = 0; i < 3; i++) {
    sim_relay[5] = 0;
    volatile int rb = sim_relay[5]; // readback (volatile prevents full elimination)
    (void)rb;
  }
}

static uint32_t reps = 0;
static unsigned long t0 = 0;

void setup() {
  Serial.begin(115200);
  Serial.print("BANNER native v3_006 reps=");
  Serial.println(REPORT_EVERY);
  t0 = micros();
}

void loop() {
  run_native();
  reps++;
  if (reps % REPORT_EVERY == 0) {
    unsigned long elapsed = micros() - t0;
    Serial.print("TICK ");
    Serial.print(reps);
    Serial.print(" ");
    Serial.print(elapsed);
    Serial.println(" 0 0");
  }
}
