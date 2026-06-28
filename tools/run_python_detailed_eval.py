#!/usr/bin/env python3
"""
Evaluate Python baseline with detailed prompt (12 rules) vs basic prompt (2 rules).
This is the prompt fairness ablation experiment (P1-#5).

Tests whether Python's 0.690 pass rate improves with a prompt of equivalent
detail to LIR's 12-rule prompt.

Usage:
  python run_python_detailed_eval.py                      # run both, compare
  python run_python_detailed_eval.py --basic-only         # run basic only
  python run_python_detailed_eval.py --detailed-only      # run detailed only
  python run_python_detailed_eval.py --model qwen3:8b     # different model
"""
from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Optional

sys.path.insert(0, str(Path(__file__).resolve().parent))

from ollama_client import ollama_generate
from run_generation_eval import (
    compile_expected_payloads,
    evaluate_candidate,
    expected_signature,
    load_jsonl,
)
from mir_compiler import compile_source

# --- Python Prompts ---

PYTHON_BASIC_PROMPT = """You generate compact Python-like control snippets for hardware control tasks.
Output only Python code.
Use only direct imperative control statements that fully represent the task.
"""

PYTHON_DETAILED_PROMPT = """You generate compact Python-like control snippets for hardware control tasks.
Follow these rules exactly:
1. Output only Python code. No explanation, no markdown fences.
2. Use only devices from the allow-list: relay1, relay2, water_sensor, temperature_sensor, humidity_sensor.
3. Every accessed device must first be declared using require_cap("device_name").
4. Use only these statements:
   - require_cap("device") -- declare device access
   - set("device", 0|1) -- set relay/actuator state
   - read("device") -- read sensor/relay value
   - wait(ms) -- wait milliseconds
   - readback("device", expected) -- verify device state
   - retry(times, body) -- retry body up to N times
   - halt() -- stop execution, must be last statement
5. Only relay1/relay2 may appear as the first argument of set().
6. The program must be a single function named task_N(task_id).
7. End every task with halt().
8. Do not add extra actions not explicitly required by the instruction.
9. If the instruction says "wait then read", the program must be exactly wait -> read -> halt after capabilities.
10. IMPORTANT retry vs repeat: retry for "try/verify/confirm" tasks; do not use repeat.
"""

PYTHON_USER_TEMPLATE = """Task ID: {task_id}
Allowed devices: {allowed_devices}
Instruction: {prompt}

Generate one valid Python control snippet.
"""


def extract_python_code(text: str) -> str:
    """Extract Python code from LLM response, stripping markdown fences."""
    cleaned = text.strip()
    m = re.search(r"```(?:python)?\s*\n?(.*?)```", cleaned, re.DOTALL)
    if m:
        return m.group(1).strip()
    return cleaned


def python_to_mir(python_code: str, task_id: str, allowed_devices: list[str]) -> Optional[str]:
    """Convert Python control snippet to LIR for evaluation.

    This is a best-effort translation for evaluation purposes.
    Handles the basic constructs: require_cap, set, read, wait, readback, retry, halt.
    """
    lines = python_code.strip().split("\n")
    mir_lines = [f"task {task_id} {{"]
    in_retry = False
    retry_indent = 0

    for line in lines:
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue

        # Skip function def
        if stripped.startswith("def "):
            continue

        # require_cap
        m = re.match(r'require_cap\(["\'](\w+)["\']\)', stripped)
        if m:
            mir_lines.append(f"  require cap({m.group(1)})")
            continue

        # set
        m = re.match(r'set\(["\'](\w+)["\']\s*,\s*(\d+)\)', stripped)
        if m:
            indent = "    " if in_retry else "  "
            mir_lines.append(f"{indent}set {m.group(1)} = {m.group(2)}")
            continue

        # read
        m = re.match(r'read\(["\'](\w+)["\']\)', stripped)
        if m:
            indent = "    " if in_retry else "  "
            mir_lines.append(f"{indent}read {m.group(1)}")
            continue

        # wait
        m = re.match(r'wait\((\d+)\)', stripped)
        if m:
            indent = "    " if in_retry else "  "
            mir_lines.append(f"{indent}wait {m.group(1)}ms")
            continue

        # readback
        m = re.match(r'readback\(["\'](\w+)["\']\s*,\s*(\d+)\)', stripped)
        if m:
            indent = "    " if in_retry else "  "
            mir_lines.append(f"{indent}readback {m.group(1)} expect {m.group(2)}")
            continue

        # retry
        m = re.match(r'retry\((\d+)\s*,', stripped)
        if m:
            mir_lines.append(f"  retry {m.group(1)} times {{")
            in_retry = True
            continue

        # halt
        if stripped == "halt()":
            if in_retry:
                mir_lines.append("  }")
                in_retry = False
            mir_lines.append("  halt")
            continue

        # Closing brace of retry
        if stripped == "}" and in_retry:
            mir_lines.append("  }")
            in_retry = False
            continue

    # Ensure proper closing
    if in_retry:
        mir_lines.append("  }")
    mir_lines.append("}")

    return "\n".join(mir_lines)


def run_python_eval(
    tasks: list[dict],
    system_prompt: str,
    model: str,
    temperature: float,
    label: str,
    expected_map: dict,
    sig_cache: dict,
) -> list[dict]:
    """Run Python evaluation and return results."""
    results = []
    n_tasks = len(tasks)

    for i, task in enumerate(tasks):
        tid = task["task_id"]
        user_prompt = PYTHON_USER_TEMPLATE.format(
            task_id=tid,
            allowed_devices=", ".join(task["allowed_devices"]),
            prompt=task["prompt"],
        )
        resp = ollama_generate(
            model, user_prompt, system=system_prompt, temperature=temperature
        )
        python_code = resp.get("response", "")
        extracted = extract_python_code(python_code)

        # Convert to LIR for evaluation
        mir_text = python_to_mir(extracted, tid, task["allowed_devices"])

        if mir_text:
            eval_result = evaluate_candidate(
                task, expected_map[tid], sig_cache[tid], 1, mir_text
            )
        else:
            eval_result = {
                "ir_valid": 0,
                "compile_pass": 0,
                "verify_pass": 0,
                "execution_pass": 0,
                "task_success": 0,
            }

        row = {
            "task_id": tid,
            "category": task["category"],
            "prompt_version": label,
            "ir_valid": int(eval_result.get("ir_valid", 0)),
            "compile_pass": int(eval_result.get("compile_pass", 0)),
            "verify_pass": int(eval_result.get("verify_pass", 0)),
            "execution_pass": int(eval_result.get("execution_pass", 0)),
            "task_success": int(eval_result.get("task_success", 0)),
            "python_code": extracted,
            "mir_translation": mir_text or "",
        }
        results.append(row)

        if (i + 1) % 20 == 0 or i == n_tasks - 1:
            succ = sum(r["task_success"] for r in results)
            print(f"  [{label}] [{i+1}/{n_tasks}] task_success={succ}/{i+1} = {succ/(i+1):.3f}")

    return results


def print_summary(results: list[dict], label: str) -> None:
    """Print summary statistics."""
    n = len(results)
    metrics = ["ir_valid", "compile_pass", "verify_pass", "execution_pass", "task_success"]
    print(f"\n{'='*60}")
    print(f"{label} ({n} tasks)")
    print(f"{'='*60}")
    for m in metrics:
        cnt = sum(r[m] for r in results)
        print(f"  {m}: {cnt}/{n} = {cnt/n:.3f}")

    # Per-category
    cats = defaultdict(list)
    for r in results:
        cats[r["category"]].append(r["task_success"])

    print(f"\nPer-category task_success:")
    for cat, vals in sorted(cats.items()):
        s = sum(vals)
        print(f"  {cat}: {s}/{len(vals)} = {s/len(vals):.3f}")

    # Error analysis
    failures = [r for r in results if not r["task_success"]]
    if failures:
        print(f"\nFailure analysis ({len(failures)} failures):")
        error_types = Counter()
        for r in failures:
            if not r["ir_valid"]:
                error_types["FORMAT_ERROR"] += 1
            elif not r["task_success"]:
                error_types["TASK_SIGNATURE_MISMATCH"] += 1
        for etype, cnt in error_types.most_common():
            print(f"  {etype}: {cnt}")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Python baseline prompt fairness ablation"
    )
    parser.add_argument("--model", default="llama3.1:8b")
    parser.add_argument(
        "--tasks",
        default=str(
            Path(__file__).resolve().parent.parent / "data" / "tasks_v2.jsonl"
        ),
    )
    parser.add_argument("--temperature", type=float, default=0.0)
    parser.add_argument("--limit", type=int, default=0, help="Limit tasks (0=all)")
    parser.add_argument("--basic-only", action="store_true")
    parser.add_argument("--detailed-only", action="store_true")
    parser.add_argument(
        "--out",
        default=str(
            Path(__file__).resolve().parent.parent
            / "result"
            / "GEN"
            / "python_detailed_eval.csv"
        ),
    )
    args = parser.parse_args()

    tasks = load_jsonl(Path(args.tasks))
    if args.limit > 0:
        tasks = tasks[:args.limit]

    expected_map = compile_expected_payloads(tasks)
    sig_cache = {task["task_id"]: expected_signature(task) for task in tasks}

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    all_results = []

    # Run basic prompt
    if not args.detailed_only:
        print(f"Running basic Python prompt (2 rules)...")
        results_basic = run_python_eval(
            tasks, PYTHON_BASIC_PROMPT, args.model, args.temperature,
            "basic", expected_map, sig_cache,
        )
        all_results.extend(results_basic)
        print_summary(results_basic, "Python basic (2 rules)")

    # Run detailed prompt
    if not args.basic_only:
        print(f"\nRunning detailed Python prompt (12 rules)...")
        results_detailed = run_python_eval(
            tasks, PYTHON_DETAILED_PROMPT, args.model, args.temperature,
            "detailed", expected_map, sig_cache,
        )
        all_results.extend(results_detailed)
        print_summary(results_detailed, "Python detailed (12 rules)")

    # Comparison
    if not args.basic_only and not args.detailed_only:
        print(f"\n{'='*60}")
        print("COMPARISON: basic vs detailed Python prompt")
        print(f"{'='*60}")

        cats_basic = defaultdict(list)
        cats_detail = defaultdict(list)
        for r in results_basic:
            cats_basic[r["category"]].append(r["task_success"])
        for r in results_detailed:
            cats_detail[r["category"]].append(r["task_success"])

        all_cats = sorted(set(list(cats_basic.keys()) + list(cats_detail.keys())))
        print(f"{'Category':<30} {'Basic':>8} {'Detail':>8} {'Delta':>8}")
        print(f"{'-'*54}")
        for cat in all_cats:
            b_s = sum(cats_basic.get(cat, [0]))
            b_n = len(cats_basic.get(cat, [1]))
            d_s = sum(cats_detail.get(cat, [0]))
            d_n = len(cats_detail.get(cat, [1]))
            b_r = b_s / b_n if b_n else 0
            d_r = d_s / d_n if d_n else 0
            print(f"  {cat:<28} {b_r:>8.3f} {d_r:>8.3f} {d_r-b_r:>+8.3f}")

        total_b = sum(r["task_success"] for r in results_basic) / len(results_basic)
        total_d = sum(r["task_success"] for r in results_detailed) / len(results_detailed)
        print(f"{'-'*54}")
        print(f"  {'TOTAL':<28} {total_b:>8.3f} {total_d:>8.3f} {total_d-total_b:>+8.3f}")

    # Write CSV
    fieldnames = [
        "task_id", "category", "prompt_version", "ir_valid", "compile_pass",
        "verify_pass", "execution_pass", "task_success", "python_code", "mir_translation",
    ]
    with out_path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(all_results)

    print(f"\nOutput: {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
