#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
from pathlib import Path

from ollama_client import ollama_generate
from run_generation_eval import load_jsonl


def extract_block(text: str, heading: str) -> str:
    idx = text.index(heading)
    start = text.index("```text", idx) + 7
    end = text.index("```", start)
    return text[start:end].strip()


def main() -> int:
    parser = argparse.ArgumentParser(description="Measure Ollama token cost across M-IR / JSON / Python formats.")
    parser.add_argument("--model", required=True)
    parser.add_argument("--tasks", default=str(Path(__file__).resolve().parent.parent / "data" / "tasks_v1.jsonl"))
    parser.add_argument("--prompts", default=str(Path(__file__).resolve().parent.parent / "data" / "prompts_compare_v1.md"))
    parser.add_argument("--out", default=str(Path(__file__).resolve().parent.parent / "result" / "TOKEN" / "token_compare_v1.csv"))
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--temperature", type=float, default=0.0)
    args = parser.parse_args()

    tasks = load_jsonl(Path(args.tasks))
    if args.limit > 0:
        tasks = tasks[: args.limit]
    text = Path(args.prompts).read_text(encoding="utf-8")
    prompts = {
        "MIR": (extract_block(text, "## M-IR System Prompt"), extract_block(text, "## M-IR User Prompt")),
        "JSON": (extract_block(text, "## JSON System Prompt"), extract_block(text, "## JSON User Prompt")),
        "PYTHON": (extract_block(text, "## Python System Prompt"), extract_block(text, "## Python User Prompt")),
    }

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8-sig", newline="") as fh:
        writer = csv.DictWriter(
            fh,
            fieldnames=[
                "task_id",
                "format",
                "prompt_eval_count",
                "eval_count",
                "output_chars",
                "output_bytes",
                "response",
                "model",
            ],
        )
        writer.writeheader()
        for task in tasks:
            for fmt, (system_prompt, user_template) in prompts.items():
                prompt = user_template.format(
                    task_id=task["task_id"],
                    allowed_devices=", ".join(task["allowed_devices"]),
                    prompt=task["prompt"],
                )
                result = ollama_generate(args.model, prompt, system=system_prompt, temperature=args.temperature)
                response = result.get("response", "")
                writer.writerow(
                    {
                        "task_id": task["task_id"],
                        "format": fmt,
                        "prompt_eval_count": result.get("prompt_eval_count"),
                        "eval_count": result.get("eval_count"),
                        "output_chars": len(response),
                        "output_bytes": len(response.encode("utf-8")),
                        "response": response,
                        "model": args.model,
                    }
                )
    print(str(out_path))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
