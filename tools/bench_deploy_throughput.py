#!/usr/bin/env python3
"""
E10 deploy metric: guarded throughput on ESP8266.

Protocol:
  send: [4-byte LE length][M bytecode]
  recv: [4-byte LE length][payload]
        OK    payload: [result varint][steps varint][0x01]
        FAULT payload: [fault varint][pc varint][0x00]
"""

from __future__ import annotations

import argparse
import csv
import os
import statistics
import time
from datetime import datetime
from typing import Dict, List, Optional, Tuple

try:
    import serial  # type: ignore
except ImportError:
    serial = None


M_LIT = 30
M_IOW = 70
M_GTWAY = 80
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


def m_lit(v: int) -> bytes:
    return op(M_LIT) + encode_uvarint(encode_zigzag64(v))


def prog_set(device: int, target: int) -> bytes:
    # GTWAY dev; LIT target; IOW dev; HALT
    buf = bytearray()
    buf += op(M_GTWAY) + encode_uvarint(device)
    buf += m_lit(target)
    buf += op(M_IOW) + encode_uvarint(device)
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
        "result": None,
        "steps": None,
        "fault": None,
        "pc": None,
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
    if flag == 0x01:
        out["result"] = v1
        out["steps"] = v2
    else:
        out["fault"] = v1
        out["pc"] = v2
    return out


def transact(ser, payload: bytes, timeout: float) -> Tuple[str, Optional[Dict[str, Optional[int]]], Optional[float]]:
    try:
        ser.timeout = timeout
        ser.reset_input_buffer()
        t0 = time.perf_counter()
        ser.write(frame(payload))
        ser.flush()
        lb = ser.read(4)
        if len(lb) < 4:
            return "timeout", None, None
        resp_len = int.from_bytes(lb, "little")
        if resp_len <= 0 or resp_len > 512:
            return "io_error", None, None
        resp = ser.read(resp_len)
        if len(resp) < resp_len:
            return "timeout", None, None
        t1 = time.perf_counter()
        return "ok", parse_response(resp), (t1 - t0) * 1000.0
    except Exception:
        return "io_error", None, None


def percentile(vals: List[float], q: float) -> float:
    if not vals:
        return 0.0
    s = sorted(vals)
    if len(s) == 1:
        return s[0]
    pos = (len(s) - 1) * q
    lo = int(pos)
    hi = min(lo + 1, len(s) - 1)
    frac = pos - lo
    return s[lo] * (1.0 - frac) + s[hi] * frac


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--serial", required=True, help="COM port, e.g., COM5")
    ap.add_argument("--repeat", type=int, default=1000)
    ap.add_argument("--timeout", type=float, default=1.0)
    ap.add_argument("--device", type=int, default=5)
    ap.add_argument("--variant", default="guarded")
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

    rows: List[Dict[str, str]] = []
    rtts: List[float] = []
    ok_count = 0
    fault_count = 0
    timeout_count = 0
    io_error_count = 0

    t_start = time.perf_counter()
    with serial.Serial(args.serial, 115200, timeout=args.timeout) as ser:
        for i in range(1, args.repeat + 1):
            target = i % 2
            status, pd, rtt_ms = transact(ser, prog_set(args.device, target), args.timeout)

            ok_flag = ""
            fault_code = ""
            if status == "ok" and pd is not None:
                ok_flag = str(int(pd["ok"] or 0))
                if int(pd["ok"] or 0) == 1:
                    ok_count += 1
                else:
                    fault_count += 1
                    fault_code = "" if pd["fault"] is None else str(pd["fault"])
            elif status == "timeout":
                timeout_count += 1
            else:
                io_error_count += 1

            if rtt_ms is not None:
                rtts.append(rtt_ms)

            rows.append(
                {
                    "iter": str(i),
                    "variant": args.variant,
                    "target": str(target),
                    "status": status,
                    "ok": ok_flag,
                    "fault": fault_code,
                    "rtt_ms": "" if rtt_ms is None else f"{rtt_ms:.3f}",
                }
            )
    t_end = time.perf_counter()
    elapsed_s = max(t_end - t_start, 1e-9)

    rtt_mean = statistics.fmean(rtts) if rtts else 0.0
    rtt_std = statistics.pstdev(rtts) if len(rtts) > 1 else 0.0
    rtt_p95 = percentile(rtts, 0.95) if rtts else 0.0
    throughput = ok_count / elapsed_s

    summary = [
        {
            "variant": args.variant,
            "n": str(args.repeat),
            "ok_count": str(ok_count),
            "fault_count": str(fault_count),
            "timeout_count": str(timeout_count),
            "io_error_count": str(io_error_count),
            "elapsed_s": f"{elapsed_s:.6f}",
            "throughput_cmd_s": f"{throughput:.6f}",
            "rtt_mean_ms": f"{rtt_mean:.3f}",
            "rtt_std_ms": f"{rtt_std:.3f}",
            "rtt_p95_ms": f"{rtt_p95:.3f}",
        }
    ]

    raw_path = os.path.join(raw_dir, f"throughput_trials_{args.variant}_{tag}.csv")
    summary_path = os.path.join(args.out_dir, f"throughput_summary_{args.variant}_{tag}.csv")

    with open(raw_path, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["iter", "variant", "target", "status", "ok", "fault", "rtt_ms"])
        w.writeheader()
        w.writerows(rows)

    with open(summary_path, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(
            f,
            fieldnames=[
                "variant",
                "n",
                "ok_count",
                "fault_count",
                "timeout_count",
                "io_error_count",
                "elapsed_s",
                "throughput_cmd_s",
                "rtt_mean_ms",
                "rtt_std_ms",
                "rtt_p95_ms",
            ],
        )
        w.writeheader()
        w.writerows(summary)

    if args.write_latest:
        latest_raw = os.path.join(args.out_dir, "throughput_trials.csv")
        latest_summary = os.path.join(args.out_dir, "throughput_summary.csv")
        with open(latest_raw, "w", encoding="utf-8", newline="") as f:
            w = csv.DictWriter(f, fieldnames=["iter", "variant", "target", "status", "ok", "fault", "rtt_ms"])
            w.writeheader()
            w.writerows(rows)
        with open(latest_summary, "w", encoding="utf-8", newline="") as f:
            w = csv.DictWriter(
                f,
                fieldnames=[
                    "variant",
                    "n",
                    "ok_count",
                    "fault_count",
                    "timeout_count",
                    "io_error_count",
                    "elapsed_s",
                    "throughput_cmd_s",
                    "rtt_mean_ms",
                    "rtt_std_ms",
                    "rtt_p95_ms",
                ],
            )
            w.writeheader()
            w.writerows(summary)
        print(f"Wrote latest aliases: {latest_raw}, {latest_summary}")

    print(f"Wrote: {raw_path}")
    print(f"Wrote: {summary_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
