#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
from collections import defaultdict
from pathlib import Path

from ollama_client import ollama_generate
from run_generation_eval import load_jsonl
from run_hex_eval import evaluate_hex_candidate


def extract_block(text: str, heading: str) -> str:
    idx = text.index(heading)
    start = text.index("```text", idx) + 7
    end = text.index("```", start)
    return text[start:end].strip()


def main() -> int:
    parser = argparse.ArgumentParser(description="Run repair-loop evaluation for direct raw M-bytecode hex.")
    parser.add_argument("--model", required=True)
    parser.add_argument("--tasks", required=True)
    parser.add_argument("--prompts", required=True)
    parser.add_argument("--out-dir", default=str(Path(__file__).resolve().parent.parent / "result" / "GEN"))
    parser.add_argument("--max-attempts", type=int, default=3)
    parser.add_argument("--temperature", type=float, default=0.0)
    parser.add_argument("--tag", default="hex_v1")
    args = parser.parse_args()

    tasks = load_jsonl(Path(args.tasks))
    text = Path(args.prompts).read_text(encoding="utf-8")
    system_prompt = extract_block(text, "## Direct Hex System Prompt")
    user_template = extract_block(text, "## Direct Hex User Prompt")
    repair_template = extract_block(text, "## Direct Hex Repair Prompt")

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
                prev = rows[-1]
                prompt = repair_template.format(
                    task_id=task["task_id"],
                    allowed_devices=", ".join(task["allowed_devices"]),
                    prompt=task["prompt"],
                    previous_output=current_output,
                    stage=prev["error_stage"],
                    error_code=prev["error_code"],
                    hint=prev["hint"],
                )
            try:
                result = ollama_generate(args.model, prompt, system=system_prompt, temperature=args.temperature)
                current_output = result.get("response", "")
                prompt_eval_count = result.get("prompt_eval_count")
                eval_count = result.get("eval_count")
            except Exception as exc:  # pragma: no cover - runtime/network fallback
                current_output = ""
                prompt_eval_count = None
                eval_count = None
                result = {"response": "", "error": str(exc)}

            row = evaluate_hex_candidate(task, current_output, attempt)
            row["prompt_eval_count"] = prompt_eval_count
            row["eval_count"] = eval_count
            rows.append(row)
            if int(row["task_success"]) == 1:
                summary[f"success@{attempt}"] += 1
                success = True
                break
        if not success:
            summary["failed"] += 1

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    csv_path = out_dir / f"hex_repair_eval_{args.tag}.csv"
    with csv_path.open("w", encoding="utf-8-sig", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(rows[0].keys()) if rows else [])
        writer.writeheader()
        writer.writerows(rows)

    md_path = out_dir / f"hex_repair_summary_{args.tag}.md"
    total = len(tasks)
    lines = ["# Direct Hex Repair Eval Summary", ""]
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
