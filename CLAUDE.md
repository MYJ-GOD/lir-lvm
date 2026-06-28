# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this repository is

This is the **experiment + paper reproduction package** for the research paper *LIR + LVM: a compact hardware-control representation for LLM generation with bounded safe execution* (面向大语言模型生成的紧凑硬件控制表示与有界安全执行框架). It is not a deployable application — it is a collection of independent experiment scripts, datasets, firmware sketches, result tables, and the LaTeX manuscript. Most files exist to produce the numbers and figures in `latex/main.tex`.

The working directory is `论文分区/ccfc` inside a larger `M-Language-Core` tree.

## Commands

Python scripts under `tools/` use **only the standard library** (Ollama is reached over HTTP via `urllib.request`). Only the CBOR/MsgPack baseline needs third-party packages.

```bash
# Optional deps (CBOR/MsgPack baseline only)
pip install -r requirements.txt   # cbor2, msgpack

# Run the compiler unit tests (run from inside tools/ — tests use flat imports)
cd tools && python -m unittest test_mir_compiler -v
cd tools && python -m unittest test_realworld -v

# Run a single test
cd tools && python -m unittest test_mir_compiler.MirCompilerTests.test_retry_success_path -v

# Compile an M-IR program to bytecode hex / AST / execution plan
python tools/mir_compiler.py path/to/prog.mir --emit-hex
python tools/mir_compiler.py path/to/prog.mir --json          # machine-readable result
python tools/mir_compiler.py path/to/prog.mir --dump-plan     # host-side execution plan

# Verify paper statistics (Wilson CIs and arithmetic claims)
python latex/verify.py

# Build the manuscript
cd latex && latexmk -pdf main.tex   # or: pdflatex main.tex; bibtex main; pdflatex x2
```

LLM experiments require a local **Ollama** server on `127.0.0.1:11434` (`ollama pull llama3.1:8b`). See `README.md` for the full per-experiment command sequence (generate → eval → repair → token cost → baselines). DeepSeek experiments use `tools/deepseek_client.py` instead.

## Architecture

The system is a **two-layer pipeline**: an LLM emits human-readable **LIR** source, which a compiler lowers to a compact **bytecode** payload that runs on a guarded stack VM (the **LVM**) on a microcontroller.

### Core modules (the only tightly-coupled code)

- **`tools/mir_compiler.py`** — the LIR compiler. `parse_program` → AST (`Statement`/`Program` dataclasses) → `compile_program` lowers to a flat `IrInstr` list → `assemble_ir` emits bytecode bytes. Supported statements: `require cap(...)`, `set`, `read`, `wait`, `halt`, `readback ... expect`, `retry N times {}`, `if read(d) OP v then {} else {}`, `repeat N times {}`. Control flow (`retry`/`repeat`/`if`) lowers to real bytecode via `LIT/DUP/JZ/JMP/SUB/DRP` with relative jump offsets. `compile_to_plan` produces a structured JSON execution plan (host-side / debugging) in parallel to bytecode.
- **`tools/backend_adapter.py`** — the reference LVM in Python. `decode_program` parses bytecode, `verify_subset` does static checks (opcode validity, jump-target bounds), `simulate_subset` executes on a stack VM enforcing guards: capability gating (`GTWAY` must authorize a device before `IOW`/`IOR`), stack-underflow faults, bad-opcode/encoding faults. Returns a `BackendResult` with `verify_pass`/`execution_pass`/`error_code`/`relay_state`.

These two files **duplicate** the opcode constants (`M_LIT`, `M_IOW`, …) and `DEVICE_IDS` map. If you change opcodes, device IDs, or encoding, you must update **both** files and `spec/mir_to_bytecode_mapping.md`, then re-run `test_mir_compiler` (golden hex strings in the tests will break).

### Encoding

Opcodes and unsigned args use uvarint; `LIT` values and jump offsets use zigzag-encoded svarint. The firmware sketches must decode identically.

### Everything else is loosely-coupled experiment scripts

`tools/` holds ~50 standalone scripts, each with its own `main()` / argparse, sharing only `mir_compiler`, `backend_adapter`, `ollama_client`, `deepseek_client`:
- `run_ollama_generate*.py` / `run_generation_eval.py` / `run_repair_eval.py` — generation → eval → closed-loop repair.
- `run_hex_eval.py`, `run_json_baseline_eval.py`, `bench_arduino_c_baseline.py`, `bench_grammar_constrained.py` — competing baselines (Direct Hex, JSON, Arduino C, grammar-constrained decoding).
- `bench_e1.py` (compression), `bench_e2*.py` (safety ablations), `bench_e4_scr.py` / `bench_scr_prior.py` (closed-loop success-after-repair), `bench_e4_json_real.py`, `bench_scalability.py`, `bench_temperature_sweep.py` — the numbered experiments E1–E5/E10.
- `measure_token_cost.py` + `analyze_token_semantics.py` — token-cost comparison across representations.
- `generate_tasks_v*.py` / `generate_tasks_random.py` — produce the `data/*.jsonl` task sets.
- `gen_figures_svg.py`, `gen_figures_nature.py`, `gen_arch_figures.py`, `gen_tikz_figs.py`, `fig_style.py` — regenerate `figures/`.

### Data and results

- `data/tasks_v*.jsonl` — task sets. Each row: `task_id`, `category`, `prompt` (Chinese NL), `allowed_devices`, `expected_status`, `expected_mir`. `tasks_v2` (113 deterministic), `tasks_v3_closed_loop` (16), `tasks_v4` (15 control-flow), plus random/realworld sets.
- `data/prompts_v*.md` — prompt templates fed to the LLM, versioned alongside task sets.
- `result/<EXP>/` — outputs as `.jsonl` (raw candidates) + `.csv` (metrics) + `.md` (judgement writeups). Loadable with pandas.

### Firmware

`固件烧录/*.ino` (ESP8266/ESP32) and `firmware/*.ino` (STM32) are the on-device LVM. The `e2_*` ablation variants (`no_auth`, `no_load_validator`, `no_step_limit`, `no_call_depth`, …) implement the safety-guard ablation matrix; `mvm_esp8266_guarded.ino` is the full-guard reference. These must keep their decoder/opcode table in sync with `backend_adapter.py`.

## Communication

- **Always respond in Chinese (中文).** The user's primary language is Chinese; all explanations, summaries, and confirmations should be in Chinese unless the user explicitly switches to English.

## Conventions

- Device allow-list is fixed: sensors `water_sensor`(1), `temperature_sensor`(2), `humidity_sensor`(3); writable relays `relay1`(5), `relay2`(6). Only relays may appear on the left of `set`, and values must be `0|1`.
- Compiler errors are typed by `code` (`MIR_PARSE_ERROR`, `UNKNOWN_DEVICE`, `INVALID_CAPABILITY`, `INVALID_SET_TARGET`, `INVALID_ARGUMENT`, `UNSUPPORTED_CONSTRUCT`, `LOWERING_ERROR`); runtime faults by `EXEC_FAULT_*`. The repair loop feeds these codes back to the LLM (`make_feedback` in `run_generation_eval.py`).
- `tools/` scripts import each other flatly (`from mir_compiler import ...`), so run them with `tools/` as the working directory or on `sys.path`.
- Result files are versioned by suffix (`_v1`, `_v2_full`, `_r2`, `_final`) rather than overwritten — match the latest when reproducing.
- When changing paper numbers, update `latex/verify.py` so its asserted statistics stay consistent with `latex/main.tex`.
