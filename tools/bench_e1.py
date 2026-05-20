#!/usr/bin/env python3
"""
E1: payload size and optional RTT benchmark for M bytecode vs JSON.
Default tasks cover relay on/off, sensor reads, and a small combo sequence.
If --serial <port> is provided, the script sends frames and measures round-trip time.
Results are saved to 论文分区/ccfc/result/e1.csv.
"""
import argparse
import csv
import os
import sys
import time
from datetime import datetime
from typing import List, Tuple, Optional

try:
    import serial  # type: ignore
except ImportError:
    serial = None

# M opcodes (varint-encoded)
M_IOW = 70
M_IOR = 71
M_WAIT = 81
M_HALT = 82
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


def encode_svarint(n: int) -> bytes:
    zz = (n << 1) ^ (n >> 31)
    return encode_uvarint(zz & 0xFFFFFFFF)


def encode_zigzag64(n: int) -> int:
    return ((n << 1) ^ (n >> 63)) & 0xFFFFFFFFFFFFFFFF


def msgpack_pack(obj) -> bytes:
    """
    Minimal MsgPack encoder for small ints/str/list/dict used in our tasks.
    Supports: int (fit in uint8/int8/int16), str (<=31 bytes), list/dict (len<=15).
    """
    out = bytearray()

    def pack(x):
        if isinstance(x, bool):
            out.append(0xc3 if x else 0xc2)
        elif isinstance(x, int):
            if -32 <= x <= 127:
                out.append(x & 0xFF)
            elif 0 <= x <= 0xFF:
                out.extend([0xcc, x])
            elif -32768 <= x <= 32767:
                out.extend([0xd1, (x >> 8) & 0xFF, x & 0xFF])
            else:
                # fall back to 32-bit signed
                out.extend([0xd2, (x >> 24) & 0xFF, (x >> 16) & 0xFF, (x >> 8) & 0xFF, x & 0xFF])
        elif isinstance(x, str):
            b = x.encode("utf-8")
            if len(b) > 31:
                raise ValueError("string too long for fixstr")
            out.append(0xa0 | len(b))
            out.extend(b)
        elif isinstance(x, list):
            if len(x) > 15:
                raise ValueError("list too long for fixarray")
            out.append(0x90 | len(x))
            for it in x:
                pack(it)
        elif isinstance(x, dict):
            if len(x) > 15:
                raise ValueError("dict too long for fixmap")
            out.append(0x80 | len(x))
            for k, v in x.items():
                if not isinstance(k, str):
                    raise ValueError("only string keys supported")
                pack(k)
                pack(v)
        else:
            raise TypeError(f"unsupported type {type(x)}")

    pack(obj)
    return bytes(out)


def op(opcode: int) -> bytes:
    return encode_uvarint(opcode)


def m_lit(v: int) -> bytes:
    return op(30) + encode_uvarint(encode_zigzag64(v))


def m_gtway(cap_id: int) -> bytes:
    return op(M_GTWAY) + encode_uvarint(cap_id)


def m_iow(dev: int, val: int) -> bytes:
    # m_vm.c semantics: IOW consumes value from stack, it is not an immediate operand.
    return m_lit(val) + op(M_IOW) + encode_uvarint(dev)


def m_ior(dev: int) -> bytes:
    return op(M_IOR) + encode_uvarint(dev)


def m_wait(ms: int) -> bytes:
    return op(M_WAIT) + encode_uvarint(ms)


def m_halt() -> bytes:
    return op(M_HALT)


def task_payloads() -> List[Tuple[str, bytes, str]]:
    """Return list of (task_name, m_bytes, json_str)."""
    tasks = []
    # T1 relay1 on (dev5)
    m = m_gtway(5) + m_iow(5, 1) + m_halt()
    j = {"dev": 5, "op": "set", "val": 1}
    tasks.append(("relay1_on", m, j))
    # T2 relay1 off (dev5)
    m = m_gtway(5) + m_iow(5, 0) + m_halt()
    j = {"dev": 5, "op": "set", "val": 0}
    tasks.append(("relay1_off", m, j))
    # T3 water level read
    m = m_gtway(1) + m_ior(1) + m_halt()
    j = {"dev": 1, "op": "get"}
    tasks.append(("water_read", m, j))
    # T4 temperature read
    m = m_gtway(2) + m_ior(2) + m_halt()
    j = {"dev": 2, "op": "get"}
    tasks.append(("temp_read", m, j))
    # T5 combo: relay1 on -> wait 500 -> water read -> halt
    m = m_gtway(5) + m_gtway(1) + m_iow(5, 1) + m_wait(500) + m_ior(1) + m_halt()
    j = [
        {"dev": 5, "op": "set", "val": 1},
        {"op": "wait", "ms": 500},
        {"dev": 1, "op": "get"},
    ]
    tasks.append(("combo_on_wait_read", m, j))
    return tasks


def to_json_line(obj) -> bytes:
    import json
    return (json.dumps(obj, separators=(",", ":")) + "\n").encode("utf-8")


def measure_serial(port: str, payload: bytes, is_json: bool, timeout: float) -> Optional[float]:
    if serial is None:
        return None
    ser = serial.Serial(port, 115200, timeout=timeout)
    try:
        start = time.perf_counter()
        ser.write(payload)
        ser.flush()
        ser.readline()  # wait for any line as ack
        end = time.perf_counter()
        return (end - start) * 1000.0
    finally:
        ser.close()


def measure_serial_fw(port: str, payload: bytes, timeout: float, expect_len: Optional[int] = None) -> Optional[float]:
    """
    Firmware protocol:
      send: [4-byte LE length][payload...]
      recv: [4-byte LE length][payload...], last byte = 0x01 ok else fault (M/E3) or single flag byte (MsgPack fw)
    """
    if serial is None:
        return None
    ser = serial.Serial(port, 115200, timeout=timeout)
    try:
        frame = len(payload).to_bytes(4, "little") + payload
        start = time.perf_counter()
        ser.write(frame)
        ser.flush()
        # read response length
        len_bytes = ser.read(4)
        if len(len_bytes) < 4:
            return None
        resp_len = int.from_bytes(len_bytes, "little")
        if expect_len is not None and resp_len != expect_len:
            return None
        resp = ser.read(resp_len)
        end = time.perf_counter()
        if len(resp) < resp_len:
            return None
        return (end - start) * 1000.0
    finally:
        ser.close()


def ensure_results_dir():
    os.makedirs("results", exist_ok=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--serial", help="COM port, e.g., COM3 or /dev/ttyUSB0")
    parser.add_argument("--timeout", type=float, default=1.0, help="serial timeout seconds")
    parser.add_argument("--repeat", type=int, default=1, help="times to measure RTT")
    parser.add_argument("--fw-proto", action="store_true", help="enable fw-proto for default protos (M,MSG)")
    parser.add_argument(
        "--fw-proto-protos",
        default="",
        help="comma list of protos that use fw-proto transport (M,JSON,MSG); overrides --fw-proto default set",
    )
    parser.add_argument(
        "--protos",
        default="M,JSON,MSG",
        help="comma list of protos to include (M,JSON,MSG). Controls measurement; size rows still written.",
    )
    parser.add_argument("--out-dir", default="论文分区/ccfc/result", help="directory to write outputs")
    parser.add_argument("--tag", default="", help="run tag; default uses timestamp")
    parser.add_argument(
        "--write-latest",
        action="store_true",
        help="also write legacy latest file names (e1.csv / e1_samples.csv)",
    )
    args = parser.parse_args()
    enabled = {p.strip().upper() for p in args.protos.split(",") if p.strip()}
    if args.fw_proto_protos.strip():
        fw_proto_set = {p.strip().upper() for p in args.fw_proto_protos.split(",") if p.strip()}
    elif args.fw_proto:
        fw_proto_set = {"M", "MSG"}
    else:
        fw_proto_set = set()

    os.makedirs(args.out_dir, exist_ok=True)
    tag = args.tag or datetime.now().strftime("%Y%m%d_%H%M%S")
    rows = []
    samples = []  # per-iteration RTTs

    for name, m_bytes, j_obj in task_payloads():
        json_bytes = to_json_line(j_obj)
        # M bytecode
        rows.append(
            {
                "task": name,
                "proto": "M",
                "bytes": len(m_bytes),
                "rtt_ms_mean": "",
                "rtt_ms_std": "",
                "payload_hex": m_bytes.hex(),
                "payload_str": "",
            }
        )
        # JSON text
        rows.append(
            {
                "task": name,
                "proto": "JSON",
                "bytes": len(json_bytes),
                "rtt_ms_mean": "",
                "rtt_ms_std": "",
                "payload_hex": "",
                "payload_str": json_bytes.decode("utf-8").strip(),
            }
        )
        # MessagePack binary
        try:
            msg_bytes = msgpack_pack(j_obj)
        except Exception:
            msg_bytes = b""
        rows.append(
            {
                "task": name,
                "proto": "MSG",
                "bytes": len(msg_bytes),
                "rtt_ms_mean": "",
                "rtt_ms_std": "",
                "payload_hex": msg_bytes.hex(),
                "payload_str": "",
            }
        )

        if args.serial:
            pairs = []
            if "M" in enabled:
                pairs.append(("M", m_bytes, False))
            if "JSON" in enabled:
                pairs.append(("JSON", json_bytes, True))
            if "MSG" in enabled:
                pairs.append(("MSG", msg_bytes, False))
            for proto, payload, is_json in pairs:
                rtts = []
                for idx in range(1, args.repeat + 1):
                    if proto in fw_proto_set:
                        rtt = measure_serial_fw(args.serial, payload, args.timeout, expect_len=None)
                    else:
                        rtt = measure_serial(args.serial, payload, is_json, args.timeout)
                    if rtt is not None:
                        rtts.append(rtt)
                        samples.append({"task": name, "proto": proto, "iter": idx, "rtt_ms": f"{rtt:.3f}"})
                if rtts:
                    avg = sum(rtts) / len(rtts)
                    var = sum((x - avg) ** 2 for x in rtts) / len(rtts)
                    std = var ** 0.5
                    for r in rows:
                        if r["task"] == name and r["proto"] == proto:
                            r["rtt_ms_mean"] = f"{avg:.3f}"
                            r["rtt_ms_std"] = f"{std:.3f}"

    out_csv = os.path.join(args.out_dir, f"e1_{tag}.csv")
    with open(out_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f, fieldnames=["task", "proto", "bytes", "rtt_ms_mean", "rtt_ms_std", "payload_hex", "payload_str"]
        )
        writer.writeheader()
        writer.writerows(rows)

    out_samples = ""
    if samples:
        out_samples = os.path.join(args.out_dir, f"e1_samples_{tag}.csv")
        with open(out_samples, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=["task", "proto", "iter", "rtt_ms"])
            writer.writeheader()
            writer.writerows(samples)
        print(f"Samples written: {out_samples}")

    if args.write_latest:
        latest_csv = os.path.join(args.out_dir, "e1.csv")
        with open(latest_csv, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(
                f, fieldnames=["task", "proto", "bytes", "rtt_ms_mean", "rtt_ms_std", "payload_hex", "payload_str"]
            )
            writer.writeheader()
            writer.writerows(rows)
        print(f"Wrote legacy latest: {latest_csv}")

        if out_samples:
            latest_samples = os.path.join(args.out_dir, "e1_samples.csv")
            with open(latest_samples, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=["task", "proto", "iter", "rtt_ms"])
                writer.writeheader()
                writer.writerows(samples)
            print(f"Wrote legacy samples: {latest_samples}")

    # summary on stdout
    for name in sorted({r["task"] for r in rows}):
        m_row = next(r for r in rows if r["task"] == name and r["proto"] == "M")
        j_row = next(r for r in rows if r["task"] == name and r["proto"] == "JSON")
        ratio = (j_row["bytes"] / m_row["bytes"]) if m_row["bytes"] else 0
        print(f"{name}: M {m_row['bytes']}B, JSON {j_row['bytes']}B, compression {ratio:.2f}x")
    print(f"CSV written: {out_csv}")


if __name__ == "__main__":
    sys.exit(main())
