#!/usr/bin/env python3
"""
Generate M-IR candidates via DeepSeek API.

Usage:
  export DEEPSEEK_API_KEY="sk-your-api-key-here"
  python run_deepseek_generate.py --model deepseek-chat --tasks ../data/tasks_v2.jsonl --out ../result/GEN/candidates_deepseek_v3.jsonl
  python run_deepseek_generate.py --model deepseek-chat --tasks ../data/tasks_v2.jsonl --out ../result/GEN/candidates_deepseek_v3_t1.0.jsonl --temperature 1.0
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import List

from deepseek_client import deepseek_generate
from run_generation_eval import load_jsonl


def parse_prompt_templates(path: Path) -> tuple[str, str]:
    text = path.read_text(encoding="utf-8")
    system_start = text.index("## 1. System Prompt")
    user_start = text.index("## 2. User Prompt Template")
    system_block = text[text.index("```text", system_start) + 7:text.index("```", text.index("```text", system_start) + 7)].strip()
    user_block = text[text.index("```text", user_start) + 7:text.index("```", text.index("```text", user_start) + 7)].strip()
    return system_block, user_block


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate M-IR candidates via DeepSeek API.")
    parser.add_argument("--model", default="deepseek-chat", help="DeepSeek model name (deepseek-chat, deepseek-reasoner)")
    parser.add_argument("--tasks", default=str(Path(__file__).resolve().parent.parent / "data" / "tasks_v2.jsonl"))
    parser.add_argument("--prompts", default=str(Path(__file__).resolve().parent.parent / "data" / "prompts_v1.md"))
    parser.add_argument("--out", required=True, help="output candidate JSONL")
    parser.add_argument("--limit", type=int, default=0, help="optional task limit")
    parser.add_argument("--temperature", type=float, default=0.0)
    parser.add_argument("--api-key", default=None, help="DeepSeek API key (or set DEEPSEEK_API_KEY env var)")
    args = parser.parse_args()

    tasks = load_jsonl(Path(args.tasks))
    if args.limit > 0:
        tasks = tasks[:args.limit]
    system_prompt, user_template = parse_prompt_templates(Path(args.prompts))

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    success = 0
    fail = 0
    with out_path.open("w", encoding="utf-8") as fh:
        for i, task in enumerate(tasks):
            prompt = user_template.format(
                task_id=task["task_id"],
                allowed_devices=", ".join(task["allowed_devices"]),
                prompt=task["prompt"],
            )
            try:
                result = deepseek_generate(
                    args.model, prompt,
                    system=system_prompt,
                    temperature=args.temperature,
                    api_key=args.api_key,
                )
                row = {
                    "task_id": task["task_id"],
                    "attempt": 1,
                    "mir": result.get("response", ""),
                    "prompt_eval_count": result.get("prompt_eval_count"),
                    "eval_count": result.get("eval_count"),
                    "model": args.model,
                }
                success += 1
            except Exception as e:
                row = {
                    "task_id": task["task_id"],
                    "attempt": 1,
                    "mir": "",
                    "error": str(e),
                    "model": args.model,
                }
                fail += 1
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")

            if (i + 1) % 10 == 0:
                print(f"  [{i+1}/{len(tasks)}] ok={success} fail={fail}")

    print(f"Done: {success} ok, {fail} fail -> {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
