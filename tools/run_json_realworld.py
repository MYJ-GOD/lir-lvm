#!/usr/bin/env python3
"""
Run JSON + Schema baseline on real-world IoT tasks.
Generates JSON candidates via LLM, evaluates them, and compares with LIR results.

This is the "industrial baseline" comparison the paper needs:
  JSON + schema validation + retry loop vs LIR + bytecode + LVM

Usage:
  python run_json_realworld.py
  python run_json_realworld.py --model qwen3:8b
  python run_json_realworld.py --limit 5   # quick test
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
import zlib
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from ollama_client import ollama_generate
from run_json_baseline_eval import (
    evaluate_json_candidate,
    get_expected_relay_state,
    wilson_ci,
)
from run_generation_eval import load_jsonl


# JSON system prompt (equivalent detail to LIR prompt)
JSON_SYSTEM_PROMPT = """You generate JSON control programs for hardware control tasks.
Output only JSON. No explanation, no markdown fences.
The JSON object must have exactly three fields: "task" (string), "cap" (array of device names), "body" (array of operations).
Allowed operations (each with an "op" field):
  {"op":"set","dev":"<d>","to":0|1} -- set relay/actuator state
  {"op":"read","dev":"<d>"} -- read sensor/relay value
  {"op":"wait","ms":<int>} -- wait milliseconds
  {"op":"readback","dev":"<d>","expect":0|1} -- verify device state (must be last in retry body)
  {"op":"retry","times":<int>,"do":[<ops>]} -- retry body up to N times, body must end with readback
  {"op":"repeat","times":<int>,"do":[<ops>]} -- repeat body exactly N times unconditionally
  {"op":"halt"} -- stop execution, must be last in body
Rules: declare all used devices in "cap"; body must end with halt; retry body must end with readback.
IMPORTANT retry vs repeat: retry for "try/verify/ensure/confirm/read back" tasks; repeat for "repeat/loop/toggle/do N times" tasks.
"""

JSON_USER_TEMPLATE = """Task ID: {task_id}
Allowed devices: {allowed_devices}
Instruction: {prompt}

Generate one valid JSON control program."""


def main() -> int:
    parser = argparse.ArgumentParser(
        description="JSON baseline evaluation on real-world IoT tasks"
    )
    parser.add_argument("--model", default="llama3.1:8b")
    parser.add_argument(
        "--tasks",
        default=str(
            Path(__file__).resolve().parent.parent / "data" / "tasks_realworld.jsonl"
        ),
    )
    parser.add_argument("--temperature", type=float, default=0.0)
    parser.add_argument("--limit", type=int, default=0, help="Limit tasks (0=all)")
    parser.add_argument(
        "--out",
        default=str(
            Path(__file__).resolve().parent.parent
            / "result"
            / "GEN"
            / "json_realworld_eval.csv"
        ),
    )
    args = parser.parse_args()

    tasks = load_jsonl(Path(args.tasks))
    if args.limit > 0:
        tasks = tasks[:args.limit]

    # Pre-compute expected relay states
    expected_relays = {}
    for task in tasks:
        expected_relays[task["task_id"]] = get_expected_relay_state(task)

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    results = []
    n_tasks = len(tasks)

    for i, task in enumerate(tasks):
        tid = task["task_id"]
        prompt = JSON_USER_TEMPLATE.format(
            task_id=tid,
            allowed_devices=", ".join(task["allowed_devices"]),
            prompt=task["prompt"],
        )
        resp = ollama_generate(
            args.model, prompt, system=JSON_SYSTEM_PROMPT, temperature=args.temperature
        )
        json_text = resp.get("response", "")

        eval_result = evaluate_json_candidate(task, expected_relays[tid], json_text)
        results.append(eval_result)

        if (i + 1) % 10 == 0 or i == n_tasks - 1:
            succ = sum(int(r["task_success"]) for r in results)
            print(f"  [{i+1}/{n_tasks}] task_success={succ}/{i+1} = {succ/(i+1):.3f}")

    # Write CSV
    fieldnames = [
        "task_id", "category", "ir_valid", "structural_ok", "execution_pass",
        "task_success", "error_stage", "error_code", "hint",
        "raw_bytes", "compact_bytes", "zlib_bytes", "cbor_bytes", "m_bytecode_bytes",
    ]
    with out_path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(results)

    # Summary
    n = len(results)
    ir_valid = sum(int(r["ir_valid"]) for r in results)
    struct_ok = sum(int(r["structural_ok"]) for r in results)
    exec_pass = sum(int(r["execution_pass"]) for r in results)
    task_succ = sum(int(r["task_success"]) for r in results)

    print(f"\n{'='*60}")
    print(f"JSON Baseline on Real-World Tasks ({n} tasks, model={args.model}, temp={args.temperature})")
    print(f"{'='*60}")
    print(f"  ir_valid:       {ir_valid}/{n} = {ir_valid/n:.3f}")
    print(f"  structural_ok:  {struct_ok}/{n} = {struct_ok/n:.3f}")
    print(f"  execution_pass: {exec_pass}/{n} = {exec_pass/n:.3f}")
    print(f"  task_success:   {task_succ}/{n} = {task_succ/n:.3f}")

    lo, hi = wilson_ci(task_succ, n)
    print(f"  task_success 95% CI: [{lo:.3f}, {hi:.3f}]")

    # Per-category
    cats = defaultdict(list)
    for r in results:
        cats[r["category"]].append(int(r["task_success"]))

    print(f"\nPer-category task_success:")
    for cat, vals in sorted(cats.items()):
        s = sum(vals)
        print(f"  {cat}: {s}/{len(vals)} = {s/len(vals):.3f}")

    # Error breakdown
    errors = Counter(r["error_code"] for r in results if r.get("error_code"))
    if errors:
        print(f"\nError breakdown:")
        for code, cnt in errors.most_common():
            print(f"  {code}: {cnt}")

    # Size comparison (for structurally valid JSON)
    valid_rows = [r for r in results if int(r.get("structural_ok", 0))]
    if valid_rows:
        avg_raw = sum(int(r["raw_bytes"]) for r in valid_rows) / len(valid_rows)
        avg_zlib = sum(int(r["zlib_bytes"]) for r in valid_rows) / len(valid_rows)
        avg_mbc = sum(int(r["m_bytecode_bytes"]) for r in valid_rows if int(r.get("m_bytecode_bytes", 0))) / max(sum(1 for r in valid_rows if int(r.get("m_bytecode_bytes", 0))), 1)
        print(f"\nSize comparison (structurally valid JSON, n={len(valid_rows)}):")
        print(f"  Avg raw JSON:     {avg_raw:.1f} bytes")
        print(f"  Avg zlib JSON:    {avg_zlib:.1f} bytes")
        print(f"  Avg M-bytecode:   {avg_mbc:.1f} bytes")
        if avg_mbc > 0:
            print(f"  Compression:      {avg_zlib/avg_mbc:.1f}x")

    # Comparison table
    print(f"\n{'='*60}")
    print("Comparison: LIR vs JSON on real-world tasks")
    print(f"{'='*60}")
    print(f"{'Metric':<30} {'LIR':>10} {'JSON':>10}")
    print(f"{'-'*50}")
    print(f"{'task_success_rate':<30} {'0.567*':>10} {task_succ/n:>10.3f}")
    print(f"{'(sequential tasks)':<30} {'1.000*':>10} {'---':>10}")
    print(f"{'(retry/readback tasks)':<30} {'0.000*':>10} {'---':>10}")
    print(f"\n* LIR results from paper Table 15 (v1 prompt)")
    print(f"  JSON results from this run (v4-equivalent prompt)")

    print(f"\nOutput: {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
