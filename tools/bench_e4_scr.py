#!/usr/bin/env python3
"""
E4 strict SCR (State Convergence Rate) benchmark.

Goal:
  Directly evaluate state grounding under set-readback-compare semantics.

Group definitions (single-board executable, text baseline via proxy):
  - G1_text_proxy:
      open-loop, one-shot, with configurable "parse noise" to simulate
      text-command ambiguity before encoding.
  - G2_m_no_o:
      open-loop, one-shot, deterministic M bytecode, no closed-loop retries.
  - G3_m_with_o:
      closed-loop retries (set -> optional disturbance -> readback -> compare),
      representing SGE observation/verification behavior.
  - G4_m_with_o_no_retry:
      readback+compare enabled but single-shot (no retry), used to
      separate observation effect from retry-policy effect.

Protocol (firmware/mvm_esp8266*.ino):
  send: [4-byte LE length][bytecode...]
  recv: [4-byte LE length][payload]
        OK    payload: [result varint][steps varint][0x01]
        FAULT payload: [fault varint][pc varint][0x00]

Outputs (under 论文分区/ccfc/result/E4 by default):
  raw/e4_attempts_<variant>_<tag>.csv
  raw/e4_trials_<variant>_<tag>.csv
  e4_summary_<variant>_<tag>.csv
  e4_judgement_<variant>_<tag>.md
  run_info.md (append mode)
Optional latest aliases (--write-latest):
  e4_attempts.csv
  e4_trials.csv
  e4_summary.csv
  e4_judgement.md
"""

from __future__ import annotations

import argparse
import csv
import os
import random
import statistics
import time
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Iterable, List, Optional, Tuple

try:
    import serial  # type: ignore
except ImportError:
    serial = None


M_LIT = 30
M_IOW = 70
M_IOR = 71
M_GTWAY = 80
M_WAIT = 81
M_HALT = 82


@dataclass(frozen=True)
class GroupConfig:
    name: str
    desc: str
    closed_loop: bool
    max_retry: int
    parse_noise_prob: float


GROUPS: Dict[str, GroupConfig] = {
    "G1_text_proxy": GroupConfig(
        name="G1_text_proxy",
        desc="Open-loop baseline with proxy text-parse ambiguity",
        closed_loop=False,
        max_retry=1,
        parse_noise_prob=0.0,  # runtime override
    ),
    "G2_m_no_o": GroupConfig(
        name="G2_m_no_o",
        desc="Open-loop M execution without closed-loop observation retries",
        closed_loop=False,
        max_retry=1,
        parse_noise_prob=0.0,
    ),
    "G3_m_with_o": GroupConfig(
        name="G3_m_with_o",
        desc="Closed-loop M execution with set-readback-compare retries",
        closed_loop=True,
        max_retry=3,  # runtime override
        parse_noise_prob=0.0,
    ),
    "G4_m_with_o_no_retry": GroupConfig(
        name="G4_m_with_o_no_retry",
        desc="Readback+compare enabled, single-shot (no retry)",
        closed_loop=True,
        max_retry=1,
        parse_noise_prob=0.0,
    ),
}


def ensure_dirs(out_dir: str) -> str:
    raw_dir = os.path.join(out_dir, "raw")
    os.makedirs(raw_dir, exist_ok=True)
    return raw_dir


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


def prog_set(device: int, target: int, settle_ms: int) -> bytes:
    # GTWAY dev; LIT target; IOW dev; WAIT settle_ms; HALT
    buf = bytearray()
    buf += op(M_GTWAY) + encode_uvarint(device)
    buf += m_lit(target)
    buf += op(M_IOW) + encode_uvarint(device)
    if settle_ms > 0:
        buf += op(M_WAIT) + encode_uvarint(settle_ms)
    buf += op(M_HALT)
    return bytes(buf)


def prog_probe(device: int) -> bytes:
    # GTWAY dev; IOR dev; HALT
    return op(M_GTWAY) + encode_uvarint(device) + op(M_IOR) + encode_uvarint(device) + op(M_HALT)


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
    """
    Return keys:
      flag, ok, result, steps, fault, pc
    """
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


def transact(ser, payload: bytes, timeout: float) -> Tuple[str, Optional[bytes], Optional[float]]:
    """
    Returns:
      status: ok|timeout|io_error
      resp_payload_bytes
      rtt_ms
    """
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
        return "ok", resp, (t1 - t0) * 1000.0
    except Exception:
        return "io_error", None, None


def mean_std(values: Iterable[float]) -> Tuple[float, float]:
    vals = [v for v in values]
    if not vals:
        return 0.0, 0.0
    m = statistics.fmean(vals)
    s = statistics.pstdev(vals) if len(vals) > 1 else 0.0
    return m, s


def run_group(
    ser,
    cfg: GroupConfig,
    repeat: int,
    device: int,
    settle_ms: int,
    disturb_prob: float,
    g1_noise_prob: float,
    g3_max_retry: int,
    timeout: float,
    seed: int,
    variant: str,
) -> Tuple[List[Dict[str, str]], List[Dict[str, str]]]:
    attempts_rows: List[Dict[str, str]] = []
    trials_rows: List[Dict[str, str]] = []

    max_retry = g3_max_retry if cfg.name == "G3_m_with_o" else cfg.max_retry
    parse_noise_prob = g1_noise_prob if cfg.name == "G1_text_proxy" else cfg.parse_noise_prob

    for i in range(1, repeat + 1):
        # Use per-iteration deterministic RNG so all groups share identical
        # disturbance schedule, improving ablation fairness.
        rng = random.Random(seed * 1000003 + i * 97)
        target = 1 if (i % 2 == 1) else 0
        parse_noise = rng.random() < parse_noise_prob
        issued_target = (1 - target) if parse_noise else target
        disturbed = rng.random() < disturb_prob

        converged = 0
        attempts_used = 0
        trial_rtt_total = 0.0

        last_set_ok = ""
        last_set_fault = ""
        last_set_rtt = ""
        last_disturb_ok = ""
        last_disturb_fault = ""
        last_disturb_rtt = ""
        last_probe_ok = ""
        last_probe_fault = ""
        last_probe_val = ""
        last_probe_rtt = ""

        for attempt in range(1, max_retry + 1):
            attempts_used = attempt

            set_payload = prog_set(device=device, target=issued_target, settle_ms=settle_ms)

            st_s, resp_s, rtt_s = transact(ser, set_payload, timeout=timeout)
            ps = parse_response(resp_s or b"")
            set_ok = int(ps["ok"]) if ps["ok"] is not None else 0
            set_fault = int(ps["fault"]) if ps["fault"] is not None else -1

            if rtt_s is not None:
                trial_rtt_total += rtt_s
            last_set_ok = str(set_ok)
            last_set_fault = "" if set_fault < 0 else str(set_fault)
            last_set_rtt = "" if rtt_s is None else f"{rtt_s:.3f}"

            disturb_ok = ""
            disturb_fault = ""
            disturb_rtt = ""

            # Disturbance is injected once per trial (before first probe/decision).
            if disturbed and attempt == 1:
                disturb_payload = prog_set(device=device, target=(1 - target), settle_ms=0)
                st_d, resp_d, rtt_d = transact(ser, disturb_payload, timeout=timeout)
                pd = parse_response(resp_d or b"")
                disturb_ok_v = int(pd["ok"]) if pd["ok"] is not None else 0
                disturb_fault_v = int(pd["fault"]) if pd["fault"] is not None else -1
                disturb_ok = str(disturb_ok_v)
                disturb_fault = "" if disturb_fault_v < 0 else str(disturb_fault_v)
                disturb_rtt = "" if rtt_d is None else f"{rtt_d:.3f}"
                if rtt_d is not None:
                    trial_rtt_total += rtt_d

            probe_ok = 0
            probe_fault = -1
            probe_value = -1
            rtt_p = None

            probe_payload = prog_probe(device=device)
            st_p, resp_p, rtt_p = transact(ser, probe_payload, timeout=timeout)
            pp = parse_response(resp_p or b"")
            probe_ok = int(pp["ok"]) if pp["ok"] is not None else 0
            probe_fault = int(pp["fault"]) if pp["fault"] is not None else -1
            probe_value = int(pp["result"]) if pp["result"] is not None else -1
            if rtt_p is not None:
                trial_rtt_total += rtt_p

            if probe_ok == 1 and probe_value == target:
                converged = 1

            last_disturb_ok = disturb_ok
            last_disturb_fault = disturb_fault
            last_disturb_rtt = disturb_rtt
            last_probe_ok = str(probe_ok)
            last_probe_fault = "" if probe_fault < 0 else str(probe_fault)
            last_probe_val = "" if probe_value < 0 else str(probe_value)
            last_probe_rtt = "" if rtt_p is None else f"{rtt_p:.3f}"

            attempts_rows.append(
                {
                    "iter": str(i),
                    "attempt": str(attempt),
                    "group": cfg.name,
                    "variant": variant,
                    "target": str(target),
                    "issued_target": str(issued_target),
                    "parse_noise": "1" if parse_noise else "0",
                    "disturbed": "1" if disturbed else "0",
                    "set_ok": str(set_ok),
                    "set_fault": "" if set_fault < 0 else str(set_fault),
                    "set_rtt_ms": "" if rtt_s is None else f"{rtt_s:.3f}",
                    "disturb_ok": disturb_ok,
                    "disturb_fault": disturb_fault,
                    "disturb_rtt_ms": disturb_rtt,
                    "probe_ok": str(probe_ok),
                    "probe_fault": "" if probe_fault < 0 else str(probe_fault),
                    "probe_value": "" if probe_value < 0 else str(probe_value),
                    "probe_rtt_ms": "" if rtt_p is None else f"{rtt_p:.3f}",
                    "converged_after_attempt": "1" if converged else "0",
                }
            )

            if converged or not cfg.closed_loop:
                break

        trials_rows.append(
            {
                "iter": str(i),
                "group": cfg.name,
                "variant": variant,
                "target": str(target),
                "issued_target": str(issued_target),
                "parse_noise": "1" if parse_noise else "0",
                "disturbed": "1" if disturbed else "0",
                "closed_loop": "1" if cfg.closed_loop else "0",
                "max_retry": str(max_retry),
                "attempts_used": str(attempts_used),
                "set_ok_last": last_set_ok,
                "set_fault_last": last_set_fault,
                "set_rtt_ms_last": last_set_rtt,
                "disturb_ok_last": last_disturb_ok,
                "disturb_fault_last": last_disturb_fault,
                "disturb_rtt_ms_last": last_disturb_rtt,
                "probe_ok_last": last_probe_ok,
                "probe_fault_last": last_probe_fault,
                "probe_value_last": last_probe_val,
                "probe_rtt_ms_last": last_probe_rtt,
                "converged": str(converged),
                "rtt_total_ms": f"{trial_rtt_total:.3f}",
            }
        )

    return attempts_rows, trials_rows


def summarize_trials(rows: List[Dict[str, str]]) -> List[Dict[str, str]]:
    by_group: Dict[str, List[Dict[str, str]]] = {}
    for r in rows:
        by_group.setdefault(r["group"], []).append(r)

    out: List[Dict[str, str]] = []
    for g in sorted(by_group.keys()):
        rs = by_group[g]
        n = len(rs)
        conv = sum(int(r["converged"]) for r in rs)
        scr = conv / n if n else 0.0

        rtts = [float(r["rtt_total_ms"]) for r in rs if r["rtt_total_ms"]]
        attempts = [float(r["attempts_used"]) for r in rs if r["attempts_used"]]
        disturbed_rate = sum(int(r["disturbed"]) for r in rs) / n if n else 0.0
        parse_noise_rate = sum(int(r["parse_noise"]) for r in rs) / n if n else 0.0
        set_fault_rate = (
            sum(1 for r in rs if r["set_ok_last"] != "1") / n if n else 0.0
        )
        probe_fault_rate = (
            sum(1 for r in rs if r["probe_ok_last"] != "1") / n if n else 0.0
        )

        rtt_m, rtt_s = mean_std(rtts)
        att_m, _ = mean_std(attempts)
        out.append(
            {
                "group": g,
                "n": str(n),
                "converged": str(conv),
                "scr": f"{scr:.6f}",
                "rtt_ms_mean": f"{rtt_m:.3f}",
                "rtt_ms_std": f"{rtt_s:.3f}",
                "attempts_mean": f"{att_m:.3f}",
                "disturbed_rate": f"{disturbed_rate:.6f}",
                "parse_noise_rate": f"{parse_noise_rate:.6f}",
                "set_fault_rate": f"{set_fault_rate:.6f}",
                "probe_fault_rate": f"{probe_fault_rate:.6f}",
            }
        )
    return out


def write_csv(path: str, rows: List[Dict[str, str]], fieldnames: List[str]) -> None:
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(rows)


def write_judgement(path: str, summary: List[Dict[str, str]], args) -> None:
    by = {r["group"]: r for r in summary}

    lines: List[str] = []
    lines.append("# E4 Strict SCR Judgement")
    lines.append("")
    lines.append(f"- Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append(f"- Variant: {args.variant}")
    lines.append(f"- Repeat per group: {args.repeat}")
    lines.append(f"- Disturbance probability: {args.disturb_prob}")
    lines.append(f"- G1 parse-noise probability: {args.g1_noise_prob}")
    lines.append(f"- G3 max retry: {args.g3_max_retry}")
    lines.append("")
    lines.append("| Group | n | converged | SCR | RTT mean(ms) | attempts_mean |")
    lines.append("|---|---:|---:|---:|---:|---:|")
    for g in ["G1_text_proxy", "G2_m_no_o", "G4_m_with_o_no_retry", "G3_m_with_o"]:
        if g not in by:
            continue
        r = by[g]
        lines.append(
            f"| {g} | {r['n']} | {r['converged']} | {r['scr']} | {r['rtt_ms_mean']} | {r['attempts_mean']} |"
        )

    lines.append("")
    if "G2_m_no_o" in by and "G4_m_with_o_no_retry" in by and "G3_m_with_o" in by:
        scr2 = float(by["G2_m_no_o"]["scr"])
        scr4 = float(by["G4_m_with_o_no_retry"]["scr"])
        scr3 = float(by["G3_m_with_o"]["scr"])
        d42 = scr4 - scr2
        d34 = scr3 - scr4
        d32 = scr3 - scr2
        lines.append(f"- Delta SCR (G4 - G2): {d42:.6f}")
        lines.append(f"- Delta SCR (G3 - G4): {d34:.6f}")
        lines.append(f"- Delta SCR (G3 - G2): {d32:.6f}")
        eps = 1e-12
        if abs(d42) <= eps and d34 > eps and d32 > eps:
            lines.append("- Verdict: PASS (readback-only shows no standalone SCR gain; improvement mainly comes from retry-enabled closed-loop).")
        elif d42 > eps and d34 >= 0 and d32 > 0:
            lines.append("- Verdict: PASS (both observation and retry show non-negative contribution; combined closed-loop best).")
        elif d42 >= -eps and d34 >= -eps and d32 > 0:
            lines.append("- Verdict: PASS (combined closed-loop improves; ablation contribution is weak/non-strict).")
        elif d32 > 0:
            lines.append("- Verdict: PARTIAL PASS (combined closed-loop improves, but ablation gaps need inspection).")
        else:
            lines.append("- Verdict: FAIL (combined closed-loop does not improve over open-loop M).")
    elif "G2_m_no_o" in by and "G3_m_with_o" in by:
        scr2 = float(by["G2_m_no_o"]["scr"])
        scr3 = float(by["G3_m_with_o"]["scr"])
        d32 = scr3 - scr2
        lines.append(f"- Delta SCR (G3 - G2): {d32:.6f}")
        if d32 > 0:
            lines.append("- Verdict: PASS (closed-loop improves strict SCR over open-loop M).")
        elif d32 == 0:
            lines.append("- Verdict: TIE (no observed SCR gain; inspect disturbance strength/retry settings).")
        else:
            lines.append("- Verdict: FAIL (closed-loop underperforms; inspect implementation and setup).")
    else:
        lines.append("- Verdict: INCOMPLETE (need at least G2 and G3; include G4 for ablation).")

    lines.append("")
    lines.append("## Notes")
    lines.append("- G1 is a proxy text baseline (parse-noise simulation), not a full JSON parser execution path.")
    lines.append("- Strict SCR uses physical readback comparison of relay target state.")

    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(lines) + "\n")


def append_run_info(path: str, args, tag: str, attempts_path: str, trials_path: str, summary_path: str, judgement_path: str) -> None:
    lines = []
    lines.append("")
    lines.append("## E4 Run")
    lines.append(f"- Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append(f"- Serial Port: {args.serial}")
    lines.append(f"- Variant: {args.variant}")
    lines.append(f"- Repeat per group: {args.repeat}")
    lines.append(f"- Groups: {args.groups}")
    lines.append(f"- Device: {args.device}")
    lines.append(f"- Settle ms: {args.settle_ms}")
    lines.append(f"- Disturbance probability: {args.disturb_prob}")
    lines.append(f"- G1 parse-noise probability: {args.g1_noise_prob}")
    lines.append(f"- G3 max retry: {args.g3_max_retry}")
    lines.append(f"- Seed: {args.seed}")
    lines.append(f"- Tag: {tag}")
    lines.append("- Output Files:")
    lines.append(f"  - {attempts_path}")
    lines.append(f"  - {trials_path}")
    lines.append(f"  - {summary_path}")
    lines.append(f"  - {judgement_path}")
    with open(path, "a", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(lines) + "\n")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--serial", required=True, help="COM port, e.g., COM5")
    parser.add_argument("--timeout", type=float, default=1.0)
    parser.add_argument("--repeat", type=int, default=50)
    parser.add_argument(
        "--groups",
        default="G1_text_proxy,G2_m_no_o,G4_m_with_o_no_retry,G3_m_with_o",
        help="comma-separated groups to run",
    )
    parser.add_argument("--device", type=int, default=5, help="relay device id (default 5)")
    parser.add_argument("--settle-ms", type=int, default=10, help="wait after set before probe")
    parser.add_argument("--disturb-prob", type=float, default=0.30, help="external disturbance probability per trial")
    parser.add_argument(
        "--g1-noise-prob",
        type=float,
        default=0.15,
        help="parse-noise probability for G1_text_proxy",
    )
    parser.add_argument("--g3-max-retry", type=int, default=3, help="max retries for G3 closed-loop")
    parser.add_argument("--seed", type=int, default=20260211)
    parser.add_argument(
        "--variant",
        default="guarded",
        choices=["guarded", "noguard", "current"],
        help="firmware/config label for output tagging",
    )
    parser.add_argument("--out-dir", default="论文分区/ccfc/result/E4", help="output directory")
    parser.add_argument("--tag", default="", help="run tag; default timestamp")
    parser.add_argument("--write-latest", action="store_true", help="also write non-tagged latest aliases")
    args = parser.parse_args()

    if serial is None:
        raise SystemExit("pyserial not installed")

    groups = [g.strip() for g in args.groups.split(",") if g.strip()]
    for g in groups:
        if g not in GROUPS:
            raise SystemExit(f"Unknown group: {g}")
    if args.repeat <= 0:
        raise SystemExit("--repeat must be > 0")
    if not (0.0 <= args.disturb_prob <= 1.0):
        raise SystemExit("--disturb-prob must be in [0,1]")
    if not (0.0 <= args.g1_noise_prob <= 1.0):
        raise SystemExit("--g1-noise-prob must be in [0,1]")
    if args.g3_max_retry <= 0:
        raise SystemExit("--g3-max-retry must be > 0")

    raw_dir = ensure_dirs(args.out_dir)
    tag = args.tag or datetime.now().strftime("%Y%m%d_%H%M%S")
    attempts_all: List[Dict[str, str]] = []
    trials_all: List[Dict[str, str]] = []

    with serial.Serial(args.serial, 115200, timeout=args.timeout) as ser:
        for g in groups:
            cfg = GROUPS[g]
            attempts, trials = run_group(
                ser=ser,
                cfg=cfg,
                repeat=args.repeat,
                device=args.device,
                settle_ms=args.settle_ms,
                disturb_prob=args.disturb_prob,
                g1_noise_prob=args.g1_noise_prob,
                g3_max_retry=args.g3_max_retry,
                timeout=args.timeout,
                seed=args.seed,
                variant=args.variant,
            )
            attempts_all.extend(attempts)
            trials_all.extend(trials)

    summary = summarize_trials(trials_all)

    attempts_path = os.path.join(raw_dir, f"e4_attempts_{args.variant}_{tag}.csv")
    trials_path = os.path.join(raw_dir, f"e4_trials_{args.variant}_{tag}.csv")
    summary_path = os.path.join(args.out_dir, f"e4_summary_{args.variant}_{tag}.csv")
    judgement_path = os.path.join(args.out_dir, f"e4_judgement_{args.variant}_{tag}.md")

    write_csv(
        attempts_path,
        attempts_all,
        fieldnames=[
            "iter",
            "attempt",
            "group",
            "variant",
            "target",
            "issued_target",
            "parse_noise",
            "disturbed",
            "set_ok",
            "set_fault",
            "set_rtt_ms",
            "disturb_ok",
            "disturb_fault",
            "disturb_rtt_ms",
            "probe_ok",
            "probe_fault",
            "probe_value",
            "probe_rtt_ms",
            "converged_after_attempt",
        ],
    )
    write_csv(
        trials_path,
        trials_all,
        fieldnames=[
            "iter",
            "group",
            "variant",
            "target",
            "issued_target",
            "parse_noise",
            "disturbed",
            "closed_loop",
            "max_retry",
            "attempts_used",
            "set_ok_last",
            "set_fault_last",
            "set_rtt_ms_last",
            "disturb_ok_last",
            "disturb_fault_last",
            "disturb_rtt_ms_last",
            "probe_ok_last",
            "probe_fault_last",
            "probe_value_last",
            "probe_rtt_ms_last",
            "converged",
            "rtt_total_ms",
        ],
    )
    write_csv(
        summary_path,
        summary,
        fieldnames=[
            "group",
            "n",
            "converged",
            "scr",
            "rtt_ms_mean",
            "rtt_ms_std",
            "attempts_mean",
            "disturbed_rate",
            "parse_noise_rate",
            "set_fault_rate",
            "probe_fault_rate",
        ],
    )
    write_judgement(judgement_path, summary, args)

    if args.write_latest:
        write_csv(os.path.join(args.out_dir, "e4_attempts.csv"), attempts_all, fieldnames=list(attempts_all[0].keys()))
        write_csv(os.path.join(args.out_dir, "e4_trials.csv"), trials_all, fieldnames=list(trials_all[0].keys()))
        write_csv(os.path.join(args.out_dir, "e4_summary.csv"), summary, fieldnames=list(summary[0].keys()))
        write_judgement(os.path.join(args.out_dir, "e4_judgement.md"), summary, args)

    run_info_path = os.path.join(args.out_dir, "run_info.md")
    if not os.path.exists(run_info_path):
        with open(run_info_path, "w", encoding="utf-8", newline="\n") as f:
            f.write("# E4 Run Info\n")
    append_run_info(run_info_path, args, tag, attempts_path, trials_path, summary_path, judgement_path)

    print(f"Wrote {attempts_path}")
    print(f"Wrote {trials_path}")
    print(f"Wrote {summary_path}")
    print(f"Wrote {judgement_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
