#!/usr/bin/env python3
"""
Compare payload sizes: M-bytecode vs JSON vs CBOR vs MessagePack.

Reads the token comparison CSV (which has LLM-generated JSON responses),
parses the JSON payloads, encodes them with CBOR and MessagePack,
compiles the golden M-IR to M-bytecode, and reports sizes.
"""
from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import cbor2
import msgpack

# Add tools dir to path for local imports
sys.path.insert(0, str(Path(__file__).resolve().parent))
from backend_adapter import DEVICE_IDS
from mir_compiler import compile_source, MirCompilerError


def extract_json_from_response(response: str) -> Optional[dict]:
    """Extract JSON object from LLM response, stripping markdown fences."""
    text = response.strip()
    # Strip ```json ... ``` fences
    m = re.search(r"```(?:json)?\s*\n?(.*?)```", text, re.DOTALL)
    if m:
        text = m.group(1).strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return None


def compile_mir_to_bytes(mir_source: str) -> Optional[bytes]:
    """Compile M-IR source to M-bytecode bytes."""
    try:
        result = compile_source(mir_source)
        # compile_source returns (Program, bytes)
        if isinstance(result, tuple) and len(result) == 2:
            return result[1]
        return result.payload
    except (MirCompilerError, Exception):
        return None


def load_token_csv(path: Path) -> List[dict]:
    """Load the token comparison CSV."""
    rows = []
    with path.open("r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(row)
    return rows


def load_tasks(path: Path) -> Dict[str, dict]:
    """Load tasks JSONL as dict keyed by task_id."""
    tasks = {}
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                obj = json.loads(line)
                tasks[obj["task_id"]] = obj
    return tasks


def main() -> int:
    parser = argparse.ArgumentParser(description="CBOR/MsgPack baseline size comparison")
    parser.add_argument(
        "--token-csv",
        default=str(Path(__file__).resolve().parent.parent / "result" / "TOKEN" / "token_compare_v3_tasks_v2_semantics_r2.csv"),
        help="Path to token comparison CSV",
    )
    parser.add_argument(
        "--tasks",
        default=str(Path(__file__).resolve().parent.parent / "data" / "tasks_v2.jsonl"),
        help="Path to tasks JSONL",
    )
    parser.add_argument(
        "--out",
        default=str(Path(__file__).resolve().parent.parent / "result" / "TOKEN" / "cbor_msgpack_baseline.csv"),
        help="Output CSV path",
    )
    parser.add_argument("--limit", type=int, default=0, help="Limit number of tasks")
    args = parser.parse_args()

    rows = load_token_csv(Path(args.token_csv))
    tasks = load_tasks(Path(args.tasks))

    # Group by task_id and format
    task_formats: Dict[str, Dict[str, dict]] = {}
    for row in rows:
        tid = row["task_id"]
        fmt = row["format"]
        if tid not in task_formats:
            task_formats[tid] = {}
        task_formats[tid][fmt] = row

    results = []
    task_ids = sorted(task_formats.keys())
    if args.limit > 0:
        task_ids = task_ids[:args.limit]

    for tid in task_ids:
        formats = task_formats[tid]
        if "JSON" not in formats:
            continue

        json_row = formats["JSON"]
        json_response = json_row.get("response", "")

        # Parse JSON from LLM response
        parsed_json = extract_json_from_response(json_response)
        json_raw_bytes = json_response.encode("utf-8")

        # Encode with CBOR and MessagePack
        cbor_bytes = cbor2.dumps(parsed_json) if parsed_json else None
        msgpack_bytes = msgpack.packb(parsed_json, use_bin_type=True) if parsed_json else None

        # Compile M-IR to bytecode
        mir_bytes = None
        if "MIR" in formats:
            mir_response = formats["MIR"].get("response", "")
            mir_bytes = compile_mir_to_bytes(mir_response)

        # Also get the golden M-IR bytecode from task data
        golden_mir_bytes = None
        if tid in tasks:
            golden_mir = tasks[tid].get("expected_mir", "")
            if golden_mir:
                golden_mir_bytes = compile_mir_to_bytes(golden_mir)

        # Use golden M-IR bytecode if available, else LLM-generated
        m_bytecode = golden_mir_bytes if golden_mir_bytes else mir_bytes

        # JSON size: use the raw LLM output (including markdown fences if any)
        json_output_bytes = int(json_row.get("output_bytes", len(json_raw_bytes)))

        # Also compute "compact JSON" (parsed then re-serialized without whitespace)
        compact_json_bytes = len(json.dumps(parsed_json, separators=(",", ":")).encode("utf-8")) if parsed_json else None

        results.append({
            "task_id": tid,
            "json_output_bytes": json_output_bytes,
            "compact_json_bytes": compact_json_bytes,
            "cbor_bytes": len(cbor_bytes) if cbor_bytes else None,
            "msgpack_bytes": len(msgpack_bytes) if msgpack_bytes else None,
            "m_bytecode_bytes": len(m_bytecode) if m_bytecode else None,
            "json_parsed": parsed_json is not None,
        })

    # Write output
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "task_id", "json_output_bytes", "compact_json_bytes",
        "cbor_bytes", "msgpack_bytes", "m_bytecode_bytes", "json_parsed",
    ]
    with out_path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for r in results:
            writer.writerow(r)

    # Compute summary statistics
    valid = [r for r in results if r["json_parsed"] and r["cbor_bytes"] is not None]
    if not valid:
        print("No valid results!")
        return 1

    n = len(valid)
    avg_json = sum(r["json_output_bytes"] for r in valid) / n
    avg_compact = sum(r["compact_json_bytes"] for r in valid) / n
    avg_cbor = sum(r["cbor_bytes"] for r in valid) / n
    avg_msgpack = sum(r["msgpack_bytes"] for r in valid) / n

    has_bytecode = [r for r in valid if r["m_bytecode_bytes"] is not None]
    avg_mbc = sum(r["m_bytecode_bytes"] for r in has_bytecode) / len(has_bytecode) if has_bytecode else 0

    print(f"\n{'='*60}")
    print(f"CBOR / MessagePack Baseline Comparison ({n} tasks)")
    print(f"{'='*60}")
    print(f"  Avg JSON (LLM raw output):  {avg_json:.2f} bytes")
    print(f"  Avg JSON (compact):         {avg_compact:.2f} bytes")
    print(f"  Avg CBOR:                   {avg_cbor:.2f} bytes")
    print(f"  Avg MessagePack:            {avg_msgpack:.2f} bytes")
    if has_bytecode:
        print(f"  Avg M-bytecode (golden):    {avg_mbc:.2f} bytes")
        print(f"  {'-'*50}")
        print(f"  M vs JSON (raw):     {avg_json/avg_mbc:.3f}x compression")
        print(f"  M vs JSON (compact): {avg_compact/avg_mbc:.3f}x compression")
        print(f"  M vs CBOR:           {avg_cbor/avg_mbc:.3f}x compression")
        print(f"  M vs MessagePack:    {avg_msgpack/avg_mbc:.3f}x compression")
    print(f"  CBOR vs JSON (compact):     {avg_compact/avg_cbor:.3f}x compression")
    print(f"  MsgPack vs JSON (compact):  {avg_compact/avg_msgpack:.3f}x compression")
    print(f"\nOutput: {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
