#!/usr/bin/env python3
"""
Summarize deployment metrics for section 7.10.

Inputs:
- throughput summary (bench_deploy_throughput.py)
- E3 memory summary (bench_deploy_e3_mem.py)
- E4 trials csv (for G3 P95 RTT)
- optional power manual csv
"""

from __future__ import annotations

import argparse
import csv
import os
from typing import Dict, List, Optional, Tuple


def read_csv(path: str) -> List[Dict[str, str]]:
    with open(path, "r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


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


def load_power(path: str) -> Tuple[Optional[float], Optional[float], Optional[float], Optional[int]]:
    if not os.path.exists(path):
        with open(path, "w", encoding="utf-8", newline="") as f:
            w = csv.DictWriter(f, fieldnames=["scenario", "avg_current_ma", "voltage_v", "duration_s", "tasks"])
            w.writeheader()
            w.writerow({"scenario": "E2_guarded", "avg_current_ma": "", "voltage_v": "5.0", "duration_s": "", "tasks": ""})
        return None, None, None, None
    rows = read_csv(path)
    if not rows:
        return None, None, None, None
    r = rows[0]
    try:
        current = float(r["avg_current_ma"]) if r.get("avg_current_ma", "") != "" else None
    except Exception:
        current = None
    try:
        voltage = float(r["voltage_v"]) if r.get("voltage_v", "") != "" else None
    except Exception:
        voltage = None
    try:
        duration = float(r["duration_s"]) if r.get("duration_s", "") != "" else None
    except Exception:
        duration = None
    try:
        tasks = int(float(r["tasks"])) if r.get("tasks", "") != "" else None
    except Exception:
        tasks = None
    return current, voltage, duration, tasks


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--throughput-summary", required=True)
    ap.add_argument("--e3-summary", required=True)
    ap.add_argument("--e4-trials", required=True)
    ap.add_argument("--power-manual", default="论文分区/ccfc/result/E10_deploy/power_manual.csv")
    ap.add_argument("--out-csv", required=True)
    ap.add_argument("--out-md", required=True)
    args = ap.parse_args()

    t_rows = read_csv(args.throughput_summary)
    if not t_rows:
        raise SystemExit(f"empty throughput summary: {args.throughput_summary}")
    t = t_rows[0]
    throughput = float(t["throughput_cmd_s"])
    n_throughput = int(float(t["n"]))

    e3_rows = read_csv(args.e3_summary)
    e3_all = next((r for r in e3_rows if r.get("group", "") == "all"), None)
    if e3_all is None:
        raise SystemExit(f"missing group=all in e3 summary: {args.e3_summary}")
    n_e3 = int(float(e3_all["n_ok"]))
    stack_waterline = float(e3_all["stack_waterline"])
    heap_waterline = float(e3_all["heap_waterline"])

    e4_rows = read_csv(args.e4_trials)
    g3_vals = []
    for r in e4_rows:
        if r.get("group", "") != "G3_m_with_o":
            continue
        try:
            g3_vals.append(float(r["rtt_total_ms"]))
        except Exception:
            pass
    if not g3_vals:
        raise SystemExit(f"no G3_m_with_o rtt_total_ms in: {args.e4_trials}")
    e4_p95 = percentile(g3_vals, 0.95)
    n_e4 = len(g3_vals)

    current_ma, voltage_v, duration_s, tasks = load_power(args.power_manual)
    power_note = ""
    avg_power_ma = ""
    energy_mwh_task = ""
    n_power = ""
    if current_ma is not None:
        avg_power_ma = f"{current_ma:.3f}"
        n_power = str(tasks) if tasks is not None else ""
    else:
        power_note = "需外接功耗仪采样并填写 power_manual.csv"

    if (
        current_ma is not None
        and voltage_v is not None
        and duration_s is not None
        and tasks is not None
        and tasks > 0
    ):
        avg_power_mw = current_ma * voltage_v
        energy_mwh_task = f"{(avg_power_mw * duration_s / 3600.0) / tasks:.6f}"

    rows: List[Dict[str, str]] = [
        {
            "platform": "ESP8266",
            "scenario": "E2 guarded",
            "metric": "平均功耗",
            "value": avg_power_ma,
            "unit": "mA",
            "n": n_power,
            "source": args.power_manual,
            "note": power_note,
        },
        {
            "platform": "ESP8266",
            "scenario": "E2 guarded",
            "metric": "单任务能耗",
            "value": energy_mwh_task,
            "unit": "mWh/task",
            "n": n_power,
            "source": args.power_manual,
            "note": power_note,
        },
        {
            "platform": "ESP8266",
            "scenario": "E2 guarded",
            "metric": "吞吐",
            "value": f"{throughput:.3f}",
            "unit": "cmd/s",
            "n": str(n_throughput),
            "source": args.throughput_summary,
            "note": "串口端到端实测",
        },
        {
            "platform": "ESP8266",
            "scenario": "E2 guarded",
            "metric": "峰值 stack 水位",
            "value": f"{stack_waterline:.3f}",
            "unit": "B",
            "n": str(n_e3),
            "source": args.e3_summary,
            "note": "以 free_stack(max-min) 作为水位代理",
        },
        {
            "platform": "ESP8266",
            "scenario": "E2 guarded",
            "metric": "峰值 heap 水位",
            "value": f"{heap_waterline:.3f}",
            "unit": "B",
            "n": str(n_e3),
            "source": args.e3_summary,
            "note": "以 free_heap(max-min) 作为水位代理",
        },
        {
            "platform": "ESP8266",
            "scenario": "E4 guarded",
            "metric": "P95 RTT",
            "value": f"{e4_p95:.3f}",
            "unit": "ms",
            "n": str(n_e4),
            "source": args.e4_trials,
            "note": "G3_m_with_o 的 rtt_total_ms 分位数",
        },
    ]

    with open(args.out_csv, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(
            f,
            fieldnames=["platform", "scenario", "metric", "value", "unit", "n", "source", "note"],
        )
        w.writeheader()
        w.writerows(rows)

    lines: List[str] = []
    lines.append("# E10 Deploy Metrics")
    lines.append("")
    lines.append("| 平台 | 场景 | 指标 | 数值 | 单位 | n | 结果文件 | 备注 |")
    lines.append("|---|---|---|---:|---|---:|---|---|")
    for r in rows:
        v = r["value"] if r["value"] != "" else "[待填]"
        n = r["n"] if r["n"] != "" else "[待填]"
        lines.append(
            f"| {r['platform']} | {r['scenario']} | {r['metric']} | {v} | {r['unit']} | {n} | `{r['source']}` | {r['note']} |"
        )
    with open(args.out_md, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(lines) + "\n")

    print(f"Wrote: {args.out_csv}")
    print(f"Wrote: {args.out_md}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
