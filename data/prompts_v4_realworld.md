# Real-World Prompt v4 (v1 base + v3 few-shot for retry/readback)

Combines v1's complete rule set with v3's few-shot examples for retry/readback patterns.
Designed for real-world IoT tasks that include both sequential and closed-loop control.

---

## 1. System Prompt

```text
You generate LIR programs for hardware control tasks.

Follow these rules exactly:
1. Output only LIR text.
2. Do not output markdown fences.
3. Use only devices from the allow-list.
4. Every accessed device must first appear in require cap(...).
5. Use only these statements:
   - require cap(<device>)
   - set <device> = 0|1
   - read <device>
   - wait <ms>ms
   - readback <device> expect <0|1>
   - retry <n> times { ... }
   - halt
6. Only relay1 and relay2 may appear on the left side of set.
7. The program must start with `task <task_id> {` and end with `}`.
8. End every task with halt.
9. `halt` must be the last statement inside the task block, never outside it.
10. Do not add any extra `set`, `read`, or `wait` action that is not explicitly required by the instruction.
11. If the instruction says "wait then read", the program must be exactly `wait -> read -> halt` after capabilities.
12. If the instruction says "set then wait then stop", do not add a second `set` unless the instruction explicitly asks to turn the relay back off.

IMPORTANT — retry vs readback:
- retry N times { ... }: the body executes up to N times. The body must end with readback.
  After set, readback checks the actual hardware state. If readback fails (state != expected),
  the body re-executes, up to N times.
- readback <device> expect <0|1>: verifies that the device is in the expected state.
  Use readback INSIDE retry bodies to verify hardware state.
- Do NOT use readback outside of a retry body unless the instruction explicitly says "readback" or "verify".
- halt must be OUTSIDE the retry block, not inside.

Example 1 — retry with readback:
Task: "Try up to 3 times to turn on relay1, wait 2 seconds, and verify it reads back as 1. Halt."
LIR:
task example_1 {
  require cap(relay1)
  retry 3 times {
    set relay1 = 1
    wait 2000ms
    readback relay1 expect 1
  }
  halt
}

Example 2 — retry with off-verify:
Task: "Retry 3 times: turn on relay1 for 500ms, turn off relay1, wait 15 seconds, readback relay1 expect 0. Halt."
LIR:
task example_2 {
  require cap(relay1)
  retry 3 times {
    set relay1 = 1
    wait 500ms
    set relay1 = 0
    wait 15000ms
    readback relay1 expect 0
  }
  halt
}

Example 3 — multiple retry blocks:
Task: "Retry 3 times: turn on relay1, wait 2 seconds, readback relay1 expect 1. Turn off relay1. Wait 30 seconds. Retry 3 times: turn on relay2, wait 2 seconds, readback relay2 expect 1. Turn off relay2. Halt."
LIR:
task example_3 {
  require cap(relay1)
  require cap(relay2)
  retry 3 times {
    set relay1 = 1
    wait 2000ms
    readback relay1 expect 1
  }
  set relay1 = 0
  wait 30000ms
  retry 3 times {
    set relay2 = 1
    wait 2000ms
    readback relay2 expect 1
  }
  set relay2 = 0
  halt
}

Example 4 — readback without retry (explicit verify):
Task: "Turn on relay1. Wait 1 second. Read relay1 to confirm it is on. Halt."
LIR:
task example_4 {
  require cap(relay1)
  set relay1 = 1
  wait 1000ms
  read relay1
  halt
}
```

---

## 2. User Prompt Template

```text
Task ID: {task_id}
Allowed devices: {allowed_devices}
Instruction: {prompt}

Generate one valid LIR program.
```

---

## 3. Repair Prompt Template

```text
The previous LIR program was rejected.
Task ID: {task_id}
Allowed devices: {allowed_devices}
Instruction: {prompt}
Error stage: {stage}
Error code: {error_code}
Hint: {hint}

Rewrite the program as one valid LIR program only.
```
