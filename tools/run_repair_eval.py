#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
from collections import defaultdict
from pathlib import Path

from ollama_client import ollama_generate
from run_generation_eval import evaluate_candidate, expected_signature, load_jsonl, compile_expected_payloads


def parse_prompt_templates(path: Path) -> tuple[str, str, str]:
    text = path.read_text(encoding="utf-8")
    def block(title: str) -> str:
        idx = text.index(title)
        start = text.index("```text", idx) + 7
        end = text.index("```", start)
        return text[start:end].strip()
    return (
        block("## 1. System Prompt"),
        block("## 2. User Prompt Template"),
        block("## 3. Repair Prompt Template"),
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Run repair-loop evaluation with local Ollama.")
    parser.add_argument("--model", required=True)
    parser.add_argument("--tasks", default=str(Path(__file__).resolve().parent.parent / "data" / "tasks_v1.jsonl"))
    parser.add_argument("--prompts", default=str(Path(__file__).resolve().parent.parent / "data" / "prompts_v1.md"))
    parser.add_argument("--out-dir", default=str(Path(__file__).resolve().parent.parent / "result" / "GEN"))
    parser.add_argument("--max-attempts", type=int, default=3)
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--temperature", type=float, default=0.0)
    parser.add_argument("--tag", default="v1")
    args = parser.parse_args()

    tasks = load_jsonl(Path(args.tasks))
    if args.limit > 0:
        tasks = tasks[: args.limit]
    tasks_by_id = {t["task_id"]: t for t in tasks}
    expected_map = compile_expected_payloads(tasks)
    expected_sig = {t["task_id"]: expected_signature(t) for t in tasks}
    system_prompt, user_template, repair_template = parse_prompt_templates(Path(args.prompts))

    rows = []
    summary = defaultdict(int)
    for task in tasks:
        current_output = ""
        success = False
        for attempt in range(1, args.max_attempts + 1):
            if attempt == 1:
                prompt = user_template.format(
                    task_id=task["task_id"],
                    allowed_devices=", ".join(task["allowed_devices"]),
                    prompt=task["prompt"],
                )
            else:
                prompt = repair_template.format(
                    task_id=task["task_id"],
                    allowed_devices=", ".join(task["allowed_devices"]),
                    prompt=task["prompt"],
                    previous_output=current_output,
                    stage=rows[-1]["error_stage"],
                    error_code=rows[-1]["error_code"],
                    hint=rows[-1]["hint"],
                )
            result = ollama_generate(args.model, prompt, system=system_prompt, temperature=args.temperature)
            current_output = result.get("response", "")
            row = evaluate_candidate(task, expected_map[task["task_id"]], expected_sig[task["task_id"]], attempt, current_output)
            row["prompt_eval_count"] = result.get("prompt_eval_count")
            row["eval_count"] = result.get("eval_count")
            rows.append(row)
            if int(row["task_success"]) == 1:
                summary[f"success@{attempt}"] += 1
                success = True
                break
        if not success:
            summary["failed"] += 1

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    csv_path = out_dir / f"repair_eval_{args.tag}.csv"
    with csv_path.open("w", encoding="utf-8-sig", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(rows[0].keys()) if rows else [])
        writer.writeheader()
        writer.writerows(rows)

    md_path = out_dir / f"repair_summary_{args.tag}.md"
    lines = ["# Repair Eval Summary", ""]
    total = len(tasks)
    for k in range(1, args.max_attempts + 1):
        succ = summary.get(f"success@{k}", 0)
        lines.append(f"- success@{k}: {succ}/{total} = {succ/total:.3f}" if total else f"- success@{k}: 0/0 = 0.000")
    lines.append(f"- failed: {summary.get('failed', 0)}")
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(str(csv_path))
    print(str(md_path))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
