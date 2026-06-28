# Data Traceability Matrix

> Maps every quantitative claim in `latex/main.tex` to its source data file, generator
> script, reproduction command, and a recompute check.
>
> **Synchronised with `main.tex` at git HEAD `0659532` (paper title: "LIR+LVM: Bounded
> Execution of LLM-Generated Code on Microcontrollers").**
>
> **Automated recompute:** every numeric claim below is re-derived from its source by
> `tools/recompute_all.py`. Last run: **114/114 PASS, 0 FAIL** (3 documented imprecisions
> reported as INFO — see "Known imprecisions" at the end).
>
> ```bash
> python tools/recompute_all.py     # re-derive & PASS/MISMATCH-check every table/figure number
> cd latex && python verify.py      # Wilson CIs + arithmetic spot-checks
> ```

## Paper metadata

| Field | Value |
|---|---|
| Title | LIR+LVM: Bounded Execution of LLM-Generated Code on Microcontrollers |
| Short title | LIR for LLM-to-MCU |
| Authors | Yingjie Ma, Mengjia Ma, Sheng Zhao, Peng Liu (corresponding) |
| Affiliation | North China Institute of Aerospace Engineering (NCIAE), Langfang, Hebei, China |
| Target venue | JSA Special Issue — Security & Efficiency of LLM-based Edge Intelligence |
| Submission deadline | 2026-06-30 |
| Artifact | https://github.com/MYJ-GOD/lir-lvm |

> **Terminology note.** The system is **LIR** (the intermediate representation) +
> **LVM** (the lightweight virtual machine). Earlier drafts used "MVM"; the source code
> still uses the historical `mir_*` / `m_bytecode` / `MIR` identifiers in scripts, CSV
> columns, and firmware. In this document, **MIR = LIR** and **MVM = LVM**; CSV column
> names such as `m_bytecode_bytes` and `format=MIR` are the on-disk spelling of LIR.

## How to use this document

Each row is a single quantitative claim in the paper. Columns:

- **Claim**: the value as it appears in `main.tex` (table/figure/section).
- **Source file(s)**: the raw data file(s) holding the numbers.
- **Generator**: the script that produced the source file (`—` = static asset / manual measurement).
- **Recompute**: the check id inside `tools/recompute_all.py` (search the label) that re-derives it.

---

## Section / table / figure → label map (current paper)

| Artifact | Label | Primary source file |
|---|---|---|
| Table — design-space comparison | `tab:rw_comparison` | literature + `result/E10_deploy/` (footprint) — qualitative |
| Table — four-scenario payload | `tab:encoding` | `result/GEN/json_baseline_eval_v1.csv`, `result/TOKEN/token_compare_v3_tasks_v2.csv`, `result/TOKEN/cbor_msgpack_baseline.csv` |
| Table — lowering rules | `tab:lowering` | `tools/mir_compiler.py` (static) |
| Table — instruction set (14) | `tab:inst_set` | `tools/mir_compiler.py`, `tools/backend_adapter.py` (static) |
| Table — LVM footprint | `tab:footprint` | Arduino IDE build report (manual) + `result/E10_deploy/throughput_summary.csv` |
| Table — fuzzing containment | `tab:fuzzing` | `result/E2/fuzzing.csv` |
| Table — system-level ablation | `tab:system_ablation` | `result/GEN/{gen_eval_llama31_8b_v2_full_r2,json_baseline_eval_v1,arduino_c_baseline}.csv`, `result/GEN/success_at_k.csv` |
| Table — temperature sweep | `tab:temperature` | `result/GEN/temperature_sweep_6pt_summary.csv` |
| Table — real-world IoT | `tab:realworld` | `result/GEN/candidates_realworld_v4.jsonl`, `result/GEN/json_realworld_eval.csv` |
| Table — grammar / best-of-K | `tab:grammar_constrained` | `result/GEN/grammar_constrained.csv`, `result/GEN/success_at_k.csv` |
| Table — consolidated 113-task | `tab:gen_results` | `result/GEN/gen_eval_llama31_8b_v2_full.csv`, `result/TOKEN/token_compare_v3_tasks_v2.csv` + `_semantics_r2.csv`, `result/GEN/python_detailed_eval.csv` |
| Table — proofs/transition rules | `app:proofs`, `app:rules` | `tools/backend_adapter.py` (static) |
| Table — control-flow + closed-loop | `tab:app_control_flow` / `tab:app_closed_loop` | `result/GEN/gen_eval_v4_llama.csv`, `result/GEN/gen_eval_v3_semantic.csv` |
| Table — multi-model | `tab:app_model_compare` | per-model `result/GEN/gen_eval_*.csv` |
| Table — JSON/CBOR/msgpack baseline | `tab:app_json_baseline` | `result/GEN/json_baseline_eval_v1.csv`, `result/TOKEN/cbor_msgpack_baseline.csv` |
| Table — random per-category | `tab:app_random_percat` | `result/GEN/random_eval_600.csv` |
| Table — real-world per-category | `tab:app_realworld_percat` | `result/GEN/candidates_realworld_v4.jsonl` |
| Table — full host ISA | `tab:full_isa` | `tools/backend_adapter.py` (static) |
| Fig — architecture | `fig:architecture` | `latex/fig1_tikz.tex` (TikZ) |
| Fig — lowering | `fig:lowering` | `latex/fig2_tikz.tex` (TikZ) |
| Fig — closed-loop FSM | `fig:fsm` | `latex/fig4_tikz.tex` (TikZ) |
| Fig — forest plot | `fig:forest_rates` | `figures/Fig11_forest_rates.pdf` ← all TSR CSVs |
| Fig — compression | `fig:compression` | `figures/Fig6_e1_compression.pdf` ← `token_compare_v3_tasks_v2.csv` |
| Fig — security ablation | `fig:ablation` | `figures/Fig7_e2_ablation_stacked.pdf` ← `result/E2_orthogonal/`, `result/E2/fuzzing.csv` |
| Fig — closed-loop (a)/(b) | `fig:closed_loop` | `figures/Fig8_e4_scr.pdf` ← `result/E4/e4_summary.csv`; `figures/Fig9_scr_curve.pdf` ← `result/E5_prior/e5_prior_matrix_final.csv` |
| Fig — gen + token | `fig:gen_token` | `figures/Fig10_combined_gen_token.pdf` ← `gen_eval_llama31_8b_v2_full.csv`, `token_compare_v3_tasks_v2.csv` |
| Fig — scalability ×3 | (in `sec:scalability`) | `figures/Fig_scalability_{length,devices,step_limit}.pdf` ← `result/scalability/d{1,2,3}_*.csv` |

---

## Section 1 — Introduction (`sec:intro`)

| Claim | Source file(s) | Generator | Recompute |
|---|---|---|---|
| "9.8× smaller than optimized JSON" | `result/GEN/json_baseline_eval_v1.csv` (zlib 106.71, bytecode 10.92) | `tools/run_json_baseline_eval.py` | `9.8x (zlib-JSON/bc)` |
| "halves interpretation energy" (48.7%) | `result/E_POWER/energy_summary.csv` | `tools/bench_energy.py` | `48.7% reduction` |
| "8,000 adversarial payloads" blocked | `result/E2/fuzzing.csv` | `tools/bench_e2_fuzzing.py` | `total payloads (8000)`, `escapes (0)` |
| "0.982 reliability on stochastic tasks" (best-of-3) | `result/GEN/success_at_k.csv` | `tools/bench_e4_scr.py` | `best-of-K@3` |
| "full pass rate on deterministic tasks" | `result/GEN/gen_eval_llama31_8b_v2_full_r2.csv` (113/113 post-repair) | `tools/run_generation_eval.py` + repair | `llama3.1:8b TSR-113 (post-repair, _r2)` |
| "<50 lines of adapter code" (ESP8266↔STM32) | `firmware/mvm_stm32.ino` vs `固件烧录/mvm_esp8266_guarded.ino` | — | manual diff |
| "running example → 14 bytes / 7 instructions" | `tools/mir_compiler.py` (`GTWAY 5; GTWAY 1; LIT 1; IOW 5; WAIT 500; IOR 1; HALT`) | — | `python tools/mir_compiler.py ... --emit-hex` |
| "204 verified outputs (113 + 91)" | 113 deterministic (`_r2`) + 91 passing closed-loop (`gen_eval_v3_semantic.csv`) | — | see §Prop.2 note |

> **Prop. 2 wording note.** Proposition 2 (`prop:consistency`) says "204 verified outputs
> (113 deterministic + 91 closed-loop)". The 91 is the **number of passing** closed-loop
> tasks (91/96), while the closed-loop **set size is 96** (Table `tab:app_closed_loop`).
> So "91 closed-loop" = the 91 that produced a verified-correct device state, not the set
> cardinality. 113 + 91 = 204. This is internally consistent but the noun "tasks" is
> slightly overloaded — see "Known imprecisions".

## Section 2 — Background and Design Space (`sec:background`)

| Claim | Source file(s) | Generator | Recompute |
|---|---|---|---|
| Table `tab:rw_comparison` — JSON+zlib 106.7 B | `result/GEN/json_baseline_eval_v1.csv` | `tools/run_json_baseline_eval.py` | `JSON zlib (106.7)` |
| Table `tab:rw_comparison` — CBOR 105.2 B | `result/GEN/json_baseline_eval_v1.csv` (cbor_bytes) | `tools/run_json_baseline_eval.py` | `CBOR (105.2)` |
| Table `tab:rw_comparison` — Arduino C 188.1 B | `result/GEN/arduino_c_baseline.csv` | `tools/bench_arduino_c_baseline.py` | `arduino mean bytes (188.1)` |
| Table `tab:rw_comparison` — LIR+LVM 10.9 B / ~2 KB | `result/GEN/json_baseline_eval_v1.csv` (m_bytecode_bytes); RAM = build report | — | `bytecode (10.9)` |
| Embedded-VM RAM figures (TinyVM/WAMR/…) | literature citations | — | descriptive |

## Section 3 — Efficiency-Driven Design: LIR and Compilation (`sec:lir`)

### 3.1–3.4 Representation, grammar, principles (static / design)

| Claim | Source | Recompute |
|---|---|---|
| "seven statement types" (EBNF) | `tools/mir_compiler.py` (`parse_program`) | read parser |
| device ids: water(1) temp(2) humidity(3) relay1(5) relay2(6) | `tools/mir_compiler.py` (`DEVICE_IDS`) | read map |
| 14-instruction bounded-execution profile | `tools/mir_compiler.py`, `tools/backend_adapter.py` (opcode table) | Table `tab:inst_set` |
| varint/zigzag encoding | `tools/mir_compiler.py` (`_emit_u`/`_emit_s`) | read functions |
| lowering rules (Table `tab:lowering`) | `tools/mir_compiler.py` (`compile_program`) | `python -m unittest test_mir_compiler` |

### 3.5 Encoding Advantages — Table `tab:encoding` (`sec:encoding`)

| Scenario (claim) | Source file(s) | Generator | Recompute |
|---|---|---|---|
| Raw LLM output: LIR 108.0 / JSON 285.9 B (2.6×) | `result/TOKEN/token_compare_v3_tasks_v2.csv` (`output_bytes`, format MIR/JSON) | `tools/measure_token_cost.py` | `LIR raw text (108.0)`, `JSON raw text (285.9)`, `2.6x raw text` |
| +zlib(9): LIR 86.1 / JSON 150.8 B (1.8×) | same, zlib level 9 on LF-normalized text | `tools/measure_token_cost.py` | `LIR zlib (86.1)`, `JSON raw zlib (150.8)`, `1.8x zlib text` |
| Cloud-compiled vs optimized JSON: 10.9 / 106.7 (9.8×) | `result/GEN/json_baseline_eval_v1.csv` | `tools/run_json_baseline_eval.py` | `bytecode (10.9)`, `JSON zlib (106.7)`, `9.8x (zlib-JSON/bc)` |
| Cloud-compiled vs raw-LLM zlib-JSON: 10.9 / 150.8 (13.8×) | above two | — | `13.8x (raw-zlib/bc)` |
| vs CBOR 105.2 (9.6×) | `result/GEN/json_baseline_eval_v1.csv` | — | `CBOR (105.2)`, `9.6x (CBOR/bc)` |
| NB-IoT 200 bps: 0.44 s vs 4.27 s | derived: 10.9·8/200, 106.7·8/200 | — | arithmetic (`verify.py`-style) |

> Appendix Table `tab:app_json_baseline` adds MessagePack 97.42 B and compact-JSON 127.18 B
> from `result/TOKEN/cbor_msgpack_baseline.csv` (recompute: `msgpack (97.42)`,
> `compact JSON (127.18)`). **Schema caveat (carried from the table footnote):** raw/zlib/CBOR
> rows use the hand-crafted minimal-schema JSON (raw 156.4 B); MessagePack and compact-JSON
> rows use the raw-LLM-output JSON (raw 285.9 B). The two baselines differ in schema.

---

## Section 4 — Security-Driven Design / Security Analysis (`sec:mvm`, `sec:security`)

| Claim | Source file(s) | Generator | Recompute |
|---|---|---|---|
| Table `tab:footprint` — ESP8266 ~2 KB RAM / ~4 KB flash / ~430 LOC / 16-level stack | Arduino IDE build report (manual) | — | INFO (manual) |
| Table `tab:footprint` — STM32F103C6 21,212 B flash (64%) / 2,740 B RAM (26%) | Arduino IDE build report; echoed in `latex/buildlog.txt:908` | — | INFO (manual) |
| Table `tab:footprint` — 64-level stack (STM32) | deepest nested test | — | INFO (manual) |
| four runtime guards + static verifier (not "6/7 guard bands") | `固件烧录/mvm_esp8266_guarded.ino`, `tools/backend_adapter.py` (`verify_subset`/`simulate_subset`) | — | read source |
| UABR = 1 within the model (Corollary `prop:uabr`) | proof (Prop. `thm:bounded`(2)) | — | analytic |

## Section 5 — Evaluation (`sec:evaluation`)

### Setup (`sec:setup`) — task sets

| Claim | Source file | Generator | Recompute (`wc -l`) |
|---|---|---|---|
| 113 deterministic tasks | `data/tasks_v2.jsonl` | `tools/generate_tasks_v2.py` | 113 |
| 96 closed-loop tasks (12 subcats) | `data/tasks_v3_expanded.jsonl` | `tools/generate_tasks_v3_expanded.py` | 96 |
| 15 control-flow tasks | `data/tasks_v4.jsonl` | `tools/generate_tasks_v4.py` | 15 |
| 600 random tasks (12 cats ×50) | `data/tasks_random_500.jsonl` | `tools/generate_tasks_random.py` | 600 |
| 29 real-world IoT tasks | `data/tasks_realworld.jsonl` | (hand-curated from HA/Tasmota/ESPHome/Arduino) | 29 |

> Note: the smaller 16-task closed-loop set (`data/tasks_v3_closed_loop.jsonl`) is the
> original seed; the paper's headline closed-loop number uses the **96-task expanded** set.

### Q1 Efficiency (`sec:exp1`)

| Claim | Source file(s) | Generator | Recompute |
|---|---|---|---|
| Compression weighted 2.6× / median 2.5× (Fig `fig:compression`) | `result/TOKEN/token_compare_v3_tasks_v2.csv` | `tools/measure_token_cost.py` → `tools/gen_figures_svg.py` | `2.6x raw text` |
| 9.8× over optimized JSON | `result/GEN/json_baseline_eval_v1.csv` | `tools/run_json_baseline_eval.py` | `9.8x (zlib-JSON/bc)` |
| 17.3× over Arduino C | `result/GEN/arduino_c_baseline.csv` | `tools/bench_arduino_c_baseline.py` | `arduino 17.3x` |
| Energy Table `tab:energy`: native 3.57 / bytecode 48.48 / JSON 94.57 µJ | `result/E_POWER/energy_summary.csv` | `tools/bench_energy.py` (UM25C 60 s windows) | `native/bytecode/json (…)` |
| 48.7% energy reduction; 1.95×; 13.6×/26.5× vs native | `result/E_POWER/energy_summary.csv` | `tools/bench_energy.py` | `48.7% reduction`, `1.95x ratio`, `bytecode 13.6x native` |
| Token cost (Table `tab:gen_results`): LIR 159.85/38.09/197.94, JSON 81.85/78.14/159.99, Py 83.85/19.96/103.81 | `result/TOKEN/token_compare_v3_tasks_v2.csv` | `tools/measure_token_cost.py` | `token MIR/JSON/PYTHON input/output` |
| Cache: 52 equiv tasks, LIR out 40.0 / JSON 77.5; 48% fewer | `result/TOKEN/token_compare_v3_tasks_v2_semantics_r2.csv` | `tools/analyze_token_semantics.py` | `three-way equiv (52)`, `MIR/JSON out-tokens`, `token saving` |
| Arduino C 188.1 B, 113/113 compile | `result/GEN/arduino_c_baseline.csv` | `tools/bench_arduino_c_baseline.py` | `arduino mean bytes`, `arduino valid` |

### Q2 Security (`sec:exp2`)

| Claim | Source file(s) | Generator | Recompute |
|---|---|---|---|
| Ablation Fig `fig:ablation`: UABR base 1.000 → no-auth 0.857 | `result/E2_orthogonal/e2_orthogonal_summary_final.csv` | `tools/bench_e2_orthogonal.py` → `tools/gen_figures_svg.py` | `base guarded UABR`, `no-auth UABR` |
| Fuzzing Table `tab:fuzzing`: 8000 payloads, 8×1000, overall 0.9999, 0 escapes | `result/E2/fuzzing.csv` | `tools/bench_e2_fuzzing.py --n 8000 --seed 42` | `total payloads`, `class … payloads`, `overall contained`, `escapes` |
| random_bytes 999/1000; unauthorized_io UABR 1.000 | `result/E2/fuzzing.csv` | `tools/bench_e2_fuzzing.py` | `random_bytes contained`, `unauthorized_io UABR` |
| interception ~50% verifier / ~50% runtime | `result/E2/fuzzing.csv` (`intercept_stage`) | `tools/bench_e2_fuzzing.py` | `verifier intercept ~50%` |
| avg 5.8 steps, 0.58% of L=1000, ~170× margin | `result/GEN/per_task_steps_v2.csv` | `tools/run_generation_eval.py` (per-task steps) | `avg exec steps`, `% of L`, `margin ~170x` |
| System ablation Table `tab:system_ablation`: Arduino 1.000/188.1; JSON 0.965/106.7; LIR 1.000/10.9 | `result/GEN/{arduino_c_baseline,json_baseline_eval_v1,gen_eval_llama31_8b_v2_full_r2}.csv` | resp. generators | `arduino…`, `JSON zlib`, `bytecode`, `llama … _r2` |
| best-of-3 recovers temp=1.0 to 0.982 | `result/GEN/success_at_k.csv` | `tools/bench_e4_scr.py` | `best-of-K@3` |

### Q3 Reliability (`sec:exp3reliability`)

| Claim | Source file(s) | Generator | Recompute |
|---|---|---|---|
| Closed-loop Fig `fig:closed_loop`(a): retry raises SCR (0.66→1.00) | `result/E4/e4_summary.csv` | `tools/bench_e4_scr.py` | `G3 …`, `G4 …`, `G1 …` |
| SAFE shunting Fig `fig:closed_loop`(b): guarded stable, noguard 0 across priors | `result/E5_prior/e5_prior_matrix_final.csv` | `tools/bench_scr_prior.py` | `noguard safe_ratio all 0` |
| JSON-real closed-loop fair baseline | `result/E4_json_real/e4_json_real_matrix_fair_final.csv` | `tools/bench_e4_json_real.py` | source map |
| Temperature Table `tab:temperature`: 1.000→0.847 (TSR), IR≥0.91 | `result/GEN/temperature_sweep_6pt_summary.csv` | `tools/bench_temperature_sweep.py` | `TSR@t`, `IRvalid@t`, `CI TSR@0.0/1.0` |
| Random 600: TSR 0.970 (582/600), IR 0.997, 7/12 cats at 100% | `result/GEN/random_eval_600.csv` | `run_ollama_generate.py`+`run_generation_eval.py` | `random total`, `categories at 100%` |
| deepseek-v4-pro random 0.987 (592/600) | `result/GEN/gen_eval_deepseek_v4_pro_random.csv` | `run_generation_eval.py` (MODEL=deepseek-v4-pro) | `deepseek-v4-pro TSR-600` |
| Real-world Table `tab:realworld`: v1 0.586/0.724, v4 0.793/0.828, JSON 0.862/1.000 | `result/GEN/candidates_realworld_v4.jsonl` (v1+v4), `result/GEN/json_realworld_eval.csv` | `tools/run_realworld_v4.py`, `tools/run_json_realworld.py` | `LIR v4/v1 …`, `JSON …` |
| Real-world sequential 17/19; closed-loop subset 6/10 | `result/GEN/candidates_realworld_v4.jsonl` | `tools/run_realworld_v4.py` | `verify.py` real-world block |
| Grammar Table `tab:grammar_constrained`: unconstrained 0.841, filtered 0.876, validity 0.950 | `result/GEN/grammar_constrained.csv` | `tools/bench_grammar_constrained.py` | `unconstrained first`, `grammar-filtered`, `avg grammar validity` |
| best-of-K 0.823/0.956/0.982/0.991/1.000 | `result/GEN/success_at_k.csv` | `tools/bench_e4_scr.py` | `best-of-K@1..5` |
| Control-flow Table `tab:app_control_flow`: 13/15 = 0.867 | `result/GEN/gen_eval_v4_llama.csv` | `run_generation_eval.py` | `control-flow TSR` |
| Closed-loop Table `tab:app_closed_loop`: 91/96 = 0.948 | `result/GEN/gen_eval_v3_semantic.csv` | `run_generation_eval.py` (v3 semantic subset) | `closed-loop TSR/IR (91/96)` |
| Multi-model Table `tab:app_model_compare`: llama 1.000, qwen3 0.903, ds-r1 1.000, ds-v4 0.991 | per-model `result/GEN/gen_eval_*.csv` | `run_generation_eval.py` | `… TSR-113` |
| Semantic pass (Table `tab:gen_results`): LIR 98/113, JSON 90/113, Py-basic 78/113, Py-detailed 113/113 | `result/TOKEN/token_compare_v3_tasks_v2_semantics_r2.csv`; `result/GEN/python_detailed_eval.csv` | `analyze_token_semantics.py`; `run_python_detailed_eval.py` | `LIR/JSON/Python-basic/detailed semantic` |
| Repair (Table `tab:gen_results`): success@1 100/113, success@2 13/113 | `result/GEN/gen_eval_llama31_8b_v2_full.csv` (first attempt) + `_r2` (post-repair) | `run_generation_eval.py`+`run_repair_eval.py` | `success@1`, `success@2` |
| Random per-cat Table `tab:app_random_percat` | `result/GEN/random_eval_600.csv` | `run_generation_eval.py` | `random total`, per-cat printout |
| Real-world per-cat Table `tab:app_realworld_percat` | `result/GEN/candidates_realworld_v4.jsonl` | `tools/run_realworld_v4.py` | manual per-cat |

### Q4 Portability (`sec:stm32`)

| Claim | Source file(s) | Generator | Recompute |
|---|---|---|---|
| STM32 21,212 B flash / 2,740 B RAM | Arduino IDE build report; `latex/buildlog.txt` | — | INFO (manual) |
| 3 bytecode programs OK on STM32 (HALT / GTWAY+IOW / GTWAY+IOR) | `firmware/test_stm32_lvm.py` (serial verification) | `firmware/mvm_stm32.ino` | INFO (hardware) |
| ESP8266 throughput 96.5 cmd/s, RTT 3.55 ms, p95 4.06 ms | `result/E10_deploy/throughput_summary.csv` | `tools/bench_*` (serial) | INFO printout |

## Formal model (`sec:formal`, `app:proofs`, `app:rules`)

| Claim | Source | Recompute |
|---|---|---|
| 14-instruction set, 17 transition rules | `tools/backend_adapter.py` (`decode_program`/`verify_subset`/`simulate_subset`) | `python -m unittest test_mir_compiler test_realworld` |
| Determinism / Progress / Bounded (Props 1–3) | hand proofs over the rule set | analytic |
| Compiler–VM consistency (Prop. 2), 204 verified outputs | 113 (`_r2`) + 91 (`gen_eval_v3_semantic.csv`) | `llama … _r2`, `closed-loop TSR (91/96)` |

---

## Core data invariants

Structural properties of the pipeline (enforced by the compiler/VM, checked by the test suite).

| Property | Enforced by | Verified by |
|---|---|---|
| `set` targets ∈ {relay1, relay2} | `tools/mir_compiler.py` | `test_mir_compiler.py` |
| `set` values ∈ {0, 1} | `tools/mir_compiler.py` | `test_mir_compiler.py` |
| `require cap(device)` must name a valid device | `tools/mir_compiler.py` | `test_mir_compiler.py` |
| IOW/IOR/READBACK require prior GTWAY authorization | `tools/mir_compiler.py`, `tools/backend_adapter.py`, `固件烧录/mvm_esp8266_guarded.ino` | `test_mir_compiler.py`, E2 ablation, fuzzing |
| `retry N` / `repeat N` require N ≥ 1 | `tools/mir_compiler.py` | `test_mir_compiler.py` |
| Jump targets within program bounds | `tools/mir_compiler.py` (assemble), `tools/backend_adapter.py` (`verify_subset`) | `test_mir_compiler.py`, fuzzing (jump_oob) |
| Stack depth ≥ 0 throughout execution | `tools/backend_adapter.py`, firmware | fuzzing (stack_underflow) |
| Opcode ∈ defined 14-instruction set | `tools/backend_adapter.py`, firmware | fuzzing (bad_opcode) |
| Varint encoding well-formed | `tools/backend_adapter.py`, firmware | fuzzing (truncated_varint) |
| Every execution terminates in ≤ L steps | step counter in `simulate_subset` / firmware | fuzzing (infinite_loop), Prop. 3 |

---

## Reproduction commands

> All `tools/` scripts use only the Python standard library except the CBOR/MsgPack
> baseline (`pip install -r requirements.txt`). LLM steps need a local Ollama on
> `127.0.0.1:11434`; DeepSeek steps use `tools/deepseek_client.py`. Run from `tools/`.

```bash
# ---- Task sets ----
cd tools && python generate_tasks_v2.py            # data/tasks_v2.jsonl (113)
cd tools && python generate_tasks_v3_expanded.py   # data/tasks_v3_expanded.jsonl (96)
cd tools && python generate_tasks_v4.py            # data/tasks_v4.jsonl (15)
cd tools && python generate_tasks_random.py        # data/tasks_random_500.jsonl (600)

# ---- 113-task generation + eval + repair (LLaMA-3.1-8B) ----
cd tools && python run_ollama_generate.py  --model llama3.1:8b --input ../data/tasks_v2.jsonl \
              --output ../result/GEN/candidates_llama31_8b_v2_full.jsonl
cd tools && python run_generation_eval.py  --candidates ../result/GEN/candidates_llama31_8b_v2_full.jsonl \
              --output ../result/GEN/gen_eval_llama31_8b_v2_full.csv          # first-attempt 100/113
cd tools && python run_repair_eval.py      --eval ../result/GEN/gen_eval_llama31_8b_v2_full.csv \
              --output ../result/GEN/gen_eval_llama31_8b_v2_full_r2.csv       # post-repair 113/113

# ---- Efficiency ----
cd tools && python measure_token_cost.py                # result/TOKEN/token_compare_v3_tasks_v2.csv
cd tools && python analyze_token_semantics.py           # ..._semantics_r2.csv (52-task cache + semantic)
cd tools && python run_json_baseline_eval.py            # result/GEN/json_baseline_eval_v1.csv
cd tools && python bench_cbor_msgpack.py                # result/TOKEN/cbor_msgpack_baseline.csv
cd tools && python bench_arduino_c_baseline.py          # result/GEN/arduino_c_baseline.csv
cd tools && python run_python_detailed_eval.py          # result/GEN/python_detailed_eval.csv
cd tools && python bench_energy.py                      # result/E_POWER/energy_summary.csv (UM25C)
cd tools && python bench_scalability.py                 # result/scalability/d{1,2,3}_*.csv

# ---- Security ----
cd tools && python bench_e2_orthogonal.py               # result/E2_orthogonal/e2_orthogonal_summary_final.csv
cd tools && python bench_e2_fuzzing.py --n 8000 --seed 42 --out ../result/E2/fuzzing.csv

# ---- Reliability ----
cd tools && python bench_temperature_sweep.py           # result/GEN/temperature_sweep_6pt*.csv
cd tools && python bench_e4_scr.py                      # result/GEN/success_at_k.csv + result/E4/e4_summary.csv
cd tools && python bench_scr_prior.py                   # result/E5_prior/e5_prior_matrix_final.csv
cd tools && python bench_grammar_constrained.py         # result/GEN/grammar_constrained.csv
cd tools && python run_realworld_v4.py                  # result/GEN/candidates_realworld_v4.jsonl (v1+v4)
cd tools && python run_json_realworld.py                # result/GEN/json_realworld_eval.csv

# ---- Multi-model (113 + random-600) ----
cd tools && python run_ollama_generate.py --model qwen3:8b ...  ; python run_generation_eval.py ...
cd tools && python run_deepseek_generate.py ...                 ; python run_generation_eval.py ...

# ---- Verify ----
python tools/recompute_all.py      # re-derive & PASS/MISMATCH every table/figure number
cd latex && python verify.py       # Wilson CIs + arithmetic

# ---- Figures / manuscript ----
cd tools && python gen_figures_svg.py ; python gen_tikz_figs.py ; python gen_arch_figures.py
cd latex && latexmk -pdf main.tex
```

---

## Diagram sources (current figure file names)

| Figure | Label | File | Generator |
|---|---|---|---|
| System architecture | `fig:architecture` | `latex/fig1_tikz.tex` (TikZ `\input`) | hand-authored TikZ |
| LIR→bytecode lowering | `fig:lowering` | `latex/fig2_tikz.tex` (TikZ `\input`) | hand-authored TikZ |
| Closed-loop FSM | `fig:fsm` | `latex/fig4_tikz.tex` (TikZ `\input`) | hand-authored TikZ |
| Compression per-task | `fig:compression` | `figures/Fig6_e1_compression.pdf` | `gen_figures_svg.py` ← `token_compare_v3_tasks_v2.csv` |
| Security ablation | `fig:ablation` | `figures/Fig7_e2_ablation_stacked.pdf` | `gen_figures_svg.py` ← `E2_orthogonal/`, `E2/fuzzing.csv` |
| Closed-loop SCR | `fig:closed_loop`(a) | `figures/Fig8_e4_scr.pdf` | `gen_figures_svg.py` ← `E4/e4_summary.csv` |
| SAFE shunting | `fig:closed_loop`(b) | `figures/Fig9_scr_curve.pdf` | `gen_figures_svg.py` ← `E5_prior/e5_prior_matrix_final.csv` |
| Gen + token | `fig:gen_token` | `figures/Fig10_combined_gen_token.pdf` | `gen_figures_svg.py` ← `gen_eval_…_v2_full.csv`, `token_compare…csv` |
| Forest plot | `fig:forest_rates` | `figures/Fig11_forest_rates.pdf` | `gen_figures_svg.py` ← all TSR CSVs |
| Scalability ×3 | (`sec:scalability`) | `figures/Fig_scalability_{length,devices,step_limit}.pdf` | `gen_figures_svg.py` ← `scalability/d{1,2,3}_*.csv` |

> Bibliography: `main.tex` uses `\bibliography{cas-refs}` → `latex/cas-refs.bib`
> (the old `references.bib` was removed; do not cite it).

---

## Known imprecisions (flagged, not blocking)

`tools/recompute_all.py` reports these as INFO; they are minor and do not affect any
headline claim, but are listed here for an honest reviewer trail.

1. **Temperature CI lower bound at temp=1.0.** Paper prints `[0.805, 0.881]`; exact Wilson
   on 287/339 gives `[0.804, 0.881]`. 0.001 rounding difference.
2. **Closed-loop 95% CI.** Paper prints `[0.886, 0.979]` for 91/96; the recompute Wilson
   gives `[0.884, 0.978]`. Rounding-method difference, ≤0.002.
3. **Scalability "per-op" figures (`sec:scalability`).** Paper states bytecode "3.47 B per
   operation (R²=0.999)" and "1.74 steps per operation". The **3.47 / 1.74** values are the
   *ratio at n=50* (173/50, 87/50), whereas the **OLS regression slope** is **3.33 B/op /
   1.67 steps/op**; the R²=0.999 belongs to the regression line, not the ratio. The two are
   conflated in one sentence. Both numbers are individually correct; recommend rewording to
   "≈3.33 B/op (regression slope, R²>0.999), ≈3.5 B/op including fixed header at n=50".
4. **IR-validity non-monotonicity (Table `tab:temperature`).** IR-valid rises from 0.914
   (temp 0.8) to 0.926 (temp 1.0). This is real sampling noise (n=339), faithfully reported;
   `latex/verify.py` flags it as a non-monotonic point — expected, not an error.
5. **Noun overload "91 closed-loop tasks" (Prop. 2 / `sec:intro`).** 91 = number of passing
   closed-loop tasks (of 96); 204 = 113 + 91. Internally consistent; consider "91 verified
   closed-loop outputs" to avoid reading 91 as the set size.

## Stale artifacts to ignore (decoys — NOT paper sources)

These files exist in `result/` but are superseded; the recompute script deliberately does
**not** read them:

- `result/GEN/realworld_eval.csv` (30 rows incl. stale `RW_030`) — real-world numbers come
  from `candidates_realworld_v4.jsonl` (29 tasks × {v1,v4}); the JSON baseline restricts
  `json_realworld_eval.csv` to the 29 v4 ids.
- `result/GEN/gen_eval_v3_expanded_llama.csv` / `…_retry_until_pass.csv` (TSR 0.52/0.50) —
  the headline closed-loop 91/96 comes from `gen_eval_v3_semantic.csv`.
- `result/GEN/gen_eval_llama31_8b_v2_full.csv` is **first-attempt** (100/113); the headline
  TSR=1.000 is the **post-repair** `…_v2_full_r2.csv` (113/113).
- `result/_archive/**`, `result/GEN/temperature_sweep.csv` (non-6pt), `token_compare_v1.csv`.



