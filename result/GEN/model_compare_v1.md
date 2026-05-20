# Multi-model Generation Comparison

- task set: `tasks_v2.jsonl`
- total tasks per model: `113`

## Summary

- `llama3.1:8b`
  - `ir_valid_rate = 1.000`
  - `compile_pass_rate = 1.000`
  - `verify_pass_rate = 1.000`
  - `execution_pass_rate = 1.000`
  - `task_success_rate = 1.000`

- `qwen3:8b`
  - `ir_valid_rate = 0.956`
  - `compile_pass_rate = 0.956`
  - `verify_pass_rate = 0.956`
  - `execution_pass_rate = 0.956`
  - `task_success_rate = 0.903`
  - primary errors:
    - `TASK_SIGNATURE_MISMATCH = 6`
    - `MIR_PARSE_ERROR = 5`

- `deepseek-r1:8b`
  - `ir_valid_rate = 1.000`
  - `compile_pass_rate = 1.000`
  - `verify_pass_rate = 1.000`
  - `execution_pass_rate = 1.000`
  - `task_success_rate = 1.000`

## Notes

- `llama3.1:8b` 和 `deepseek-r1:8b` 均在 113 任务上达到 1.000 通过率。
- `qwen3:8b` 的主要弱点集中在：
  - `set_wait_halt`：`10/16 = 0.625`
  - `single_set`：`3/4 = 0.750`
  - `set_wait_read`：`44/48 = 0.917`
- `wait_read`、`multi_read` 与 `pulse` 子类在该模型上仍能稳定通过。
- 三个模型中两个达到满分，说明 M-IR 链路对主流 8B 模型具有较好兼容性，但模型选择仍影响通过率。
