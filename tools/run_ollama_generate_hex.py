#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from ollama_client import ollama_generate
from run_generation_eval import load_jsonl


def extract_block(text: str, heading: str) -> str:
    idx = text.index(heading)
    start = text.index("```text", idx) + 7
    end = text.index("```", start)
    return text[start:end].strip()


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate direct M-bytecode hex candidates with local Ollama.")
    parser.add_argument("--model", required=True)
    parser.add_argument("--tasks", required=True)
    parser.add_argument("--prompts", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--temperature", type=float, default=0.0)
    args = parser.parse_args()

    tasks = load_jsonl(Path(args.tasks))
    if args.limit > 0:
        tasks = tasks[: args.limit]
    text = Path(args.prompts).read_text(encoding="utf-8")
    system_prompt = extract_block(text, "## Direct Hex System Prompt")
    user_template = extract_block(text, "## Direct Hex User Prompt")

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8") as fh:
        for task in tasks:
            prompt = user_template.format(
                task_id=task["task_id"],
                allowed_devices=", ".join(task["allowed_devices"]),
                prompt=task["prompt"],
            )
            try:
                result = ollama_generate(args.model, prompt, system=system_prompt, temperature=args.temperature)
                response = result.get("response", "")
                prompt_eval_count = result.get("prompt_eval_count")
                eval_count = result.get("eval_count")
                total_duration = result.get("total_duration")
                error = ""
            except Exception as exc:  # pragma: no cover - network/runtime fallback
                response = ""
                prompt_eval_count = None
                eval_count = None
                total_duration = None
                error = str(exc)
            row = {
                "task_id": task["task_id"],
                "attempt": 1,
                "hex": response,
                "prompt_eval_count": prompt_eval_count,
                "eval_count": eval_count,
                "total_duration": total_duration,
                "model": args.model,
                "error": error,
            }
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")
    print(str(out_path))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
