#!/usr/bin/env python3
"""E-Grammar: directly-measured success@K and grammar-filtered success@K.

Unlike bench_grammar_constrained.py (which records only first-candidate and
first-valid outcomes), this script evaluates EVERY one of K candidates per task
at temperature=1.0 and computes, as a function of k = 1..K:

  * success@k            : fraction of tasks with >=1 task-successful candidate
                           among the first k (unconstrained best-of-k)
  * gfilter_success@k    : same, but restricted to grammar-valid candidates
                           (the realistic post-hoc grammar-constrained pipeline)
  * grammar_valid_rate   : fraction of all candidates passing the LIR grammar

This turns the paper's K-best row (K=1/2/3) from a filtering proxy into a
directly measured best-of-k curve. Requires a local Ollama server; no MCU.

Usage:
  python bench_success_at_k.py --model llama3.1:8b --candidates 5 \
      --temperature 1.0 --out ../result/GEN/success_at_k.csv
"""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import List

from ollama_client import ollama_generate
from run_generation_eval import (
    compile_expected_payloads,
    evaluate_candidate,
    expected_signature,
    load_jsonl,
)
from bench_grammar_constrained import (
    is_lir_grammar_valid,
    parse_prompt_templates,
)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default="llama3.1:8b")
    ap.add_argument("--tasks", default=str(Path(__file__).resolve().parent.parent / "data" / "tasks_v2.jsonl"))
    ap.add_argument("--prompts", default=str(Path(__file__).resolve().parent.parent / "data" / "prompts_v1.md"))
    ap.add_argument("--temperature", type=float, default=1.0)
    ap.add_argument("--candidates", type=int, default=5)
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--out", default=str(Path(__file__).resolve().parent.parent / "result" / "GEN" / "success_at_k.csv"))
    args = ap.parse_args()

    tasks = load_jsonl(Path(args.tasks))
    if args.limit > 0:
        tasks = tasks[:args.limit]
    K = args.candidates

    system_prompt, user_template = parse_prompt_templates(Path(args.prompts))
    expected_map = compile_expected_payloads(tasks)
    sig_cache = {t["task_id"]: expected_signature(t) for t in tasks}

    # per task: lists over k of (task_ok, grammar_valid)
    per_task = []
    n = len(tasks)
    for i, task in enumerate(tasks):
        tid = task["task_id"]
        prompt = user_template.format(
            task_id=tid,
            allowed_devices=", ".join(task["allowed_devices"]),
            prompt=task["prompt"],
        )
        oks: List[int] = []
        valids: List[int] = []
        for k in range(K):
            resp = ollama_generate(args.model, prompt, system=system_prompt,
                                   temperature=args.temperature)
            mir_text = resp.get("response", "")
            valid, _ = is_lir_grammar_valid(mir_text)
            ev = evaluate_candidate(task, expected_map[tid], sig_cache[tid], 1, mir_text)
            oks.append(int(bool(ev.get("task_success", 0))))
            valids.append(int(valid))
        per_task.append({"task_id": tid, "oks": oks, "valids": valids})
        if (i + 1) % 20 == 0 or i == n - 1:
            print(f"  [{i+1}/{n}] generated K={K} candidates each")

    # compute curves
    rows = []
    for k in range(1, K + 1):
        succ_uncon = 0
        succ_gfilt = 0
        for t in per_task:
            window_ok = t["oks"][:k]
            window_valid = t["valids"][:k]
            if any(window_ok):
                succ_uncon += 1
            # grammar-filtered best-of-k: success among grammar-valid candidates;
            # if none valid, the pipeline would reject (count as failure).
            gok = [o for o, v in zip(window_ok, window_valid) if v]
            if gok and any(gok):
                succ_gfilt += 1
        rows.append({
            "k": k,
            "success_at_k": round(succ_uncon / n, 4),
            "gfilter_success_at_k": round(succ_gfilt / n, 4),
        })

    all_valid = [v for t in per_task for v in t["valids"]]
    grammar_valid_rate = round(sum(all_valid) / len(all_valid), 4)

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["k", "success_at_k", "gfilter_success_at_k"])
        w.writeheader()
        w.writerows(rows)
    # also dump raw per-task for auditability
    raw_path = out_path.with_name(out_path.stem + "_raw.json")
    raw_path.write_text(json.dumps(per_task, indent=2), encoding="utf-8")

    print(f"\n{'='*60}")
    print(f"success@K (measured)  model={args.model} temp={args.temperature} K={K} n={n}")
    print(f"{'='*60}")
    print(f"{'k':>3}{'success@k':>14}{'gfilter@k':>14}")
    for r in rows:
        print(f"{r['k']:>3}{r['success_at_k']:>14.4f}{r['gfilter_success_at_k']:>14.4f}")
    print(f"\navg grammar-valid rate = {grammar_valid_rate:.4f}")
    print(f"out: {out_path}")
    print(f"raw: {raw_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
