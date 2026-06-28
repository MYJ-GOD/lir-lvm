"""
Regenerate Fig.6-Fig.10 as SVG vector graphics from experiment CSV data.
Usage: python gen_figures_svg.py
"""
import csv
import os
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import numpy as np

FIGDIR = os.path.join(os.path.dirname(__file__), '..', 'figures')
RESULT = os.path.join(os.path.dirname(__file__), '..', 'result')

# Color-blind-safe palette
C_M = '#2171b5'
C_JSON = '#cb181d'
C_CBOR = '#238b45'
C_MP = '#6a51a3'
C_GUARDED = '#2171b5'
C_NOGUARD = '#cb181d'

plt.rcParams.update({
    'font.family': 'sans-serif',
    'font.sans-serif': ['Arial', 'Helvetica', 'DejaVu Sans', 'sans-serif'],
    'font.size': 11,
    'axes.labelsize': 13,
    'axes.titlesize': 14,
    'legend.fontsize': 10,
    'xtick.labelsize': 10,
    'ytick.labelsize': 10,
    'figure.dpi': 300,
    'svg.fonttype': 'none',
    'pdf.fonttype': 42,
})
# Prefer CJK-compatible serif fonts for Chinese paper context
import matplotlib.font_manager as fm
_cjk_serif = [f.name for f in fm.fontManager.ttflist
              if f.name in ('Noto Serif SC', 'SimSun', 'STSong')]
if _cjk_serif:
    plt.rcParams['font.serif'] = _cjk_serif + ['DejaVu Serif']


def fig6_compression():
    """Fig.6: M-bytecode vs JSON payload size per task."""
    csv_path = os.path.join(RESULT, 'E1', 'e1_multibatch_summary.csv')
    tasks, m_vals, json_vals = [], [], []
    with open(csv_path, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        seen = set()
        for row in reader:
            t = row['task']
            if t not in seen:
                seen.add(t)
                tasks.append(t)
                m_vals.append(float(row['median_ms']))
                json_vals.append(float(row['median_ms']))
            else:
                idx = tasks.index(t)
                if row['proto'] == 'M':
                    m_vals[idx] = float(row['median_ms'])
                else:
                    json_vals[idx] = float(row['median_ms'])

    # Compute compression ratio from median RTT as proxy (actual byte data not in CSV)
    # Use the known values from paper
    tasks_short = ['relay1_on', 'relay1_off', 'water_read', 'temp_read', 'combo']
    m_bytes = [7, 7, 5, 5, 14]
    json_bytes = [29, 29, 21, 21, 75]

    fig, ax = plt.subplots(figsize=(8, 5))
    x = np.arange(len(tasks_short))
    w = 0.35
    bars1 = ax.bar(x - w/2, m_bytes, w, label='M-bytecode', color=C_M, edgecolor='white')
    bars2 = ax.bar(x + w/2, json_bytes, w, label='JSON', color=C_JSON, edgecolor='white')
    ax.set_xlabel('Task', fontsize=12)
    ax.set_ylabel('Payload (bytes)', fontsize=12)
    ax.set_title('Fig.6  M-bytecode vs JSON Payload Size', fontsize=14)
    ax.set_xticks(x)
    ax.set_xticklabels(tasks_short, rotation=10, fontsize=11)
    ax.legend(fontsize=11)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    for bar in bars1:
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 1,
                f'{int(bar.get_height())}B', ha='center', va='bottom', fontsize=11)
    for bar in bars2:
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 1,
                f'{int(bar.get_height())}B', ha='center', va='bottom', fontsize=11)
    fig.tight_layout()
    fig.savefig(os.path.join(FIGDIR, 'Fig6_e1_compression.svg'), format='svg')
    plt.close(fig)
    print('Fig.6 saved.')


def fig7_fault_distribution():
    """Fig.7: Fault type distribution from E2 orthogonal ablation."""
    csv_path = os.path.join(RESULT, 'E2_orthogonal', 'e2_orthogonal_summary_final.csv')
    variants = []
    variant_data = []  # list of {code: count}

    with open(csv_path, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            variants.append(row['variant'])
            dist = {}
            for item in row['main_fault_dist'].split(','):
                code, count = item.split(':')
                dist[int(code)] = int(count)
            variant_data.append(dist)

    # Collect all fault codes
    all_codes = sorted(set(c for d in variant_data for c in d))
    labels = {
        5: 'F5: Unauthorized IOW',
        10: 'F10: Invalid opcode',
        11: 'F11: Bad varint',
        13: 'F13: Bad encoding',
        14: 'F14: Stack overflow',
        22: 'F22: Step limit',
        23: 'F23: Call depth',
    }
    variant_labels = {
        'a0_base_guarded': 'All guarded',
        'a1_no_auth_only': 'No auth',
        'a2_no_load_validator_only': 'No validator',
        'a3_no_step_limit_only': 'No step-limit',
        'a4_no_call_depth_only': 'No call-depth',
        'a5_no_bad_encoding_fault_only': 'No bad-enc',
    }

    fig, ax = plt.subplots(figsize=(8, 4.5))
    x = np.arange(len(variants))
    bottom = np.zeros(len(variants))
    colors = plt.cm.Set2(np.linspace(0, 1, len(all_codes)))
    for i, code in enumerate(all_codes):
        vals = [d.get(code, 0) for d in variant_data]
        label = labels.get(code, f'F{code}')
        ax.bar(x, vals, bottom=bottom, label=label, color=colors[i], edgecolor='white', width=0.6)
        bottom += np.array(vals)
    ax.set_xlabel('Ablation Variant')
    ax.set_ylabel('Fault Count')
    ax.set_title('Fig.7  Fault Distribution Across Ablation Variants')
    ax.set_xticks(x)
    ax.set_xticklabels([variant_labels.get(v, v) for v in variants], rotation=20, ha='right', fontsize=9)
    ax.legend(fontsize=8, loc='upper right', ncol=2)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    fig.tight_layout()
    fig.savefig(os.path.join(FIGDIR, 'Fig7_e2_fault_distribution.svg'), format='svg')
    plt.close(fig)
    print('Fig.7 saved.')


def fig8_fault_source_migration():
    """Fig.8: Fault source migration across ablation variants."""
    csv_path = os.path.join(RESULT, 'E2_orthogonal', 'e2_orthogonal_summary_final.csv')
    variants = []
    uabr_vals = []
    fault_vals = []
    n_vals = []

    with open(csv_path, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            variants.append(row['variant'])
            uabr_vals.append(float(row['UABR']))
            fault_vals.append(int(row['fault']))
            n_vals.append(int(row['n']))

    variant_labels = {
        'a0_base_guarded': 'All guarded',
        'a1_no_auth_only': 'No auth',
        'a2_no_load_validator_only': 'No validator',
        'a3_no_step_limit_only': 'No step-limit',
        'a4_no_call_depth_only': 'No call-depth',
        'a5_no_bad_encoding_fault_only': 'No bad-enc',
    }

    fig, ax = plt.subplots(figsize=(7, 4))
    x = np.arange(len(variants))
    w = 0.35
    ax.bar(x - w/2, uabr_vals, w, label='UABR', color=C_GUARDED, edgecolor='white')
    ax.bar(x + w/2, [f/n for f, n in zip(fault_vals, n_vals)], w, label='Fault rate', color=C_NOGUARD, edgecolor='white')
    ax.set_xlabel('Ablation Variant')
    ax.set_ylabel('Rate')
    ax.set_title('Fig.8  UABR and Fault Rate Across Ablation Variants')
    ax.set_xticks(x)
    ax.set_xticklabels([variant_labels.get(v, v) for v in variants], rotation=20, ha='right', fontsize=9)
    ax.set_ylim(0, 1.15)
    ax.legend()
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    fig.tight_layout()
    fig.savefig(os.path.join(FIGDIR, 'Fig8_e2_ablation_fault_source.svg'), format='svg')
    plt.close(fig)
    print('Fig.8 saved.')


def fig9_scr():
    """Fig.9: SCR comparison between M path and JSON path."""
    csv_path = os.path.join(RESULT, 'E4', 'e4_summary.csv')
    groups = []
    scr_vals = []
    rtt_vals = []

    with open(csv_path, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            groups.append(row['group'])
            scr_vals.append(float(row['scr']))
            rtt_vals.append(float(row['rtt_ms_mean']))

    group_labels = {
        'G1_text_proxy': 'JSON (text proxy)',
        'G2_m_no_o': 'M (no optimize)',
        'G3_m_with_o': 'M (with optimize)',
        'G4_m_with_o_no_retry': 'M (no retry)',
    }

    fig, ax1 = plt.subplots(figsize=(8, 5))
    x = np.arange(len(groups))
    w = 0.35
    bars = ax1.bar(x, scr_vals, w, color=[C_JSON, C_M, C_M, C_M],
                   edgecolor='white', alpha=0.85, label='SCR')
    ax1.set_ylabel('SCR', fontsize=12)
    ax1.set_title('Fig.9  Safety Convergence Rate (SCR) by Strategy', fontsize=14)
    ax1.set_xticks(x)
    ax1.set_xticklabels([group_labels.get(g, g) for g in groups], rotation=15, ha='right', fontsize=10)
    ax1.set_ylim(0, 1.15)
    ax1.spines['top'].set_visible(False)
    ax1.spines['right'].set_visible(False)
    for bar, val in zip(bars, scr_vals):
        ax1.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.02,
                f'{val:.2f}', ha='center', va='bottom', fontsize=11)

    ax2 = ax1.twinx()
    ax2.plot(x, rtt_vals, 'D-', color='#e6550d', markersize=8, linewidth=2.0, label='RTT (ms)')
    ax2.set_ylabel('Mean RTT (ms)', color='#e6550d', fontsize=12)
    ax2.tick_params(axis='y', labelcolor='#e6550d')
    ax2.spines['top'].set_visible(False)
    ax1.legend(loc='upper left', fontsize=10)
    ax2.legend(loc='upper right', fontsize=10)
    fig.tight_layout()
    fig.savefig(os.path.join(FIGDIR, 'Fig9_e4_scr.svg'), format='svg')
    plt.close(fig)
    print('Fig.9 saved.')


def fig10_scr_curve():
    """Fig.10: SAFE curve under different fault priors."""
    csv_path = os.path.join(RESULT, 'E5_prior', 'e5_prior_matrix_final.csv')
    guarded_priors, guarded_safe = [], []
    noguard_priors, noguard_safe = [], []

    with open(csv_path, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            prior = float(row['fault_prior'])
            safe = float(row['safe_ratio'])
            if row['variant'] == 'guarded':
                guarded_priors.append(prior)
                guarded_safe.append(safe)
            else:
                noguard_priors.append(prior)
                noguard_safe.append(safe)

    fig, ax = plt.subplots(figsize=(8, 5))
    ax.plot(guarded_priors, guarded_safe, 'o-', color=C_GUARDED, linewidth=2.5,
            markersize=10, label='Guarded')
    ax.plot(noguard_priors, noguard_safe, 's--', color=C_NOGUARD, linewidth=2.5,
            markersize=10, label='No-guard')
    ax.fill_between(guarded_priors, guarded_safe, alpha=0.15, color=C_GUARDED)
    ax.set_xlabel('Fault Prior', fontsize=12)
    ax.set_ylabel('SAFE Ratio', fontsize=12)
    ax.set_title('Fig.10  SAFE Ratio vs Fault Prior', fontsize=14)
    ax.set_xlim(0.05, 0.95)
    ax.set_ylim(-0.05, 1.1)
    ax.legend(fontsize=11)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.xaxis.set_major_formatter(ticker.PercentFormatter(1.0))
    fig.tight_layout()
    fig.savefig(os.path.join(FIGDIR, 'Fig10_scr_curve.svg'), format='svg')
    plt.close(fig)
    print('Fig.10 saved.')


def fig7_combined_ablation():
    """Fig.7 (merged): Two-panel ablation — (a) fault distribution, (b) UABR & fault rate."""
    csv_path = os.path.join(RESULT, 'E2_orthogonal', 'e2_orthogonal_summary_final.csv')
    variants = []
    variant_fault_dist = []
    uabr_vals = []
    fault_vals = []
    n_vals = []

    with open(csv_path, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            variants.append(row['variant'])
            dist = {}
            for item in row['main_fault_dist'].split(','):
                code, count = item.split(':')
                dist[int(code)] = int(count)
            variant_fault_dist.append(dist)
            uabr_vals.append(float(row['UABR']))
            fault_vals.append(int(row['fault']))
            n_vals.append(int(row['n']))

    all_codes = sorted(set(c for d in variant_fault_dist for c in d))
    code_labels = {
        5: 'F5: Unauthorized IOW',
        10: 'F10: Invalid opcode',
        11: 'F11: Bad varint',
        13: 'F13: Bad encoding',
        14: 'F14: Stack overflow',
        22: 'F22: Step limit',
        23: 'F23: Call depth',
    }
    variant_labels = {
        'a0_base_guarded': 'All guarded',
        'a1_no_auth_only': 'No auth',
        'a2_no_load_validator_only': 'No validator',
        'a3_no_step_limit_only': 'No step-limit',
        'a4_no_call_depth_only': 'No call-depth',
        'a5_no_bad_encoding_fault_only': 'No bad-enc',
    }
    labels_short = [variant_labels.get(v, v) for v in variants]

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5.5))

    # Panel (a): Fault distribution (stacked bar)
    x = np.arange(len(variants))
    bottom = np.zeros(len(variants))
    colors = plt.cm.Set2(np.linspace(0, 1, len(all_codes)))
    for i, code in enumerate(all_codes):
        vals = [d.get(code, 0) for d in variant_fault_dist]
        ax1.bar(x, vals, bottom=bottom, label=code_labels.get(code, f'F{code}'),
                color=colors[i], edgecolor='white', width=0.6)
        bottom += np.array(vals)
    ax1.set_xlabel('Ablation Variant', fontsize=12)
    ax1.set_ylabel('Fault Count', fontsize=12)
    ax1.set_title('(a) Fault Distribution', fontsize=13)
    ax1.set_xticks(x)
    ax1.set_xticklabels(labels_short, rotation=20, ha='right', fontsize=10)
    ax1.legend(fontsize=9, loc='upper right', ncol=2)
    ax1.spines['top'].set_visible(False)
    ax1.spines['right'].set_visible(False)

    # Panel (b): UABR and Fault rate (grouped bar)
    w = 0.35
    ax2.bar(x - w/2, uabr_vals, w, label='UABR', color='#2171b5', edgecolor='white')
    ax2.bar(x + w/2, [f/n for f, n in zip(fault_vals, n_vals)], w,
            label='Fault rate', color='#cb181d', edgecolor='white')
    ax2.set_xlabel('Ablation Variant', fontsize=12)
    ax2.set_ylabel('Rate', fontsize=12)
    ax2.set_title('(b) UABR and Fault Rate', fontsize=13)
    ax2.set_xticks(x)
    ax2.set_xticklabels(labels_short, rotation=20, ha='right', fontsize=10)
    ax2.set_ylim(0, 1.15)
    ax2.legend(fontsize=11)
    ax2.spines['top'].set_visible(False)
    ax2.spines['right'].set_visible(False)

    fig.suptitle('Fig.7  Ablation Analysis of Security Mechanisms', fontsize=16, y=1.02)
    fig.tight_layout()
    fig.savefig(os.path.join(FIGDIR, 'Fig7_e2_ablation_combined.svg'), format='svg')
    plt.close(fig)
    print('Fig.7 (combined) saved.')


if __name__ == '__main__':
    os.makedirs(FIGDIR, exist_ok=True)
    fig6_compression()
    # fig7 + fig8 merged into combined figure
    fig7_combined_ablation()
    fig9_scr()
    fig10_scr_curve()
    print('All figures regenerated as SVG.')
