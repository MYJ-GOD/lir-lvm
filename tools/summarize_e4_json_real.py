#!/usr/bin/env python3
"""
Merge one or more E4+ JSON-real summaries with the existing E4 summary.
Outputs a paper-ready matrix CSV/MD for section 7.9.
"""

from __future__ import annotations

import argparse
import csv
import math
from typing import Dict, List, Tuple


def read_csv(path: str) -> List[Dict[str, str]]:
    with open(path, "r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def wilson_ci(k: int, n: int, z: float = 1.959963984540054) -> Tuple[float, float]:
    if n <= 0:
        return 0.0, 0.0
    phat = k / n
    den = 1.0 + (z * z) / n
    center = (phat + (z * z) / (2.0 * n)) / den
    half = (z / den) * math.sqrt((phat * (1.0 - phat) / n) + (z * z) / (4.0 * n * n))
    return max(0.0, center - half), min(1.0, center + half)


def two_prop(k1: int, n1: int, k2: int, n2: int) -> Tuple[float, float]:
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


def fmt_ci(lo: float, hi: float) -> str:
    return f"[{lo:.3f}, {hi:.3f}]"


def desc_for_group(group: str) -> str:
    mapping = {
        "G0_json_real": "MCU端真实JSON/文本解析链路（开环）",
        "G0_json_real_with_o_no_retry": "JSON+读回无重试（应用层）",
        "G0_json_real_with_o": "JSON+读回+重试（应用层）",
        "G2_m_no_o": "M 开环",
        "G4_m_with_o_no_retry": "M+读回无重试",
        "G3_m_with_o": "M+读回+重试",
    }
    return mapping.get(group, group)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--json-summary", action="append", required=True, help="one or more e4_json_real_summary*.csv")
    ap.add_argument("--e4-summary", required=True, help="existing e4_summary.csv")
    ap.add_argument("--out-csv", required=True)
    ap.add_argument("--out-md", required=True)
    args = ap.parse_args()

    e4_rows = read_csv(args.e4_summary)
    e4_map = {r["group"]: r for r in e4_rows}
    required_e4 = ["G2_m_no_o", "G4_m_with_o_no_retry", "G3_m_with_o"]
    missing = [g for g in required_e4 if g not in e4_map]
    if missing:
        raise SystemExit(f"missing groups in {args.e4_summary}: {', '.join(missing)}")

    json_rows: List[Tuple[str, Dict[str, str]]] = []
    for path in args.json_summary:
        rows = read_csv(path)
        if not rows:
            raise SystemExit(f"empty json summary: {path}")
        row = rows[0]
        group = row.get("group", "")
        if not group:
            raise SystemExit(f"missing group column in {path}")
        json_rows.append((path, row))

    n3 = int(e4_map["G3_m_with_o"]["n"])
    k3 = int(e4_map["G3_m_with_o"]["converged"])

    merged: List[Tuple[str, Dict[str, str], str]] = []
    for path, row in json_rows:
        merged.append((row["group"], row, path))
    merged.extend(
        [
            ("G2_m_no_o", e4_map["G2_m_no_o"], args.e4_summary),
            ("G4_m_with_o_no_retry", e4_map["G4_m_with_o_no_retry"], args.e4_summary),
            ("G3_m_with_o", e4_map["G3_m_with_o"], args.e4_summary),
        ]
    )

    order = {
        "G0_json_real": 0,
        "G0_json_real_with_o_no_retry": 1,
        "G0_json_real_with_o": 2,
        "G2_m_no_o": 3,
        "G4_m_with_o_no_retry": 4,
        "G3_m_with_o": 5,
    }
    merged.sort(key=lambda item: order.get(item[0], 999))

    rows: List[Dict[str, str]] = []
    for group, row, src in merged:
        n = int(row["n"])
        k = int(row["converged"])
        scr = float(row["scr"])

        if row.get("ci_lo") and row.get("ci_hi"):
            ci_lo = float(row["ci_lo"])
            ci_hi = float(row["ci_hi"])
        else:
            ci_lo, ci_hi = wilson_ci(k, n)

        rtt_mean = float(row.get("rtt_ms_mean", "0") or 0.0)
        rtt_std = float(row.get("rtt_ms_std", "0") or 0.0)
        attempts = float(row.get("attempts_mean", "1") or 1.0)

        if group == "G3_m_with_o":
            test = "baseline"
        else:
            z, p = two_prop(k, n, k3, n3)
            test = f"z={z:.2f}, p={fmt_p(p)}"

        rows.append(
            {
                "group": group,
                "desc": desc_for_group(group),
                "converged_n": f"{k}/{n}",
                "scr": f"{scr:.3f}",
                "ci95": fmt_ci(ci_lo, ci_hi),
                "rtt_ms": f"{rtt_mean:.3f}±{rtt_std:.3f}",
                "attempts_mean": f"{attempts:.3f}",
                "test_vs_g3": test,
                "source": src,
            }
        )

    fields = [
        "group",
        "desc",
        "converged_n",
        "scr",
        "ci95",
        "rtt_ms",
        "attempts_mean",
        "test_vs_g3",
        "source",
    ]
    with open(args.out_csv, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)

    lines: List[str] = []
    lines.append("# E4+ JSON Real Matrix")
    lines.append("")
    lines.append("| group | 说明 | converged/n | SCR | 95%CI | RTT mean±SD (ms) | attempts_mean | 与 G3 差异检验 | 结果文件 |")
    lines.append("|---|---|---:|---:|---|---|---:|---|---|")
    for row in rows:
        lines.append(
            f"| {row['group']} | {row['desc']} | {row['converged_n']} | {row['scr']} | {row['ci95']} | {row['rtt_ms']} | {row['attempts_mean']} | {row['test_vs_g3']} | `{row['source']}` |"
        )
    with open(args.out_md, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(lines) + "\n")

    print(f"Wrote: {args.out_csv}")
    print(f"Wrote: {args.out_md}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
