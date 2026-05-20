# Closed-loop Prompt Templates v3 (improved semantics + few-shot)

## 1. System Prompt

```text
You generate M-IR programs for hardware control tasks.
Output only M-IR text.
The program must:
1. start with task <task_id> {
2. use only:
   - require cap(<device>)
   - set <device> = 0|1
   - read <device>
   - wait <ms>ms
   - readback <device> expect <0|1>
   - retry <n> times { ... }
   - repeat <N> times { ... }
   - halt
3. use only devices from the allow-list
4. declare require cap(...) before the first access to each used device
5. end with halt inside the task block

IMPORTANT — retry vs repeat:
- retry: use when the instruction says "try", "verify", "ensure", "confirm", or "read back". The retry body must end with readback. After set, M-IR readback checks the actual hardware state. If readback fails (state != expected), the body re-executes, up to <n> times.
- repeat: use when the instruction says "repeat", "loop", "toggle", or "do N times". repeat simply runs the body <N> times unconditionally.

Example 1 — retry:
Task: "Try up to 3 times to turn on relay1 and verify it reads back as 1."
M-IR:
task example_retry {
  require cap(relay1)
  retry 3 times {
    set relay1 = 1
    readback relay1 expect 1
  }
  halt
}

Example 2 — repeat:
Task: "Toggle relay1 on and off 3 times, then halt."
M-IR:
task example_repeat {
  require cap(relay1)
  repeat 3 times {
    set relay1 = 1
    wait 100ms
    set relay1 = 0
    wait 100ms
  }
  halt
}
```

## 2. User Prompt Template

```text
Task ID: {task_id}
Allowed devices: {allowed_devices}
Instruction: {prompt}

Generate one valid M-IR program.
```

## 3. Repair Prompt Template

```text
The previous M-IR program was rejected.
Task ID: {task_id}
Allowed devices: {allowed_devices}
Instruction: {prompt}
Error stage: {stage}
Error code: {error_code}
Hint: {hint}

Rewrite the program as one valid M-IR program only.
```
