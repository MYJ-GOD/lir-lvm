#!/usr/bin/env python3
"""
E2+ orthogonal ablation harness.

This script is a non-destructive fork of tools/bench_e2.py for CCFC E2+
single-mechanism experiments (A0~A5). It keeps the same malformed case set
and serial protocol, but extends --variant naming and always writes
variant-specific latest CSV files when --write-latest is enabled.
"""
import argparse
import csv
import os
import sys
import time
from datetime import datetime
from typing import List, Dict, Optional, Tuple

try:
    import serial  # type: ignore
except ImportError:
    serial = None

# Opcodes
M_IOW = 70
M_IOR = 71
M_HALT = 82
M_LIT = 30
M_CL = 17
M_FN = 15
M_B = 10
M_E = 11
M_JMP = 100
M_LET = 32


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


def encode_svarint(n: int) -> bytes:
    zz = (n << 1) ^ (n >> 31)
    return encode_uvarint(zz & 0xFFFFFFFF)


def encode_zigzag64(n: int) -> int:
    return ((n << 1) ^ (n >> 63)) & 0xFFFFFFFFFFFFFFFF


def lit(v: int) -> bytes:
    return op(M_LIT) + encode_uvarint(encode_zigzag64(v))


def case_invalid_opcode() -> bytes:
    # 255 is outside the implemented subset and should trigger UNKNOWN_OP.
    return op(255)


def case_bad_varint() -> bytes:
    # opcode LIT (30) then an unterminated varint (0x80) -> decode fail
    return op(M_LIT) + bytes([0x80])


def case_stack_overflow() -> bytes:
    # Define recurse() { recurse(); } then call recurse()
    buf = bytearray()
    fn_addr = len(buf)
    buf += op(M_FN) + encode_uvarint(0)  # arity 0
    buf += op(M_B)
    buf += op(M_CL) + encode_uvarint(fn_addr) + encode_uvarint(0)  # call self
    buf += op(M_E)
    buf += op(M_CL) + encode_uvarint(fn_addr) + encode_uvarint(0)  # main call
    buf += op(M_HALT)
    return bytes(buf)


def case_locals_oob() -> bytes:
    # LIT 1; LET 500 -> LOCALS_OOB
    return lit(1) + op(M_LET) + encode_uvarint(500) + op(M_HALT)


def case_unauthorized_iow() -> bytes:
    # LIT 1; IOW dev 250; HALT (no GTWAY for dev250 -> UNAUTHORIZED)
    return lit(1) + op(M_IOW) + encode_uvarint(250) + op(M_HALT)


def case_step_limit() -> bytes:
    # Tight self-loop for token-relative jump semantics:
    # JMP -1 means "from next opcode index back to current JMP opcode".
    return op(M_JMP) + encode_svarint(-1)


def case_call_depth() -> bytes:
    # Deeply nested calls: recurse depth via explicit repeats
    buf = bytearray()
    fn_addr = len(buf)
    buf += op(M_FN) + encode_uvarint(0) + op(M_B)
    # call itself twice to accelerate depth
    for _ in range(40):
        buf += op(M_CL) + encode_uvarint(fn_addr) + encode_uvarint(0)
    buf += op(M_E)
    buf += op(M_CL) + encode_uvarint(fn_addr) + encode_uvarint(0)
    buf += op(M_HALT)
    return bytes(buf)


CASES_BASE = {
    "F1_invalid_opcode": case_invalid_opcode,
    "F2_bad_varint": case_bad_varint,
    "F3_stack_overflow": case_stack_overflow,
    "F4_locals_oob": case_locals_oob,
    "F5_unauthorized_iow": case_unauthorized_iow,
}

CASES_EXT = {
    "F6_step_limit": case_step_limit,
    "F7_call_depth": case_call_depth,
}


def ensure_dirs(out_dir: str):
    os.makedirs(os.path.join(out_dir, "e2_cases"), exist_ok=True)
    os.makedirs(out_dir, exist_ok=True)


def save_cases(out_dir: str, selected=None, include_ext=False) -> List[Dict]:
    rows = []
    cases = dict(CASES_BASE)
    if include_ext:
        cases.update(CASES_EXT)
    for name, fn in cases.items():
        if selected and name not in selected:
            continue
        data = fn()
        path = os.path.join(out_dir, "e2_cases", f"{name}.bin")
        with open(path, "wb") as f:
            f.write(data)
        # runtime stats populated after serial run
        rows.append(
            {
                "case": name,
                "bytes": len(data),
                "payload_hex": data.hex(),
                "response": "",
                "rtt_ms_mean": "",
                "rtt_ms_std": "",
                "ok_count": "",
                "fault_count": "",
                "main_fault": "",
            }
        )
    return rows


def measure_serial_fw(port: str, payload: bytes, timeout: float) -> Optional[Tuple[str, float]]:
    """
    Firmware protocol: send [4-byte LE len][payload], expect [4-byte LE len][resp_payload].
    resp_payload last byte 0x01=OK, 0x00=FAULT. Script just records hex string and RTT.
    """
    if serial is None:
        return None
    ser = serial.Serial(port, 115200, timeout=timeout)
    try:
        frame = len(payload).to_bytes(4, "little") + payload
        start = time.perf_counter()
        ser.write(frame)
        ser.flush()
        len_bytes = ser.read(4)
        if len(len_bytes) < 4:
            return None
        resp_len = int.from_bytes(len_bytes, "little")
        resp = ser.read(resp_len)
        end = time.perf_counter()
        if len(resp) < resp_len:
            return None
        return resp.hex(), (end - start) * 1000.0
    finally:
        ser.close()


def measure_serial_line(port: str, payload: bytes, timeout: float) -> Optional[Tuple[str, float]]:
    if serial is None:
        return None
    ser = serial.Serial(port, 115200, timeout=timeout)
    try:
        start = time.perf_counter()
        ser.write(payload)
        ser.flush()
        line = ser.readline().decode(errors="ignore").strip()
        end = time.perf_counter()
        return line, (end - start) * 1000.0
    finally:
        ser.close()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--serial", help="COM port, e.g., COM3 or /dev/ttyUSB0")
    parser.add_argument("--timeout", type=float, default=1.0)
    parser.add_argument(
        "--timeout-step",
        type=float,
        default=0.0,
        help="override timeout seconds for F6_step_limit case; 0 means use --timeout",
    )
    parser.add_argument("--repeat", type=int, default=1)
    parser.add_argument("--fw-proto", action="store_true", help="use firmware length-prefixed protocol")
    parser.add_argument("--all-cases", action="store_true", help="include extended cases F6/F7")
    parser.add_argument("--cases", help="comma-separated case names to run (default all in set)")
    parser.add_argument(
        "--variant",
        default="current",
        choices=[
            "guarded",
            "noguard",
            "no_validator",
            "ablation_guarded",
            "ablation_no_validator",
            "a0_base_guarded",
            "a1_no_auth_only",
            "a2_no_load_validator_only",
            "a3_no_step_limit_only",
            "a4_no_call_depth_only",
            "a5_no_bad_encoding_fault_only",
            "current",
        ],
        help="output file variant label",
    )
    parser.add_argument("--out-dir", default="results", help="directory to write outputs")
    parser.add_argument("--tag", default="", help="run tag; default uses timestamp")
    parser.add_argument(
        "--write-latest",
        action="store_true",
        help="also update latest file names (e2.csv and e2_<variant>.csv)",
    )
    args = parser.parse_args()

    ensure_dirs(args.out_dir)
    tag = args.tag or datetime.now().strftime("%Y%m%d_%H%M%S")
    selected = None
    if args.cases:
        selected = [c.strip() for c in args.cases.split(",") if c.strip()]
    rows = save_cases(args.out_dir, selected=selected, include_ext=args.all_cases)
    samples = []  # per-iteration records

    if args.serial:
        for row in rows:
            rtts = []
            oks = 0
            fault_counts = {}
            last_resp = ""
            for i in range(1, args.repeat + 1):
                try:
                    timeout = args.timeout
                    if row["case"] == "F6_step_limit" and args.timeout_step > 0:
                        timeout = args.timeout_step
                    if args.fw_proto:
                        res = measure_serial_fw(args.serial, bytes.fromhex(row["payload_hex"]), timeout)
                    else:
                        res = measure_serial_line(args.serial, bytes.fromhex(row["payload_hex"]), timeout)
                except Exception:
                    res = None
                if res:
                    resp, rtt = res
                    last_resp = resp
                    rtts.append(rtt)
                    samples.append(
                        {
                            "case": row["case"],
                            "iter": i,
                            "response": resp,
                            "rtt_ms": f"{rtt:.3f}",
                        }
                    )
                    # parse flag for fw_proto
                    if args.fw_proto and resp:
                        try:
                            b = bytes.fromhex(resp)
                            flag = b[-1]
                            if flag == 0x01:
                                oks += 1
                            else:
                                # fault code is first varint
                                fc = 0
                                shift = 0
                                idx = 0
                                while idx < len(b)-1:
                                    v = b[idx]
                                    idx += 1
                                    fc |= (v & 0x7F) << shift
                                    if v & 0x80 == 0:
                                        break
                                    shift += 7
                                fault_counts[fc] = fault_counts.get(fc, 0) + 1
                        except Exception:
                            pass
                else:
                    fault_counts["timeout"] = fault_counts.get("timeout", 0) + 1
                    samples.append(
                        {
                            "case": row["case"],
                            "iter": i,
                            "response": "",
                            "rtt_ms": "",
                        }
                    )
            if rtts:
                avg = sum(rtts)/len(rtts)
                var = sum((x-avg)**2 for x in rtts)/len(rtts)
                std = var**0.5
                row["response"] = last_resp
                row["rtt_ms_mean"] = f"{avg:.3f}"
                row["rtt_ms_std"] = f"{std:.3f}"
                row["ok_count"] = oks
                row["fault_count"] = args.repeat - oks
                if fault_counts:
                    # pick most common fault
                    fc_main = max(fault_counts.items(), key=lambda x: x[1])[0]
                    row["main_fault"] = fc_main
                else:
                    row["main_fault"] = ""
            elif fault_counts:
                row["response"] = ""
                row["rtt_ms_mean"] = ""
                row["rtt_ms_std"] = ""
                row["ok_count"] = oks
                row["fault_count"] = args.repeat - oks
                fc_main = max(fault_counts.items(), key=lambda x: x[1])[0]
                row["main_fault"] = fc_main

    out_csv = os.path.join(args.out_dir, f"e2_{args.variant}_{tag}.csv")
    with open(out_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "case",
                "bytes",
                "payload_hex",
                "response",
                "rtt_ms_mean",
                "rtt_ms_std",
                "ok_count",
                "fault_count",
                "main_fault",
            ],
        )
        writer.writeheader()
        writer.writerows(rows)

    out_samples = ""
    if samples:
        out_samples = os.path.join(args.out_dir, f"e2_samples_{args.variant}_{tag}.csv")
        with open(out_samples, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=["case", "iter", "response", "rtt_ms"])
            writer.writeheader()
            writer.writerows(samples)
        print(f"Samples written: {out_samples}")

    if args.write_latest:
        latest_common = os.path.join(args.out_dir, "e2.csv")
        with open(latest_common, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(
                f,
                fieldnames=[
                    "case",
                    "bytes",
                    "payload_hex",
                    "response",
                    "rtt_ms_mean",
                    "rtt_ms_std",
                    "ok_count",
                    "fault_count",
                    "main_fault",
                ],
            )
            writer.writeheader()
            writer.writerows(rows)
        print(f"Wrote legacy latest: {latest_common}")

        latest_variant = os.path.join(args.out_dir, f"e2_{args.variant}.csv")
        with open(latest_variant, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(
                f,
                fieldnames=[
                    "case",
                    "bytes",
                    "payload_hex",
                    "response",
                    "rtt_ms_mean",
                    "rtt_ms_std",
                    "ok_count",
                    "fault_count",
                    "main_fault",
                ],
            )
            writer.writeheader()
            writer.writerows(rows)
        print(f"Wrote legacy latest: {latest_variant}")

        if out_samples:
            latest_samples_variant = os.path.join(args.out_dir, f"e2_samples_{args.variant}.csv")
            with open(latest_samples_variant, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=["case", "iter", "response", "rtt_ms"])
                writer.writeheader()
                writer.writerows(samples)
            print(f"Wrote legacy samples: {latest_samples_variant}")

        if out_samples:
            latest_samples = os.path.join(args.out_dir, "e2_samples.csv")
            with open(latest_samples, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=["case", "iter", "response", "rtt_ms"])
                writer.writeheader()
                writer.writerows(samples)
            print(f"Wrote legacy samples: {latest_samples}")

    print(f"Generated {len(rows)} cases under {os.path.join(args.out_dir, 'e2_cases')}/")
    print(f"CSV written: {out_csv}")


if __name__ == "__main__":
    sys.exit(main())
