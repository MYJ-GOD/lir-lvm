# Generation Feedback Schema v0.1

适用范围：

- `LLM -> M-IR -> compiler -> verifier -> executor -> repair`
- 当前先服务于 `ccfc` 论文的 P0-3 / P0-6 实验

---

## 1. 设计目标

反馈结构需要同时满足：

1. 便于程序统计；
2. 便于作为 repair loop 的回灌输入；
3. 能区分失败发生在哪一层；
4. 不把底层执行细节直接泄漏成无结构长文本。

---

## 2. 顶层结构

建议统一返回如下 JSON：

```json
{
  "ok": false,
  "task_id": "T001",
  "attempt": 1,
  "stage": "compile",
  "error_code": "INVALID_CAPABILITY",
  "message": "device 'relay1' used without require cap(...)",
  "hint": "Add require cap(relay1) before the first access.",
  "details": {
    "line": 3,
    "device": "relay1"
  }
}
```

---

## 3. 字段定义

| 字段 | 类型 | 含义 |
|---|---|---|
| `ok` | bool | 当前阶段是否成功 |
| `task_id` | string | 任务 ID |
| `attempt` | int | 第几轮生成 / 修复 |
| `stage` | string | 失败阶段 |
| `error_code` | string | 结构化错误码 |
| `message` | string | 面向人类的短消息 |
| `hint` | string | 面向 repair 的短修复建议 |
| `details` | object | 结构化补充字段 |

---

## 4. `stage` 取值

| stage | 含义 |
|---|---|
| `parse` | M-IR 词法 / 语法解析失败 |
| `compile` | 语义检查或 lowering 失败 |
| `verify` | bytecode verifier 失败 |
| `execute` | MVM 执行 fault |
| `readback` | 闭环比对失败 |
| `success` | 本轮任务完成 |

---

## 5. 当前错误码约定

### 5.1 parse / compile

| error_code | stage |
|---|---|
| `MIR_PARSE_ERROR` | `parse` |
| `UNKNOWN_DEVICE` | `compile` |
| `INVALID_CAPABILITY` | `compile` |
| `INVALID_SET_TARGET` | `compile` |
| `INVALID_ARGUMENT` | `compile` |
| `UNSUPPORTED_CONSTRUCT` | `compile` |
| `LOWERING_ERROR` | `compile` |

### 5.2 verify

| error_code | stage |
|---|---|
| `VERIFY_BAD_ENCODING` | `verify` |
| `VERIFY_UNAUTHORIZED_DEVICE` | `verify` |
| `VERIFY_BAD_LOCAL_INDEX` | `verify` |
| `VERIFY_BAD_CONTROL_FLOW` | `verify` |

### 5.3 execute

| error_code | stage |
|---|---|
| `EXEC_FAULT_BAD_OPCODE` | `execute` |
| `EXEC_FAULT_STACK_UNDERFLOW` | `execute` |
| `EXEC_FAULT_STEP_LIMIT` | `execute` |
| `EXEC_FAULT_CALL_DEPTH` | `execute` |
| `EXEC_FAULT_UNAUTHORIZED_IO` | `execute` |

### 5.4 readback

| error_code | stage |
|---|---|
| `READBACK_MISMATCH` | `readback` |
| `READBACK_TIMEOUT` | `readback` |

---

## 6. hint 生成规则

hint 必须短、直接、可执行。建议采用模板化生成：

| error_code | hint 模板 |
|---|---|
| `MIR_PARSE_ERROR` | `Rewrite the program using the M-IR grammar exactly.` |
| `UNKNOWN_DEVICE` | `Use only devices from the provided allow-list.` |
| `INVALID_CAPABILITY` | `Add require cap(<device>) before the first access.` |
| `INVALID_SET_TARGET` | `Only relay1 and relay2 may appear on the left side of set.` |
| `INVALID_ARGUMENT` | `Keep binary actuator values in {0,1} and wait in non-negative milliseconds.` |
| `UNSUPPORTED_CONSTRUCT` | `Avoid readback/retry in compiler v0.1 unless the task explicitly requests host-side handling.` |
| `VERIFY_UNAUTHORIZED_DEVICE` | `Remove unauthorized device accesses or declare the correct capability.` |
| `READBACK_MISMATCH` | `Regenerate the control sequence so the final observed state matches the target.` |

---

## 7. repair loop 输入建议

回灌模型时，不建议原样拼接长日志，建议固定为：

```json
{
  "task_id": "T001",
  "previous_output": "task ...",
  "feedback": {
    "stage": "compile",
    "error_code": "INVALID_CAPABILITY",
    "hint": "Add require cap(relay1) before the first access.",
    "details": {
      "line": 3,
      "device": "relay1"
    }
  }
}
```

---

## 8. 当前 v0.1 边界

当前版本已经能稳定覆盖：

1. `parse`
2. `compile`
3. 基于期望 payload 的 `task_success` 判定

尚未统一接入：

1. host verifier CLI
2. simulator execution CLI
3. board execution CLI
4. `readback/retry` lowering
