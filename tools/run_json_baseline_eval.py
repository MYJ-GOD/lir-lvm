#!/usr/bin/env python3
"""
Evaluate LLM-generated JSON control programs as a fairer negative baseline
(replacing Direct Hex).

For each candidate:
  1. Parse JSON from LLM response
  2. Validate JSON structure against the expected schema
  3. Interpret the JSON program to compute final device state
  4. Compare with expected signature (from golden M-IR)
  5. Compress valid JSON with zlib / CBOR
  6. Compare compressed sizes vs M-bytecode

Produces a CSV and a summary markdown comparable to Direct Hex eval.
"""
from __future__ import annotations

import argparse
import csv
import json
import re
import zlib
from collections import Counter
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))
from backend_adapter import DEVICE_IDS, DEFAULT_SENSOR_VALUES, DEFAULT_RELAY_STATE
from mir_compiler import compile_source, MirCompilerError
from run_generation_eval import load_jsonl, compile_expected_payloads, expected_signature

try:
    import cbor2
    HAS_CBOR = True
except ImportError:
    HAS_CBOR = False


# ---------------------------------------------------------------------------
# JSON extraction
# ---------------------------------------------------------------------------

def extract_json(text: str) -> Optional[dict]:
    """Extract JSON object from LLM response, stripping markdown fences."""
    cleaned = text.strip()
    # Strip ```json ... ``` or ``` ... ``` fences
    m = re.search(r"```(?:json)?\s*\n?(.*?)```", cleaned, re.DOTALL)
    if m:
        cleaned = m.group(1).strip()
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        return None


# ---------------------------------------------------------------------------
# JSON program interpreter
# ---------------------------------------------------------------------------

class JSONExecError(Exception):
    def __init__(self, code: str, message: str):
        self.code = code
        self.message = message


def _resolve_device(name: str) -> int:
    if name not in DEVICE_IDS:
        raise JSONExecError("JSON_UNKNOWN_DEVICE", f"Device '{name}' not in allow-list.")
    return DEVICE_IDS[name]


def _check_cap(dev_name: str, dev_id: int, caps: set) -> None:
    if dev_id not in caps:
        raise JSONExecError(
            "JSON_CAPABILITY_ERROR",
            f"Device '{dev_name}' (id={dev_id}) not declared in 'cap' array.",
        )


def _execute_body(
    body: list,
    caps: set,
    relays: Dict[str, int],
    step_limit: int = 10000,
) -> Tuple[Optional[int], int]:
    """Execute a list of operations. Returns (result_top, steps_executed)."""
    result_top: Optional[int] = None
    steps = 0
    i = 0
    while i < len(body):
        steps += 1
        if steps > step_limit:
            raise JSONExecError("JSON_STEP_LIMIT", f"Exceeded step limit of {step_limit}.")

        op = body[i]
        if not isinstance(op, dict):
            raise JSONExecError("JSON_INVALID_OP", f"Operation at index {i} is not a JSON object.")

        op_type = op.get("op", "")

        if op_type == "set":
            dev_name = op.get("dev", "")
            dev_id = _resolve_device(dev_name)
            _check_cap(dev_name, dev_id, caps)
            val = op.get("to")
            if val not in (0, 1):
                raise JSONExecError("JSON_INVALID_VALUE", f"set 'to' must be 0 or 1, got {val}.")
            if dev_name not in ("relay1", "relay2"):
                raise JSONExecError(
                    "JSON_INVALID_SET_TARGET",
                    f"Only relay1/relay2 can be set, got '{dev_name}'.",
                )
            relays[dev_name] = val
            i += 1

        elif op_type == "read":
            dev_name = op.get("dev", "")
            dev_id = _resolve_device(dev_name)
            _check_cap(dev_name, dev_id, caps)
            if dev_name in relays:
                result_top = relays[dev_name]
            else:
                result_top = DEFAULT_SENSOR_VALUES.get(dev_id, 0)
            i += 1

        elif op_type == "wait":
            ms = op.get("ms", 0)
            if not isinstance(ms, int) or ms < 0:
                raise JSONExecError("JSON_INVALID_ARGUMENT", f"wait 'ms' must be non-negative integer, got {ms}.")
            i += 1

        elif op_type == "readback":
            dev_name = op.get("dev", "")
            dev_id = _resolve_device(dev_name)
            _check_cap(dev_name, dev_id, caps)
            expected = op.get("expect")
            if expected not in (0, 1):
                raise JSONExecError("JSON_INVALID_VALUE", f"readback 'expect' must be 0 or 1, got {expected}.")
            actual = relays.get(dev_name, DEFAULT_SENSOR_VALUES.get(dev_id, 0))
            result_top = 1 if actual == expected else 0
            i += 1

        elif op_type == "retry":
            times = op.get("times", 1)
            sub_body = op.get("do", [])
            if not isinstance(sub_body, list) or not sub_body:
                raise JSONExecError("JSON_RETRY_BODY_ERROR", "retry 'do' must be a non-empty array.")
            if not isinstance(times, int) or times < 1:
                raise JSONExecError("JSON_INVALID_ARGUMENT", f"retry 'times' must be positive integer, got {times}.")
            # Verify last op in retry body is readback
            last_op = sub_body[-1]
            if not isinstance(last_op, dict) or last_op.get("op") != "readback":
                raise JSONExecError(
                    "JSON_RETRY_BODY_ERROR",
                    "retry body must end with readback.",
                )
            for attempt in range(times):
                sub_result, sub_steps = _execute_body(sub_body, caps, relays, step_limit - steps)
                steps += sub_steps
                result_top = sub_result
                if result_top == 1:
                    break
            i += 1

        elif op_type == "repeat":
            times = op.get("times", 1)
            sub_body = op.get("do", [])
            if not isinstance(sub_body, list) or not sub_body:
                raise JSONExecError("JSON_REPEAT_BODY_ERROR", "repeat 'do' must be a non-empty array.")
            if not isinstance(times, int) or times < 1:
                raise JSONExecError("JSON_INVALID_ARGUMENT", f"repeat 'times' must be positive integer, got {times}.")
            for _ in range(times):
                sub_result, sub_steps = _execute_body(sub_body, caps, relays, step_limit - steps)
                steps += sub_steps
                result_top = sub_result
            i += 1

        elif op_type == "halt":
            i += 1
            break

        else:
            raise JSONExecError("JSON_INVALID_OP", f"Unknown operation '{op_type}'.")

    return result_top, steps


def interpret_json_program(prog: dict) -> dict:
    """Interpret a JSON control program and return evaluation row fields."""
    row = {
        "ir_valid": 0,
        "structural_ok": 0,
        "execution_pass": 0,
        "relay1": 0,
        "relay2": 0,
        "result_top": None,
        "error_stage": "",
        "error_code": "",
        "hint": "",
    }

    # Structural validation
    if not isinstance(prog, dict):
        row["error_stage"] = "parse"
        row["error_code"] = "JSON_PARSE_ERROR"
        row["hint"] = "Output must be a JSON object."
        return row

    row["ir_valid"] = 1

    if "body" not in prog or not isinstance(prog.get("body"), list):
        row["error_stage"] = "schema"
        row["error_code"] = "JSON_SCHEMA_ERROR"
        row["hint"] = "JSON must have a 'body' array."
        return row

    row["structural_ok"] = 1

    # Execute
    caps_raw = prog.get("cap", [])
    if not isinstance(caps_raw, list):
        row["error_stage"] = "schema"
        row["error_code"] = "JSON_SCHEMA_ERROR"
        row["hint"] = "'cap' must be an array of device names."
        return row

    caps = set()
    for c in caps_raw:
        if c in DEVICE_IDS:
            caps.add(DEVICE_IDS[c])

    relays = {"relay1": 0, "relay2": 0}

    try:
        result_top, _ = _execute_body(prog["body"], caps, relays)
        row["execution_pass"] = 1
        row["result_top"] = result_top
    except JSONExecError as e:
        row["error_stage"] = "execute"
        row["error_code"] = e.code
        row["hint"] = e.message
        return row

    row["relay1"] = relays.get("relay1", 0)
    row["relay2"] = relays.get("relay2", 0)
    return row


# ---------------------------------------------------------------------------
# Expected signature from golden M-IR
# ---------------------------------------------------------------------------

def get_expected_relay_state(task: dict) -> Dict[str, int]:
    """Compile and simulate golden M-IR, return expected relay states."""
    try:
        _, payload = compile_source(task["expected_mir"])
        from backend_adapter import simulate_subset
        backend = simulate_subset(payload)
        return {
            "relay1": backend.relay_state.get(DEVICE_IDS["relay1"], 0),
            "relay2": backend.relay_state.get(DEVICE_IDS["relay2"], 0),
        }
    except Exception:
        return {"relay1": 0, "relay2": 0}


# ---------------------------------------------------------------------------
# Main evaluation
# ---------------------------------------------------------------------------

def evaluate_json_candidate(task: dict, expected_relays: Dict[str, int], json_text: str) -> dict:
    """Evaluate a single JSON candidate."""
    row = {
        "task_id": task["task_id"],
        "category": task.get("category", ""),
        "ir_valid": 0,
        "structural_ok": 0,
        "execution_pass": 0,
        "task_success": 0,
        "error_stage": "",
        "error_code": "",
        "hint": "",
        "candidate_json": json_text.strip(),
        "raw_bytes": len(json_text.encode("utf-8")),
        "compact_bytes": 0,
        "zlib_bytes": 0,
        "cbor_bytes": 0,
        "m_bytecode_bytes": 0,
    }

    # Parse JSON
    prog = extract_json(json_text)
    if prog is None:
        row["error_stage"] = "parse"
        row["error_code"] = "JSON_PARSE_ERROR"
        row["hint"] = "Output valid JSON without markdown fences or extra text."
        return row

    # Interpret
    interp = interpret_json_program(prog)
    row["ir_valid"] = interp["ir_valid"]
    row["structural_ok"] = interp["structural_ok"]
    row["execution_pass"] = interp["execution_pass"]
    row["error_stage"] = interp["error_stage"]
    row["error_code"] = interp["error_code"]
    row["hint"] = interp["hint"]

    if not interp["execution_pass"]:
        return row

    # Check task success: final relay state matches expected
    if (interp["relay1"] == expected_relays.get("relay1", 0) and
            interp["relay2"] == expected_relays.get("relay2", 0)):
        row["task_success"] = 1
    else:
        row["error_stage"] = "task"
        row["error_code"] = "TASK_SIGNATURE_MISMATCH"
        expected_str = f"relay1={expected_relays.get('relay1')}, relay2={expected_relays.get('relay2')}"
        got_str = f"relay1={interp['relay1']}, relay2={interp['relay2']}"
        row["hint"] = f"Final relay state mismatch. Expected: {expected_str}. Got: {got_str}."

    # Size metrics
    raw_json = json_text.encode("utf-8")
    row["raw_bytes"] = len(raw_json)

    # Compact JSON (no whitespace)
    compact = json.dumps(prog, separators=(",", ":")).encode("utf-8")
    row["compact_bytes"] = len(compact)

    # zlib compression (level 9)
    row["zlib_bytes"] = len(zlib.compress(compact, level=9))

    # CBOR
    if HAS_CBOR:
        try:
            row["cbor_bytes"] = len(cbor2.dumps(prog))
        except Exception:
            row["cbor_bytes"] = 0
    else:
        row["cbor_bytes"] = 0

    # M-bytecode from golden M-IR
    try:
        _, m_payload = compile_source(task["expected_mir"])
        row["m_bytecode_bytes"] = len(m_payload)
    except Exception:
        row["m_bytecode_bytes"] = 0

    return row


def wilson_ci(k: int, n: int, z: float = 1.959963984540054) -> Tuple[float, float]:
    if n <= 0:
        return 0.0, 0.0
    import math
    phat = k / n
    den = 1.0 + (z * z) / n
    center = (phat + (z * z) / (2.0 * n)) / den
    half = (z / den) * math.sqrt((phat * (1.0 - phat) / n) + (z * z) / (4.0 * n * n))
    return max(0.0, center - half), min(1.0, center + half)


def write_summary(path: Path, rows: List[dict]) -> None:
    import math
    total = len(rows)
    ir_valid = sum(int(r["ir_valid"]) for r in rows)
    structural_ok = sum(int(r["structural_ok"]) for r in rows)
    execution_pass = sum(int(r["execution_pass"]) for r in rows)
    task_success = sum(int(r["task_success"]) for r in rows)
    errors = Counter(r["error_code"] for r in rows if r["error_code"])

    # Size stats (only for structurally valid JSON)
    valid_rows = [r for r in rows if r["structural_ok"]]
    n_valid = len(valid_rows)
    if n_valid > 0:
        avg_raw = sum(r["raw_bytes"] for r in valid_rows) / n_valid
        avg_compact = sum(r["compact_bytes"] for r in valid_rows) / n_valid
        avg_zlib = sum(r["zlib_bytes"] for r in valid_rows) / n_valid
        avg_cbor = sum(r["cbor_bytes"] for r in valid_rows if r["cbor_bytes"] > 0) / max(
            sum(1 for r in valid_rows if r["cbor_bytes"] > 0), 1
        )
        avg_mbc = sum(r["m_bytecode_bytes"] for r in valid_rows if r["m_bytecode_bytes"] > 0) / max(
            sum(1 for r in valid_rows if r["m_bytecode_bytes"] > 0), 1
        )
    else:
        avg_raw = avg_compact = avg_zlib = avg_cbor = avg_mbc = 0.0

    # Wilson CI for key rates
    json_ci_lo, json_ci_hi = wilson_ci(ir_valid, total)
    task_ci_lo, task_ci_hi = wilson_ci(task_success, total)

    lines = [
        "# JSON Baseline Eval Summary",
        "",
        f"- total: {total}",
        f"- json_valid_rate: {ir_valid / total:.3f} (95% CI [{json_ci_lo:.3f}, {json_ci_hi:.3f}])",
        f"- structural_ok_rate: {structural_ok / total:.3f}",
        f"- execution_pass_rate: {execution_pass / total:.3f}",
        f"- task_success_rate: {task_success / total:.3f} (95% CI [{task_ci_lo:.3f}, {task_ci_hi:.3f}])",
        "",
        "## Size Comparison (structurally valid JSON only)",
        "",
        f"- n: {n_valid}",
        f"- Avg raw JSON (LLM output):  {avg_raw:.1f} bytes",
        f"- Avg compact JSON:           {avg_compact:.1f} bytes",
        f"- Avg zlib (level 9):         {avg_zlib:.1f} bytes",
        f"- Avg CBOR:                   {avg_cbor:.1f} bytes",
        f"- Avg M-bytecode (golden):    {avg_mbc:.1f} bytes",
    ]

    if avg_mbc > 0 and avg_zlib > 0:
        lines.append(f"- M vs raw JSON:      {avg_raw / avg_mbc:.1f}x compression")
        lines.append(f"- M vs compact JSON:  {avg_compact / avg_mbc:.1f}x compression")
        lines.append(f"- M vs zlib JSON:     {avg_zlib / avg_mbc:.1f}x compression")
        if avg_cbor > 0:
            lines.append(f"- M vs CBOR:          {avg_cbor / avg_mbc:.1f}x compression")

    lines.append("")
    lines.append("## Error Breakdown")
    lines.append("")
    if errors:
        for code, count in errors.most_common():
            lines.append(f"- {code}: {count}")
    else:
        lines.append("- none")

    lines.append("")
    lines.append("## Comparison to Direct Hex Baseline")
    lines.append("")
    lines.append("| Metric | Direct Hex | JSON + Schema | M-IR (golden) |")
    lines.append("|---|---|---|---|")
    hex_success = 0.000  # known from prior experiments
    lines.append(f"| ir_valid_rate | 0.000 | {ir_valid / total:.3f} | 1.000 |")
    lines.append(f"| task_success_rate | {hex_success:.3f} | {task_success / total:.3f} | 1.000 |")
    if avg_mbc > 0:
        lines.append(f"| Avg payload bytes | N/A | {avg_zlib:.1f} (zlib) | {avg_mbc:.1f} |")

    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Evaluate JSON baseline candidates.")
    parser.add_argument(
        "--tasks",
        default=str(Path(__file__).resolve().parent.parent / "data" / "tasks_v2.jsonl"),
    )
    parser.add_argument("--candidates", required=True, help="JSON candidates JSONL")
    parser.add_argument(
        "--out-dir",
        default=str(Path(__file__).resolve().parent.parent / "result" / "GEN"),
    )
    parser.add_argument("--tag", default="json_baseline_v1")
    args = parser.parse_args()

    tasks = load_jsonl(Path(args.tasks))
    tasks_by_id = {t["task_id"]: t for t in tasks}

    # Pre-compute expected relay states from golden M-IR
    expected_relays = {t["task_id"]: get_expected_relay_state(t) for t in tasks}

    # Pre-compute golden M-bytecode (for verification that compile works)
    _ = compile_expected_payloads(tasks)

    rows = []
    for item in load_jsonl(Path(args.candidates)):
        tid = item["task_id"]
        if tid not in tasks_by_id:
            continue
        task = tasks_by_id[tid]
        json_text = item.get("mir", item.get("json", ""))
        rows.append(evaluate_json_candidate(task, expected_relays[tid], json_text))

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    # Write CSV
    csv_path = out_dir / f"json_baseline_eval_{args.tag}.csv"
    fieldnames = [
        "task_id", "category", "ir_valid", "structural_ok", "execution_pass",
        "task_success", "error_stage", "error_code", "hint",
        "raw_bytes", "compact_bytes", "zlib_bytes", "cbor_bytes", "m_bytecode_bytes",
        "candidate_json",
    ]
    with csv_path.open("w", encoding="utf-8-sig", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)

    # Write summary
    md_path = out_dir / f"json_baseline_eval_{args.tag}.md"
    write_summary(md_path, rows)

    print(str(csv_path))
    print(str(md_path))

    # Quick summary to stdout
    total = len(rows)
    if total:
        print(f"\nJSON Baseline ({total} tasks):")
        print(f"  json_valid:     {sum(int(r['ir_valid']) for r in rows) / total:.3f}")
        print(f"  structural_ok:  {sum(int(r['structural_ok']) for r in rows) / total:.3f}")
        print(f"  execution_pass: {sum(int(r['execution_pass']) for r in rows) / total:.3f}")
        print(f"  task_success:   {sum(int(r['task_success']) for r in rows) / total:.3f}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
