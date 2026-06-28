"""
Regenerate Fig.6–Fig.10 as publication-quality vector graphics (JSA style).

JSA style guide compliance:
  - Monochrome blue-grey base with ≤3 accent colors
  - Line width 1.5pt, markers size 5, no marker fill
  - Error bars: black, capsize=3, linewidth=0.8
  - Axis labels: "Metric (Unit)" format, 9pt
  - No gradients, shadows, or decoration
  - Export as PDF only

Usage: python gen_figures_nature.py
"""
import csv
import os
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
from matplotlib.patches import Patch
from matplotlib.lines import Line2D
import numpy as np

# Shared JSA style
from fig_style import (
    FIGDIR, RESULT,
    C_BLUE, C_RED, C_GREEN, C_TEAL, C_GREY, C_TEXT, C_LIGHT,
    COL1, COL15, COL2, HATCHES,
    save_pub, wilson_ci, error_bars, panel_label,
)


# ═════════════════════════════════════════════════════════════════════════════
# Fig.6: Compression — ALL 113 tasks
# Scatter (LIR vs JSON bytes) + ratio histogram
# ═════════════════════════════════════════════════════════════════════════════

def fig6_compression():
    mir_bytes, json_bytes = {}, {}
    csv_path = os.path.join(RESULT, 'TOKEN', 'token_compare_v3_tasks_v2.csv')
    with open(csv_path, newline='', encoding='utf-8-sig') as f:
        for row in csv.DictReader(f):
            tid, fmt = row['task_id'], row['format']
            b = int(row['output_bytes'])
            if fmt == 'MIR': mir_bytes[tid] = b
            elif fmt == 'JSON': json_bytes[tid] = b

    common = sorted(set(mir_bytes) & set(json_bytes))
    m = np.array([mir_bytes[t] for t in common])
    j = np.array([json_bytes[t] for t in common])
    ratios = j / m
    median_ratio = np.median(ratios)
    mean_ratio = ratios.mean()

    fig, (ax_main, ax_hist) = plt.subplots(
        1, 2, figsize=(3.6, 2.6),
        gridspec_kw={'width_ratios': [3, 1], 'wspace': 0.08},
        layout='constrained'
    )

    # Hero scatter: all points in JSA blue, no viridis
    ax_main.scatter(m, j, c=C_BLUE, s=16, alpha=0.7,
                    edgecolors='white', linewidths=0.3, zorder=3)

    # y=x reference
    lim = max(m.max(), j.max()) * 1.05
    ax_main.plot([40, lim], [40, lim], '--', color=C_GREY,
                 linewidth=0.8, alpha=0.5, zorder=1, label='y = x')

    # Median ratio line (single reference; mean is reported in the stats box)
    x_fit = np.linspace(40, m.max() * 1.1, 100)
    ax_main.plot(x_fit, x_fit * median_ratio, '-', color=C_RED,
                 linewidth=1.5, alpha=0.8, zorder=2,
                 label=f'Median {median_ratio:.1f}×')

    ax_main.set_xlabel('LIR output (bytes)')
    ax_main.set_ylabel('JSON output (bytes)')
    ax_main.set_xlim(40, 165)
    ax_main.set_ylim(40, 560)
    ax_main.legend(fontsize=7, loc='upper left', frameon=False)

    # Stats box (upper-right: the empty quadrant, clear of the y=x line at
    # the bottom-right and the steep median line; legend sits upper-left)
    ax_main.text(0.97, 0.97,
                 f'n = {len(common)}\nMean {ratios.mean():.1f}×\nMedian {median_ratio:.1f}×',
                 transform=ax_main.transAxes, fontsize=7, va='top', ha='right',
                 bbox=dict(boxstyle='round,pad=0.3', facecolor='white',
                           edgecolor=C_GREY, alpha=0.9))

    # Side histogram
    ax_hist.hist(ratios, bins=18, orientation='horizontal',
                 color=C_BLUE, alpha=0.7, edgecolor='white', linewidth=0.3)
    ax_hist.axhline(median_ratio, color=C_RED, linewidth=1, linestyle='-')
    ax_hist.set_xlabel('Count', fontsize=7)
    ax_hist.set_ylabel('Ratio (JSON / LIR)', fontsize=7)
    ax_hist.yaxis.set_label_position('right')
    ax_hist.yaxis.tick_right()
    ax_hist.set_ylim(1, max(7, ratios.max() * 1.05))
    ax_hist.tick_params(labelsize=7)
    ax_hist.invert_xaxis()

    save_pub(fig, 'Fig6_e1_compression')
    print(f'Fig.6 — {len(common)} tasks, median ratio {median_ratio:.1f}×.')


# ═════════════════════════════════════════════════════════════════════════════
# Fig.7: Ablation — (a) fault distribution, (b) UABR + CI
# ═════════════════════════════════════════════════════════════════════════════

def fig7_combined_ablation():
    csv_path = os.path.join(RESULT, 'E2_orthogonal', 'e2_orthogonal_summary_final.csv')
    variants, variant_fault_dist = [], []
    uabr_vals, fault_vals, n_vals, ci_lo, ci_hi = [], [], [], [], []

    with open(csv_path, newline='', encoding='utf-8') as f:
        for row in csv.DictReader(f):
            variants.append(row['variant'])
            dist = {}
            for item in row['main_fault_dist'].split(','):
                code, count = item.split(':')
                dist[int(code)] = int(count)
            variant_fault_dist.append(dist)
            uabr_vals.append(float(row['UABR']))
            fault_vals.append(int(row['fault']))
            n_vals.append(int(row['n']))
            ci_str = row['CI95'].strip('[]" ')
            lo, hi = ci_str.split(',')
            ci_lo.append(float(lo))
            ci_hi.append(float(hi))

    all_codes = sorted(set(c for d in variant_fault_dist for c in d))
    code_labels = {
        5: 'F5: Unauthorized IOW', 10: 'F10: Invalid opcode',
        11: 'F11: Bad varint', 13: 'F13: Bad encoding',
        14: 'F14: Stack overflow', 22: 'F22: Step limit',
        23: 'F23: Call depth',
    }
    variant_labels = {
        'a0_base_guarded': 'All guarded', 'a1_no_auth_only': 'No auth',
        'a2_no_load_validator_only': 'No validator',
        'a3_no_step_limit_only': 'No step-limit',
        'a4_no_call_depth_only': 'No call-depth',
        'a5_no_bad_encoding_fault_only': 'No bad-enc',
    }
    labels_short = [variant_labels.get(v, v) for v in variants]

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(COL2, 2.8), layout='constrained')

    # Panel (a): Stacked fault distribution — JSA palette, max 4-5 colors
    x = np.arange(len(variants))
    bottom = np.zeros(len(variants))
    # Use JSA blue family + red for the fault types
    fault_colors = [C_BLUE, C_TEAL, C_GREEN, C_GREY, C_RED, '#D4756A', '#E9A6A1']
    for i, code in enumerate(all_codes):
        vals = [d.get(code, 0) for d in variant_fault_dist]
        ax1.bar(x, vals, bottom=bottom, label=code_labels.get(code, f'F{code}'),
                color=fault_colors[i % len(fault_colors)],
                hatch=HATCHES[i % len(HATCHES)],
                edgecolor='white', linewidth=0.3, width=0.6)
        bottom += np.array(vals)

    ax1.set_xlabel('Ablation variant')
    ax1.set_ylabel('Fault count')
    ax1.set_xticks(x)
    ax1.set_xticklabels(labels_short, rotation=25, ha='right', fontsize=6)
    ax1.set_ylim(0, bottom.max() * 1.42)
    ax1.legend(fontsize=5.5, loc='upper center', ncol=4, frameon=False,
               columnspacing=0.8, handletextpad=0.4,
               bbox_to_anchor=(0.5, 1.0))
    panel_label(ax1, '(a)', x=0.01, y=0.95)

    # Panel (b): UABR + Fault rate with CI
    w = 0.35
    fault_rates = [f / n for f, n in zip(fault_vals, n_vals)]

    uabr_err = [(max(0, v - lo), max(0, hi - v)) for v, lo, hi in zip(uabr_vals, ci_lo, ci_hi)]
    fr_err = [error_bars(f/n, n) for f, n in zip(fault_vals, n_vals)]

    bars_u = ax2.bar(x - w/2, uabr_vals, w, label='UABR',
                     color=C_BLUE, hatch='////', edgecolor='white', linewidth=0.5)
    bars_f = ax2.bar(x + w/2, fault_rates, w, label='Fault rate',
                     color=C_RED, hatch='....', edgecolor='white', linewidth=0.5)

    ax2.errorbar(x - w/2, uabr_vals,
                 yerr=[[e[0] for e in uabr_err], [e[1] for e in uabr_err]],
                 fmt='none', ecolor=C_TEXT, elinewidth=0.8, capsize=3, capthick=0.8)
    ax2.errorbar(x + w/2, fault_rates,
                 yerr=[[e[0] for e in fr_err], [e[1] for e in fr_err]],
                 fmt='none', ecolor=C_TEXT, elinewidth=0.8, capsize=3, capthick=0.8)

    ax2.set_xlabel('Ablation variant')
    ax2.set_ylabel('Rate')
    ax2.set_xticks(x)
    ax2.set_xticklabels(labels_short, rotation=25, ha='right', fontsize=6)
    ax2.set_ylim(0, 1.18)
    ax2.legend(fontsize=7, loc='lower center', ncol=2, frameon=False,
               bbox_to_anchor=(0.5, 1.02), columnspacing=1.6, handletextpad=0.4)

    for bar, v in zip(bars_u, uabr_vals):
        ax2.text(bar.get_x() + bar.get_width()/2, v + 0.035, f'{v:.3f}',
                 ha='center', va='bottom', fontsize=6, color=C_BLUE, rotation=90)
    for bar, v in zip(bars_f, fault_rates):
        ax2.text(bar.get_x() + bar.get_width()/2, v + 0.035, f'{v:.3f}',
                 ha='center', va='bottom', fontsize=6, color=C_RED, rotation=90)
    panel_label(ax2, '(b)', x=0.01, y=0.95)

    save_pub(fig, 'Fig7_e2_ablation_combined')
    print('Fig.7 — with CI error bars.')


# ═════════════════════════════════════════════════════════════════════════════
# Fig.7 stacked: same data, constrained layout, output → Fig7_e2_ablation_stacked
# ═════════════════════════════════════════════════════════════════════════════

def fig7_stacked():
    csv_path = os.path.join(RESULT, 'E2_orthogonal', 'e2_orthogonal_summary_final.csv')
    variants, variant_fault_dist = [], []
    uabr_vals, fault_vals, n_vals, ci_lo, ci_hi = [], [], [], [], []

    with open(csv_path, newline='', encoding='utf-8') as f:
        for row in csv.DictReader(f):
            variants.append(row['variant'])
            dist = {}
            for item in row['main_fault_dist'].split(','):
                code, count = item.split(':')
                dist[int(code)] = int(count)
            variant_fault_dist.append(dist)
            uabr_vals.append(float(row['UABR']))
            fault_vals.append(int(row['fault']))
            n_vals.append(int(row['n']))
            ci_str = row['CI95'].strip('[]" ')
            lo, hi = ci_str.split(',')
            ci_lo.append(float(lo))
            ci_hi.append(float(hi))

    all_codes = sorted(set(c for d in variant_fault_dist for c in d))
    code_labels = {
        5: 'F5: Unauthorized IOW', 10: 'F10: Invalid opcode',
        11: 'F11: Bad varint', 13: 'F13: Bad encoding',
        14: 'F14: Stack overflow', 22: 'F22: Step limit',
        23: 'F23: Call depth',
    }
    variant_labels = {
        'a0_base_guarded': 'All guarded', 'a1_no_auth_only': 'No auth',
        'a2_no_load_validator_only': 'No validator',
        'a3_no_step_limit_only': 'No step-limit',
        'a4_no_call_depth_only': 'No call-depth',
        'a5_no_bad_encoding_fault_only': 'No bad-enc',
    }
    labels_short = [variant_labels.get(v, v) for v in variants]

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(COL2, 2.8), layout='constrained')

    # Panel (a): stacked fault distribution
    x = np.arange(len(variants))
    bottom = np.zeros(len(variants))
    fault_colors = [C_BLUE, C_TEAL, C_GREEN, C_GREY, C_RED, '#D4756A', '#E9A6A1']
    for i, code in enumerate(all_codes):
        vals = [d.get(code, 0) for d in variant_fault_dist]
        ax1.bar(x, vals, bottom=bottom, label=code_labels.get(code, f'F{code}'),
                color=fault_colors[i % len(fault_colors)],
                hatch=HATCHES[i % len(HATCHES)],
                edgecolor='white', linewidth=0.3, width=0.6)
        bottom += np.array(vals)

    ax1.set_xlabel('Ablation variant')
    ax1.set_ylabel('Fault count')
    ax1.set_xticks(x)
    ax1.set_xticklabels(labels_short, rotation=25, ha='right')
    ax1.set_ylim(0, bottom.max() * 1.12)
    ax1.legend(fontsize=5.5, loc='lower center', ncol=4, frameon=False,
               columnspacing=0.8, handletextpad=0.4, bbox_to_anchor=(0.5, 1.02))
    panel_label(ax1, '(a)', x=0.01, y=0.95)

    # Panel (b): grouped UABR + fault rate with Wilson CI
    w = 0.35
    fault_rates = [f / n for f, n in zip(fault_vals, n_vals)]
    uabr_err = [(max(0, v - lo), max(0, hi - v)) for v, lo, hi in zip(uabr_vals, ci_lo, ci_hi)]
    fr_err = [error_bars(f / n, n) for f, n in zip(fault_vals, n_vals)]

    bars_u = ax2.bar(x - w / 2, uabr_vals, w, label='UABR',
                     color=C_BLUE, edgecolor='black', linewidth=0.5)
    bars_f = ax2.bar(x + w / 2, fault_rates, w, label='Fault rate',
                     color=C_RED, edgecolor='black', linewidth=0.5)

    ax2.errorbar(x - w / 2, uabr_vals,
                 yerr=[[e[0] for e in uabr_err], [e[1] for e in uabr_err]],
                 fmt='none', ecolor=C_TEXT, elinewidth=0.8, capsize=3, capthick=0.8)
    ax2.errorbar(x + w / 2, fault_rates,
                 yerr=[[e[0] for e in fr_err], [e[1] for e in fr_err]],
                 fmt='none', ecolor=C_TEXT, elinewidth=0.8, capsize=3, capthick=0.8)

    ax2.set_xlabel('Ablation variant')
    ax2.set_ylabel('Rate')
    ax2.set_xticks(x)
    ax2.set_xticklabels(labels_short, rotation=25, ha='right')
    ax2.set_ylim(0, 1.18)
    ax2.legend(fontsize=7, loc='lower center', ncol=2, frameon=False,
               bbox_to_anchor=(0.5, 1.02), columnspacing=1.6, handletextpad=0.4)

    panel_label(ax2, '(b)', x=0.01, y=0.95)

    save_pub(fig, 'Fig7_e2_ablation_stacked')
    print('Fig.7 stacked — with CI error bars.')


# ═════════════════════════════════════════════════════════════════════════════
# Fig.8: SCR — fair JSON baseline + Wilson CI
# ═════════════════════════════════════════════════════════════════════════════

def fig8_scr():
    fair_path = os.path.join(RESULT, 'E4_json_real', 'e4_json_real_matrix_fair_final.csv')
    fair_data = {}
    with open(fair_path, newline='', encoding='utf-8-sig') as f:
        for row in csv.DictReader(f):
            fair_data[row['group']] = {
                'scr': float(row['scr']),
                'rtt': float(row['rtt_ms'].split('±')[0]),
            }

    lir_path = os.path.join(RESULT, 'E4', 'e4_summary.csv')
    lir_data = {}
    with open(lir_path, newline='', encoding='utf-8') as f:
        for row in csv.DictReader(f):
            lir_data[row['group']] = {
                'scr': float(row['scr']),
                'rtt': float(row['rtt_ms_mean']),
            }

    groups = ['G0_json_real_with_o', 'G3_m_with_o', 'G2_m_no_o', 'G4_m_with_o_no_retry']
    gl = {
        'G0_json_real_with_o': 'JSON\n(with opt)',
        'G2_m_no_o': 'LIR\n(no opt)',
        'G3_m_with_o': 'LIR\n(with opt)',
        'G4_m_with_o_no_retry': 'LIR\n(no retry)',
    }

    scr, rtt = [], []
    for g in groups:
        d = fair_data[g] if g.startswith('G0') else lir_data[g]
        scr.append(d['scr'])
        rtt.append(d['rtt'])

    labels = [gl[g] for g in groups]
    n_per_group = 100

    ci_lo = [max(0, p - wilson_ci(p, n_per_group)[0]) for p in scr]
    ci_hi = [max(0, wilson_ci(p, n_per_group)[1] - p) for p in scr]

    fig, ax1 = plt.subplots(figsize=(COL1, 2.4), layout='constrained')
    x = np.arange(len(groups))
    w = 0.5

    bar_colors = [C_RED, C_BLUE, C_BLUE, C_BLUE]
    bars = ax1.bar(x, scr, w, color=bar_colors,
                   edgecolor='black', linewidth=0.5)
    ax1.errorbar(x, scr, yerr=[ci_lo, ci_hi], fmt='none',
                 ecolor=C_TEXT, elinewidth=0.8, capsize=3, capthick=0.8)

    ax1.set_ylabel('SCR')
    ax1.set_xticks(x)
    ax1.set_xticklabels(labels, fontsize=7)
    ax1.set_ylim(0, 1.25)

    for bar, val in zip(bars, scr):
        ax1.text(bar.get_x() + bar.get_width() / 2, val + 0.05,
                 f'{val:.2f}', ha='center', va='bottom', fontsize=8,
                 fontweight='bold', color=C_TEXT)

    # RTT overlay
    ax2 = ax1.twinx()
    ax2.plot(x, rtt, 'D-', color=C_RED, markersize=5, linewidth=1.5,
             markeredgecolor=C_RED, markerfacecolor='white', markeredgewidth=0.8, zorder=4)
    ax2.set_ylabel('Mean RTT (ms)', color=C_RED, fontsize=9)
    ax2.tick_params(axis='y', labelcolor=C_RED, labelsize=8)
    ax2.spines['top'].set_visible(False)

    for xi, yi in zip(x, rtt):
        ax2.annotate(f'{yi:.0f}', xy=(xi, yi), xytext=(7, 5),
                     textcoords='offset points', fontsize=7,
                     color=C_RED, ha='left', va='bottom', zorder=6,
                     bbox=dict(boxstyle='round,pad=0.12', facecolor='white',
                               edgecolor='none', alpha=0.85))

    handles = [Patch(facecolor=C_BLUE, label='SCR (LIR)'),
               Patch(facecolor=C_RED, label='SCR (JSON)'),
               Line2D([0], [0], color=C_RED, marker='D', markersize=4,
                      markerfacecolor='white', label='RTT')]
    ax1.legend(handles=handles, fontsize=7, loc='upper center',
               ncol=3, frameon=False, bbox_to_anchor=(0.5, 1.16),
               columnspacing=1.0, handletextpad=0.4)

    save_pub(fig, 'Fig8_e4_scr')
    print('Fig.8 — fair JSON baseline + Wilson CI.')


# ═════════════════════════════════════════════════════════════════════════════
# Fig.9: SAFE curve — Wilson CI error bars
# ═════════════════════════════════════════════════════════════════════════════

def fig9_scr_curve():
    csv_path = os.path.join(RESULT, 'E5_prior', 'e5_prior_matrix_final.csv')
    g_priors, g_safe, g_n = [], [], []
    ng_priors, ng_safe, ng_n = [], [], []

    with open(csv_path, newline='', encoding='utf-8') as f:
        for row in csv.DictReader(f):
            p = float(row['fault_prior'])
            s = float(row['safe_ratio'])
            n = int(row['n'])
            if row['variant'] == 'guarded':
                g_priors.append(p); g_safe.append(s); g_n.append(n)
            else:
                ng_priors.append(p); ng_safe.append(s); ng_n.append(n)

    g_err = [(max(0, s - wilson_ci(s, n)[0]), max(0, wilson_ci(s, n)[1] - s))
             for s, n in zip(g_safe, g_n)]
    ng_err = [(max(0, s - wilson_ci(max(s, 0.001), n)[0]),
               max(0, wilson_ci(max(s, 0.001), n)[1] - s))
              for s, n in zip(ng_safe, ng_n)]

    fig, ax = plt.subplots(figsize=(COL1, 2.4), layout='constrained')

    # Guarded: blue circles, solid line, JSA style
    ax.errorbar(g_priors, g_safe,
                yerr=[[e[0] for e in g_err], [e[1] for e in g_err]],
                fmt='o-', color=C_BLUE, linewidth=1.5, markersize=5,
                markeredgecolor=C_BLUE, markerfacecolor='white', markeredgewidth=0.8,
                ecolor=C_BLUE, elinewidth=0.8, capsize=3, capthick=0.8,
                label='Guarded', zorder=3)

    # No-guard: red squares, dashed line
    ax.errorbar(ng_priors, ng_safe,
                yerr=[[e[0] for e in ng_err], [e[1] for e in ng_err]],
                fmt='s--', color=C_RED, linewidth=1.5, markersize=5,
                markeredgecolor=C_RED, markerfacecolor='white', markeredgewidth=0.8,
                ecolor=C_RED, elinewidth=0.8, capsize=3, capthick=0.8,
                label='No-guard', zorder=3)

    ax.set_xlabel('Fault prior')
    ax.set_ylabel('SAFE ratio')
    ax.set_xlim(0.05, 0.95)
    ax.set_ylim(-0.05, 1.1)
    ax.xaxis.set_major_formatter(ticker.PercentFormatter(1.0))
    ax.legend(fontsize=7, loc='upper left', frameon=False)

    save_pub(fig, 'Fig9_scr_curve')
    print('Fig.9 — Wilson CI error bars.')


# ═════════════════════════════════════════════════════════════════════════════
# Fig.10: Generation/repair results + three-way token cost
# ═════════════════════════════════════════════════════════════════════════════

def fig10_gen_token():
    stages = ['IR valid', 'Compile', 'Verify', 'Execute', 'Success@1', 'Success@2']
    stage_vals = [1.000, 1.000, 1.000, 1.000, 0.885, 0.115]
    n_tasks = 113
    stage_err = [(0, 0), (0, 0), (0, 0), (0, 0),
                 error_bars(0.885, n_tasks), error_bars(0.115, n_tasks)]

    fmts = ['LIR', 'JSON', 'Python']
    in_tok  = [161.15, 83.15, 85.15]
    out_tok = [40.00, 77.54, 17.19]

    fig, (axa, axb) = plt.subplots(1, 2, figsize=(COL2, 2.8),
                                   gridspec_kw={'width_ratios': [1, 1], 'wspace': 0.28},
                                   layout='constrained')

    # Panel (a): pipeline + repair bars
    xa = np.arange(len(stages))
    colors_a = [C_BLUE]*4 + [C_TEAL, C_TEAL]
    bars_a = axa.bar(xa, stage_vals, 0.62, color=colors_a,
                     edgecolor='black', linewidth=0.5)
    axa.errorbar(xa, stage_vals,
                 yerr=[[e[0] for e in stage_err], [e[1] for e in stage_err]],
                 fmt='none', ecolor=C_TEXT, elinewidth=0.8, capsize=3, capthick=0.8)
    for xi, v in zip(xa, stage_vals):
        axa.text(xi, v + 0.03, f'{v:.3f}', ha='center', va='bottom',
                 fontsize=7, color=C_TEXT)
    axa.set_ylabel('Rate')
    axa.set_ylim(0, 1.22)
    axa.set_xticks(xa)
    axa.set_xticklabels(stages, rotation=20, ha='right', fontsize=7)
    panel_label(axa, '(a)')

    # Panel (b): three-way token cost
    xb = np.arange(len(fmts))
    w = 0.6
    bars_out = axb.bar(xb, out_tok, w, color=C_BLUE, hatch='////',
                       edgecolor='black', linewidth=0.5, label='Output tokens')
    bars_in = axb.bar(xb, in_tok, w, bottom=out_tok, color=C_LIGHT, hatch='....',
                      edgecolor='black', linewidth=0.5,
                      label='Input tokens (system prompt)')
    # JSON output bar in red
    bars_out[1].set_color(C_RED)
    for xi, o, i in zip(xb, out_tok, in_tok):
        axb.text(xi, o / 2, f'{o:.1f}', ha='center', va='center',
                 fontsize=7, color='white', fontweight='bold')
        axb.text(xi, o + i + 4, f'{o + i:.1f}', ha='center', va='bottom',
                 fontsize=7, color=C_TEXT)
    axb.set_ylabel('Tokens')
    axb.set_xticks(xb)
    axb.set_xticklabels(fmts, fontsize=9)
    axb.set_ylim(0, max(a + b for a, b in zip(in_tok, out_tok)) * 1.28)
    axb.legend(fontsize=7, loc='upper center', ncol=1, frameon=False,
               bbox_to_anchor=(0.5, 1.02))
    panel_label(axb, '(b)')

    save_pub(fig, 'Fig10_combined_gen_token')
    print('Fig.10 — gen/repair + token cost (paper-authoritative values).')


# ═════════════════════════════════════════════════════════════════════════════
# Fig.11: Forest plot — headline success rates with 95% Wilson CIs
# Consolidates TSR / SCR / UABR point estimates scattered across the tables
# ═════════════════════════════════════════════════════════════════════════════
def fig11_forest():
    # (label, k, n, group) — values authoritative against latex/verify.py
    rows = [
        ('LIR deterministic (113)',        113, 113, 'gen'),
        ('LIR best-of-$K$, $K{=}3$ (113)', 111, 113, 'gen'),
        ('LIR random (600)',               582, 600, 'gen'),
        ('deepseek-v4-pro random (600)',   592, 600, 'gen'),
        ('LIR real-world (29)',             23,  29, 'gen'),
        ('JSON real-world (29)',            25,  29, 'gen'),
        ('LIR closed-loop (10)',             6,  10, 'gen'),
        ('UABR adversarial (8000)',       8000,8000, 'safe'),
    ]
    colors = {'gen': C_BLUE, 'safe': C_GREEN}
    labels, points, los, his, cols = [], [], [], [], []
    for label, k, n, grp in rows:
        p = k / n
        lo, hi = wilson_ci(p, n)
        labels.append(label)
        points.append(p)
        los.append(p - lo)
        his.append(hi - p)
        cols.append(colors[grp])

    # Plot top-to-bottom in listed order
    y = np.arange(len(rows))[::-1]
    fig, ax = plt.subplots(figsize=(3.6, 2.8), layout='constrained')
    ax.errorbar(points, y, xerr=[los, his], fmt='none',
                ecolor=C_GREY, elinewidth=0.9, capsize=3, capthick=0.9, zorder=2)
    ax.scatter(points, y, c=cols, s=26, edgecolors='white',
               linewidths=0.4, zorder=3)

    for yi, (label, k, n, _), p in zip(y, rows, points):
        ax.text(0.012, yi + 0.30, f'{p:.3f} ({k}/{n})',
                fontsize=6.5, color=C_TEXT, va='center', ha='left')

    ax.axvline(1.0, color=C_GREY, linewidth=0.7, linestyle='--', alpha=0.6, zorder=1)
    ax.set_yticks(y)
    ax.set_yticklabels(labels, fontsize=7)
    ax.set_xlabel('Success rate (95\\% Wilson CI)')
    ax.set_xlim(0.0, 1.05)
    ax.set_ylim(-0.6, len(rows) - 0.4)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)

    legend = [
        Line2D([0], [0], marker='o', color='w', markerfacecolor=C_BLUE,
               markersize=6, label='Generation TSR'),
        Line2D([0], [0], marker='o', color='w', markerfacecolor=C_GREEN,
               markersize=6, label='Safety UABR'),
    ]
    ax.legend(handles=legend, fontsize=6.5, loc='lower center',
              bbox_to_anchor=(0.5, 1.0), ncol=2, frameon=False,
              columnspacing=1.6, handletextpad=0.4)

    save_pub(fig, 'Fig11_forest_rates')
    print('Fig.11 — forest plot of headline rates with Wilson CIs.')


# ═════════════════════════════════════════════════════════════════════════════

if __name__ == '__main__':
    os.makedirs(FIGDIR, exist_ok=True)
    fig6_compression()
    fig7_combined_ablation()
    fig7_stacked()
    fig8_scr()
    fig9_scr_curve()
    fig10_gen_token()
    fig11_forest()
    print('All figures regenerated (JSA style).')
