#!/usr/bin/env python3
"""
E5+ prior-sweep harness for SAFE diversion evaluation.

Compared with bench_scr.py (fixed 50/50 alternating), this script samples
scenarios with configurable fault prior and reports classification metrics:
TP/FP/FN/TN, Precision, Recall, FPR, FNR, plus OK/SAFE ratios.

Prediction rule:
- flag == 0x01 -> predict_ok
- flag == 0x00 -> predict_fault
- no response/parse error -> predict_unknown (counted as misclassification)
"""

import argparse
import csv
import os
import random
import statistics
import time
from datetime import datetime
from typing import Optional, Tuple

try:
    import serial  # type: ignore
except ImportError:
    serial = None

M_IOW = 70
M_HALT = 82
M_LIT = 30
M_GTWAY = 80


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


def op(opcode: int) -> bytes:
    return encode_uvarint(opcode)


def encode_zigzag64(n: int) -> int:
    return ((n << 1) ^ (n >> 63)) & 0xFFFFFFFFFFFFFFFF


def lit(v: int) -> bytes:
    return op(M_LIT) + encode_uvarint(encode_zigzag64(v))


def program_ok_relay_on() -> bytes:
    return op(M_GTWAY) + encode_uvarint(5) + lit(1) + op(M_IOW) + encode_uvarint(5) + op(M_HALT)


def program_fault_bad_varint() -> bytes:
    return op(M_LIT) + bytes([0x80])


def frame(payload: bytes) -> bytes:
    return len(payload).to_bytes(4, "little") + payload


def measure(port: str, payload: bytes, timeout: float) -> Optional[Tuple[str, float]]:
    if serial is None:
        return None
    with serial.Serial(port, 115200, timeout=timeout) as ser:
        ser.reset_input_buffer()
        start = time.perf_counter()
        ser.write(frame(payload))
        ser.flush()
        len_bytes = ser.read(4)
        if len(len_bytes) < 4:
            return None
        resp_len = int.from_bytes(len_bytes, "little")
        if resp_len <= 0 or resp_len > 256:
            return None
        resp = ser.read(resp_len)
        if len(resp) < resp_len:
            return None
        end = time.perf_counter()
        return resp.hex(), (end - start) * 1000.0


def parse_flag_and_fault(resp_hex: str) -> Tuple[Optional[int], Optional[int]]:
    if not resp_hex:
        return None, None
    b = bytes.fromhex(resp_hex)
    if len(b) == 0:
        return None, None
    flag = b[-1]
    fault = None
    if flag != 0x01:
        fc = 0
        shift = 0
        idx = 0
        while idx < len(b) - 1:
            v = b[idx]
            idx += 1
            fc |= (v & 0x7F) << shift
            if v & 0x80 == 0:
                break
            shift += 7
        fault = fc
    return flag, fault


def safe_div(a: float, b: float) -> float:
    return a / b if b > 0 else 0.0


def pct_key(prior: float) -> str:
    return f"p{int(round(prior * 100)):02d}"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--serial", required=True, help="COM port, e.g., COM5")
    parser.add_argument("--timeout", type=float, default=1.0)
    parser.add_argument("--n", type=int, default=200, help="total samples")
    parser.add_argument("--fault-prior", type=float, required=True, help="fault scenario prior in [0,1]")
    parser.add_argument("--seed", type=int, default=20260218)
    parser.add_argument("--variant", default="guarded", choices=["guarded", "noguard", "current"])
    parser.add_argument("--out-dir", default="论文分区/ccfc/result/E5_prior")
    parser.add_argument("--tag", default="")
    parser.add_argument("--write-latest", action="store_true")
    args = parser.parse_args()

    if args.n <= 0:
        raise SystemExit("--n must be > 0")
    if not (0.0 <= args.fault_prior <= 1.0):
        raise SystemExit("--fault-prior must be in [0,1]")

    os.makedirs(args.out_dir, exist_ok=True)

    prior_key = pct_key(args.fault_prior)
    tag = args.tag or datetime.now().strftime("%Y%m%d_%H%M%S")

    payload_ok = program_ok_relay_on()
    payload_fault = program_fault_bad_varint()

    rng = random.Random(args.seed)

    tp = fp = fn = tn = 0
    ok_count = safe_count = unknown_count = 0
    rtts = []
    rows = []

    for i in range(1, args.n + 1):
        is_fault = rng.random() < args.fault_prior
        scenario = "fault_path" if is_fault else "ok_path"
        gt = "fault" if is_fault else "ok"
        payload = payload_fault if is_fault else payload_ok

        res = measure(args.serial, payload, args.timeout)
        resp_hex = ""
        rtt_ms = ""
        flag = None
        fault_code = None
        pred = "unknown"

        if res:
            resp_hex, rtt = res
            rtt_ms = f"{rtt:.3f}"
            rtts.append(rtt)
            flag, fault_code = parse_flag_and_fault(resp_hex)
            if flag == 0x01:
                pred = "ok"
                ok_count += 1
            elif flag == 0x00:
                pred = "fault"
                safe_count += 1
            else:
                pred = "unknown"
                unknown_count += 1
        else:
            unknown_count += 1

        if gt == "fault":
            if pred == "fault":
                tp += 1
            else:
                fn += 1
        else:
            if pred == "fault":
                fp += 1
            elif pred == "ok":
                tn += 1
            else:
                fp += 1  # conservative: unknown on ok-path counted as false alarm

        rows.append(
            {
                "iter": i,
                "scenario": scenario,
                "ground_truth": gt,
                "resp_hex": resp_hex,
                "flag": "" if flag is None else flag,
                "fault_code": "" if fault_code is None else fault_code,
                "pred": pred,
                "rtt_ms": rtt_ms,
                "tp_cum": tp,
                "fp_cum": fp,
                "fn_cum": fn,
                "tn_cum": tn,
                "ok_cum": ok_count,
                "safe_cum": safe_count,
            }
        )

    precision = safe_div(tp, tp + fp)
    recall = safe_div(tp, tp + fn)
    fpr = safe_div(fp, fp + tn)
    fnr = safe_div(fn, fn + tp)
    ok_ratio = safe_div(ok_count, args.n)
    safe_ratio = safe_div(safe_count, args.n)
    rtt_mean = statistics.fmean(rtts) if rtts else 0.0
    rtt_std = statistics.pstdev(rtts) if len(rtts) > 1 else 0.0

    detail_file = os.path.join(args.out_dir, f"scr_prior_{args.variant}_{prior_key}_{tag}.csv")
    with open(detail_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "iter",
                "scenario",
                "ground_truth",
                "resp_hex",
                "flag",
                "fault_code",
                "pred",
                "rtt_ms",
                "tp_cum",
                "fp_cum",
                "fn_cum",
                "tn_cum",
                "ok_cum",
                "safe_cum",
            ],
        )
        writer.writeheader()
        writer.writerows(rows)

    summary = {
        "variant": args.variant,
        "fault_prior": f"{args.fault_prior:.3f}",
        "prior_key": prior_key,
        "n": args.n,
        "tp": tp,
        "fp": fp,
        "fn": fn,
        "tn": tn,
        "precision": f"{precision:.6f}",
        "recall": f"{recall:.6f}",
        "fpr": f"{fpr:.6f}",
        "fnr": f"{fnr:.6f}",
        "ok_ratio": f"{ok_ratio:.6f}",
        "safe_ratio": f"{safe_ratio:.6f}",
        "rtt_ms_mean": f"{rtt_mean:.3f}",
        "rtt_ms_std": f"{rtt_std:.3f}",
        "unknown_count": unknown_count,
        "detail_file": detail_file,
    }

    summary_file = os.path.join(args.out_dir, f"scr_prior_summary_{args.variant}_{prior_key}_{tag}.csv")
    with open(summary_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(summary.keys()))
        writer.writeheader()
        writer.writerow(summary)

    print(f"Wrote {detail_file}")
    print(f"Wrote {summary_file}")

    if args.write_latest:
        detail_latest = os.path.join(args.out_dir, f"scr_prior_{args.variant}_{prior_key}.csv")
        summary_latest = os.path.join(args.out_dir, f"scr_prior_summary_{args.variant}_{prior_key}.csv")
        with open(detail_latest, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(
                f,
                fieldnames=[
                    "iter",
                    "scenario",
                    "ground_truth",
                    "resp_hex",
                    "flag",
                    "fault_code",
                    "pred",
                    "rtt_ms",
                    "tp_cum",
                    "fp_cum",
                    "fn_cum",
                    "tn_cum",
                    "ok_cum",
                    "safe_cum",
                ],
            )
            writer.writeheader()
            writer.writerows(rows)
        with open(summary_latest, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=list(summary.keys()))
            writer.writeheader()
            writer.writerow(summary)
        print(f"Wrote latest {detail_latest}")
        print(f"Wrote latest {summary_latest}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
