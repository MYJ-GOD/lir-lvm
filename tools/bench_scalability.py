"""
Scalability analysis for LIR pipeline (M1 in 解决方案.md).
Three dimensions:
  1. Task length scan (1→50 steps): bytecode size, compile time, exec steps
  2. Device count scan (2→8 devices): bytecode size, stack depth, RAM
  3. Step-limit sensitivity (L=10→1000): completion rate vs fault rate

No hardware required — uses existing simulator (backend_adapter.py).
Outputs: CSV data + PDF figures (JSA style).
"""
import csv
import os
import sys
import time
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

# Add current dir for imports
sys.path.insert(0, os.path.dirname(__file__))
from mir_compiler import compile_source, MirCompilerError
from backend_adapter import simulate_subset, verify_subset, DEVICE_IDS

# Import shared JSA style
from fig_style import (
    FIGDIR, save_pub,
    C_BLUE, C_RED, C_GREEN, C_TEAL, C_GREY, C_TEXT, C_LIGHT,
    wilson_ci, error_bars,
)

RESULT = os.path.join(os.path.dirname(__file__), '..', 'result', 'scalability')
os.makedirs(RESULT, exist_ok=True)

DEVICE_NAMES = ['relay1', 'relay2', 'water_sensor', 'temperature_sensor',
                'humidity_sensor', None, None, None]


# ═══════════════════════════════════════════════════════════════════════════════
# Helpers
# ═══════════════════════════════════════════════════════════════════════════════

def build_lir(n_ops: int, device_count: int = 2) -> str:
    """Generate a deterministic LIR program with `n_ops` operations."""
    devices = DEVICE_NAMES[:max(device_count, 2)]
    lines = []
    for d in devices:
        if d is None:
            break
        lines.append(f'require cap({d})')

    op_idx = 0
    while op_idx < n_ops:
        d = devices[op_idx % len(devices)]
        if d is None:
            d = 'relay1'
        if d in ('relay1', 'relay2'):
            lines.append(f'set {d} = {(op_idx % 2)}')
        else:
            lines.append(f'read {d}')
        op_idx += 1
        if op_idx >= n_ops:
            break
        if op_idx % 3 == 0:
            lines.append('wait 100ms')
            op_idx += 1

    lines.append('halt')
    body = '\n  '.join(lines)
    return f'task scal_test {{\n  {body}\n}}'


def compile_and_simulate(source: str):
    """Compile LIR → bytecode, verify, simulate. Returns result dict."""
    t0 = time.perf_counter()
    try:
        program, payload = compile_source(source)
        compile_time_us = (time.perf_counter() - t0) * 1e6
    except MirCompilerError as e:
        return {'compile_ok': False, 'error': str(e), 'compile_time_us': 0,
                'bytecode_size': 0, 'exec_steps': 0, 'exec_ok': False}

    compile_time_us = (time.perf_counter() - t0) * 1e6
    ok, err_code, err_msg = verify_subset(payload)
    if not ok:
        return {'compile_ok': True, 'verify_ok': False, 'error': err_msg,
                'compile_time_us': compile_time_us, 'bytecode_size': len(payload),
                'exec_steps': 0, 'exec_ok': False}

    result = simulate_subset(payload)
    return {
        'compile_ok': True,
        'verify_ok': True,
        'compile_time_us': compile_time_us,
        'bytecode_size': len(payload),
        'exec_steps': result.steps,
        'exec_ok': result.execution_pass,
        'lir_lines': source.count('\n'),
    }


# ═════════════════════════════════════════════════════════════════════════════
# D1: Task length scan
# ═════════════════════════════════════════════════════════════════════════════

def run_length_scan(max_ops=50, step=1):
    print('=== D1: Task Length Scan ===')
    rows = []
    for n in range(1, max_ops + 1, step):
        source = build_lir(n, device_count=2)
        r = compile_and_simulate(source)
        r['n_ops'] = n
        rows.append(r)
        if n % 10 == 0:
            print(f'  n={n}: {r["bytecode_size"]}B, {r["exec_steps"]} steps, '
                  f'{r["compile_time_us"]:.0f}us')

    csv_path = os.path.join(RESULT, 'd1_length_scan.csv')
    with open(csv_path, 'w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=['n_ops', 'bytecode_size', 'exec_steps',
                                           'compile_time_us', 'lir_lines'])
        w.writeheader()
        for r in rows:
            w.writerow({k: r[k] for k in w.fieldnames})
    print(f'  Saved: {csv_path}')

    ns = [r['n_ops'] for r in rows]
    bc_sizes = [r['bytecode_size'] for r in rows]
    exec_steps = [r['exec_steps'] for r in rows]

    fig, ax1 = plt.subplots(figsize=(3.5, 2.4))
    ax1.plot(ns, bc_sizes, 'o-', color=C_BLUE, linewidth=1.5, markersize=5,
             label='Bytecode size (B)', markeredgecolor=C_BLUE, markerfacecolor='white',
             markeredgewidth=0.8)
    ax1.set_xlabel('Number of LIR operations')
    ax1.set_ylabel('Bytecode size (B)', color=C_BLUE)
    ax1.tick_params(axis='y', labelcolor=C_BLUE)

    ax1.set_ylim(0, max(bc_sizes) * 1.1)

    ax2 = ax1.twinx()
    ax2.plot(ns, exec_steps, 's--', color=C_RED, linewidth=1.5, markersize=5,
             label='Execution steps', markeredgecolor=C_RED, markerfacecolor='white',
             markeredgewidth=0.8)
    ax2.set_ylabel('Execution steps', color=C_RED)
    ax2.tick_params(axis='y', labelcolor=C_RED)
    # Offset the two y-axis scales so the (otherwise near-identical) linear
    # curves separate visually: bytecode rides high, execution steps lower.
    ax2.set_ylim(0, max(exec_steps) * 2.0)

    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, loc='upper left', fontsize=7)
    fig.tight_layout()
    save_pub(fig, 'Fig_scalability_length')
    return rows


# ═════════════════════════════════════════════════════════════════════════════
# D2: Device count scan
# ═════════════════════════════════════════════════════════════════════════════

def run_device_scan(n_ops=10):
    print('=== D2: Device Count Scan ===')
    rows = []
    for nd in [2, 3, 4, 5, 6]:
        source = build_lir(n_ops, device_count=nd)
        r = compile_and_simulate(source)
        r['n_devices'] = nd
        rows.append(r)
        print(f'  devices={nd}: {r["bytecode_size"]}B, {r["exec_steps"]} steps')

    csv_path = os.path.join(RESULT, 'd2_device_scan.csv')
    with open(csv_path, 'w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=['n_devices', 'bytecode_size', 'exec_steps',
                                           'compile_time_us'])
        w.writeheader()
        for r in rows:
            w.writerow({k: r[k] for k in w.fieldnames})
    print(f'  Saved: {csv_path}')

    nds = [r['n_devices'] for r in rows]
    bc_sizes = [r['bytecode_size'] for r in rows]
    exec_steps = [r['exec_steps'] for r in rows]

    fig, ax1 = plt.subplots(figsize=(3.5, 2.4))
    x = np.arange(len(nds))
    w = 0.35

    bars1 = ax1.bar(x - w/2, bc_sizes, w, label='Bytecode size (B)',
                    color=C_BLUE, edgecolor='black', linewidth=0.5)
    bars2 = ax1.bar(x + w/2, exec_steps, w, label='Execution steps',
                    color=C_RED, edgecolor='black', linewidth=0.5)

    for bar in bars1:
        ax1.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.3,
                f'{int(bar.get_height())}', ha='center', fontsize=7, color=C_BLUE)
    for bar in bars2:
        ax1.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.3,
                f'{int(bar.get_height())}', ha='center', fontsize=7, color=C_RED)

    ax1.set_xlabel('Number of devices')
    ax1.set_ylabel('Count')
    ax1.set_xticks(x)
    ax1.set_xticklabels([str(d) for d in nds])
    ax1.set_ylim(0, max(max(bc_sizes), max(exec_steps)) * 1.30)
    ax1.legend(fontsize=7, loc='upper center', ncol=2, frameon=False,
               columnspacing=1.2, handletextpad=0.4, bbox_to_anchor=(0.5, 1.02))
    fig.tight_layout()
    save_pub(fig, 'Fig_scalability_devices')
    return rows


# ═════════════════════════════════════════════════════════════════════════════
# D3: Step-limit sensitivity
# ═════════════════════════════════════════════════════════════════════════════

def build_fixed_size_tasks():
    """Build a small test set of varying complexity for step-limit scan."""
    tasks = []
    tasks.append(('simple_3ops', build_lir(3, device_count=2)))
    tasks.append(('medium_10ops', build_lir(10, device_count=2)))
    tasks.append(('long_30ops', build_lir(30, device_count=2)))
    tasks.append(('retry_3', '''task retry_test {
  require cap(relay1)
  retry 3 times {
    set relay1 = 1
    readback relay1 expect 1
  }
  halt
}'''))
    return tasks


def run_step_limit_scan():
    print('=== D3: Step-Limit Sensitivity ===')
    tasks = build_fixed_size_tasks()
    limits = [10, 20, 50, 100, 200, 500, 1000]
    rows = []

    for task_name, source in tasks:
        try:
            _, payload = compile_source(source)
        except MirCompilerError:
            continue
        base_steps = simulate_subset(payload).steps
        print(f'  {task_name}: base={base_steps} steps, {len(payload)}B')

        for L in limits:
            result = simulate_subset(payload)
            if result.steps > L:
                completed = False
            else:
                completed = result.execution_pass
            rows.append({
                'task': task_name,
                'step_limit': L,
                'actual_steps': result.steps,
                'completed': int(completed),
                'bytecode_size': len(payload),
                'base_steps': base_steps,
            })

    csv_path = os.path.join(RESULT, 'd3_step_limit_scan.csv')
    with open(csv_path, 'w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=['task', 'step_limit', 'actual_steps',
                                           'completed', 'bytecode_size', 'base_steps'])
        w.writeheader()
        for r in rows:
            w.writerow(r)
    print(f'  Saved: {csv_path}')

    fig, ax = plt.subplots(figsize=(3.5, 2.4))
    linestyles = ['-', '--', '-.', ':']
    markers = ['o', 's', 'D', '^']
    task_colors = [C_BLUE, C_RED, C_GREEN, C_TEAL]
    for i, task_name in enumerate(sorted(set(r['task'] for r in rows))):
        task_rows = [r for r in rows if r['task'] == task_name]
        Ls = [r['step_limit'] for r in task_rows]
        completed = [r['completed'] for r in task_rows]
        ax.plot(Ls, completed, f'{markers[i]}{linestyles[i]}', label=task_name,
                color=task_colors[i % len(task_colors)],
                linewidth=1.5, markersize=5, markeredgecolor=task_colors[i % len(task_colors)],
                markerfacecolor='white', markeredgewidth=0.8)

    ax.set_xlabel('Step limit (L)')
    ax.set_ylabel('Completion (1=pass, 0=fail)')
    ax.set_xscale('log')
    ax.set_ylim(-0.05, 1.15)
    ax.set_yticks([0, 1])
    ax.set_yticklabels(['Fail', 'Pass'])
    ax.legend(fontsize=7, loc='lower right')
    fig.tight_layout()
    save_pub(fig, 'Fig_scalability_step_limit')

    print('\n  Summary:')
    for task_name in sorted(set(r['task'] for r in rows)):
        task_rows = [r for r in rows if r['task'] == task_name]
        base = task_rows[0]['base_steps']
        min_L = min(r['step_limit'] for r in task_rows if r['completed'])
        print(f'    {task_name}: {base} base steps, minimum safe L={min_L} '
              f'(margin={min_L/base:.1f}×)')

    return rows


# ═════════════════════════════════════════════════════════════════════════════

def plot_from_csv():
    """Plot from existing CSV data (no simulation needed)."""
    import pandas as pd

    # D1: Length scan
    csv1 = os.path.join(RESULT, 'd1_length_scan.csv')
    if os.path.exists(csv1):
        df = pd.read_csv(csv1)
        ns = df['n_ops'].tolist()
        bc_sizes = df['bytecode_size'].tolist()
        exec_steps = df['exec_steps'].tolist()

        fig, ax1 = plt.subplots(figsize=(3.5, 2.4))
        ax1.plot(ns, bc_sizes, 'o-', color=C_BLUE, linewidth=1.5, markersize=5,
                 label='Bytecode size (B)', markeredgecolor=C_BLUE, markerfacecolor='white',
                 markeredgewidth=0.8)
        ax1.set_xlabel('Number of LIR operations')
        ax1.set_ylabel('Bytecode size (B)', color=C_BLUE)
        ax1.tick_params(axis='y', labelcolor=C_BLUE)

        ax1.set_ylim(0, max(bc_sizes) * 1.1)

        ax2 = ax1.twinx()
        ax2.plot(ns, exec_steps, 's--', color=C_RED, linewidth=1.5, markersize=5,
                 label='Execution steps', markeredgecolor=C_RED, markerfacecolor='white',
                 markeredgewidth=0.8)
        ax2.set_ylabel('Execution steps', color=C_RED)
        ax2.tick_params(axis='y', labelcolor=C_RED)
        # Offset the two y-axis scales so the near-identical linear curves
        # separate visually: bytecode rides high, execution steps lower.
        ax2.set_ylim(0, max(exec_steps) * 2.0)

        lines1, labels1 = ax1.get_legend_handles_labels()
        lines2, labels2 = ax2.get_legend_handles_labels()
        ax1.legend(lines1 + lines2, labels1 + labels2, loc='upper left', fontsize=7)
        fig.tight_layout()
        save_pub(fig, 'Fig_scalability_length')
        print('  Fig_scalability_length plotted from CSV.')

    # D2: Device scan
    csv2 = os.path.join(RESULT, 'd2_device_scan.csv')
    if os.path.exists(csv2):
        df = pd.read_csv(csv2)
        nds = df['n_devices'].tolist()
        bc_sizes = df['bytecode_size'].tolist()
        exec_steps = df['exec_steps'].tolist()

        fig, ax1 = plt.subplots(figsize=(3.5, 2.4))
        x = np.arange(len(nds))
        w = 0.35

        bars1 = ax1.bar(x - w/2, bc_sizes, w, label='Bytecode size (B)',
                        color=C_BLUE, edgecolor='black', linewidth=0.5)
        bars2 = ax1.bar(x + w/2, exec_steps, w, label='Execution steps',
                        color=C_RED, edgecolor='black', linewidth=0.5)

        for bar in bars1:
            ax1.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.3,
                    f'{int(bar.get_height())}', ha='center', fontsize=7, color=C_BLUE)
        for bar in bars2:
            ax1.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.3,
                    f'{int(bar.get_height())}', ha='center', fontsize=7, color=C_RED)

        ax1.set_xlabel('Number of devices')
        ax1.set_ylabel('Count')
        ax1.set_xticks(x)
        ax1.set_xticklabels([str(d) for d in nds])
        ax1.set_ylim(0, max(max(bc_sizes), max(exec_steps)) * 1.30)
        ax1.legend(fontsize=7, loc='upper center', ncol=2, frameon=False,
                   columnspacing=1.2, handletextpad=0.4, bbox_to_anchor=(0.5, 1.02))
        fig.tight_layout()
        save_pub(fig, 'Fig_scalability_devices')
        print('  Fig_scalability_devices plotted from CSV.')

    # D3: Step-limit scan
    csv3 = os.path.join(RESULT, 'd3_step_limit_scan.csv')
    if os.path.exists(csv3):
        df = pd.read_csv(csv3)
        fig, ax = plt.subplots(figsize=(3.5, 2.4))
        linestyles = ['-', '--', '-.', ':']
        markers = ['o', 's', 'D', '^']
        task_colors = [C_BLUE, C_RED, C_GREEN, C_TEAL]
        for i, task_name in enumerate(sorted(df['task'].unique())):
            tdf = df[df['task'] == task_name]
            ax.plot(tdf['step_limit'], tdf['completed'],
                    f'{markers[i]}{linestyles[i]}', label=task_name,
                    color=task_colors[i % len(task_colors)],
                    linewidth=1.5, markersize=5,
                    markeredgecolor=task_colors[i % len(task_colors)],
                    markerfacecolor='white', markeredgewidth=0.8)

        ax.set_xlabel('Step limit (L)')
        ax.set_ylabel('Completion (1=pass, 0=fail)')
        ax.set_xscale('log')
        ax.set_ylim(-0.05, 1.15)
        ax.set_yticks([0, 1])
        ax.set_yticklabels(['Fail', 'Pass'])
        ax.legend(fontsize=7, loc='lower right')
        fig.tight_layout()
        save_pub(fig, 'Fig_scalability_step_limit')
        print('  Fig_scalability_step_limit plotted from CSV.')


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--plot-only', action='store_true',
                        help='Plot from existing CSVs without re-running simulations')
    args = parser.parse_args()

    os.makedirs(RESULT, exist_ok=True)
    if args.plot_only:
        plot_from_csv()
    else:
        run_length_scan(max_ops=50, step=1)
        run_device_scan(n_ops=10)
        run_step_limit_scan()
    print('\nAll scalability analyses complete.')
