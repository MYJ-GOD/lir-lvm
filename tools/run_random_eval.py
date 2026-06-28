#!/usr/bin/env python3
"""
Run LIR generation evaluation on random tasks (H1 experiment).
Wraps run_generation_eval.py with random task file.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from ollama_client import ollama_generate
from run_generation_eval import (
    compile_expected_payloads,
    evaluate_candidate,
    expected_signature,
    load_jsonl,
)
from mir_compiler import compile_source, MirCompilerError


def parse_prompt_templates(path: Path) -> tuple[str, str]:
    text = path.read_text(encoding="utf-8")
    system_start = text.index("## 1. System Prompt")
    user_start = text.index("## 2. User Prompt Template")
    system_block = text[text.index("```text", system_start) + 7:text.index("```", text.index("```text", system_start) + 7)].strip()
    user_block = text[text.index("```text", user_start) + 7:text.index("```", text.index("```text", user_start) + 7)].strip()
    return system_block, user_block


def main() -> int:
    parser = argparse.ArgumentParser(description="Evaluate LIR generation on random tasks")
    parser.add_argument("--model", default="llama3.1:8b")
    parser.add_argument("--tasks", default=str(Path(__file__).resolve().parent.parent / "data" / "tasks_random_500.jsonl"))
    parser.add_argument("--prompts", default=str(Path(__file__).resolve().parent.parent / "data" / "prompts_v1.md"))
    parser.add_argument("--temperature", type=float, default=0.0)
    parser.add_argument("--limit", type=int, default=0, help="Limit tasks (0=all)")
    parser.add_argument("--out", default=str(Path(__file__).resolve().parent.parent / "result" / "GEN" / "random_eval.csv"))
    parser.add_argument("--out_candidates", default=str(Path(__file__).resolve().parent.parent / "result" / "GEN" / "candidates_random.jsonl"))
    args = parser.parse_args()

    tasks = load_jsonl(Path(args.tasks))
    if args.limit > 0:
        tasks = tasks[:args.limit]

    system_prompt, user_template = parse_prompt_templates(Path(args.prompts))
    expected_map = compile_expected_payloads(tasks)

    # Build signature cache
    sig_cache = {}
    for task in tasks:
        sig_cache[task["task_id"]] = expected_signature(task)

    import csv
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    cand_path = Path(args.out_candidates)

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
        resp = ollama_generate(args.model, prompt, system=system_prompt, temperature=args.temperature)
        mir_text = resp.get("response", "")

        eval_result = evaluate_candidate(task, expected_map[tid], sig_cache[tid], 1, mir_text)
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
        candidates.append({
            "task_id": tid,
            "run": 1,
            "candidate_mir": mir_text,
            **{k: v for k, v in eval_result.items()},
        })

        if (i + 1) % 50 == 0 or i == n_tasks - 1:
            succ = sum(r["task_success"] for r in results)
            print(f"  [{i+1}/{n_tasks}] task_success={succ}/{i+1} = {succ/(i+1):.3f}")

    # Write CSV
    fieldnames = ["task_id", "category", "ir_valid", "compile_pass", "verify_pass", "execution_pass", "task_success"]
    with out_path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)

    # Write candidates JSONL
    with cand_path.open("w", encoding="utf-8") as f:
        for c in candidates:
            f.write(json.dumps(c, ensure_ascii=False) + "\n")

    # Summary
    n = len(results)
    metrics = ["ir_valid", "compile_pass", "verify_pass", "execution_pass", "task_success"]
    print(f"\n{'='*60}")
    print(f"Random Task Evaluation ({n} tasks, model={args.model}, temp={args.temperature})")
    print(f"{'='*60}")
    for m in metrics:
        cnt = sum(r[m] for r in results)
        print(f"  {m}: {cnt}/{n} = {cnt/n:.3f}")

    # Per-category breakdown
    from collections import Counter, defaultdict
    cats = defaultdict(list)
    for r in results:
        cats[r["category"]].append(r["task_success"])

    print(f"\nPer-category task_success:")
    for cat, vals in sorted(cats.items()):
        s = sum(vals)
        print(f"  {cat}: {s}/{len(vals)} = {s/len(vals):.3f}")

    print(f"\nOutput: {out_path}")
    print(f"Candidates: {cand_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
