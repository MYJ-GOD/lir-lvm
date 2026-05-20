#!/usr/bin/env python3
"""
Batch evaluation harness for M-IR generation tasks.

Current v0.1 supports two modes:
  1. golden  : compile each task's expected_mir as a sanity baseline
  2. file    : evaluate candidate outputs from a JSONL file

The script reports:
  - ir_valid
  - compile_pass
  - task_success

verify_pass / execution_pass are kept as reserved columns for later adapter hooks.
"""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from pathlib import Path
from typing import Dict, Iterable, List, Optional

from backend_adapter import simulate_subset
from mir_compiler import MirCompilerError, compile_source


def load_jsonl(path: Path) -> List[dict]:
    rows = []
    with path.open("r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            rows.append(json.loads(line))
    return rows


def compile_expected_payloads(tasks: Iterable[dict]) -> Dict[str, str]:
    expected = {}
    for task in tasks:
        _, payload = compile_source(task["expected_mir"])
        expected[task["task_id"]] = payload.hex()
    return expected


def make_feedback(exc: MirCompilerError) -> dict:
    stage = "parse" if exc.code == "MIR_PARSE_ERROR" else "compile"
    hint_map = {
        "MIR_PARSE_ERROR": "Rewrite the program using the M-IR grammar exactly.",
        "UNKNOWN_DEVICE": "Use only devices from the provided allow-list.",
        "INVALID_CAPABILITY": "Add require cap(<device>) before the first access.",
        "INVALID_SET_TARGET": "Only relay1 and relay2 may appear on the left side of set.",
        "INVALID_ARGUMENT": "Keep actuator values in {0,1} and waits in non-negative milliseconds.",
        "UNSUPPORTED_CONSTRUCT": "Keep the program within the currently supported M-IR subset and valid retry body rules.",
    }
    return {
        "stage": stage,
        "error_code": exc.code,
        "message": exc.message,
        "hint": hint_map.get(exc.code, "Rewrite the program so it fits M-IR v0.1."),
        "details": {"line": exc.line_no},
    }


def expected_signature(task: dict) -> tuple:
    _, payload = compile_source(task["expected_mir"])
    result = simulate_subset(payload)
    return result.signature()


def normalize_candidate_mir(task_id: str, text: str) -> str:
    cleaned = text.strip()
    if cleaned.startswith("```"):
        parts = cleaned.split("```")
        if len(parts) >= 3:
            cleaned = parts[1]
            if cleaned.startswith("text"):
                cleaned = cleaned[4:]
            cleaned = cleaned.strip()
    if not cleaned.startswith("task "):
        safe_name = task_id.lower().replace("-", "_")
        body = "\n".join(f"  {line}" for line in cleaned.splitlines() if line.strip())
        cleaned = f"task {safe_name} {{\n{body}\n}}"
    return cleaned


def evaluate_candidate(task: dict, expected_hex: str, expected_sig: tuple, attempt: int, mir_text: str) -> dict:
    normalized_mir = normalize_candidate_mir(task["task_id"], mir_text)
    row = {
        "task_id": task["task_id"],
        "category": task["category"],
        "attempt": attempt,
        "ir_valid": 0,
        "compile_pass": 0,
        "verify_pass": 0,
        "execution_pass": 0,
        "task_success": 0,
        "payload_hex": "",
        "error_stage": "",
        "error_code": "",
        "hint": "",
        "candidate_mir": normalized_mir,
    }
    try:
        _, payload = compile_source(normalized_mir)
        row["ir_valid"] = 1
        row["compile_pass"] = 1
        row["payload_hex"] = payload.hex()
        backend = simulate_subset(payload)
        row["verify_pass"] = 1 if backend.verify_pass else 0
        row["execution_pass"] = 1 if backend.execution_pass else 0
        if not backend.verify_pass or not backend.execution_pass:
            row["error_stage"] = backend.stage
            row["error_code"] = backend.error_code
            row["hint"] = backend.message
            return row
        if backend.signature() == expected_sig:
            row["task_success"] = 1
        else:
            row["error_stage"] = "task"
            row["error_code"] = "TASK_SIGNATURE_MISMATCH"
            row["hint"] = "Rewrite the program so the final device state and return signature match the instruction exactly."
        return row
    except MirCompilerError as exc:
        feedback = make_feedback(exc)
        row["error_stage"] = feedback["stage"]
        row["error_code"] = feedback["error_code"]
        row["hint"] = feedback["hint"]
        if feedback["stage"] == "compile":
            row["ir_valid"] = 1
        return row


def evaluate_golden(tasks: List[dict], expected_map: Dict[str, str]) -> List[dict]:
    rows = []
    for task in tasks:
        rows.append(
            evaluate_candidate(
                task,
                expected_map[task["task_id"]],
                expected_signature(task),
                1,
                task["expected_mir"],
            )
        )
    return rows


def evaluate_from_file(tasks: List[dict], expected_map: Dict[str, str], candidates_path: Path) -> List[dict]:
    tasks_by_id = {task["task_id"]: task for task in tasks}
    rows = []
    for item in load_jsonl(candidates_path):
        task_id = item["task_id"]
        task = tasks_by_id[task_id]
        attempt = int(item.get("attempt", 1))
        mir_text = item["mir"]
        rows.append(evaluate_candidate(task, expected_map[task_id], expected_signature(task), attempt, mir_text))
    return rows


def write_csv(path: Path, rows: List[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "task_id",
        "category",
        "attempt",
        "ir_valid",
        "compile_pass",
        "verify_pass",
        "execution_pass",
        "task_success",
        "payload_hex",
        "error_stage",
        "error_code",
        "hint",
        "candidate_mir",
    ]
    with path.open("w", encoding="utf-8-sig", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def write_summary(path: Path, rows: List[dict]) -> None:
    total = len(rows)
    ir_valid = sum(int(row["ir_valid"]) for row in rows)
    compile_pass = sum(int(row["compile_pass"]) for row in rows)
    task_success = sum(int(row["task_success"]) for row in rows)
    errors = Counter(row["error_code"] for row in rows if row["error_code"])
    lines = [
        "# Generation Eval Summary",
        "",
        f"- total: {total}",
        f"- ir_valid_rate: {ir_valid / total:.3f}" if total else "- ir_valid_rate: 0.000",
        f"- compile_pass_rate: {compile_pass / total:.3f}" if total else "- compile_pass_rate: 0.000",
        f"- verify_pass_rate: {sum(int(row['verify_pass']) for row in rows) / total:.3f}" if total else "- verify_pass_rate: 0.000",
        f"- execution_pass_rate: {sum(int(row['execution_pass']) for row in rows) / total:.3f}" if total else "- execution_pass_rate: 0.000",
        f"- task_success_rate: {task_success / total:.3f}" if total else "- task_success_rate: 0.000",
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


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run batch generation evaluation for M-IR tasks.")
    parser.add_argument(
        "--tasks",
        default=str(Path(__file__).resolve().parent.parent / "data" / "tasks_v1.jsonl"),
        help="task JSONL file",
    )
    parser.add_argument(
        "--mode",
        choices=["golden", "file"],
        default="golden",
        help="golden: evaluate expected_mir; file: evaluate candidate JSONL",
    )
    parser.add_argument("--candidates", help="candidate JSONL file when --mode file")
    parser.add_argument(
        "--out-dir",
        default=str(Path(__file__).resolve().parent.parent / "result" / "GEN"),
        help="output directory",
    )
    parser.add_argument("--tag", default="v1", help="output tag")
    return parser


def main() -> int:
    args = build_arg_parser().parse_args()
    tasks_path = Path(args.tasks)
    tasks = load_jsonl(tasks_path)
    expected_map = compile_expected_payloads(tasks)

    if args.mode == "golden":
        rows = evaluate_golden(tasks, expected_map)
    else:
        if not args.candidates:
            raise SystemExit("--candidates is required when --mode file")
        rows = evaluate_from_file(tasks, expected_map, Path(args.candidates))

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    csv_path = out_dir / f"gen_eval_{args.tag}.csv"
    summary_path = out_dir / f"gen_eval_{args.tag}.md"
    write_csv(csv_path, rows)
    write_summary(summary_path, rows)
    print(str(csv_path))
    print(str(summary_path))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
