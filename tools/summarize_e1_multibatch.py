#!/usr/bin/env python3
"""
Summarize E1 multi-batch RTT samples and evaluate rules in 论文分区/ccfc/result/E1/e1_data_rules.md.

Inputs:
  - 论文分区/ccfc/result/E1/e1_multibatch_tags.txt
  - 论文分区/ccfc/result/E1/raw/e1_<tag>.csv
  - 论文分区/ccfc/result/E1/raw/e1_samples_<tag>.csv

Outputs:
  - 论文分区/ccfc/result/E1/e1_multibatch_summary.csv
  - 论文分区/ccfc/result/E1/e1_multibatch_compare.csv
  - 论文分区/ccfc/result/E1/e1_multibatch_compression.csv
  - 论文分区/ccfc/result/E1/e1_multibatch_outliers.csv
  - 论文分区/ccfc/result/E1/e1_temp_m_outlier_iter_hist.csv
  - 论文分区/ccfc/result/E1/e1_multibatch_judgement.md
"""

from __future__ import annotations

import argparse
import csv
import os
from collections import Counter, defaultdict
from datetime import datetime
from statistics import median
from typing import Dict, List, Tuple


def read_csv(path: str) -> List[Dict[str, str]]:
    with open(path, "r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def write_csv(path: str, fieldnames: List[str], rows: List[Dict[str, str]]) -> None:
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(rows)


def percentile(values: List[float], q: float) -> float:
    if not values:
        return 0.0
    s = sorted(values)
    if len(s) == 1:
        return s[0]
    pos = (len(s) - 1) * q
    lo = int(pos)
    hi = min(lo + 1, len(s) - 1)
    frac = pos - lo
    return s[lo] * (1.0 - frac) + s[hi] * frac


def mean(values: List[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def std_pop(values: List[float]) -> float:
    if not values:
        return 0.0
    m = mean(values)
    return (sum((x - m) * (x - m) for x in values) / len(values)) ** 0.5


def mad(values: List[float], med: float) -> float:
    if not values:
        return 0.0
    dev = [abs(x - med) for x in values]
    return median(dev)


def robust_outlier_info(values: List[float]) -> Tuple[List[bool], float, float, List[float]]:
    if not values:
        return [], 0.0, 0.0, []
    med = median(values)
    m = mad(values, med)
    if m == 0:
        return [False] * len(values), med, m, [0.0] * len(values)
    mask = []
    zvals = []
    for x in values:
        z = 0.6745 * (x - med) / m
        zvals.append(z)
        mask.append(abs(z) > 3.5)
    return mask, med, m, zvals


def fmt(x: float) -> str:
    return f"{x:.3f}"


def load_tags(path: str) -> List[str]:
    with open(path, "r", encoding="utf-8") as f:
        out = []
        for ln in f:
            t = ln.strip().lstrip("\ufeff")
            if t:
                out.append(t)
        return out


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--tags-file", default="论文分区/ccfc/result/E1/e1_multibatch_tags.txt")
    p.add_argument("--raw-dir", default="论文分区/ccfc/result/E1/raw")
    p.add_argument("--out-dir", default="论文分区/ccfc/result/E1")
    args = p.parse_args()

    tags = load_tags(args.tags_file)
    if not tags:
        raise RuntimeError(f"no tags found in {args.tags_file}")

    size_rows: Dict[Tuple[str, str], Dict[str, str]] = {}
    samples: Dict[Tuple[str, str], List[Tuple[str, int, float]]] = defaultdict(list)

    for tag in tags:
        size_path = os.path.join(args.raw_dir, f"e1_{tag}.csv")
        samp_path = os.path.join(args.raw_dir, f"e1_samples_{tag}.csv")
        if not os.path.exists(size_path):
            raise FileNotFoundError(size_path)
        if not os.path.exists(samp_path):
            raise FileNotFoundError(samp_path)

        for r in read_csv(size_path):
            task = r.get("task", "")
            proto = r.get("proto", "")
            if proto not in ("M", "JSON"):
                continue
            size_rows[(task, proto)] = r

        for r in read_csv(samp_path):
            task = r.get("task", "")
            proto = r.get("proto", "")
            if proto not in ("M", "JSON"):
                continue
            try:
                x = float(r.get("rtt_ms", ""))
                it = int(r.get("iter", "0") or "0")
            except ValueError:
                continue
            samples[(task, proto)].append((tag, it, x))

    tasks = sorted({k[0] for k in samples.keys()})
    protos = ["M", "JSON"]

    summary_rows: List[Dict[str, str]] = []
    outlier_rows: List[Dict[str, str]] = []
    for task in tasks:
        for proto in protos:
            recs = samples.get((task, proto), [])
            if not recs:
                continue
            vals = [x for _, _, x in recs]
            out_mask, med, mdev, zvals = robust_outlier_info(vals)
            p95 = percentile(vals, 0.95)
            m = mean(vals)
            s = std_pop(vals)
            mn = min(vals)
            mx = max(vals)
            out_count = sum(1 for b in out_mask if b)
            kept = [v for v, b in zip(vals, out_mask) if not b]
            for (tg, it, v), is_out, z in zip(recs, out_mask, zvals):
                if is_out:
                    outlier_rows.append(
                        {
                            "task": task,
                            "proto": proto,
                            "tag": tg,
                            "iter": str(it),
                            "rtt_ms": fmt(v),
                            "median_ms": fmt(med),
                            "mad_ms": fmt(mdev),
                            "robust_z": fmt(z),
                        }
                    )
            summary_rows.append(
                {
                    "task": task,
                    "proto": proto,
                    "n": str(len(vals)),
                    "mean_ms": fmt(m),
                    "std_ms": fmt(s),
                    "median_ms": fmt(med),
                    "p95_ms": fmt(p95),
                    "min_ms": fmt(mn),
                    "max_ms": fmt(mx),
                    "mad_ms": fmt(mdev),
                    "outlier_count": str(out_count),
                    "outlier_rate": fmt(out_count / len(vals)),
                    "trimmed_n": str(len(kept)),
                    "trimmed_mean_ms": fmt(mean(kept) if kept else 0.0),
                    "trimmed_std_ms": fmt(std_pop(kept) if kept else 0.0),
                }
            )

    summary_path = os.path.join(args.out_dir, "e1_multibatch_summary.csv")
    write_csv(
        summary_path,
        [
            "task",
            "proto",
            "n",
            "mean_ms",
            "std_ms",
            "median_ms",
            "p95_ms",
            "min_ms",
            "max_ms",
            "mad_ms",
            "outlier_count",
            "outlier_rate",
            "trimmed_n",
            "trimmed_mean_ms",
            "trimmed_std_ms",
        ],
        sorted(summary_rows, key=lambda r: (r["task"], r["proto"])),
    )

    outlier_path = os.path.join(args.out_dir, "e1_multibatch_outliers.csv")
    write_csv(
        outlier_path,
        ["task", "proto", "tag", "iter", "rtt_ms", "median_ms", "mad_ms", "robust_z"],
        sorted(outlier_rows, key=lambda r: (r["task"], r["proto"], r["tag"], int(r["iter"]))),
    )

    hist_counter: Counter[int] = Counter()
    for r in outlier_rows:
        if r["task"] == "temp_read" and r["proto"] == "M":
            hist_counter[int(r["iter"])] += 1
    hist_rows = [
        {"iter": str(it), "count": str(cnt)} for it, cnt in sorted(hist_counter.items(), key=lambda kv: kv[0])
    ]
    hist_path = os.path.join(args.out_dir, "e1_temp_m_outlier_iter_hist.csv")
    write_csv(hist_path, ["iter", "count"], hist_rows)

    by_key = {(r["task"], r["proto"]): r for r in summary_rows}
    compare_rows: List[Dict[str, str]] = []
    for task in tasks:
        rm = by_key.get((task, "M"))
        rj = by_key.get((task, "JSON"))
        if not rm or not rj:
            continue
        med_m = float(rm["median_ms"])
        med_j = float(rj["median_ms"])
        p95_m = float(rm["p95_ms"])
        p95_j = float(rj["p95_ms"])
        compare_rows.append(
            {
                "task": task,
                "n_M": rm["n"],
                "n_JSON": rj["n"],
                "median_M_ms": rm["median_ms"],
                "median_JSON_ms": rj["median_ms"],
                "median_gain_json_minus_m_ms": fmt(med_j - med_m),
                "p95_M_ms": rm["p95_ms"],
                "p95_JSON_ms": rj["p95_ms"],
                "p95_gain_json_minus_m_ms": fmt(p95_j - p95_m),
                "trimmed_std_M_ms": rm["trimmed_std_ms"],
                "trimmed_std_JSON_ms": rj["trimmed_std_ms"],
            }
        )

    compare_path = os.path.join(args.out_dir, "e1_multibatch_compare.csv")
    write_csv(
        compare_path,
        [
            "task",
            "n_M",
            "n_JSON",
            "median_M_ms",
            "median_JSON_ms",
            "median_gain_json_minus_m_ms",
            "p95_M_ms",
            "p95_JSON_ms",
            "p95_gain_json_minus_m_ms",
            "trimmed_std_M_ms",
            "trimmed_std_JSON_ms",
        ],
        sorted(compare_rows, key=lambda r: r["task"]),
    )

    comp_rows: List[Dict[str, str]] = []
    ratios: List[float] = []
    m_sum = 0
    j_sum = 0
    for task in tasks:
        mrow = size_rows.get((task, "M"))
        jrow = size_rows.get((task, "JSON"))
        if not mrow or not jrow:
            continue
        bm = int(mrow.get("bytes", "0") or "0")
        bj = int(jrow.get("bytes", "0") or "0")
        ratio = (bj / bm) if bm else 0.0
        ratios.append(ratio)
        m_sum += bm
        j_sum += bj
        comp_rows.append(
            {
                "task": task,
                "bytes_M": str(bm),
                "bytes_JSON": str(bj),
                "R_task_json_over_m": fmt(ratio),
            }
        )
    r_avg = mean(ratios) if ratios else 0.0
    r_weighted = (j_sum / m_sum) if m_sum else 0.0
    comp_path = os.path.join(args.out_dir, "e1_multibatch_compression.csv")
    write_csv(
        comp_path,
        ["task", "bytes_M", "bytes_JSON", "R_task_json_over_m"],
        sorted(comp_rows, key=lambda r: r["task"]),
    )

    io_tasks = ["relay1_on", "relay1_off", "water_read", "temp_read"]
    combo_task = "combo_on_wait_read"

    def get_metric(task: str, proto: str, key: str, default: float = 0.0) -> float:
        rr = by_key.get((task, proto))
        if not rr:
            return default
        return float(rr.get(key, "0") or "0")

    r1_pass = all(
        int(size_rows[(t, "M")]["bytes"]) < int(size_rows[(t, "JSON")]["bytes"])
        for t in tasks
        if (t, "M") in size_rows and (t, "JSON") in size_rows
    )
    r3_items = []
    r3_pass = True
    for t in io_tasks:
        med_m = get_metric(t, "M", "median_ms")
        med_j = get_metric(t, "JSON", "median_ms")
        ok = med_m < med_j
        r3_items.append((t, med_m, med_j, ok))
        r3_pass = r3_pass and ok

    combo_med_m = get_metric(combo_task, "M", "median_ms")
    r5_pass = 500.0 <= combo_med_m <= 520.0

    lines: List[str] = []
    lines.append("# E1 Multi-Batch Judgement")
    lines.append("")
    lines.append(f"- Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append(f"- Tags: {', '.join(tags)}")
    lines.append(f"- Total batches: {len(tags)}")
    lines.append("- Rule source: `论文分区/ccfc/result/E1/e1_data_rules.md`")
    lines.append("")
    lines.append("## Compression")
    lines.append("")
    lines.append(f"- R1 bytes_M < bytes_JSON (all tasks): {'PASS' if r1_pass else 'FAIL'}")
    lines.append(f"- R_avg (mean of R_task): {fmt(r_avg)}x")
    lines.append(f"- R_weighted (sum JSON / sum M): {fmt(r_weighted)}x")
    lines.append("")
    lines.append("## Latency (IO Tasks Only)")
    lines.append("")
    lines.append(f"- R3 median_M < median_JSON for IO tasks: {'PASS' if r3_pass else 'FAIL'}")
    for t, med_m, med_j, ok in r3_items:
        lines.append(
            f"- {t}: median_M={fmt(med_m)} ms, median_JSON={fmt(med_j)} ms, delta(JSON-M)={fmt(med_j - med_m)} ms => {'PASS' if ok else 'FAIL'}"
        )
    lines.append("")
    lines.append("## Stability")
    lines.append("")
    for t in io_tasks:
        out_m = get_metric(t, "M", "outlier_rate")
        out_j = get_metric(t, "JSON", "outlier_rate")
        ts_m = get_metric(t, "M", "trimmed_std_ms")
        ts_j = get_metric(t, "JSON", "trimmed_std_ms")
        lines.append(
            f"- {t}: outlier_rate(M/JSON)={fmt(out_m)}/{fmt(out_j)}, trimmed_std(M/JSON)={fmt(ts_m)}/{fmt(ts_j)} ms"
        )
    if hist_rows:
        hist_desc = ", ".join(f"iter={r['iter']} -> {r['count']}" for r in hist_rows)
        lines.append(f"- temp_read/M outlier-iter histogram: {hist_desc}")
    lines.append("")
    lines.append("## Semantic Check")
    lines.append("")
    lines.append(
        f"- R5 combo_on_wait_read median_M in [500,520] ms: {'PASS' if r5_pass else 'FAIL'} (observed {fmt(combo_med_m)} ms)"
    )
    lines.append("- combo task is excluded from protocol-overhead speed conclusion by rule.")
    lines.append("")
    lines.append("## Files")
    lines.append("")
    lines.append("- `论文分区/ccfc/result/E1/e1_multibatch_summary.csv`")
    lines.append("- `论文分区/ccfc/result/E1/e1_multibatch_compare.csv`")
    lines.append("- `论文分区/ccfc/result/E1/e1_multibatch_compression.csv`")
    lines.append("- `论文分区/ccfc/result/E1/e1_multibatch_outliers.csv`")
    lines.append("- `论文分区/ccfc/result/E1/e1_temp_m_outlier_iter_hist.csv`")
    lines.append("- `论文分区/ccfc/result/E1/e1_multibatch_judgement.md`")

    judgement_path = os.path.join(args.out_dir, "e1_multibatch_judgement.md")
    os.makedirs(os.path.dirname(judgement_path) or ".", exist_ok=True)
    with open(judgement_path, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(lines) + "\n")

    print(f"Wrote: {summary_path}")
    print(f"Wrote: {compare_path}")
    print(f"Wrote: {comp_path}")
    print(f"Wrote: {outlier_path}")
    print(f"Wrote: {hist_path}")
    print(f"Wrote: {judgement_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
