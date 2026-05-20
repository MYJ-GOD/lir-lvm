# M-IR + MVM 论文实验复现指南

本文档对应论文《M-IR + MVM：面向大语言模型生成的紧凑硬件控制表示与有界安全执行框架》的实验部分。

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
├── ccfc论文草稿.md          # 论文正文
├── 问题清单.md               # 审稿反馈
├── 优化方案.md               # 修改方案
├── figures/                  # 论文图表
├── data/
│   ├── tasks_v2.jsonl               # 113 个确定性任务
│   ├── tasks_v3_closed_loop.jsonl   # 16 个闭环任务
│   ├── tasks_v4.jsonl               # 15 个控制流任务（if/else + repeat）
│   └── prompts_v4.md                # v4 任务的 prompt 模板
├── tools/
│   ├── mir_compiler.py              # M-IR 编译器（含 if/else、repeat 支持）
│   ├── backend_adapter.py           # 后端仿真适配器
│   ├── ollama_client.py             # Ollama API 客户端
│   ├── run_ollama_generate.py       # 生成实验主脚本
│   ├── run_generation_eval.py       # 生成结果评估
│   ├── run_repair_eval.py           # repair loop 评估
│   ├── run_hex_eval.py              # Direct Hex 基线评估
│   ├── run_hex_repair_eval.py       # Hex repair 评估
│   ├── measure_token_cost.py        # Token 成本测量
│   ├── analyze_token_semantics.py   # 语义等价性分析
│   ├── bench_e1.py                  # E1 压缩率实验
│   ├── bench_e2.py                  # E2 安全实验
│   ├── bench_e4_scr.py              # E4 闭环实验
│   ├── bench_cbor_msgpack.py        # CBOR/MsgPack 基线实验
│   ├── bench_temperature_sweep.py   # Temperature 扫描实验
│   ├── generate_tasks_v2.py         # v2 任务生成
│   ├── generate_tasks_v4.py         # v4 控制流任务生成
│   └── ...
└── result/
    ├── GEN/                         # 生成实验结果
    ├── TOKEN/                       # Token 对比结果
    ├── E1/                          # 压缩率实验结果
    ├── E2/                          # 安全实验结果
    └── ...
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

## 数据说明

- `tasks_v2.jsonl`：113 个确定性任务，覆盖 7 种任务类型
- `tasks_v3_closed_loop.jsonl`：16 个闭环任务，覆盖 readback/retry 等语义
- `tasks_v4.jsonl`：15 个控制流任务，覆盖 if/else、repeat 及其嵌套
- 所有结果文件均为 JSONL 或 CSV 格式，可直接用 pandas 加载分析

## 引用

如果使用本文代码或数据，请引用论文。
