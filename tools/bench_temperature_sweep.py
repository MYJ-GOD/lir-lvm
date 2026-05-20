#!/usr/bin/env python3
"""
Temperature sweep experiment: run generation at multiple temperatures,
evaluate pass rates, and report mean ± std dev.
"""
from __future__ import annotations

import argparse
import csv
import json
import statistics
import sys
from pathlib import Path
from typing import Dict, List

from ollama_client import ollama_generate
from run_generation_eval import (
    compile_expected_payloads,
    evaluate_candidate,
    expected_signature,
    load_jsonl,
    normalize_candidate_mir,
)
from mir_compiler import compile_source, MirCompilerError

sys.path.insert(0, str(Path(__file__).resolve().parent))


def parse_prompt_templates(path: Path) -> tuple[str, str]:
    text = path.read_text(encoding="utf-8")
    system_start = text.index("## 1. System Prompt")
    user_start = text.index("## 2. User Prompt Template")
    system_block = text[text.index("```text", system_start) + 7:text.index("```", text.index("```text", system_start) + 7)].strip()
    user_block = text[text.index("```text", user_start) + 7:text.index("```", text.index("```text", user_start) + 7)].strip()
    return system_block, user_block


def evaluate_single(mir_text: str, task: dict, expected_hex: str, expected_sig: tuple) -> Dict[str, bool]:
    """Evaluate a single M-IR candidate against a task."""
    eval_result = evaluate_candidate(task, expected_hex, expected_sig, 1, mir_text)
    return {
        "ir_valid": bool(eval_result.get("ir_valid", 0)),
        "compile_pass": bool(eval_result.get("compile_pass", 0)),
        "verify_pass": bool(eval_result.get("verify_pass", 0)),
        "execution_pass": bool(eval_result.get("execution_pass", 0)),
        "task_success": bool(eval_result.get("task_success", 0)),
    }


def run_temperature(
    model: str,
    tasks: List[dict],
    expected_map: Dict[str, str],
    system_prompt: str,
    user_template: str,
    temperature: float,
    runs: int,
) -> List[dict]:
    """Run generation at a given temperature for multiple runs."""
    sig_cache = {}
    for task in tasks:
        sig_cache[task["task_id"]] = expected_signature(task)

    all_results = []
    for run_idx in range(runs):
        print(f"  Temperature {temperature}, run {run_idx + 1}/{runs}...")
        for task in tasks:
            prompt = user_template.format(
                task_id=task["task_id"],
                allowed_devices=", ".join(task["allowed_devices"]),
                prompt=task["prompt"],
            )
            result = ollama_generate(
                model, prompt,
                system=system_prompt,
                temperature=temperature,
            )
            mir_text = result.get("response", "")
            eval_result = evaluate_single(
                mir_text, task,
                expected_map[task["task_id"]],
                sig_cache[task["task_id"]],
            )
            all_results.append({
                "task_id": task["task_id"],
                "temperature": temperature,
                "run": run_idx + 1,
                "mir": mir_text,
                **eval_result,
            })
    return all_results


def main() -> int:
    parser = argparse.ArgumentParser(description="Temperature sweep experiment")
    parser.add_argument("--model", default="llama3.1:8b")
    parser.add_argument("--tasks", default=str(Path(__file__).resolve().parent.parent / "data" / "tasks_v2.jsonl"))
    parser.add_argument("--prompts", default=str(Path(__file__).resolve().parent.parent / "data" / "prompts_v1.md"))
    parser.add_argument("--temperatures", type=float, nargs="+", default=[0.0, 0.3, 0.6, 1.0])
    parser.add_argument("--runs", type=int, default=5, help="Number of runs per temperature")
    parser.add_argument("--limit", type=int, default=0, help="Limit number of tasks")
    parser.add_argument("--out", default=str(Path(__file__).resolve().parent.parent / "result" / "GEN" / "temperature_sweep.csv"))
    args = parser.parse_args()

    tasks = load_jsonl(Path(args.tasks))
    if args.limit > 0:
        tasks = tasks[:args.limit]

    system_prompt, user_template = parse_prompt_templates(Path(args.prompts))
    expected_map = compile_expected_payloads(tasks)

    all_results = []
    for temp in args.temperatures:
        print(f"\n=== Temperature = {temp} ===")
        results = run_temperature(
            args.model, tasks, expected_map, system_prompt, user_template,
            temp, args.runs,
        )
        all_results.extend(results)

    # Write detailed results
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "task_id", "temperature", "run", "ir_valid", "compile_pass",
        "verify_pass", "execution_pass", "task_success", "mir",
    ]
    with out_path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for r in all_results:
            writer.writerow(r)

    # Compute summary
    print(f"\n{'='*70}")
    print(f"Temperature Sweep Summary ({len(tasks)} tasks, {args.runs} runs each)")
    print(f"{'='*70}")
    print(f"{'Temp':>6} {'IR Valid':>10} {'Compile':>10} {'Verify':>10} {'Execute':>10} {'Success':>10}")
    print(f"{'-'*70}")

    summary_rows = []
    for temp in args.temperatures:
        temp_results = [r for r in all_results if r["temperature"] == temp]
        n = len(temp_results)
        if n == 0:
            continue
        for metric in ["ir_valid", "compile_pass", "verify_pass", "execution_pass", "task_success"]:
            values = [1.0 if r[metric] else 0.0 for r in temp_results]
            mean = statistics.mean(values)
            if len(values) > 1:
                stdev = statistics.stdev(values)
            else:
                stdev = 0.0
            summary_rows.append({
                "temperature": temp,
                "metric": metric,
                "mean": mean,
                "stdev": stdev,
                "n": n,
            })

        # Print row
        ir = [r for r in summary_rows if r["temperature"] == temp and r["metric"] == "ir_valid"][0]
        comp = [r for r in summary_rows if r["temperature"] == temp and r["metric"] == "compile_pass"][0]
        ver = [r for r in summary_rows if r["temperature"] == temp and r["metric"] == "verify_pass"][0]
        exe = [r for r in summary_rows if r["temperature"] == temp and r["metric"] == "execution_pass"][0]
        suc = [r for r in summary_rows if r["temperature"] == temp and r["metric"] == "task_success"][0]
        print(f"{temp:>6.1f} {ir['mean']:.3f}±{ir['stdev']:.3f} {comp['mean']:.3f}±{comp['stdev']:.3f} {ver['mean']:.3f}±{ver['stdev']:.3f} {exe['mean']:.3f}±{exe['stdev']:.3f} {suc['mean']:.3f}±{suc['stdev']:.3f}")

    # Write summary CSV
    summary_path = out_path.with_name(out_path.stem + "_summary.csv")
    with summary_path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["temperature", "metric", "mean", "stdev", "n"])
        writer.writeheader()
        for r in summary_rows:
            writer.writerow(r)

    print(f"\nDetailed: {out_path}")
    print(f"Summary:  {summary_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
