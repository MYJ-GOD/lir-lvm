# M-IR Examples v0.1

---

## Example 1: 单动作

```text
task relay1_on {
  require cap(relay1)
  set relay1 = 1
  halt
}
```

预期行为：

- 打开 `relay1`

---

## Example 2: 单次读传感器

```text
task read_water {
  require cap(water_sensor)
  read water_sensor
  halt
}
```

预期行为：

- 读取水位值并作为返回值

---

## Example 3: 顺序动作

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

预期行为：

- 打开 `relay1`
- 等待 500ms
- 读取水位值

---

## Example 4: 闭环读回

```text
task relay1_set_and_check {
  require cap(relay1)
  set relay1 = 1
  readback relay1 expect 1
  halt
}
```

预期行为：

- 设定 `relay1=1`
- 读回 `relay1`
- 比较是否等于 1

说明：

- 该语义目前在论文实验中已有后端支持
- 统一 compiler/repair loop 仍待补做

---

## Example 5: 带 retry 的闭环

```text
task relay1_retry_until_match {
  require cap(relay1)
  retry 3 times {
    set relay1 = 1
    readback relay1 expect 1
  }
  halt
}
```

预期行为：

- 至多尝试 3 次
- 每次都执行 `set -> readback -> compare`

说明：

- 第一版可由宿主侧循环实现
- 第二版再 lowering 为 bytecode branch

---

## Example 6: 非法例子（缺 capability）

```text
task invalid_missing_cap {
  set relay1 = 1
  halt
}
```

应触发：

- `VERIFY_UNAUTHORIZED_DEVICE` 或等价编译/验证错误

---

## Example 7: 非法例子（未知设备）

```text
task invalid_unknown_device {
  require cap(pump1)
  set pump1 = 1
  halt
}
```

应触发：

- `UNKNOWN_DEVICE`

