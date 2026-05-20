#!/usr/bin/env python3
"""
Summarize E2+ orthogonal ablation results (A0~A5).

Input CSV format: same as bench_e2(_orthogonal).py outputs:
  case,bytes,payload_hex,response,rtt_ms_mean,rtt_ms_std,ok_count,fault_count,main_fault
"""
import argparse
import csv
import math
import os
from typing import Dict, List, Tuple

VARIANTS = [
    "a0_base_guarded",
    "a1_no_auth_only",
    "a2_no_load_validator_only",
    "a3_no_step_limit_only",
    "a4_no_call_depth_only",
    "a5_no_bad_encoding_fault_only",
]


def wilson_ci(k: int, n: int, z: float = 1.96) -> Tuple[float, float]:
    if n <= 0:
        return 0.0, 0.0
    p = k / n
    den = 1.0 + (z * z) / n
    center = (p + (z * z) / (2 * n)) / den
    half = (z / den) * math.sqrt((p * (1 - p) / n) + ((z * z) / (4 * n * n)))
    lo = max(0.0, center - half)
    hi = min(1.0, center + half)
    return lo, hi


def load_variant(path: str) -> Dict:
    rows = list(csv.DictReader(open(path, "r", encoding="utf-8")))
    n = 0
    ok = 0
    fault = 0
    fault_dist: Dict[str, int] = {}
    for r in rows:
        ok_i = int(r.get("ok_count") or 0)
        fault_i = int(r.get("fault_count") or 0)
        ok += ok_i
        fault += fault_i
        n += ok_i + fault_i
        mf = str(r.get("main_fault") or "").strip()
        if mf:
            fault_dist[mf] = fault_dist.get(mf, 0) + fault_i
    uabr = (fault / n) if n > 0 else 0.0
    lo, hi = wilson_ci(fault, n)
    fault_dist_text = ",".join(f"{k}:{v}" for k, v in sorted(fault_dist.items(), key=lambda x: x[0]))
    return {
        "n": n,
        "ok": ok,
        "fault": fault,
        "uabr": uabr,
        "ci_lo": lo,
        "ci_hi": hi,
        "fault_dist": fault_dist_text,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--results-dir", default="论文分区/ccfc/result/E2_orthogonal")
    ap.add_argument("--tag", default="", help="optional tag suffix for output files")
    args = ap.parse_args()

    out_rows: List[Dict[str, str]] = []
    missing: List[str] = []

    for v in VARIANTS:
        p = os.path.join(args.results_dir, f"e2_{v}.csv")
        if not os.path.exists(p):
            missing.append(p)
            continue
        s = load_variant(p)
        out_rows.append(
            {
                "variant": v,
                "n": str(s["n"]),
                "ok": str(s["ok"]),
                "fault": str(s["fault"]),
                "UABR": f"{s['uabr']:.6f}",
                "CI95": f"[{s['ci_lo']:.3f}, {s['ci_hi']:.3f}]",
                "main_fault_dist": s["fault_dist"],
                "source": p,
            }
        )

    os.makedirs(args.results_dir, exist_ok=True)
    suffix = f"_{args.tag}" if args.tag else ""
    out_csv = os.path.join(args.results_dir, f"e2_orthogonal_summary{suffix}.csv")
    with open(out_csv, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(
            f,
            fieldnames=["variant", "n", "ok", "fault", "UABR", "CI95", "main_fault_dist", "source"],
        )
        w.writeheader()
        w.writerows(out_rows)

    out_md = os.path.join(args.results_dir, f"e2_orthogonal_summary{suffix}.md")
    with open(out_md, "w", encoding="utf-8", newline="\n") as f:
        f.write("# E2+ Orthogonal Summary\n\n")
        f.write("| variant | n | ok | fault | UABR | 95%CI | main_fault_dist | source |\n")
        f.write("|---|---:|---:|---:|---:|---|---|---|\n")
        for r in out_rows:
            f.write(
                f"| {r['variant']} | {r['n']} | {r['ok']} | {r['fault']} | {r['UABR']} | {r['CI95']} | {r['main_fault_dist']} | `{r['source']}` |\n"
            )
        if missing:
            f.write("\n## Missing Files\n")
            for m in missing:
                f.write(f"- `{m}`\n")

    print(f"Wrote {out_csv}")
    print(f"Wrote {out_md}")
    if missing:
        print("Missing files:")
        for m in missing:
            print(f"  - {m}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
