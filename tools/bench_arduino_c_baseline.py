#!/usr/bin/env python3
"""
Arduino C baseline evaluation (M2 experiment).

Asks LLM to generate Arduino C code for hardware control tasks.
Measures output size and compilation feasibility.
Compares with LIR -> compact bytecode path.
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path
from typing import List

from ollama_client import ollama_generate
from run_generation_eval import load_jsonl

sys.path.insert(0, str(Path(__file__).resolve().parent))

ARDUINO_SYSTEM_PROMPT = """You generate Arduino C code for hardware control tasks.

Rules:
1. Output only valid Arduino C code (setup + loop functions).
2. Use digitalWrite(), digitalRead(), analogRead(), delay() for I/O.
3. Pin mappings: relay1=D1(GPIO5), relay2=D2(GPIO4), water_sensor=A0, temperature_sensor=A1, humidity_sensor=A2.
4. Output ONLY the code, no explanation, no markdown fences.
5. The code must compile and run on ESP8266.
6. Use Serial.println() to output sensor readings.
7. Keep the code minimal - only what the task requires.
"""

USER_TEMPLATE = """Task: {prompt}
Pins: relay1=D1, relay2=D2, water_sensor=A0, temperature_sensor=A1, humidity_sensor=A2

Write the Arduino C code:"""


def extract_code(text: str) -> str:
    """Extract code from LLM output, removing markdown fences."""
    import re
    # Remove markdown code fences
    text = re.sub(r"```(?:c|cpp|arduino)?\s*\n?", "", text)
    return text.strip()


def has_arduino_structure(code: str) -> bool:
    """Check if code has basic Arduino structure."""
    return "void setup()" in code or "void setup ()" in code


def main() -> int:
    parser = argparse.ArgumentParser(description="Arduino C baseline evaluation")
    parser.add_argument("--model", default="llama3.1:8b")
    parser.add_argument("--tasks", default=str(Path(__file__).resolve().parent.parent / "data" / "tasks_v2.jsonl"))
    parser.add_argument("--temperature", type=float, default=0.0)
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--out", default=str(Path(__file__).resolve().parent.parent / "result" / "GEN" / "arduino_c_baseline.csv"))
    args = parser.parse_args()

    tasks = load_jsonl(Path(args.tasks))
    if args.limit > 0:
        tasks = tasks[:args.limit]

    results = []
    n_tasks = len(tasks)

    for i, task in enumerate(tasks):
        tid = task["task_id"]
        prompt = USER_TEMPLATE.format(prompt=task["prompt"])

        resp = ollama_generate(args.model, prompt, system=ARDUINO_SYSTEM_PROMPT, temperature=args.temperature)
        raw_output = resp.get("response", "")
        code = extract_code(raw_output)

        output_bytes = len(code.encode("utf-8"))
        valid_structure = has_arduino_structure(code)

        results.append({
            "task_id": tid,
            "category": task["category"],
            "output_bytes": output_bytes,
            "valid_structure": int(valid_structure),
            "code": code[:200],  # First 200 chars for inspection
        })

        if (i + 1) % 50 == 0 or i == n_tasks - 1:
            avg_bytes = sum(r["output_bytes"] for r in results) / len(results)
            valid_cnt = sum(r["valid_structure"] for r in results)
            print(f"  [{i+1}/{n_tasks}] avg_bytes={avg_bytes:.0f} valid_structure={valid_cnt}/{i+1}")

    # Write CSV
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["task_id", "category", "output_bytes", "valid_structure", "code"])
        writer.writeheader()
        writer.writerows(results)

    # Summary
    n = len(results)
    avg_bytes = sum(r["output_bytes"] for r in results) / n
    valid_cnt = sum(r["valid_structure"] for r in results)

    # Compare with LIR bytecode size
    lir_bytecode_avg = 10.9  # From paper data

    print(f"\n{'='*60}")
    print(f"Arduino C Baseline ({n} tasks, model={args.model})")
    print(f"{'='*60}")
    print(f"  Avg output bytes:     {avg_bytes:.1f}")
    print(f"  Valid structure:      {valid_cnt}/{n} = {valid_cnt/n:.3f}")
    print(f"  LIR bytecode avg:     {lir_bytecode_avg:.1f} bytes")
    print(f"  Ratio (C/bytecode):   {avg_bytes/lir_bytecode_avg:.1f}x")

    # Per-category
    from collections import defaultdict
    cats = defaultdict(list)
    for r in results:
        cats[r["category"]].append(r["output_bytes"])
    print(f"\nPer-category avg bytes:")
    for cat, vals in sorted(cats.items()):
        print(f"  {cat}: {sum(vals)/len(vals):.0f}")

    print(f"\nOutput: {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
