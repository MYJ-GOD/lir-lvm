#!/usr/bin/env python3
"""
E10 deploy metric: E3 telemetry probe (time/free_heap/free_stack).

Protocol:
  send: [4-byte LE length][M bytecode]
  recv: [4-byte LE length][payload]
        payload tail: [flag]
        payload body: [result|fault][steps|pc][time_us][free_heap][free_stack]
"""

from __future__ import annotations

import argparse
import csv
import os
import statistics
from datetime import datetime
from typing import Dict, List, Optional, Tuple

try:
    import serial  # type: ignore
except ImportError:
    serial = None


M_LIT = 30
M_DRP = 65
M_MUL = 52
M_ADD = 50
M_HALT = 82


def encode_uvarint(n: int) -> bytes:
    out = bytearray()
    while True:
        b = n & 0x7F
        n >>= 7
        if n:
            out.append(b | 0x80)
        else:
            out.append(b)
            break
    return bytes(out)


def encode_zigzag64(n: int) -> int:
    return ((n << 1) ^ (n >> 63)) & 0xFFFFFFFFFFFFFFFF


def op(code: int) -> bytes:
    return encode_uvarint(code)


def lit(v: int) -> bytes:
    return op(M_LIT) + encode_uvarint(encode_zigzag64(v))


def prog_arith() -> bytes:
    # 5 + 3*2
    return lit(5) + lit(3) + lit(2) + op(M_MUL) + op(M_ADD) + op(M_HALT)


def prog_loop100() -> bytes:
    buf = bytearray()
    for _ in range(100):
        buf += lit(1)
        buf += op(M_DRP)
    buf += op(M_HALT)
    return bytes(buf)


def frame(payload: bytes) -> bytes:
    return len(payload).to_bytes(4, "little") + payload


def decode_uvarint_from_bytes(buf: bytes, pos: int = 0) -> Tuple[Optional[int], int]:
    res = 0
    shift = 0
    i = pos
    while i < len(buf):
        b = buf[i]
        i += 1
        res |= (b & 0x7F) << shift
        if (b & 0x80) == 0:
            return res, i
        shift += 7
        if shift >= 64:
            return None, pos
    return None, pos


def parse_response(resp: bytes) -> Dict[str, Optional[int]]:
    out: Dict[str, Optional[int]] = {
        "flag": None,
        "ok": None,
        "v1": None,
        "v2": None,
        "time_us": None,
        "free_heap": None,
        "free_stack": None,
    }
    if not resp:
        return out
    flag = resp[-1]
    payload = resp[:-1]
    out["flag"] = flag
    out["ok"] = 1 if flag == 0x01 else 0

    p = 0
    v1, p = decode_uvarint_from_bytes(payload, p)
    v2, p = decode_uvarint_from_bytes(payload, p)
    v3, p = decode_uvarint_from_bytes(payload, p)
    v4, p = decode_uvarint_from_bytes(payload, p)
    v5, p = decode_uvarint_from_bytes(payload, p)
    out["v1"] = v1
    out["v2"] = v2
    out["time_us"] = v3
    out["free_heap"] = v4
    out["free_stack"] = v5
    return out


def transact(ser, payload: bytes, timeout: float) -> Tuple[str, Optional[Dict[str, Optional[int]]]]:
    try:
        ser.timeout = timeout
        ser.reset_input_buffer()
        ser.write(frame(payload))
        ser.flush()
        lb = ser.read(4)
        if len(lb) < 4:
            return "timeout", None
        resp_len = int.from_bytes(lb, "little")
        if resp_len <= 0 or resp_len > 512:
            return "io_error", None
        resp = ser.read(resp_len)
        if len(resp) < resp_len:
            return "timeout", None
        return "ok", parse_response(resp)
    except Exception:
        return "io_error", None


def mean_or_zero(vals: List[float]) -> float:
    return statistics.fmean(vals) if vals else 0.0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--serial", required=True, help="COM port, e.g., COM5")
    ap.add_argument("--repeat", type=int, default=30)
    ap.add_argument("--timeout", type=float, default=2.0)
    ap.add_argument("--variant", default="e3_telemetry")
    ap.add_argument("--out-dir", default="论文分区/ccfc/result/E10_deploy")
    ap.add_argument("--tag", default="", help="run tag; default timestamp")
    ap.add_argument("--write-latest", action="store_true")
    args = ap.parse_args()

    if serial is None:
        raise SystemExit("pyserial not installed")
    if args.repeat <= 0:
        raise SystemExit("--repeat must be > 0")

    os.makedirs(args.out_dir, exist_ok=True)
    raw_dir = os.path.join(args.out_dir, "raw")
    os.makedirs(raw_dir, exist_ok=True)
    tag = args.tag or datetime.now().strftime("%Y%m%d_%H%M%S")

    tests = [("arith", prog_arith()), ("loop100", prog_loop100())]
    rows: List[Dict[str, str]] = []

    with serial.Serial(args.serial, 115200, timeout=args.timeout) as ser:
        for name, payload in tests:
            for i in range(1, args.repeat + 1):
                status, pd = transact(ser, payload, args.timeout)
                if status != "ok" or pd is None:
                    rows.append(
                        {
                            "test": name,
                            "iter": str(i),
                            "status": status,
                            "ok": "",
                            "val_or_fault": "",
                            "steps_or_pc": "",
                            "time_us": "",
                            "free_heap": "",
                            "free_stack": "",
                        }
                    )
                    continue

                rows.append(
                    {
                        "test": name,
                        "iter": str(i),
                        "status": status,
                        "ok": str(int(pd["ok"] or 0)),
                        "val_or_fault": "" if pd["v1"] is None else str(pd["v1"]),
                        "steps_or_pc": "" if pd["v2"] is None else str(pd["v2"]),
                        "time_us": "" if pd["time_us"] is None else str(pd["time_us"]),
                        "free_heap": "" if pd["free_heap"] is None else str(pd["free_heap"]),
                        "free_stack": "" if pd["free_stack"] is None else str(pd["free_stack"]),
                    }
                )

    def summarize(sub_rows: List[Dict[str, str]], name: str) -> Dict[str, str]:
        ok_rows = [r for r in sub_rows if r["ok"] == "1"]
        heaps = [float(r["free_heap"]) for r in ok_rows if r["free_heap"] != ""]
        stacks = [float(r["free_stack"]) for r in ok_rows if r["free_stack"] != ""]
        times = [float(r["time_us"]) for r in ok_rows if r["time_us"] != ""]
        heap_min = min(heaps) if heaps else 0.0
        heap_max = max(heaps) if heaps else 0.0
        stack_min = min(stacks) if stacks else 0.0
        stack_max = max(stacks) if stacks else 0.0
        return {
            "group": name,
            "variant": args.variant,
            "n_total": str(len(sub_rows)),
            "n_ok": str(len(ok_rows)),
            "time_us_mean": f"{mean_or_zero(times):.3f}",
            "free_heap_min": f"{heap_min:.3f}",
            "free_heap_mean": f"{mean_or_zero(heaps):.3f}",
            "free_heap_max": f"{heap_max:.3f}",
            "free_stack_min": f"{stack_min:.3f}",
            "free_stack_mean": f"{mean_or_zero(stacks):.3f}",
            "free_stack_max": f"{stack_max:.3f}",
            "heap_waterline": f"{(heap_max - heap_min):.3f}",
            "stack_waterline": f"{(stack_max - stack_min):.3f}",
        }

    summary_rows: List[Dict[str, str]] = []
    for name, _ in tests:
        summary_rows.append(summarize([r for r in rows if r["test"] == name], name))
    summary_rows.append(summarize(rows, "all"))

    raw_path = os.path.join(raw_dir, f"e3_mem_results_{args.variant}_{tag}.csv")
    summary_path = os.path.join(args.out_dir, f"e3_mem_summary_{args.variant}_{tag}.csv")

    with open(raw_path, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(
            f,
            fieldnames=[
                "test",
                "iter",
                "status",
                "ok",
                "val_or_fault",
                "steps_or_pc",
                "time_us",
                "free_heap",
                "free_stack",
            ],
        )
        w.writeheader()
        w.writerows(rows)

    with open(summary_path, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(
            f,
            fieldnames=[
                "group",
                "variant",
                "n_total",
                "n_ok",
                "time_us_mean",
                "free_heap_min",
                "free_heap_mean",
                "free_heap_max",
                "free_stack_min",
                "free_stack_mean",
                "free_stack_max",
                "heap_waterline",
                "stack_waterline",
            ],
        )
        w.writeheader()
        w.writerows(summary_rows)

    if args.write_latest:
        latest_raw = os.path.join(args.out_dir, "e3_mem_results.csv")
        latest_summary = os.path.join(args.out_dir, "e3_mem_summary.csv")
        with open(latest_raw, "w", encoding="utf-8", newline="") as f:
            w = csv.DictWriter(
                f,
                fieldnames=[
                    "test",
                    "iter",
                    "status",
                    "ok",
                    "val_or_fault",
                    "steps_or_pc",
                    "time_us",
                    "free_heap",
                    "free_stack",
                ],
            )
            w.writeheader()
            w.writerows(rows)
        with open(latest_summary, "w", encoding="utf-8", newline="") as f:
            w = csv.DictWriter(
                f,
                fieldnames=[
                    "group",
                    "variant",
                    "n_total",
                    "n_ok",
                    "time_us_mean",
                    "free_heap_min",
                    "free_heap_mean",
                    "free_heap_max",
                    "free_stack_min",
                    "free_stack_mean",
                    "free_stack_max",
                    "heap_waterline",
                    "stack_waterline",
                ],
            )
            w.writeheader()
            w.writerows(summary_rows)
        print(f"Wrote latest aliases: {latest_raw}, {latest_summary}")

    print(f"Wrote: {raw_path}")
    print(f"Wrote: {summary_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
