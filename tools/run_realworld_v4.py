#!/usr/bin/env python3
"""
Evaluate LIR generation on real-world IoT tasks using v4 prompt (with few-shot examples).
Compares v1 (no retry/readback) vs v4 (with retry/readback few-shot) prompts.

Usage:
  python run_realworld_v4.py                          # run v4 prompt only
  python run_realworld_v4.py --compare                 # run both v1 and v4, compare
  python run_realworld_v4.py --model qwen3:8b          # use different model
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from ollama_client import ollama_generate
from run_generation_eval import (
    compile_expected_payloads,
    evaluate_candidate,
    expected_signature,
    load_jsonl,
)


def parse_prompt_templates(path: Path) -> tuple[str, str]:
    """Parse system and user prompt templates from markdown file."""
    text = path.read_text(encoding="utf-8")
    system_start = text.index("## 1. System Prompt")
    user_start = text.index("## 2. User Prompt Template")
    system_block = text[
        text.index("```text", system_start) + 7 : text.index(
            "```", text.index("```text", system_start) + 7
        )
    ].strip()
    user_block = text[
        text.index("```text", user_start) + 7 : text.index(
            "```", text.index("```text", user_start) + 7
        )
    ].strip()
    return system_block, user_block


def run_eval(
    tasks: list[dict],
    system_prompt: str,
    user_template: str,
    expected_map: dict,
    sig_cache: dict,
    model: str,
    temperature: float,
    label: str,
) -> tuple[list[dict], list[dict]]:
    """Run evaluation and return (results, candidates)."""
    results = []
    candidates = []
    n_tasks = len(tasks)

    for i, task in enumerate(tasks):
        tid = task["task_id"]
        prompt = user_template.format(
            task_id=tid,
            allowed_devices=", ".join(task["allowed_devices"]),
            prompt=task["prompt"],
        )
        resp = ollama_generate(
            model, prompt, system=system_prompt, temperature=temperature
        )
        mir_text = resp.get("response", "")

        eval_result = evaluate_candidate(
            task, expected_map[tid], sig_cache[tid], 1, mir_text
        )
        row = {
            "task_id": tid,
            "category": task["category"],
            "ir_valid": int(eval_result.get("ir_valid", 0)),
            "compile_pass": int(eval_result.get("compile_pass", 0)),
            "verify_pass": int(eval_result.get("verify_pass", 0)),
            "execution_pass": int(eval_result.get("execution_pass", 0)),
            "task_success": int(eval_result.get("task_success", 0)),
        }
        results.append(row)
        candidates.append(
            {
                "task_id": tid,
                "prompt_version": label,
                "run": 1,
                "candidate_mir": mir_text,
                **{k: v for k, v in eval_result.items()},
            }
        )

        if (i + 1) % 10 == 0 or i == n_tasks - 1:
            succ = sum(r["task_success"] for r in results)
            print(f"  [{label}] [{i+1}/{n_tasks}] task_success={succ}/{i+1} = {succ/(i+1):.3f}")

    return results, candidates


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

    # Per-category breakdown
    cats = defaultdict(list)
    for r in results:
        cats[r["category"]].append(r["task_success"])

    print(f"\nPer-category task_success:")
    for cat, vals in sorted(cats.items()):
        s = sum(vals)
        print(f"  {cat}: {s}/{len(vals)} = {s/len(vals):.3f}")

    # Failure analysis
    failures = [r for r in results if not r["task_success"]]
    if failures:
        print(f"\nFailure analysis ({len(failures)} failures):")
        error_types = Counter()
        for r in failures:
            if not r["ir_valid"]:
                error_types["MIR_PARSE_ERROR"] += 1
            elif not r["task_success"]:
                error_types["TASK_SIGNATURE_MISMATCH"] += 1
        for etype, cnt in error_types.most_common():
            print(f"  {etype}: {cnt}")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Evaluate LIR generation on real-world IoT tasks (v4 prompt)"
    )
    parser.add_argument("--model", default="llama3.1:8b")
    parser.add_argument(
        "--tasks",
        default=str(
            Path(__file__).resolve().parent.parent / "data" / "tasks_realworld.jsonl"
        ),
    )
    parser.add_argument(
        "--prompts-v4",
        default=str(
            Path(__file__).resolve().parent.parent / "data" / "prompts_v4_realworld.md"
        ),
    )
    parser.add_argument(
        "--prompts-v1",
        default=str(
            Path(__file__).resolve().parent.parent / "data" / "prompts_v1.md"
        ),
    )
    parser.add_argument("--temperature", type=float, default=0.0)
    parser.add_argument("--compare", action="store_true", help="Run both v1 and v4, compare results")
    parser.add_argument("--limit", type=int, default=0, help="Limit tasks (0=all)")
    parser.add_argument(
        "--out",
        default=str(
            Path(__file__).resolve().parent.parent
            / "result"
            / "GEN"
            / "realworld_v4_eval.csv"
        ),
    )
    parser.add_argument(
        "--out_candidates",
        default=str(
            Path(__file__).resolve().parent.parent
            / "result"
            / "GEN"
            / "candidates_realworld_v4.jsonl"
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
    cand_path = Path(args.out_candidates)

    all_candidates = []

    # Run v4 prompt
    print(f"Running v4 prompt (with few-shot examples)...")
    sys_v4, user_v4 = parse_prompt_templates(Path(args.prompts_v4))
    results_v4, cands_v4 = run_eval(
        tasks, sys_v4, user_v4, expected_map, sig_cache,
        args.model, args.temperature, "v4"
    )
    all_candidates.extend(cands_v4)
    print_summary(results_v4, "v4 prompt (with retry/readback few-shot)")

    # Optionally run v1 prompt for comparison
    if args.compare:
        print(f"\nRunning v1 prompt (no retry/readback)...")
        sys_v1, user_v1 = parse_prompt_templates(Path(args.prompts_v1))
        results_v1, cands_v1 = run_eval(
            tasks, sys_v1, user_v1, expected_map, sig_cache,
            args.model, args.temperature, "v1"
        )
        all_candidates.extend(cands_v1)
        print_summary(results_v1, "v1 prompt (no retry/readback)")

        # Comparison
        print(f"\n{'='*60}")
        print("COMPARISON: v1 vs v4")
        print(f"{'='*60}")
        cats_v1 = defaultdict(list)
        cats_v4 = defaultdict(list)
        for r in results_v1:
            cats_v1[r["category"]].append(r["task_success"])
        for r in results_v4:
            cats_v4[r["category"]].append(r["task_success"])

        all_cats = sorted(set(list(cats_v1.keys()) + list(cats_v4.keys())))
        print(f"{'Category':<30} {'v1':>6} {'v4':>6} {'Delta':>6}")
        print(f"{'-'*48}")
        for cat in all_cats:
            v1_s = sum(cats_v1.get(cat, [0]))
            v1_n = len(cats_v1.get(cat, [1]))
            v4_s = sum(cats_v4.get(cat, [0]))
            v4_n = len(cats_v4.get(cat, [1]))
            v1_r = v1_s / v1_n if v1_n else 0
            v4_r = v4_s / v4_n if v4_n else 0
            delta = v4_r - v1_r
            print(f"  {cat:<28} {v1_r:>6.3f} {v4_r:>6.3f} {delta:>+6.3f}")

        total_v1 = sum(r["task_success"] for r in results_v1) / len(results_v1)
        total_v4 = sum(r["task_success"] for r in results_v4) / len(results_v4)
        print(f"{'-'*48}")
        print(f"  {'TOTAL':<28} {total_v1:>6.3f} {total_v4:>6.3f} {total_v4-total_v1:>+6.3f}")
    else:
        # Write v4 results only
        fieldnames = [
            "task_id", "category", "ir_valid", "compile_pass",
            "verify_pass", "execution_pass", "task_success",
        ]
        with out_path.open("w", encoding="utf-8-sig", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(results_v4)

    # Write all candidates
    with cand_path.open("w", encoding="utf-8") as f:
        for c in all_candidates:
            f.write(json.dumps(c, ensure_ascii=False) + "\n")

    print(f"\nOutput: {out_path}")
    print(f"Candidates: {cand_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
