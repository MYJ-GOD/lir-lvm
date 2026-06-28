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

`readback` 和 `retry` 在当前实现中**已完整 lowering 为 bytecode**（不再停留在宿主/控制层）。

### 4.1 `readback <device> expect <value>`

lowering 为三条基础指令序列：

```text
IOR <device_id> ; LIT <value> ; EQ
```

即读回设备状态、压入期望值、比较，比较结果（0/1）留在栈顶供后续 `retry`/`JZ` 消费。`readback` 没有独立 opcode；它复用 `IOR` 的字节码，差异仅在 host 侧执行计划（execution plan）中记录为「闭环验证读」以便故障分级。

示例（`set relay1 = 1` 后 `readback relay1 expect 1`）实测 hex：

```text
50 05  1e 02  46 05   GTWAY 5 ; LIT 1 ; IOW 5
47 05  1e 02  2c      IOR 5 ; LIT 1 ; EQ
52                    HALT
```

### 4.2 `retry n times { ... }`

lowering 为显式 bytecode 控制流，由 `LIT/DUP/JZ/JMP/SUB/DRP` 组成的递减计数循环：

1. `LIT n` 初始化重试计数；
2. 循环体 `B`（要求以 `readback` 或嵌套 `retry` 结尾，产生布尔结果）；
3. 计数递减（`SUB`）并按布尔/计数条件回跳（`JZ`/`JMP`）。

计数为编译期常量；循环体每次迭代使全局 step 计数 +1，故要么在 `n` 次内终止，要么触发 step-limit 故障（见论文 Proposition「Bounded execution」与附录 RETRY 编译策略）。`retry` 同样没有独立 opcode，完全展开为上述基础指令。

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

