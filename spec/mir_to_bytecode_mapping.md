# M-IR to M-bytecode Mapping v0.1

适用范围：

- 当前 ESP8266 实验子集
- 与 `bench_e1.py`、`mvm_esp8266.ino` 的编码约定一致

---

## 1. 设备符号映射

| M-IR 设备名 | device_id |
|---|---:|
| `water_sensor` | 1 |
| `temperature_sensor` | 2 |
| `humidity_sensor` | 3 |
| `relay1` | 5 |
| `relay2` | 6 |

---

## 2. 核心 lowering 规则

| M-IR 语句 | lowering 结果 |
|---|---|
| `require cap(relay1)` | `GTWAY 5` |
| `require cap(water_sensor)` | `GTWAY 1` |
| `set relay1 = 1` | `LIT 1 ; IOW 5` |
| `set relay1 = 0` | `LIT 0 ; IOW 5` |
| `set relay2 = 1` | `LIT 1 ; IOW 6` |
| `read water_sensor` | `IOR 1` |
| `read temperature_sensor` | `IOR 2` |
| `read humidity_sensor` | `IOR 3` |
| `read relay1` | `IOR 5` |
| `read relay2` | `IOR 6` |
| `wait 500ms` | `WAIT 500` |
| `halt` | `HALT` |

---

## 3. 组合示例

### M-IR

```text
task relay_on_wait_read {
  require cap(relay1)
  require cap(water_sensor)
  set relay1 = 1
  wait 500ms
  read water_sensor
  halt
}
```

### Lowered instruction sequence

```text
GTWAY 5
GTWAY 1
LIT 1
IOW 5
WAIT 500
IOR 1
HALT
```

---

## 4. 闭环相关 lowering 约定

`readback` 和 `retry` 在 v0.1 中采用分阶段处理：

### 4.1 `readback <device> expect <value>`

可拆分为两层：

1. bytecode 层：
   - `IOR <device_id>`
2. 宿主/控制层：
   - 比较读回值与目标值

也就是说，`readback` 目前是 **IR-level control intent**，还不是单条固定 bytecode 指令。

### 4.2 `retry n times { ... }`

v0.1 建议先不 lowering 为纯 bytecode loop，而采用：

1. 宿主循环控制
2. 或实验脚本中的重试逻辑

原因：

- 当前论文后端已经对闭环策略有实验数据
- 但统一 compiler 还未把 retry 机制编译进 branch 子集

---

## 5. 错误映射建议

| 错误类别 | 触发阶段 |
|---|---|
| `MIR_PARSE_ERROR` | M-IR parsing |
| `UNKNOWN_DEVICE` | symbol resolution |
| `INVALID_CAPABILITY` | semantic check |
| `INVALID_SET_TARGET` | semantic check |
| `UNSUPPORTED_CONSTRUCT` | lowering |
| `VERIFY_BAD_ENCODING` | verifier |
| `VERIFY_UNAUTHORIZED_DEVICE` | verifier / semantic check |
| `EXEC_FAULT_*` | runtime execution |

