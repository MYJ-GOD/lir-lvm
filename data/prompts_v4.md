# Prompts v4

适用范围：

- `tasks_v4.jsonl`
- M-IR compiler v0.2 (支持 if/else 和 repeat)
- 覆盖 if/else 条件分支和 repeat 循环构造

---

## 1. System Prompt

```text
You generate M-IR programs for hardware control tasks.

Follow these rules exactly:
1. Output only M-IR text.
2. Do not output markdown fences.
3. Use only devices from the allow-list.
4. Every accessed device must first appear in require cap(...).
5. Use only these statements:
   - require cap(<device>)
   - set <device> = 0|1
   - read <device>
   - wait <ms>ms
   - halt
   - if read(<device>) <op> <value> then { ... }
   - if read(<device>) <op> <value> then { ... } else { ... }
   - repeat <N> times { ... }
6. Comparison operators: >, <, >=, <=, ==, !=
7. Only relay1 and relay2 may appear on the left side of set.
8. The program must start with `task <task_id> {` and end with `}`.
9. End every task with halt.
10. `halt` must be the last statement inside the task block, never outside it.
11. Do not add any extra action that is not explicitly required by the instruction.
12. Braces must be on their own line or after then/else keywords.
13. Nested if and repeat blocks are allowed.
```

---

## 2. User Prompt Template

```text
Task ID: {task_id}
Allowed devices: {allowed_devices}
Instruction: {prompt}

Generate one valid M-IR program.
```

---

## 3. Repair Prompt Template

```text
Task ID: {task_id}
Allowed devices: {allowed_devices}
Instruction: {prompt}

Previous output:
{previous_output}

Feedback:
- stage: {stage}
- error_code: {error_code}
- hint: {hint}

Rewrite the program as one valid M-IR program.
Requirements:
1. Output only the final M-IR program.
2. Start with task <task_id> {{
3. End with halt inside the task block.
4. Do not add extra text before or after the task block.
5. Make the final device state and return behavior match the instruction exactly.
```

---

## 4. 当前评测边界

`tasks_v4.jsonl` 覆盖 compiler v0.2 新增的控制流构造：

1. `if/else` 条件分支 (含无 else 变体)
2. `repeat N times` 循环
3. 比较运算符: >, <, >=, <=, ==, !=
4. 多设备条件判断
5. if + repeat 嵌套组合

与 v1 的区别：
- v1 只覆盖线性执行流 (require → set → read → wait → halt)
- v4 覆盖条件分支和循环，验证 LLM 能否生成结构化控制流
