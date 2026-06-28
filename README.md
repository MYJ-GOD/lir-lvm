# M-IR + MVM 论文实验复现指南

本文档对应论文《M-IR + MVM：面向大语言模型生成的紧凑硬件控制表示与有界安全执行框架》的实验部分。

> **术语映射（重要）**：投稿版论文将 **M-IR 更名为 LIR**、**MVM 更名为 LVM**。
> 代码库仍沿用历史前缀，对应关系如下，复现时请按此对照：
>
> | 论文术语 | 代码库 / 文件 / 符号 |
> |---|---|
> | LIR（结构化 IR） | `mir_compiler.py`、M-IR、`.mir` 程序 |
> | LVM（轻量虚拟机） | `backend_adapter.py`（参考 VM）、MVM、`mvm_*.ino` 固件 |
> | compact bytecode | M-bytecode，`M_LIT`/`M_IOW`/… 等 `M_*` 操作码常量 |
>
> 语义与编码完全一致，仅命名不同。

> **纯软件复现（无需 MCU / LLM）**：运行 `bash reproduce_software_only.sh`
> 可离线复现编译器-VM 单元测试、E1 载荷体积（Table: encoding）以及
> E2-Fuzz 对抗性字节码围栏实验（Table: fuzzing，预期 8000 条全部围栏、0 逃逸）。

## 环境要求

- Python 3.9+
- Ollama（本地 LLM 推理服务）
- ESP8266（仅后端实机实验需要）

Python 依赖（标准库即可，无需额外 pip 安装）：

```
# tools/ 下大部分脚本仅依赖 Python 标准库
# 外部依赖：ollama（通过 HTTP API 调用，使用 urllib.request）
# CBOR/MsgPack 基线实验需要：pip install cbor2 msgpack
```

## 项目结构

```
ccfc/
├── CLAUDE.md                 # 仓库说明（给 AI 协作者的指南）
├── README.md                 # 本文件
├── reproduce_software_only.sh # 纯软件离线复现脚本（无需 MCU / LLM）
├── latex/                    # LaTeX 投稿稿
│   ├── main.tex              #   论文正文（投稿版）
│   ├── cas-refs.bib          #   参考文献
│   └── verify.py             #   论文统计自检（Wilson CI / 算术复算）
├── spec/                     # 规范文档
│   └── mir_to_bytecode_mapping.md   # LIR→bytecode 映射规范（编译器/固件须同步）
├── vm_full/                  # 完整通用 LVM 的 C 参考实现（~50 指令；见 vm_full/README.md）
│   ├── include/              #   opcode 表 / 反汇编器 / 静态校验器接口
│   └── src/                  #   VM 核心 + 反汇编器 + 校验器 + 测试入口
├── figures/                  # 论文图表（PDF/SVG + TikZ 源在 latex/）
├── firmware/                 # STM32 固件（.ino，板级 LVM）
├── 固件烧录/                  # ESP8266/ESP32 固件 + e2_* 安全消融变体
├── data/
│   ├── tasks_v2.jsonl               # 113 个确定性任务
│   ├── tasks_v3_closed_loop.jsonl   # 16 个闭环任务
│   ├── tasks_v3_expanded.jsonl      # 96 个扩展闭环任务（12 子类）
│   ├── tasks_v4.jsonl               # 15 个控制流任务（if/else + repeat）
│   ├── tasks_random_500.jsonl       # 随机参数化任务（600 题来源）
│   ├── tasks_realworld.jsonl        # 29 个真实 IoT 部署任务
│   └── prompts_*.md                 # 各任务集的 prompt 模板（v1~v4、compare）
├── tools/                           # ~50 个独立实验脚本（共享 mir_compiler / backend_adapter）
│   ├── mir_compiler.py              # LIR 编译器（含 if/else、repeat 支持）
│   ├── backend_adapter.py           # 参考 LVM（解码 / 静态校验 / 栈机仿真）
│   ├── ollama_client.py             # Ollama API 客户端
│   ├── deepseek_client.py           # DeepSeek API 客户端
│   ├── run_ollama_generate*.py      # 生成实验主脚本
│   ├── run_generation_eval.py       # 生成结果评估（含 repair 反馈码）
│   ├── run_repair_eval.py           # repair loop 评估
│   ├── run_hex_eval.py              # Direct Hex 基线评估
│   ├── run_json_baseline_eval.py    # JSON 基线评估
│   ├── measure_token_cost.py        # Token 成本测量
│   ├── analyze_token_semantics.py   # 语义等价性分析
│   ├── bench_e1.py                  # E1 压缩率实验
│   ├── bench_e2*.py                 # E2 安全消融实验
│   ├── bench_e4_scr.py              # E4 闭环 SCR 实验
│   ├── bench_scr_prior.py           # E5 故障先验扫描
│   ├── bench_scalability.py         # 可扩展性实验（长度/设备/步限）
│   ├── bench_temperature_sweep.py   # Temperature 扫描实验
│   ├── gen_figures_svg.py           # 论文结果图生成
│   ├── generate_tasks_v*.py         # 任务集生成
│   └── ...
└── result/
    ├── GEN/                         # 生成 / 评测主结果（候选 + CSV + 判定 md）
    ├── TOKEN/                       # Token 与压缩率对比
    ├── E1/                          # 压缩率多批次
    ├── E2/                          # 对抗性 fuzzing（8000 载荷）
    ├── E2_orthogonal/               # UABR 正交单机制消融
    ├── E4/                          # 闭环 SCR（n=100）
    ├── E4_json_real/                # 闭环 JSON 公平基线
    ├── E5_prior/                    # 故障先验扫描（n=200）
    ├── E_POWER/                     # 能耗实测（UM25C）
    ├── E10_deploy/                  # 部署指标（部分列需外接功耗仪）
    ├── e2_cases/                    # E2 攻击样例（.bin）
    ├── scalability/                 # d1/d2/d3 可扩展性扫描
    └── _archive/                    # 被新版取代的旧版本结果（非论文引用）
```

## 复现步骤

### 1. 生成实验（实验 C）

```bash
# 确保 ollama 已启动并拉取模型
ollama pull llama3.1:8b

# 运行生成实验
python tools/run_ollama_generate.py \
  --model llama3.1:8b \
  --tasks data/tasks_v2.jsonl \
  --output result/GEN/candidates_llama31_8b_v2_full_r2.jsonl

# 评估生成结果
python tools/run_generation_eval.py \
  --candidates result/GEN/candidates_llama31_8b_v2_full_r2.jsonl \
  --tasks data/tasks_v2.jsonl \
  --output result/GEN/gen_eval_llama31_8b_v2_full_r2.csv
```

### 2. Repair 实验

```bash
python tools/run_repair_eval.py \
  --candidates result/GEN/candidates_llama31_8b_v2_full_r2.jsonl \
  --tasks data/tasks_v2.jsonl \
  --model llama3.1:8b \
  --max-rounds 3 \
  --output result/GEN/repair_eval_v1.csv
```

### 3. Token 成本对比（实验 E）

```bash
python tools/measure_token_cost.py \
  --tasks data/tasks_v2.jsonl \
  --model llama3.1:8b \
  --output result/TOKEN/token_compare_v3_tasks_v2.csv

python tools/analyze_token_semantics.py \
  --input result/TOKEN/token_compare_v3_tasks_v2.csv \
  --output result/TOKEN/token_compare_v3_tasks_v2_semantics_r2.csv
```

### 4. Direct Hex 基线

```bash
python tools/run_ollama_generate_hex.py \
  --model llama3.1:8b \
  --tasks data/tasks_v3_closed_loop.jsonl \
  --output result/GEN/candidates_hex_llama31_8b_closed_loop_v1.jsonl

python tools/run_hex_eval.py \
  --candidates result/GEN/candidates_hex_llama31_8b_closed_loop_v1.jsonl \
  --tasks data/tasks_v3_closed_loop.jsonl \
  --output result/GEN/hex_eval_llama31_8b_closed_loop_v1.csv
```

### 5. 控制流任务实验（tasks_v4）

```bash
# 生成 tasks_v4.jsonl（如果尚未生成）
python tools/generate_tasks_v4.py

# 运行 v4 生成实验
python tools/run_ollama_generate.py \
  --model llama3.1:8b \
  --tasks data/tasks_v4.jsonl \
  --prompts data/prompts_v4.md \
  --output result/GEN/candidates_v4_llama.jsonl

# 评估 v4 结果
python tools/run_generation_eval.py \
  --candidates result/GEN/candidates_v4_llama.jsonl \
  --tasks data/tasks_v4.jsonl \
  --output result/GEN/gen_eval_v4_llama.md
```

### 6. CBOR/MsgPack 基线实验

```bash
pip install -r requirements.txt

python tools/bench_cbor_msgpack.py \
  --input result/TOKEN/token_compare_v3_tasks_v2.csv \
  --output result/TOKEN/cbor_msgpack_baseline.csv
```

### 7. Temperature 扫描实验

```bash
python tools/bench_temperature_sweep.py \
  --model llama3.1:8b \
  --tasks data/tasks_v2.jsonl \
  --temperatures 0.6 1.0 \
  --runs 3 \
  --output result/GEN/temperature_sweep.csv
```

### 8. 安全实验（E2：fuzzing + 消融，离线 / 实机）

```bash
# 8a. 对抗性字节码 fuzzing（纯软件，无需实机）—— 8000 载荷，预期 0 逃逸
python tools/bench_e2_fuzzing.py --n 8000 --seed 42 \
  --out result/E2/fuzzing.csv

# 8b. UABR 正交单机制消融（需 ESP8266/ESP32 串口）
python tools/bench_e2_orthogonal.py --serial COM3 --repeat 30 \
  --out-dir result/E2_orthogonal
```

### 9. 闭环 SCR 与故障先验扫描（E4 / E5，需实机串口）

```bash
# E4：闭环 Safe Convergence Rate（n=100/组）
python tools/bench_e4_scr.py --serial COM5 --repeat 100 --write-latest

# E5：故障先验扫描（每个先验点 n=200）
for p in 0.1 0.3 0.5 0.7 0.9; do
  python tools/bench_scr_prior.py --serial COM5 --n 200 \
    --fault-prior $p --variant guarded --write-latest
done
```

### 10. 可扩展性分析（纯软件）

```bash
# 长度 / 设备数 / 步限三轴扫描（host 仿真，无需实机）
python tools/bench_scalability.py
```

## 论文构建与统计自检

```bash
# 统计自检：复算论文中的 Wilson CI 与算术声明
python latex/verify.py

# 编译投稿稿
cd latex && latexmk -pdf main.tex     # 或：pdflatex main; bibtex main; pdflatex ×2
```

## 数据说明

- `tasks_v2.jsonl`：113 个确定性任务，覆盖 7 种任务类型
- `tasks_v3_closed_loop.jsonl`：16 个闭环任务，覆盖 readback/retry 等语义
- `tasks_v3_expanded.jsonl`：96 个扩展闭环任务，覆盖 12 个子类
- `tasks_v4.jsonl`：15 个控制流任务，覆盖 if/else、repeat 及其嵌套
- `tasks_random_500.jsonl`：随机参数化任务（论文 600 题随机覆盖实验的来源）
- `tasks_realworld.jsonl`：29 个真实 IoT 部署任务（Home Assistant / Tasmota / ESPHome / Arduino）
- 所有结果文件均为 JSONL 或 CSV 格式，可直接用 pandas 加载分析
- 结果文件按后缀版本化（`_v1`/`_v2_full`/`_r2` 等），复现时匹配最新版本
- `result/_archive/` 存放被新版取代的旧结果，**论文不引用**，仅作版本留痕

> **数据溯源**：`DATA_TRACEABILITY.md` 记录论文每个图、每张表所引用数字的
> 计算方式与数据源文件，可据此从 `result/`、`data/` 原始数据逐项复算。

## 完整 VM 与实验子集的关系

`vm_full/` 是 LVM 的**完整通用实现**（C，约 50 条指令：函数、循环、数组、动态内存、算术、调试），已实现并通过单元测试。论文的**形式化分析与全部实验**（压缩、fuzzing、能耗、任务成功率）只针对其中 **14 条指令的有界执行子集**——该子集由 `tools/`（Python 参考实现）与 `固件烧录/`、`firmware/`（ESP8266/STM32 固件）承载。完整 VM 提供出来是为了让论文中"通用指令集"的陈述可被查证，**它不是实验数据的来源**。详见 `vm_full/README.md`。

## 引用

如果使用本文代码或数据，请引用论文。
