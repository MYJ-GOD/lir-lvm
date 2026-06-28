#!/usr/bin/env python3
"""
Analyze results from new experiments (H1, H2, M8) and generate LaTeX tables.
"""
from __future__ import annotations

import csv
import json
import sys
from collections import defaultdict
from pathlib import Path
from typing import Dict, List

RESULT_DIR = Path(__file__).resolve().parent.parent / "result" / "GEN"


def load_csv(path: Path) -> List[dict]:
    rows = []
    with path.open("r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(row)
    return rows


def analyze_temperature_sweep():
    """H2: Analyze 6-point temperature sweep."""
    path = RESULT_DIR / "temperature_sweep_6pt_summary.csv"
    if not path.exists():
        print(f"[H2] {path} not found, skipping")
        return

    rows = load_csv(path)

    print("=" * 60)
    print("H2: Temperature 6-Point Sweep Results")
    print("=" * 60)

    # Group by temperature
    temps = {}
    for r in rows:
        t = float(r["temperature"])
        metric = r["metric"]
        if t not in temps:
            temps[t] = {}
        temps[t][metric] = {
            "mean": float(r["mean"]),
            "stdev": float(r["stdev"]),
            "n": int(r["n"]),
        }

    # Print table
    print(f"\n{'Temp':>6} {'Task Success':>20} {'IR Valid':>20} {'Compile':>20}")
    print("-" * 70)
    for t in sorted(temps.keys()):
        d = temps[t]
        ts = d.get("task_success", {})
        ir = d.get("ir_valid", {})
        cp = d.get("compile_pass", {})
        print(f"{t:>6.1f} {ts.get('mean',0):.3f}±{ts.get('stdev',0):.3f}   {ir.get('mean',0):.3f}±{ir.get('stdev',0):.3f}   {cp.get('mean',0):.3f}±{cp.get('stdev',0):.3f}")

    # Generate LaTeX table
    print("\n% LaTeX table for paper")
    print("\\begin{table}[t]")
    print("\\centering")
    print("\\caption{Temperature 扫描实验结果（6 点）}")
    print("\\label{tab:temperature_6pt}")
    print("\\begin{tabular}{lcc}")
    print("\\toprule")
    print("Temperature & Task Success Rate (mean $\\pm$ std) & IR Valid Rate \\\\")
    print("\\midrule")
    for t in sorted(temps.keys()):
        d = temps[t]
        ts = d.get("task_success", {})
        ir = d.get("ir_valid", {})
        label = f"{t:.1f}" if t > 0 else "0.0（确定性）"
        print(f"{label} & {ts['mean']:.3f}$\\pm${ts['stdev']:.3f} & {ir['mean']:.3f} \\\\")
    print("\\bottomrule")
    print("\\end{tabular}")
    print("\\end{table}")


def analyze_random_tasks():
    """H1: Analyze random task evaluation."""
    path = RESULT_DIR / "random_eval_600.csv"
    if not path.exists():
        print(f"[H1] {path} not found, skipping")
        return

    rows = load_csv(path)
    n = len(rows)

    print("\n" + "=" * 60)
    print(f"H1: Random Task Evaluation ({n} tasks)")
    print("=" * 60)

    metrics = ["ir_valid", "compile_pass", "verify_pass", "execution_pass", "task_success"]
    for m in metrics:
        cnt = sum(int(r[m]) for r in rows)
        print(f"  {m}: {cnt}/{n} = {cnt/n:.3f}")

    # Per-category
    cats = defaultdict(list)
    for r in rows:
        cats[r["category"]].append(int(r["task_success"]))

    print(f"\nPer-category task_success ({len(cats)} categories):")
    for cat, vals in sorted(cats.items(), key=lambda x: -sum(x[1])/len(x[1])):
        s = sum(vals)
        print(f"  {cat}: {s}/{len(vals)} = {s/len(vals):.3f}")

    # Generate LaTeX table
    print("\n% LaTeX table for paper")
    print("\\begin{table}[t]")
    print("\\centering")
    print("\\caption{随机任务生成实验（$n$=" + str(n) + "，temperature=0.0）}")
    print("\\label{tab:random_tasks}")
    print("\\begin{tabular}{lcc}")
    print("\\toprule")
    print("指标 & 数值 & 95\\% Wilson CI \\\\")
    print("\\midrule")
    for m in metrics:
        cnt = sum(int(r[m]) for r in rows)
        rate = cnt / n
        # Wilson CI approximation
        import math
        z = 1.96
        denom = 1 + z**2 / n
        center = (rate + z**2 / (2*n)) / denom
        margin = z * math.sqrt((rate * (1 - rate) + z**2 / (4*n)) / n) / denom
        lo = max(0, center - margin)
        hi = min(1, center + margin)
        label = m.replace("_", "\\_")
        print(f"{label} & {rate:.3f} & [{lo:.3f}, {hi:.3f}] \\\\")
    print("\\bottomrule")
    print("\\end{tabular}")
    print("\\end{table}")


def analyze_grammar_constrained():
    """M8: Analyze grammar-constrained decoding results."""
    path = RESULT_DIR / "grammar_constrained.csv"
    if not path.exists():
        print(f"[M8] {path} not found, skipping")
        return

    rows = load_csv(path)
    n = len(rows)

    print("\n" + "=" * 60)
    print(f"M8: Grammar-Constrained Decoding ({n} tasks)")
    print("=" * 60)

    raw_s = sum(int(r["raw_success"]) for r in rows)
    filt_s = sum(int(r["filtered_success"]) for r in rows)
    avg_grammar = sum(float(r["grammar_valid_rate"]) for r in rows) / n

    print(f"  Raw success (unconstrained):  {raw_s}/{n} = {raw_s/n:.3f}")
    print(f"  Filtered success (grammar):   {filt_s}/{n} = {filt_s/n:.3f}")
    print(f"  Avg grammar-valid rate:       {avg_grammar:.3f}")
    print(f"  Improvement:                  +{(filt_s - raw_s)/n:.3f}")

    # Generate LaTeX table
    print("\n% LaTeX table for paper")
    print("\\begin{table}[t]")
    print("\\centering")
    print("\\caption{Grammar-constrained decoding 模拟实验（temperature=1.0）}")
    print("\\label{tab:grammar_constrained}")
    print("\\begin{tabular}{lc}")
    print("\\toprule")
    print("指标 & 数值 \\\\")
    print("\\midrule")
    print(f"无约束成功率（首候选） & {raw_s/n:.3f} \\\\")
    print(f"Grammar 过滤成功率（首合法） & {filt_s/n:.3f} \\\\")
    print(f"平均 grammar 合法率 & {avg_grammar:.3f} \\\\")
    print(f"提升幅度 & +{(filt_s - raw_s)/n:.3f} \\\\")
    print("\\bottomrule")
    print("\\end{tabular}")
    print("\\end{table}")


def analyze_arduino_baseline():
    """M2: Analyze Arduino C baseline results."""
    path = RESULT_DIR / "arduino_c_baseline.csv"
    if not path.exists():
        print(f"[M2] {path} not found, skipping")
        return

    rows = load_csv(path)
    n = len(rows)

    print("\n" + "=" * 60)
    print(f"M2: Arduino C Baseline ({n} tasks)")
    print("=" * 60)

    avg_bytes = sum(int(r["output_bytes"]) for r in rows) / n
    valid_cnt = sum(int(r["valid_structure"]) for r in rows)
    lir_avg = 10.9

    print(f"  Avg Arduino C output:  {avg_bytes:.1f} bytes")
    print(f"  Valid structure:       {valid_cnt}/{n} = {valid_cnt/n:.3f}")
    print(f"  LIR bytecode avg:      {lir_avg:.1f} bytes")
    print(f"  Ratio (C/bytecode):    {avg_bytes/lir_avg:.1f}x")

    # Per-category
    cats = defaultdict(list)
    for r in rows:
        cats[r["category"]].append(int(r["output_bytes"]))
    print(f"\nPer-category avg bytes:")
    for cat, vals in sorted(cats.items(), key=lambda x: sum(x[1])/len(x[1])):
        print(f"  {cat}: {sum(vals)/len(vals):.0f}")


def main():
    print("Analyzing new experiments...\n")
    analyze_temperature_sweep()
    analyze_random_tasks()
    analyze_grammar_constrained()
    analyze_arduino_baseline()

    # Check which experiments are still pending
    pending = []
    for name, path in [
        ("H2 temperature sweep", RESULT_DIR / "temperature_sweep_6pt_summary.csv"),
        ("H1 random tasks", RESULT_DIR / "random_eval_600.csv"),
        ("M8 grammar-constrained", RESULT_DIR / "grammar_constrained.csv"),
        ("M2 Arduino C baseline", RESULT_DIR / "arduino_c_baseline.csv"),
    ]:
        if not path.exists():
            pending.append(name)

    if pending:
        print(f"\n{'='*60}")
        print(f"Pending experiments ({len(pending)}):")
        for p in pending:
            print(f"  - {p}")


if __name__ == "__main__":
    main()
