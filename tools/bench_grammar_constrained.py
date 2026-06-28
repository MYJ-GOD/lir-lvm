#!/usr/bin/env python3
"""
Grammar-constrained decoding simulation (M8 experiment).

Strategy: at temperature=1.0, generate K candidates per task.
Filter each candidate through LIR grammar validation.
Report:
  - raw_success: success rate of first candidate (unconstrained)
  - filtered_success: success rate when taking first grammar-valid candidate
  - grammar_valid_rate: fraction of candidates that pass grammar check

This simulates grammar-constrained decoding by post-hoc filtering.
"""
from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from ollama_client import ollama_generate
from run_generation_eval import (
    compile_expected_payloads,
    evaluate_candidate,
    expected_signature,
    load_jsonl,
)
from mir_compiler import compile_source, MirCompilerError

sys.path.insert(0, str(Path(__file__).resolve().parent))

# ── LIR grammar regex (relaxed but practical) ──
# Matches: task <id> { <statements> }
# Statements: require cap(...), set/read/wait/halt/readback/retry
LIR_STATEMENT_RE = re.compile(
    r"^\s*("
    r"require\s+cap\(\w+\)"
    r"|set\s+\w+\s*=\s*[01]"
    r"|read\s+\w+"
    r"|wait\s+\d+ms"
    r"|halt"
    r"|readback\s+\w+\s+expect\s+[01]"
    r"|retry\s+\d+\s+times\s*\{"
    r"|\}"
    r")\s*$"
)

LIR_TASK_RE = re.compile(r"^\s*task\s+\w+\s*\{")


def is_lir_grammar_valid(text: str) -> Tuple[bool, Optional[str]]:
    """Check if text is valid LIR grammar. Returns (valid, error_reason)."""
    lines = text.strip().split("\n")
    if not lines:
        return False, "empty"

    # Check first line: task <id> {
    if not LIR_TASK_RE.match(lines[0]):
        return False, "no_task_header"

    # Check last line: }
    if not lines[-1].strip() == "}":
        return False, "no_closing_brace"

    # Check each statement line
    for i, line in enumerate(lines[1:], 2):
        stripped = line.strip()
        if not stripped:
            continue
        if not LIR_STATEMENT_RE.match(stripped):
            return False, f"invalid_stmt_line_{i}"

    return True, None


def extract_lir_candidates(text: str) -> List[str]:
    """Extract LIR program(s) from LLM output (handles markdown fences etc)."""
    # Remove markdown code fences
    text = re.sub(r"```(?:lir|m-ir|text)?\s*\n?", "", text)
    text = text.strip()

    # Try to find task blocks
    candidates = []
    pattern = re.compile(r"(task\s+\w+\s*\{[^}]*\})", re.DOTALL)
    matches = pattern.findall(text)
    if matches:
        candidates.extend(matches)

    if not candidates:
        # Try the whole text as one candidate
        candidates.append(text)

    return candidates


def parse_prompt_templates(path: Path) -> Tuple[str, str]:
    text = path.read_text(encoding="utf-8")
    system_start = text.index("## 1. System Prompt")
    user_start = text.index("## 2. User Prompt Template")
    system_block = text[text.index("```text", system_start) + 7:text.index("```", text.index("```text", system_start) + 7)].strip()
    user_block = text[text.index("```text", user_start) + 7:text.index("```", text.index("```text", user_start) + 7)].strip()
    return system_block, user_block


def main() -> int:
    parser = argparse.ArgumentParser(description="Grammar-constrained decoding simulation")
    parser.add_argument("--model", default="llama3.1:8b")
    parser.add_argument("--tasks", default=str(Path(__file__).resolve().parent.parent / "data" / "tasks_v2.jsonl"))
    parser.add_argument("--prompts", default=str(Path(__file__).resolve().parent.parent / "data" / "prompts_v1.md"))
    parser.add_argument("--temperature", type=float, default=1.0)
    parser.add_argument("--candidates", type=int, default=5, help="Candidates per task")
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--out", default=str(Path(__file__).resolve().parent.parent / "result" / "GEN" / "grammar_constrained.csv"))
    args = parser.parse_args()

    tasks = load_jsonl(Path(args.tasks))
    if args.limit > 0:
        tasks = tasks[:args.limit]

    system_prompt, user_template = parse_prompt_templates(Path(args.prompts))
    expected_map = compile_expected_payloads(tasks)
    sig_cache = {t["task_id"]: expected_signature(t) for t in tasks}

    results = []
    n_tasks = len(tasks)

    for i, task in enumerate(tasks):
        tid = task["task_id"]
        prompt = user_template.format(
            task_id=tid,
            allowed_devices=", ".join(task["allowed_devices"]),
            prompt=task["prompt"],
        )

        # Generate K candidates
        raw_success = False
        filtered_success = False
        grammar_valid_count = 0
        first_grammar_valid_success = None

        for k in range(args.candidates):
            resp = ollama_generate(args.model, prompt, system=system_prompt, temperature=args.temperature)
            mir_text = resp.get("response", "")

            # Check grammar validity
            is_valid, _ = is_lir_grammar_valid(mir_text)
            if is_valid:
                grammar_valid_count += 1

            # Evaluate
            eval_result = evaluate_candidate(task, expected_map[tid], sig_cache[tid], 1, mir_text)
            task_ok = bool(eval_result.get("task_success", 0))

            if k == 0:
                raw_success = task_ok

            if is_valid and first_grammar_valid_success is None:
                first_grammar_valid_success = task_ok

        if first_grammar_valid_success is not None:
            filtered_success = first_grammar_valid_success

        results.append({
            "task_id": tid,
            "raw_success": int(raw_success),
            "filtered_success": int(filtered_success),
            "grammar_valid_count": grammar_valid_count,
            "grammar_valid_rate": grammar_valid_count / args.candidates,
        })

        if (i + 1) % 20 == 0 or i == n_tasks - 1:
            raw_s = sum(r["raw_success"] for r in results)
            filt_s = sum(r["filtered_success"] for r in results)
            print(f"  [{i+1}/{n_tasks}] raw={raw_s}/{i+1}={raw_s/(i+1):.3f}  filtered={filt_s}/{i+1}={filt_s/(i+1):.3f}")

    # Write CSV
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["task_id", "raw_success", "filtered_success", "grammar_valid_count", "grammar_valid_rate"])
        writer.writeheader()
        writer.writerows(results)

    # Summary
    n = len(results)
    raw_s = sum(r["raw_success"] for r in results)
    filt_s = sum(r["filtered_success"] for r in results)
    avg_grammar = sum(r["grammar_valid_rate"] for r in results) / n

    print(f"\n{'='*60}")
    print(f"Grammar-Constrained Decoding Simulation")
    print(f"Model={args.model}, Temp={args.temperature}, K={args.candidates}, Tasks={n}")
    print(f"{'='*60}")
    print(f"  Raw success (1st candidate):     {raw_s}/{n} = {raw_s/n:.3f}")
    print(f"  Filtered success (1st valid):    {filt_s}/{n} = {filt_s/n:.3f}")
    print(f"  Avg grammar-valid rate:          {avg_grammar:.3f}")
    print(f"  Improvement (filtered vs raw):   +{(filt_s - raw_s)/n:.3f}")

    print(f"\nOutput: {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
