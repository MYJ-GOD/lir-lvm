#!/usr/bin/env python3
import argparse
import csv
import glob
import os


def read_summary(path):
    with open(path, 'r', encoding='utf-8') as f:
        r = list(csv.DictReader(f))
    return r[0] if r else None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--results-dir', default='论文分区/ccfc/result/E5_prior')
    ap.add_argument('--tag', default='')
    args = ap.parse_args()

    pats = [
        os.path.join(args.results_dir, 'scr_prior_summary_guarded_p*.csv'),
        os.path.join(args.results_dir, 'scr_prior_summary_noguard_p*.csv'),
    ]
    files = []
    for p in pats:
        files.extend(glob.glob(p))

    rows = []
    for fp in sorted(files):
        if '_20' in os.path.basename(fp):
            # skip timestamped files, keep latest aliases
            continue
        row = read_summary(fp)
        if row:
            rows.append(row)

    rows.sort(key=lambda x: (x.get('variant',''), float(x.get('fault_prior','0'))))

    out_csv = os.path.join(args.results_dir, f'e5_prior_matrix{("_"+args.tag) if args.tag else ""}.csv')
    with open(out_csv, 'w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()) if rows else [
            'variant','fault_prior','prior_key','n','tp','fp','fn','tn','precision','recall','fpr','fnr','ok_ratio','safe_ratio','rtt_ms_mean','rtt_ms_std','unknown_count','detail_file'
        ])
        w.writeheader()
        if rows:
            w.writerows(rows)

    out_md = os.path.join(args.results_dir, f'e5_prior_matrix{("_"+args.tag) if args.tag else ""}.md')
    with open(out_md, 'w', encoding='utf-8', newline='\n') as f:
        f.write('# E5 Prior Matrix\n\n')
        f.write('| variant | prior | n | TP | FP | FN | TN | Precision | Recall | FPR | FNR | OK ratio | SAFE ratio | RTT mean±SD (ms) | source |\n')
        f.write('|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---|\n')
        for r in rows:
            f.write(
                f"| {r['variant']} | {float(r['fault_prior']):.1f} | {r['n']} | {r['tp']} | {r['fp']} | {r['fn']} | {r['tn']} | {float(r['precision']):.3f} | {float(r['recall']):.3f} | {float(r['fpr']):.3f} | {float(r['fnr']):.3f} | {float(r['ok_ratio']):.3f} | {float(r['safe_ratio']):.3f} | {r['rtt_ms_mean']}±{r['rtt_ms_std']} | `{os.path.basename(r['detail_file'])}` |\n"
            )

    print(f'Wrote {out_csv}')
    print(f'Wrote {out_md}')


if __name__ == '__main__':
    main()
