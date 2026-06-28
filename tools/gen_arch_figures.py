"""
Redraw Fig.1–Fig.5 architecture diagrams — JSA publication quality.

JSA style guide compliance:
  - Sharp 90° corners on all boxes (no rounded corners)
  - 0.5pt black border, white or very light fill
  - Solid 1pt black arrows, standard triangle arrowheads
  - Right-angle (orthogonal) arrow paths, no curved connections
  - Font: Arial/Helvetica, ≥8pt, bold only for component names
  - Monochrome blue-grey base with ≤3 accent colors
  - No gradients, shadows, or decoration
  - Generous spacing: text must fit inside boxes comfortably

Usage: python gen_arch_figures.py
"""
import os
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
import numpy as np

from fig_style import (
    FIGDIR, save_pub,
    C_BLUE, C_BLUE_LIGHT, C_RED, C_GREEN, C_TEAL,
    C_GREY, C_DARK, C_TEXT, C_LIGHT, C_WHITE,
)


def draw_box(ax, x, y, w, h, label, sublabel='', fill=C_WHITE,
             border=C_TEXT, fontsize=8, lw=0.5, border_lw=0.5):
    """Sharp-cornered rectangle with centered label + optional sublabel."""
    rect = Rectangle((x, y), w, h, facecolor=fill, edgecolor='none',
                      linewidth=0, zorder=1)
    ax.add_patch(rect)
    border_rect = Rectangle((x, y), w, h, facecolor='none',
                             edgecolor=border, linewidth=border_lw, zorder=2)
    ax.add_patch(border_rect)
    cy = y + h / 2
    sub_off = 0.030 if sublabel else 0
    ax.text(x + w/2, cy + sub_off, label, ha='center', va='center',
            fontsize=fontsize, fontweight='bold', color=C_TEXT, linespacing=1.15,
            zorder=3)
    if sublabel:
        ax.text(x + w/2, cy - 0.038, sublabel, ha='center', va='center',
                fontsize=max(6, fontsize - 2), color=C_GREY, linespacing=1.0,
                zorder=3)


def arr(ax, x1, y1, x2, y2, color=C_TEXT, lw=1.0, style='->', ls='-'):
    ax.annotate('', xy=(x2, y2), xytext=(x1, y1),
                arrowprops=dict(arrowstyle=style, color=color, lw=lw,
                                linestyle=ls),
                zorder=4)


def arr_h(ax, x1, x2, y, color=C_TEXT, lw=1.0):
    arr(ax, x1, y, x2, y, color, lw)


# ═════════════════════════════════════════════════════════════════════════════
# Fig.1: System Architecture
# ═════════════════════════════════════════════════════════════════════════════

def fig1_architecture():
    fig, ax = plt.subplots(figsize=(7.2, 4.2))
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis('off')

    # ── Layer backgrounds ─────────────────────────────────────────────────
    fe_bg = Rectangle((0.0, 0.68), 0.98, 0.30, facecolor=C_BLUE_LIGHT,
                       edgecolor=C_GREY, linewidth=0.5, zorder=0)
    ax.add_patch(fe_bg)
    ax.text(0.01, 0.965, 'Frontend: LLM Generation Pipeline', fontsize=9,
            fontweight='bold', color=C_BLUE, va='top', zorder=1)

    be_bg = Rectangle((0.0, 0.36), 0.98, 0.28, facecolor=C_LIGHT,
                       edgecolor=C_GREY, linewidth=0.5, zorder=0)
    ax.add_patch(be_bg)
    ax.text(0.01, 0.625, 'Backend: MCU Execution & Safety', fontsize=9,
            fontweight='bold', color=C_DARK, va='top', zorder=1)

    sec_bg = Rectangle((0.0, 0.04), 0.98, 0.28, facecolor='#FDE8E8',
                        edgecolor=C_GREY, linewidth=0.5, zorder=0)
    ax.add_patch(sec_bg)
    ax.text(0.01, 0.285, 'Runtime Protection Mechanisms', fontsize=9,
            fontweight='bold', color=C_RED, va='top', zorder=1)

    # ── Frontend row: 6 boxes ─────────────────────────────────────────────
    fy, fh = 0.72, 0.20
    gap = 0.025
    fe_w = 0.120
    fe_start = 0.02
    fe = []
    labels_fe = [
        ('Natural\nLanguage', 'user input'),
        ('LLM', 'llama / qwen'),
        ('LIR', 'structured DSL'),
        ('Compiler', 'deterministic\nlowering'),
        ('Verifier', 'static check'),
        ('Compact\nBytecode', 'varint\nencoded'), # 换行防止长文本戳破边框
    ]
    cx = fe_start
    for lab, sub in labels_fe:
        fe.append((cx, fy, fe_w, fh, lab, sub))
        cx += fe_w + gap
    for x, y, w, h, lab, sub in fe:
        draw_box(ax, x, y, w, h, lab, sub, fill=C_WHITE, border=C_BLUE)
    for i in range(len(fe) - 1):
        arr_h(ax, fe[i][0]+fe[i][2], fe[i+1][0], fy+fh/2)

    # ── Backend row: 5 boxes ──────────────────────────────────────────────
    by, bh = 0.40, 0.20
    be_w = 0.140
    be_start = 0.02
    be = []
    labels_be = [
        ('Transmission', 'serial / WiFi'),
        ('LVM', 'ESP8266\nstack-based'),
        ('Hardware I/O', 'relay / sensor'),
        ('Feedback', 'fault / readback'),
        ('Repair Loop', 'structured fix'),
    ]
    cx = be_start
    for lab, sub in labels_be:
        be.append((cx, by, be_w, bh, lab, sub))
        cx += be_w + gap
    for x, y, w, h, lab, sub in be:
        draw_box(ax, x, y, w, h, lab, sub, fill=C_WHITE, border=C_DARK)
    for i in range(len(be) - 1):
        arr_h(ax, be[i][0]+be[i][2], be[i+1][0], by+bh/2)

    # ── Security row: 4 boxes ─────────────────────────────────────────────
    sy, sh = 0.08, 0.16
    sec_w = 0.175
    sec_start = 0.02
    sec = []
    labels_sec = [
        ('Capability\nGating', ''),
        ('Step Limit', ''),
        ('Fault Audit', ''),
        ('Closed-loop\nVerify', ''),
    ]
    cx = sec_start
    for lab, sub in labels_sec:
        sec.append((cx, sy, sec_w, sh, lab, sub))
        cx += sec_w + gap
    for x, y, w, h, lab, sub in sec:
        draw_box(ax, x, y, w, h, lab, sub, fill='#FDE8E8', border=C_RED)

    # Bracket under security row
    bl, br = sec_start, sec[-1][0] + sec[-1][2]
    by_br = sy - 0.01
    ax.plot([bl, br], [by_br, by_br], color=C_RED, lw=0.5, clip_on=False, zorder=5)
    ax.plot([bl, bl], [by_br, by_br-0.015], color=C_RED, lw=0.5, clip_on=False, zorder=5)
    ax.plot([br, br], [by_br, by_br-0.015], color=C_RED, lw=0.5, clip_on=False, zorder=5)
    bcx = (bl + br) / 2
    arr(ax, bcx, by_br-0.015, be[1][0]+be[1][2]/2, by+bh+0.01, C_RED, 1.0, '->', 'dashed')
    ax.text(bcx, by_br-0.04, 'enforce at runtime', fontsize=7,
            color=C_RED, ha='center', style='italic')

    # ── Feedback → LLM 改为 JSA 要求的直角折线连接 ────────────────────────
    # 路径: (Feedback中点, by+bh) -> 垂直上升到 0.65 -> 水平左移到 (LLM中点) -> 垂直上升到 fy
    f_llm_x = fe[1][0] + fe[1][2]/2
    t_fb_x = be[3][0] + be[3][2]/2
    ax.plot([t_fb_x, t_fb_x, f_llm_x, f_llm_x], [by+bh, 0.65, 0.65, fy],
            color=C_TEAL, lw=1.0, linestyle='dashed', zorder=4)
    # 在末端补充硬质箭头标准端点
    arr(ax, f_llm_x, fy+0.01, f_llm_x, fy, color=C_TEAL, lw=1.0)
    ax.text(t_fb_x+0.01, 0.66, 'error feedback', fontsize=7,
            color=C_TEAL, ha='left', va='bottom', style='italic')

    save_pub(fig, 'Fig1_architecture')


# ═════════════════════════════════════════════════════════════════════════════
# Fig.2: LIR-to-Bytecode Lowering
# ═════════════════════════════════════════════════════════════════════════════

def fig2_lowering():
    fig, ax = plt.subplots(figsize=(6.0, 3.0))
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis('off')

    ry = [0.80 - i * 0.095 for i in range(6)]

    # LIR source
    draw_box(ax, 0.01, 0.05, 0.30, 0.88, '', '', fill=C_BLUE_LIGHT, border=C_BLUE)
    ax.text(0.16, 0.92, 'LIR Source', ha='center', fontsize=9,
            fontweight='bold', color=C_BLUE)
    for y, line in zip(ry, ['require cap(relay1)', 'require cap(water_sensor)',
                             'set relay1 = 1', 'wait 500ms',
                             'read water_sensor', 'halt']):
        ax.text(0.025, y, line, fontsize=7, fontfamily='monospace', color=C_TEXT)
    ax.text(0.16, 0.10, 'LLM-generated\nrunning example',
            ha='center', fontsize=7, color=C_GREY, style='italic')

    # Compiler
    draw_box(ax, 0.36, 0.05, 0.30, 0.88, '', '', fill=C_LIGHT, border=C_DARK)
    ax.text(0.51, 0.92, 'Compiler', ha='center', fontsize=9,
            fontweight='bold', color=C_DARK)
    for y, line in zip(ry, ['cap(5)   → GTWAY 5', 'cap(1)   → GTWAY 1',
                             'set 1    → LIT 1; IOW 5', 'wait 500 → WAIT 500',
                             'read s   → IOR 1', 'halt     → HALT']):
        ax.text(0.375, y, line, fontsize=7, fontfamily='monospace', color=C_TEXT)
    ax.text(0.51, 0.10, 'O(n) deterministic\nunique output',
            ha='center', fontsize=7, color=C_GREY, style='italic')

    # Bytecode (修复点：边框改回 C_BLUE，收敛整体色调，不滥用强调色)
    draw_box(ax, 0.71, 0.05, 0.27, 0.88, '', '', fill=C_WHITE, border=C_BLUE)
    ax.text(0.845, 0.92, 'Bytecode', ha='center', fontsize=9,
            fontweight='bold', color=C_BLUE)
    bc = ['GTWAY 5', 'GTWAY 1', 'LIT 1', 'IOW 5', 'WAIT 500', 'IOR 1', 'HALT']
    bcy = [0.80 - i * 0.085 for i in range(7)]
    for y, line in zip(bcy, bc):
        ax.text(0.725, y, line, fontsize=7, fontfamily='monospace', color=C_TEXT)
    ax.text(0.845, 0.10, '12 bytes\nvarint encoded',
            ha='center', fontsize=7, color=C_GREY, style='italic')

    # Arrows with labels
    arr_h(ax, 0.31, 0.36, 0.49)
    arr_h(ax, 0.66, 0.71, 0.49)
    ax.text(0.335, 0.54, 'lower', fontsize=7, color=C_DARK, ha='center')
    ax.text(0.685, 0.54, 'encode', fontsize=7, color=C_DARK, ha='center')

    save_pub(fig, 'Fig2_lir_lowering')


# ═════════════════════════════════════════════════════════════════════════════
# Fig.3: LVM Execution Flow
# ═════════════════════════════════════════════════════════════════════════════

def fig3_mvm_flow():
    fig, ax = plt.subplots(figsize=(6.5, 2.6))
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis('off')

    bw, bh = 0.130, 0.40
    gap = 0.020
    start_x = 0.01
    by = 0.32

    steps_data = [
        ('Load\nFrame', 'fetch bytecode'),
        ('Decode\nOpcode', 'instruction decode'),
        ('Static\nChecks', 'bounds / encoding'),
        ('Runtime\nGuards', 'cap / step stack'),
        ('Execute\nIOW/IOR', 'stack-based exec'),
        ('Emit\nResult', 'OK or FAULT'),
    ]
    stage_names = ['FETCH', 'DECODE', 'VALIDATE', 'GUARD', 'EXECUTE', 'OUTPUT']

    steps = []
    cx = start_x
    for (lab, sub), sn in zip(steps_data, stage_names):
        steps.append((cx, by, bw, bh, lab, sub))
        cx += bw + gap

    for (x, y, w, h, lab, sub), sn in zip(steps, stage_names):
        cx_box = x + w/2
        ax.text(cx_box, 0.92, sn, fontsize=7, color=C_GREY, ha='center',
                fontweight='bold')
        draw_box(ax, x, y, w, h, lab, sub, fill=C_WHITE, border=C_TEXT)

    for i in range(len(steps)-1):
        arr_h(ax, steps[i][0]+steps[i][2], steps[i+1][0], by+bh/2)

    # Fault branch
    guard_x = steps[3][0]
    draw_box(ax, guard_x, 0.04, bw, 0.20, 'Fault', 'code, pc',
             fill='#FDE8E8', border=C_RED)
    arr(ax, guard_x+bw/2, by, guard_x+bw/2, 0.24, C_RED, 1.0, '->', 'dashed')
    ax.text(guard_x+bw/2+0.015, 0.28, 'violation', fontsize=7, color=C_RED)

    save_pub(fig, 'Fig3_mvm_flow')


# ═════════════════════════════════════════════════════════════════════════════
# Fig.4: Closed-Loop FSM
# ═════════════════════════════════════════════════════════════════════════════

def fig4_fsm():
    fig, ax = plt.subplots(figsize=(6.0, 3.0))
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis('off')

    # Initial state
    ax.plot(0.015, 0.60, 'ko', markersize=6, zorder=5)
    arr(ax, 0.03, 0.60, 0.07, 0.60)

    # Main chain
    cy, ch = 0.48, 0.28
    bw = 0.155
    gap = 0.040
    start_x = 0.07
    states_data = [
        ('SET', 'write device'),
        ('ACK', 'confirm write'),
        ('READBACK', 'read device'),
        ('COMPARE', 'match check'),
    ]

    states = []
    cx = start_x
    for lab, sub in states_data:
        states.append((cx, cy, bw, ch, lab, sub))
        cx += bw + gap

    for x, y, w, h, lab, sub in states:
        # 修复点：移除了 FancyBboxPatch 圆角组件，改为符合 JSA 要求的直角 Rectangle
        rect = Rectangle((x, y), w, h, facecolor=C_WHITE, edgecolor=C_TEXT,
                         linewidth=0.8, zorder=2)
        ax.add_patch(rect)
        cy_mid = y + h / 2
        ax.text(x + w/2, cy_mid + 0.03, lab, ha='center', va='center',
                fontsize=9, fontweight='bold', color=C_TEXT, zorder=3)
        ax.text(x + w/2, cy_mid - 0.04, sub, ha='center', va='center',
                fontsize=7, color=C_GREY, zorder=3)

    for i in range(len(states)-1):
        arr_h(ax, states[i][0]+states[i][2], states[i+1][0], cy+ch/2)

    # CONVERGED terminal
    last_x = states[-1][0] + states[-1][2]
    ax.plot(0.90, 0.72, 'ko', markersize=6, zorder=5)
    ax.plot(0.90, 0.72, 'ko', markersize=12, fillstyle='none', markeredgewidth=0.8, zorder=5)
    arr(ax, last_x, 0.70, 0.87, 0.72, C_GREEN, 1.0)
    ax.text(0.90, 0.84, 'CONVERGED', fontsize=8, color=C_GREEN,
            ha='center', fontweight='bold')

    # SAFE/FAULT terminal
    ax.plot(0.90, 0.20, 'ko', markersize=6, zorder=5)
    ax.plot(0.90, 0.20, 'ko', markersize=12, fillstyle='none', markeredgewidth=0.8, zorder=5)
    arr(ax, last_x, 0.50, 0.87, 0.26, C_RED, 1.0)
    ax.text(0.90, 0.10, 'SAFE/FAULT', fontsize=8, color=C_RED,
            ha='center', fontweight='bold')

    # ── Retry loop 改为直角折线 ───────────────────────────────────────────
    # 路径: 从最后框下方出发 -> 垂直下移到 0.25 -> 水平左移到第一框中点下方 -> 垂直上移到 0.48
    ret_start_x = last_x - 0.02
    ret_end_x = states[0][0] + states[0][2]/2
    ax.plot([ret_start_x, ret_start_x, ret_end_x, ret_end_x], [0.48, 0.25, 0.25, 0.48],
            color=C_DARK, lw=1.0, linestyle='dashed', zorder=4)
    # 补充指向 SET 的正向直角箭头端点
    arr(ax, ret_end_x, 0.47, ret_end_x, 0.48, color=C_DARK, lw=1.0)
    ax.text((ret_start_x + ret_end_x)/2, 0.27, 'mismatch → retry', fontsize=8, color=C_DARK, ha='center', va='bottom')

    save_pub(fig, 'Fig4_closed_loop_fsm')


# ═════════════════════════════════════════════════════════════════════════════
# Fig.5: Generation Pipeline with Repair Loop
# ═════════════════════════════════════════════════════════════════════════════

def fig5_pipeline():
    fig, ax = plt.subplots(figsize=(7.2, 4.2))
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis('off')

    # ── Layer backgrounds ─────────────────────────────────────────────────
    pipe_bg = Rectangle((0.0, 0.55), 0.98, 0.43, facecolor=C_BLUE_LIGHT,
                         edgecolor=C_GREY, linewidth=0.5, zorder=0)
    ax.add_patch(pipe_bg)
    ax.text(0.01, 0.965, 'Generation Pipeline', fontsize=9,
            fontweight='bold', color=C_BLUE, va='top', zorder=1)

    repair_bg = Rectangle((0.0, 0.04), 0.98, 0.45, facecolor=C_LIGHT,
                           edgecolor=C_GREY, linewidth=0.5, zorder=0)
    ax.add_patch(repair_bg)
    ax.text(0.01, 0.475, 'Repair Loop (on failure)', fontsize=9,
            fontweight='bold', color=C_TEAL, va='top', zorder=1)

    # ── Main pipeline: 6 boxes ────────────────────────────────────────────
    py, ph = 0.60, 0.24
    bw = 0.125
    gap = 0.025
    start_x = 0.02

    pipe_data = [
        ('Task\nPrompt', 'NL goal +\ndevice schema'),
        ('LLM', 'structured\ngeneration'),
        ('LIR', 'textual DSL'),
        ('Compiler', 'IR lowering +\nbytecode enc.'), # 稍微缩短，确保极端环境不下溢
        ('Verifier', 'opcode / varint /\nbounds / cap'),
        ('LVM', 'bounded exec.\non MCU'),
    ]

    boxes = []
    cx = start_x
    for lab, sub in pipe_data:
        boxes.append((cx, py, bw, ph, lab, sub))
        cx += bw + gap

    for x, y, w, h, lab, sub in boxes:
        draw_box(ax, x, y, w, h, lab, sub, fill=C_WHITE, border=C_BLUE)
    for i in range(len(boxes)-1):
        arr_h(ax, boxes[i][0]+boxes[i][2], boxes[i+1][0], py+ph/2)

    # ── Repair loop: 5 boxes ──────────────────────────────────────────────
    ry, rh = 0.12, 0.24
    rbw = 0.130
    rgap = 0.025
    r_start = 0.02

    repair_data = [
        ('LVM\nOutput', 'OK or\nFAULT', C_WHITE, C_DARK),
        ('Parse\nResult', 'stage /\nerror code', C_WHITE, C_DARK),
        ('Error\nFormatter', 'stage / code /\nmessage / hint', '#FDE8E8', C_RED),
        ('LLM\nRepair', 'regenerate\nwith context', C_WHITE, C_BLUE),
        ('Fault\nTrace', 'pc / fault /\nsteps', C_WHITE, C_TEAL),
    ]

    rboxes = []
    cx = r_start
    for lab, sub, fill, border in repair_data:
        rboxes.append((cx, ry, rbw, rh, lab, sub, fill, border))
        cx += rbw + rgap

    for x, y, w, h, lab, sub, fill, border in rboxes:
        draw_box(ax, x, y, w, h, lab, sub, fill=fill, border=border)
    for i in range(len(rboxes)-1):
        arr_h(ax, rboxes[i][0]+rboxes[i][2], rboxes[i+1][0], ry+rh/2)

    # LVM → LVM Output (正向直角下移)
    lvm_x = boxes[-1][0] + boxes[-1][2]/2
    lvo_x = rboxes[0][0] + rboxes[0][2]/2
    arr(ax, lvm_x, py, lvo_x, ry+rh, C_DARK, 1.0)

    # Accept box
    draw_box(ax, rboxes[1][0]-0.01, 0.01, 0.120, 0.08, 'Accept', 'task done',
             fill='#E8F5E9', border=C_GREEN)
    arr(ax, rboxes[1][0]+rboxes[1][2]/2, ry, rboxes[1][0]+rboxes[1][2]/2, 0.09, C_GREEN, 1.0)
    ax.text(rboxes[1][0]+rboxes[1][2]/2+0.015, 0.10, 'OK', fontsize=8,
            color=C_GREEN, ha='left', va='center')

    # ── Repair → Compiler 改为直角折线 ───────────────────────────────────
    # 路径: (Repair中点, ry+rh) -> 垂直上升到 0.50 -> 水平左移到 (Compiler中点) -> 垂直上升到 py
    compiler_x = boxes[3][0] + boxes[3][2]/2
    repair_x = rboxes[3][0] + rboxes[3][2]/2
    ax.plot([repair_x, repair_x, compiler_x, compiler_x], [ry+rh, 0.50, 0.50, py],
            color=C_TEAL, lw=1.0, linestyle='dashed', zorder=4)
    # 补齐硬质指向箭头端点
    arr(ax, compiler_x, py+0.01, compiler_x, py, color=C_TEAL, lw=1.0)
    ax.text(repair_x-0.01, 0.51, 're-compile\n(max 3 rounds)', fontsize=7,
            color=C_TEAL, ha='right', va='bottom')

    # Audit label
    ax.text(rboxes[4][0]+rboxes[4][2]/2, ry+rh/2+0.04, 'audit', fontsize=7,
            color=C_TEAL, ha='center')

    save_pub(fig, 'Fig5_generation_pipeline')


# ═════════════════════════════════════════════════════════════════════════════

if __name__ == '__main__':
    os.makedirs(FIGDIR, exist_ok=True)
    print('Generating Fig.1–5 (JSA style):')
    fig1_architecture()
    fig2_lowering()
    fig3_mvm_flow()
    fig4_fsm()
    fig5_pipeline()
    print('Done.')