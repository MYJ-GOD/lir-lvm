# Closed-loop Prompt Templates v2

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
6. keep retry bodies valid: they must end with readback or nested retry, and must not contain halt inside the retry body
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
