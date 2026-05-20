#!/usr/bin/env python3
"""
E4+ real JSON/text parsing benchmark.

Board protocol (mvm_esp8266_e4_json_real.ino):
  send: [4-byte LE length][UTF-8 JSON command]
  recv: [4-byte LE length][payload]
        OK    payload: [result zigzag-varint][steps varint][0x01]
        FAULT payload: [fault varint][pc varint][0x00]

Modes:
  - open_loop: set -> optional disturb -> get
  - closed_loop_no_retry: set -> optional disturb -> get/compare
  - closed_loop_retry: set -> optional disturb -> get/compare -> retry

The JSON path remains app-driven, so closed-loop here is an application-layer
retry baseline rather than an execution-plane built-in mechanism.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import os
import random
import statistics
import time
from datetime import datetime
from typing import Dict, List, Optional, Tuple

try:
    import serial  # type: ignore
except ImportError:
    serial = None


MODE_TO_GROUP = {
    "open_loop": "G0_json_real",
    "closed_loop_no_retry": "G0_json_real_with_o_no_retry",
    "closed_loop_retry": "G0_json_real_with_o",
}


def encode_cmd(op: str, device: Optional[int] = None, val: Optional[int] = None, ms: Optional[int] = None) -> bytes:
    obj: Dict[str, int | str] = {"op": op}
    if device is not None:
        obj["dev"] = int(device)
    if val is not None:
        obj["val"] = int(val)
    if ms is not None:
        obj["ms"] = int(ms)
    return json.dumps(obj, separators=(",", ":")).encode("utf-8")


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


def decode_zigzag64(n: int) -> int:
    return (n >> 1) ^ (-(n & 1))


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
    if v1 is None or v2 is None:
        return out
    if flag == 0x01:
        out["result"] = decode_zigzag64(v1)
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


def mean_std(values: List[float]) -> Tuple[float, float]:
    if not values:
        return 0.0, 0.0
    m = statistics.fmean(values)
    s = statistics.pstdev(values) if len(values) > 1 else 0.0
    return m, s


def wilson_ci(k: int, n: int, z: float = 1.959963984540054) -> Tuple[float, float]:
    if n <= 0:
        return 0.0, 0.0
    phat = k / n
    den = 1.0 + (z * z) / n
    center = (phat + (z * z) / (2.0 * n)) / den
    half = (z / den) * math.sqrt((phat * (1.0 - phat) / n) + (z * z) / (4.0 * n * n))
    return max(0.0, center - half), min(1.0, center + half)


def two_prop_pvalue(k1: int, n1: int, k2: int, n2: int) -> Tuple[float, float]:
    if n1 <= 0 or n2 <= 0:
        return 0.0, 1.0
    p1 = k1 / n1
    p2 = k2 / n2
    p_pool = (k1 + k2) / (n1 + n2)
    se = math.sqrt(max(p_pool * (1.0 - p_pool) * (1.0 / n1 + 1.0 / n2), 0.0))
    if se == 0.0:
        return 0.0, 1.0
    z = (p1 - p2) / se
    p = math.erfc(abs(z) / math.sqrt(2.0))
    return z, p


def fmt_p(p: float) -> str:
    if p < 1e-4:
        return "<1e-4"
    return f"{p:.4f}"


def load_g3_baseline(path: str) -> Optional[Tuple[int, int, float]]:
    if not os.path.exists(path):
        return None
    with open(path, "r", encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))
    for row in rows:
        if row.get("group", "") == "G3_m_with_o":
            n = int(row.get("n", "0") or 0)
            k = int(row.get("converged", "0") or 0)
            scr = float(row.get("scr", "0") or 0.0)
            return n, k, scr
    return None


def append_run_info(path: str, *, args, tag: str, trials_path: str, summary_path: str, judgement_path: str) -> None:
    lines: List[str] = []
    lines.append("")
    lines.append("## E4+ JSON Real Run")
    lines.append(f"- Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append(f"- Serial Port: {args.serial}")
    lines.append(f"- Variant: {args.variant}")
    lines.append(f"- Mode: {args.mode}")
    lines.append(f"- Repeat: {args.repeat}")
    lines.append(f"- Device: {args.device}")
    lines.append(f"- Settle ms: {args.settle_ms}")
    lines.append(f"- Disturbance probability: {args.disturb_prob}")
    lines.append(f"- Max retry: {args.max_retry}")
    lines.append(f"- Seed: {args.seed}")
    lines.append(f"- Tag: {tag}")
    lines.append("- Output Files:")
    lines.append(f"  - {trials_path}")
    lines.append(f"  - {summary_path}")
    lines.append(f"  - {judgement_path}")
    with open(path, "a", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(lines) + "\n")


def write_judgement(
    path: str,
    *,
    args,
    group_name: str,
    attempts_mean: float,
    n: int,
    k: int,
    scr: float,
    ci_lo: float,
    ci_hi: float,
    rtt_mean: float,
    rtt_std: float,
    disturbed_rate: float,
    g3: Optional[Tuple[int, int, float]],
) -> None:
    lines: List[str] = []
    lines.append("# E4+ JSON Real Baseline Judgement")
    lines.append("")
    lines.append("## Run")
    lines.append(f"- Serial Port: {args.serial}")
    lines.append(f"- Variant: {args.variant}")
    lines.append(f"- Mode: {args.mode}")
    lines.append(f"- Repeat: {args.repeat}")
    lines.append(f"- Device: {args.device}")
    lines.append(f"- Settle ms: {args.settle_ms}")
    lines.append(f"- Disturbance probability: {args.disturb_prob}")
    lines.append(f"- Max retry: {args.max_retry}")
    lines.append(f"- Seed: {args.seed}")
    lines.append("")
    lines.append(f"## {group_name}")
    lines.append(f"- Converged: {k}/{n}")
    lines.append(f"- SCR: {scr:.6f} (95% CI [{ci_lo:.6f}, {ci_hi:.6f}])")
    lines.append(f"- RTT mean±std (ms): {rtt_mean:.3f} ± {rtt_std:.3f}")
    lines.append(f"- Attempts mean: {attempts_mean:.3f}")
    lines.append(f"- Disturbed rate: {disturbed_rate:.6f}")
    if g3 is not None:
        n3, k3, scr3 = g3
        z, p = two_prop_pvalue(k, n, k3, n3)
        lines.append("")
        lines.append("## Compare To G3_m_with_o")
        lines.append(f"- G3 converged: {k3}/{n3} (SCR={scr3:.6f})")
        lines.append(f"- Delta SCR ({group_name} - G3): {scr - scr3:.6f}")
        lines.append(f"- Two-proportion z: {z:.4f}, p={fmt_p(p)}")
    else:
        lines.append("")
        lines.append("## Compare To G3_m_with_o")
        lines.append("- Baseline file missing; statistical comparison skipped.")
    lines.append("")
    if args.mode == "closed_loop_retry":
        lines.append(
            "- Note: this run is the application-layer JSON readback+retry baseline for testing whether M's gain comes from built-in execution-plane semantics or from a generic while-loop."
        )
    elif args.mode == "closed_loop_no_retry":
        lines.append("- Note: this run enables readback+compare on the JSON path but disables retry.")
    else:
        lines.append(
            "- Note: G0 is a real MCU-side JSON/text parsing execution path; it replaces the proxy-only baseline for external validity."
        )
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(lines) + "\n")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--serial", required=True, help="COM port, e.g., COM5")
    parser.add_argument("--timeout", type=float, default=1.0)
    parser.add_argument("--repeat", type=int, default=100)
    parser.add_argument("--device", type=int, default=5)
    parser.add_argument("--settle-ms", type=int, default=10)
    parser.add_argument("--disturb-prob", type=float, default=0.30)
    parser.add_argument(
        "--mode",
        default="open_loop",
        choices=["open_loop", "closed_loop_no_retry", "closed_loop_retry"],
        help="JSON baseline execution mode",
    )
    parser.add_argument("--max-retry", type=int, default=3, help="max attempts for closed_loop_retry")
    parser.add_argument("--seed", type=int, default=20260218)
    parser.add_argument("--variant", default="json_real")
    parser.add_argument("--baseline-e4-summary", default="论文分区/ccfc/result/E4/e4_summary.csv")
    parser.add_argument("--out-dir", default="论文分区/ccfc/result/E4_json_real")
    parser.add_argument("--tag", default="", help="run tag; default timestamp")
    parser.add_argument("--write-latest", action="store_true")
    args = parser.parse_args()

    if serial is None:
        raise SystemExit("pyserial not installed")
    if args.repeat <= 0:
        raise SystemExit("--repeat must be > 0")
    if not (0.0 <= args.disturb_prob <= 1.0):
        raise SystemExit("--disturb-prob must be in [0,1]")
    if args.max_retry <= 0:
        raise SystemExit("--max-retry must be > 0")

    os.makedirs(args.out_dir, exist_ok=True)
    raw_dir = os.path.join(args.out_dir, "raw")
    os.makedirs(raw_dir, exist_ok=True)
    tag = args.tag or datetime.now().strftime("%Y%m%d_%H%M%S")
    rng = random.Random(args.seed)

    group_name = MODE_TO_GROUP[args.mode]
    closed_loop = args.mode != "open_loop"
    max_attempts = args.max_retry if args.mode == "closed_loop_retry" else 1

    trials: List[Dict[str, str]] = []
    totals: List[float] = []
    converged_k = 0
    disturbed_k = 0
    set_fault_k = 0
    probe_fault_k = 0
    attempts_used_total = 0.0

    with serial.Serial(args.serial, 115200, timeout=args.timeout) as ser:
        for trial in range(1, args.repeat + 1):
            target = trial % 2
            disturbed = rng.random() < args.disturb_prob
            if disturbed:
                disturbed_k += 1

            converged = 0
            attempts_used = 0
            total_rtt = 0.0

            set_status = ""
            set_fault = ""
            set_rtt: Optional[float] = None
            disturb_status = ""
            disturb_fault = ""
            disturb_rtt: Optional[float] = None
            probe_status = ""
            probe_fault = ""
            probe_result = ""
            probe_rtt: Optional[float] = None

            for attempt in range(1, max_attempts + 1):
                attempts_used = attempt

                set_status, set_pd, set_rtt = transact(
                    ser,
                    encode_cmd("set", device=args.device, val=target),
                    args.timeout,
                )
                set_fault = ""
                set_ok = False
                if set_status == "ok" and set_pd is not None:
                    set_ok = int(set_pd["ok"] or 0) == 1
                    if not set_ok:
                        set_fault = "" if set_pd["fault"] is None else str(set_pd["fault"])
                        set_fault_k += 1
                if set_rtt is not None:
                    total_rtt += set_rtt

                wait_status = ""
                wait_fault = ""
                wait_rtt: Optional[float] = None
                wait_ok = True
                if set_ok and args.settle_ms > 0:
                    wait_status, wait_pd, wait_rtt = transact(
                        ser,
                        encode_cmd("wait", ms=args.settle_ms),
                        args.timeout,
                    )
                    if wait_status == "ok" and wait_pd is not None:
                        wait_ok = int(wait_pd["ok"] or 0) == 1
                        if not wait_ok:
                            wait_fault = "" if wait_pd["fault"] is None else str(wait_pd["fault"])
                    else:
                        wait_ok = False
                    if wait_rtt is not None:
                        total_rtt += wait_rtt
                else:
                    wait_ok = set_ok

                disturb_status = ""
                disturb_fault = ""
                disturb_rtt = None
                disturb_ok = True
                if disturbed and attempt == 1:
                    disturb_status, disturb_pd, disturb_rtt = transact(
                        ser,
                        encode_cmd("set", device=args.device, val=(1 - target)),
                        args.timeout,
                    )
                    if disturb_status == "ok" and disturb_pd is not None:
                        disturb_ok = int(disturb_pd["ok"] or 0) == 1
                        if not disturb_ok:
                            disturb_fault = "" if disturb_pd["fault"] is None else str(disturb_pd["fault"])
                    else:
                        disturb_ok = False
                    if disturb_rtt is not None:
                        total_rtt += disturb_rtt

                probe_status, probe_pd, probe_rtt = transact(
                    ser,
                    encode_cmd("get", device=args.device),
                    args.timeout,
                )
                probe_ok = False
                probe_result = ""
                probe_fault = ""
                if probe_status == "ok" and probe_pd is not None:
                    probe_ok = int(probe_pd["ok"] or 0) == 1 and probe_pd["result"] is not None
                    if probe_ok:
                        probe_result = str(int(probe_pd["result"] or 0))
                    else:
                        probe_fault = "" if probe_pd["fault"] is None else str(probe_pd["fault"])
                        probe_fault_k += 1
                else:
                    probe_fault_k += 1
                if probe_rtt is not None:
                    total_rtt += probe_rtt

                converged = int(set_ok and wait_ok and disturb_ok and probe_ok and probe_result == str(target))
                if converged or not closed_loop:
                    break

            converged_k += converged
            attempts_used_total += attempts_used
            totals.append(total_rtt)

            trials.append(
                {
                    "trial": str(trial),
                    "group": group_name,
                    "variant": args.variant,
                    "mode": args.mode,
                    "target": str(target),
                    "disturbed": "1" if disturbed else "0",
                    "closed_loop": "1" if closed_loop else "0",
                    "max_retry": str(max_attempts),
                    "attempts_used": str(attempts_used),
                    "set_status": set_status,
                    "set_fault": set_fault,
                    "set_rtt_ms": "" if set_rtt is None else f"{set_rtt:.3f}",
                    "wait_status": wait_status,
                    "wait_fault": wait_fault,
                    "wait_rtt_ms": "" if wait_rtt is None else f"{wait_rtt:.3f}",
                    "disturb_status": disturb_status,
                    "disturb_fault": disturb_fault,
                    "disturb_rtt_ms": "" if disturb_rtt is None else f"{disturb_rtt:.3f}",
                    "probe_status": probe_status,
                    "probe_fault": probe_fault,
                    "probe_result": probe_result,
                    "probe_rtt_ms": "" if probe_rtt is None else f"{probe_rtt:.3f}",
                    "converged": str(converged),
                    "total_rtt_ms": f"{total_rtt:.3f}",
                }
            )

    n = args.repeat
    scr = converged_k / n if n else 0.0
    ci_lo, ci_hi = wilson_ci(converged_k, n)
    rtt_mean, rtt_std = mean_std(totals)
    disturbed_rate = disturbed_k / n if n else 0.0
    set_fault_rate = set_fault_k / n if n else 0.0
    probe_fault_rate = probe_fault_k / n if n else 0.0
    attempts_mean = attempts_used_total / n if n else 0.0

    summary = [
        {
            "group": group_name,
            "variant": args.variant,
            "mode": args.mode,
            "n": str(n),
            "converged": str(converged_k),
            "scr": f"{scr:.6f}",
            "ci_lo": f"{ci_lo:.6f}",
            "ci_hi": f"{ci_hi:.6f}",
            "rtt_ms_mean": f"{rtt_mean:.3f}",
            "rtt_ms_std": f"{rtt_std:.3f}",
            "attempts_mean": f"{attempts_mean:.3f}",
            "disturbed_rate": f"{disturbed_rate:.6f}",
            "set_fault_rate": f"{set_fault_rate:.6f}",
            "probe_fault_rate": f"{probe_fault_rate:.6f}",
        }
    ]

    trials_path = os.path.join(raw_dir, f"e4_json_real_trials_{args.variant}_{tag}.csv")
    summary_path = os.path.join(args.out_dir, f"e4_json_real_summary_{args.variant}_{tag}.csv")
    judgement_path = os.path.join(args.out_dir, f"e4_json_real_judgement_{args.variant}_{tag}.md")

    with open(trials_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "trial",
                "group",
                "variant",
                "mode",
                "target",
                "disturbed",
                "closed_loop",
                "max_retry",
                "attempts_used",
                "set_status",
                "set_fault",
                "set_rtt_ms",
                "wait_status",
                "wait_fault",
                "wait_rtt_ms",
                "disturb_status",
                "disturb_fault",
                "disturb_rtt_ms",
                "probe_status",
                "probe_fault",
                "probe_result",
                "probe_rtt_ms",
                "converged",
                "total_rtt_ms",
            ],
        )
        writer.writeheader()
        writer.writerows(trials)

    with open(summary_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "group",
                "variant",
                "mode",
                "n",
                "converged",
                "scr",
                "ci_lo",
                "ci_hi",
                "rtt_ms_mean",
                "rtt_ms_std",
                "attempts_mean",
                "disturbed_rate",
                "set_fault_rate",
                "probe_fault_rate",
            ],
        )
        writer.writeheader()
        writer.writerows(summary)

    g3 = load_g3_baseline(args.baseline_e4_summary)
    write_judgement(
        judgement_path,
        args=args,
        group_name=group_name,
        attempts_mean=attempts_mean,
        n=n,
        k=converged_k,
        scr=scr,
        ci_lo=ci_lo,
        ci_hi=ci_hi,
        rtt_mean=rtt_mean,
        rtt_std=rtt_std,
        disturbed_rate=disturbed_rate,
        g3=g3,
    )

    if args.write_latest:
        latest_trials = os.path.join(args.out_dir, "e4_json_real_trials.csv")
        latest_summary = os.path.join(args.out_dir, "e4_json_real_summary.csv")
        latest_judgement = os.path.join(args.out_dir, "e4_json_real_judgement.md")
        with open(latest_trials, "w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=list(trials[0].keys()))
            writer.writeheader()
            writer.writerows(trials)
        with open(latest_summary, "w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=list(summary[0].keys()))
            writer.writeheader()
            writer.writerows(summary)
        with open(latest_judgement, "w", encoding="utf-8", newline="\n") as f:
            f.write(open(judgement_path, "r", encoding="utf-8").read())
        print(f"Wrote latest aliases: {latest_trials}, {latest_summary}, {latest_judgement}")

    run_info_path = os.path.join(args.out_dir, "run_info.md")
    if not os.path.exists(run_info_path):
        with open(run_info_path, "w", encoding="utf-8", newline="\n") as f:
            f.write("# E4+ JSON Real Run Info\n")
    append_run_info(
        run_info_path,
        args=args,
        tag=tag,
        trials_path=trials_path,
        summary_path=summary_path,
        judgement_path=judgement_path,
    )

    print(f"Wrote: {trials_path}")
    print(f"Wrote: {summary_path}")
    print(f"Wrote: {judgement_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
