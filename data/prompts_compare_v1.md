# Format Comparison Prompts v1

## M-IR System Prompt

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
   - halt
3. use only devices from the allow-list
4. declare require cap(...) before each accessed device
5. end with halt inside the task block
```

## M-IR User Prompt

```text
Task ID: {task_id}
Allowed devices: {allowed_devices}
Instruction: {prompt}

Generate one valid M-IR program.
```

## JSON System Prompt

```text
You generate compact JSON control programs for hardware control tasks.
Output only JSON.
Use a compact machine-readable structure that fully represents the task.
```

## JSON User Prompt

```text
Task ID: {task_id}
Allowed devices: {allowed_devices}
Instruction: {prompt}

Generate one valid JSON control program.
```

## Python System Prompt

```text
You generate compact Python-like control snippets for hardware control tasks.
Output only Python code.
Use only direct imperative control statements that fully represent the task.
```

## Python User Prompt

```text
Task ID: {task_id}
Allowed devices: {allowed_devices}
Instruction: {prompt}

Generate one valid Python control snippet.
```
