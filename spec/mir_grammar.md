# M-IR Grammar v0.1

状态：

- 面向当前 `ccfc` 论文实验子集
- 目标是作为 LLM 输出层
- 编译目标是当前 ESP8266 可执行的 M-bytecode 子集

---

## 1. 设计目标

M-IR 不直接追求最短字节数，而追求：

1. 便于 LLM 生成
2. 便于人类审查
3. 便于确定性编译
4. 便于静态验证与错误回传

它是一个 **textual control IR**，不是最终执行格式。

---

## 2. 当前实验子集支持的设备名

| 设备名 | 设备 ID | 角色 |
|---|---:|---|
| `water_sensor` | 1 | 模拟水位输入 |
| `temperature_sensor` | 2 | DHT11 温度读取 |
| `humidity_sensor` | 3 | DHT11 湿度读取 |
| `relay1` | 5 | 执行器 |
| `relay2` | 6 | 执行器 |

说明：

1. 当前子集只允许以上符号名；
2. `relay1` / `relay2` 既可被写入，也可被读回；
3. capability 以设备 ID 为授权粒度。

---

## 3. 语法总览

最小形式采用块式 DSL：

```text
task <task_name> {
  require cap(<device_name>)
  ...
  <stmt>
  <stmt>
}
```

### 3.1 词法约定

1. 标识符：`[A-Za-z_][A-Za-z0-9_]*`
2. 整数：十进制非负整数
3. 布尔写入值：`0 | 1`
4. 注释：以 `#` 开头，直到行尾

### 3.2 最小语法（EBNF）

```ebnf
program        ::= task_def
task_def       ::= "task" ident "{" requirement* stmt* "}"
requirement    ::= "require" "cap" "(" device ")"

stmt           ::= set_stmt
                 | read_stmt
                 | wait_stmt
                 | halt_stmt
                 | readback_stmt
                 | retry_stmt

set_stmt       ::= "set" device "=" int
read_stmt      ::= "read" device
wait_stmt      ::= "wait" int "ms"
halt_stmt      ::= "halt"

readback_stmt  ::= "readback" device "expect" int
retry_stmt     ::= "retry" int "times" "{" stmt* "}"

device         ::= "relay1"
                 | "relay2"
                 | "water_sensor"
                 | "temperature_sensor"
                 | "humidity_sensor"

ident          ::= /[A-Za-z_][A-Za-z0-9_]*/
int            ::= /0|[1-9][0-9]*/
```

---

## 4. 语义约束

### 4.1 `require cap(...)`

用于声明该任务需要访问哪些设备。

示例：

```text
require cap(relay1)
require cap(water_sensor)
```

语义：

- 编译时会 lowering 为 `GTWAY <device_id>`
- 若访问设备但未先 `require cap(...)`，应在编译或验证阶段报错

### 4.2 `set`

```text
set relay1 = 1
set relay2 = 0
```

语义：

- 当前子集仅支持对 `relay1/relay2` 写入
- 值当前限定为 `0` 或 `1`

### 4.3 `read`

```text
read water_sensor
read relay1
```

语义：

- 读取设备当前值
- 结果压入执行栈
- 若后续没有消费，默认允许保留为任务返回值

### 4.4 `wait`

```text
wait 500ms
```

语义：

- lowering 为 `WAIT <ms>`
- 当前必须为非负整数

### 4.5 `readback`

```text
readback relay1 expect 1
```

语义：

- 这是 M-IR 层面的闭环语义，不是单条 bytecode 指令
- 当前可 lowering 为：
  1. `IOR <device>`
  2. 比较读值与目标值
  3. 若不一致，则由外围 repair / retry 策略决定是否重试

说明：

- 当前论文后端已经有“set -> readback -> compare -> retry”的实验链路
- 但尚未把它完整编译进统一 M-IR compiler

### 4.6 `retry`

```text
retry 3 times {
  set relay1 = 1
  readback relay1 expect 1
}
```

语义：

- 当前先作为前端 IR 结构保留
- 第一版 compiler 可不把它 lowering 为纯 bytecode loop，而是展开为宿主侧控制逻辑
- 第二版再考虑 lowering 到 `JZ/JNZ/JMP`

---

## 5. 当前不支持的语法

以下内容不应出现在 v0.1 M-IR 中：

1. 浮点数
2. 字符串
3. 数组
4. 任意表达式嵌套
5. 自定义函数
6. 未命名设备 ID 直接裸写
7. 任意算术条件组合

原因：

- 当前目标是先对齐 ESP8266 已验证子集
- 先把生成链路跑通，再扩展语言能力

---

## 6. 输出要求

给 LLM 的输出约束建议：

1. 只输出 M-IR 程序本身
2. 不输出解释文字
3. 不输出 Markdown 代码块标记
4. 设备名必须来自白名单
5. 每个被访问设备都必须先显式 `require cap(...)`

