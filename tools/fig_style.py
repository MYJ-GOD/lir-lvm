"""
Shared figure style for the LIR/LVM paper (JSA submission).

Single source of truth for palette, rcParams, and helpers so all figure
generators produce a visually consistent set following the JSA style guide:
  - Monochrome blue-grey base with ≤3 accent colors
  - Sans-serif font (Arial/Helvetica), ≥8pt
  - Sharp corners on boxes, right-angle arrows
  - No gradients, shadows, or decoration
  - Export as PDF (vector)

Usage:
    from fig_style import *
    save_pub(fig, 'Fig7_e2_ablation_combined')
"""
import os
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

FIGDIR = os.path.join(os.path.dirname(__file__), '..', 'figures')
RESULT = os.path.join(os.path.dirname(__file__), '..', 'result')

# ── PALETTE: JSA monochrome blue-grey + accent (≤5 semantic colors) ──────────
# Blue family = proposed method / primary
C_BLUE       = '#1f497d'   # deep blue — hero / this-work
C_BLUE_LIGHT = '#D9E6F2'   # very light blue — subsystem layer fill
# Red family = baseline / comparison
C_RED        = '#c0504d'   # muted red — baseline
# Green = improvement / converged
C_GREEN      = '#9cbb58'   # olive green — success
# Teal = secondary / verify / repair
C_TEAL       = '#4bacc6'   # muted teal — verify
# Neutral / structural
C_GREY       = '#767676'   # mid grey — reference, secondary text
C_DARK       = '#4D4D4D'   # dark grey — connectors
C_TEXT       = '#272727'   # near-black — primary text, borders
C_LIGHT      = '#F2F2F2'   # very light grey — hierarchy background fill
C_WHITE      = '#FFFFFF'   # white — foreground boxes

# ── rcParams: JSA two-column publication density ──────────────────────────────
plt.rcParams.update({
    'font.family': 'sans-serif',
    'font.sans-serif': ['Arial', 'Helvetica', 'DejaVu Sans', 'sans-serif'],
    'svg.fonttype': 'none',
    'pdf.fonttype': 42,
    # JSA spec: 9pt labels, 10pt sub-titles, 8pt ticks, ≥8pt minimum
    'font.size': 9,
    'axes.spines.right': False,
    'axes.spines.top': False,
    'axes.linewidth': 0.8,
    'axes.labelsize': 9,
    'axes.titlesize': 10,
    'legend.frameon': False,
    'legend.fontsize': 9,
    'xtick.labelsize': 8,
    'ytick.labelsize': 8,
    'lines.linewidth': 1.5,
    'lines.markersize': 5,
    'figure.dpi': 300,
    'savefig.dpi': 600,
})

# Standard figure widths (inches): single column ~3.5, 1.5 col ~5.0, double ~7.2
COL1, COL15, COL2 = 3.5, 5.0, 7.2

# Hatch patterns for grayscale-safe bar charts (cycle through for series)
HATCHES = ['', '////', '....', 'xxxx', '----', 'oooo', '++++']


def save_pub(fig, name):
    """Export PDF only (JSA vector spec) into FIGDIR."""
    fig.savefig(os.path.join(FIGDIR, f'{name}.pdf'), bbox_inches='tight')
    plt.close(fig)
    print(f'{name} saved.')


def wilson_ci(p, n, z=1.96):
    """Wilson score interval, clamped to [0, 1]."""
    if n <= 0:
        return p, p
    denom = 1 + z**2 / n
    center = (p + z**2 / (2 * n)) / denom
    spread = z * np.sqrt((p * (1 - p) + z**2 / (4 * n)) / n) / denom
    return max(0.0, center - spread), min(1.0, center + spread)


def error_bars(p, n):
    """Return (err_lo, err_hi) for asymmetric Wilson CI error bars."""
    lo, hi = wilson_ci(p, n)
    return max(0.0, p - lo), max(0.0, hi - p)


def panel_label(ax, label, x=-0.12, y=1.08):
    """Bold panel label (a)/(b) at top-left, per JSA spec."""
    ax.text(x, y, label, transform=ax.transAxes,
            fontsize=10, fontweight='bold', color=C_TEXT)


def annotate_bars(ax, bars, fmt='{:.2f}', fontsize=7, offset=0.02,
                  color=None, bold=False):
    """Value labels above bars."""
    weight = 'bold' if bold else 'normal'
    for bar in bars:
        val = bar.get_height()
        ax.text(bar.get_x() + bar.get_width() / 2, val + offset,
                fmt.format(val), ha='center', va='bottom',
                fontsize=fontsize, color=color or C_TEXT, weight=weight)
