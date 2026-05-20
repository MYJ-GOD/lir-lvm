#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import re
from collections import Counter
from pathlib import Path
from typing import List

from backend_adapter import simulate_subset, verify_subset
from run_generation_eval import compile_expected_payloads, expected_signature, load_jsonl


HEX_RE = re.compile(r"[0-9a-fA-F]+")


def normalize_hex(text: str) -> str:
    cleaned = text.strip()
    if cleaned.startswith("```"):
        parts = cleaned.split("```")
        if len(parts) >= 3:
            cleaned = parts[1]
            if cleaned.startswith("text"):
                cleaned = cleaned[4:]
            cleaned = cleaned.strip()
    cleaned = cleaned.replace("0x", "").replace("0X", "")
    pieces = HEX_RE.findall(cleaned)
    return "".join(pieces).lower()


def evaluate_hex_candidate(task: dict, candidate_text: str, attempt: int) -> dict:
    row = {
        "task_id": task["task_id"],
        "category": task["category"],
        "attempt": attempt,
        "hex_valid": 0,
        "decode_pass": 0,
        "verify_pass": 0,
        "execution_pass": 0,
        "task_success": 0,
        "candidate_hex": "",
        "error_stage": "",
        "error_code": "",
        "hint": "",
        "candidate_text": candidate_text.strip(),
    }
    normalized = normalize_hex(candidate_text)
    row["candidate_hex"] = normalized
    if not normalized or len(normalized) % 2 != 0:
        row["error_stage"] = "parse"
        row["error_code"] = "HEX_PARSE_ERROR"
        row["hint"] = "Output only lowercase hexadecimal bytes with even length."
        return row
    try:
        payload = bytes.fromhex(normalized)
    except ValueError:
        row["error_stage"] = "parse"
        row["error_code"] = "HEX_PARSE_ERROR"
        row["hint"] = "Output only valid hexadecimal bytes."
        return row

    row["hex_valid"] = 1
    verify_ok, verify_code, verify_msg = verify_subset(payload)
    row["decode_pass"] = 1
    row["verify_pass"] = 1 if verify_ok else 0
    if not verify_ok:
        row["error_stage"] = "verify"
        row["error_code"] = verify_code
        row["hint"] = verify_msg
        return row

    backend = simulate_subset(payload)
    row["execution_pass"] = 1 if backend.execution_pass else 0
    if not backend.execution_pass:
        row["error_stage"] = backend.stage
        row["error_code"] = backend.error_code
        row["hint"] = backend.message
        return row

    if backend.signature() == expected_signature(task):
        row["task_success"] = 1
    else:
        row["error_stage"] = "task"
        row["error_code"] = "TASK_SIGNATURE_MISMATCH"
        row["hint"] = "Payload executed, but final relay state or top-of-stack result does not match the task."
    return row


def write_summary(path: Path, rows: List[dict]) -> None:
    total = len(rows)
    errors = Counter(row["error_code"] for row in rows if row["error_code"])
    lines = [
        "# Direct Hex Eval Summary",
        "",
        f"- total: {total}",
        f"- hex_valid_rate: {sum(int(r['hex_valid']) for r in rows) / total:.3f}" if total else "- hex_valid_rate: 0.000",
        f"- decode_pass_rate: {sum(int(r['decode_pass']) for r in rows) / total:.3f}" if total else "- decode_pass_rate: 0.000",
        f"- verify_pass_rate: {sum(int(r['verify_pass']) for r in rows) / total:.3f}" if total else "- verify_pass_rate: 0.000",
        f"- execution_pass_rate: {sum(int(r['execution_pass']) for r in rows) / total:.3f}" if total else "- execution_pass_rate: 0.000",
        f"- task_success_rate: {sum(int(r['task_success']) for r in rows) / total:.3f}" if total else "- task_success_rate: 0.000",
        "",
        "## Error Breakdown",
        "",
    ]
    if errors:
        for code, count in errors.most_common():
            lines.append(f"- {code}: {count}")
    else:
        lines.append("- none")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Evaluate direct M-bytecode hex candidates.")
    parser.add_argument("--tasks", required=True)
    parser.add_argument("--candidates", required=True)
    parser.add_argument("--out-dir", default=str(Path(__file__).resolve().parent.parent / "result" / "GEN"))
    parser.add_argument("--tag", default="hex_v1")
    args = parser.parse_args()

    tasks = load_jsonl(Path(args.tasks))
    tasks_by_id = {task["task_id"]: task for task in tasks}
    _ = compile_expected_payloads(tasks)
    rows = []
    for item in load_jsonl(Path(args.candidates)):
        task = tasks_by_id[item["task_id"]]
        rows.append(evaluate_hex_candidate(task, item["hex"], int(item.get("attempt", 1))))

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    csv_path = out_dir / f"hex_eval_{args.tag}.csv"
    md_path = out_dir / f"hex_eval_{args.tag}.md"
    with csv_path.open("w", encoding="utf-8-sig", newline="") as fh:
        writer = csv.DictWriter(
            fh,
            fieldnames=[
                "task_id",
                "category",
                "attempt",
                "hex_valid",
                "decode_pass",
                "verify_pass",
                "execution_pass",
                "task_success",
                "candidate_hex",
                "error_stage",
                "error_code",
                "hint",
                "candidate_text",
            ],
        )
        writer.writeheader()
        writer.writerows(rows)
    write_summary(md_path, rows)
    print(str(csv_path))
    print(str(md_path))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
