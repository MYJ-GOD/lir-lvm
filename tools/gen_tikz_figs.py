"""
Auto-generate TikZ code for Fig 1-5 with correct coordinates.
All layout math is computed — no manual coordinate guessing.

Usage: python gen_tikz_figs.py
Output: latex/fig{1..5}_tikz.tex
"""
import os, textwrap

LATEX_DIR = os.path.join(os.path.dirname(__file__), "..", "latex")

# ── Shared helpers ──────────────────────────────────────────────

def _box(name, x, y, w, h, label, style="box"):
    """Return a TikZ \\node for a rounded-rect box."""
    return (
        f"\\node[{style}] ({name}) at ({x:.2f}, {y:.2f}) "
        f"{{ {label} }};"
    )

def _annot(x, y, text, color="black!45"):
    """Return a small annotation \\node below a box."""
    return (
        f"\\node[font=\\sffamily\\tiny, {color}, anchor=north] "
        f"at ({x:.2f}, {y:.2f}) {{{text}}};"
    )

def _arrow(src, dst, style="arr", extra=""):
    """Return a straight arrow between two nodes."""
    return f"\\draw[{style}] ({src}) -- ({dst}) {extra};"

def _arrow_label(src, dst, label, pos="above", style="arr"):
    """Arrow with a label."""
    return f"\\draw[{style}] ({src}) -- node[font=\\sffamily\\tiny, black!50, {pos}] {{{label}}} ({dst});"

def _ortho_arrow(src, dst, via_points, style="arr"):
    """Orthogonal arrow through explicit waypoints."""
    path = " -- ".join(f"({p[0]:.2f}, {p[1]:.2f})" if isinstance(p, tuple) else f"({p})" for p in via_points)
    return f"\\draw[{style}] ({src}) -- {path};"


# ── Fig 1: System Architecture ──────────────────────────────────

def gen_fig1():
    lines = []
    lines.append("% Fig.1: System Architecture — auto-generated")
    lines.append("\\begin{tikzpicture}[scale=0.55, transform shape,")
    lines.append("  >=Stealth, font=\\sffamily\\small,")
    lines.append("  box/.style={draw=black!80, fill=white, minimum width=1.9cm,")
    lines.append("             minimum height=0.85cm, align=center, inner sep=2pt,")
    lines.append("             font=\\sffamily\\scriptsize\\bfseries},")
    lines.append("  arr/.style={-Stealth, thick, draw=black!70},")
    lines.append("  darrow/.style={-Stealth, thick, draw=black!70, dashed},")
    lines.append("]")
    lines.append("")

    # Layout parameters
    Y_FE, Y_BE, Y_SEC = 3.3, 1.0, -1.3
    BOX_W, BOX_H = 1.9, 0.85

    # --- Layer backgrounds ---
    lines.append("% Layer backgrounds")
    lines.append("\\fill[black!3, draw=black!15, line width=0.3pt]")
    lines.append("  (-0.6, 2.3) rectangle (15.8, 4.5);")
    lines.append("\\node[font=\\sffamily\\small\\bfseries, black!60, anchor=north west]")
    lines.append("  at (-0.5, 4.45) {Frontend: LLM Generation Pipeline};")
    lines.append("")
    lines.append("\\fill[black!3, draw=black!15, line width=0.3pt]")
    lines.append("  (-0.6, 0.0) rectangle (15.8, 2.1);")
    lines.append("\\node[font=\\sffamily\\small\\bfseries, black!60, anchor=north west]")
    lines.append("  at (-0.5, 2.05) {Backend: MCU Execution \\& Safety};")
    lines.append("")
    lines.append("\\fill[black!3, draw=black!15, line width=0.3pt]")
    lines.append("  (-0.6, -2.3) rectangle (15.8, -0.2);")
    lines.append("\\node[font=\\sffamily\\small\\bfseries, black!60, anchor=north west]")
    lines.append("  at (-0.5, -0.25) {Runtime Protection Mechanisms};")
    lines.append("")

    # --- Frontend row ---
    fe_items = [
        ("nl",  "Natural\\\\[-1pt]Language", "user input"),
        ("llm", "LLM", "llama / qwen"),
        ("lir", "LIR", "structured DSL"),
        ("cmp", "Compiler", "deterministic"),
        ("vfy", "Verifier", "static check"),
        ("bc",  "Compact\\\\[-1pt]Bytecode", "varint encoded"),
    ]
    n = len(fe_items)
    x_start = 0.8
    x_gap = 2.5
    lines.append("% Frontend row")
    for i, (name, label, annot) in enumerate(fe_items):
        x = x_start + i * x_gap
        lines.append(_box(name, x, Y_FE, BOX_W, BOX_H, label))
    lines.append("")
    for i, (name, label, annot) in enumerate(fe_items):
        x = x_start + i * x_gap
        lines.append(_annot(x, Y_FE - BOX_H/2 - 0.08, annot))
    lines.append("")
    # Arrows
    for i in range(n - 1):
        src = fe_items[i][0]
        dst = fe_items[i+1][0]
        lines.append(_arrow(f"{src}.east", f"{dst}.west"))
    lines.append("")

    # --- Backend row ---
    be_items = [
        ("tx",  "Transmission", "serial / WiFi"),
        ("lvm", "LVM", "ESP8266"),
        ("hw",  "Hardware I/O", "relay / sensor"),
        ("fb",  "Feedback", "fault / readback"),
        ("rp",  "Repair Loop", "structured fix"),
    ]
    n_be = len(be_items)
    x_start_be = 0.8
    x_gap_be = 2.7
    lines.append("% Backend row")
    for i, (name, label, annot) in enumerate(be_items):
        x = x_start_be + i * x_gap_be
        lines.append(_box(name, x, Y_BE, BOX_W, BOX_H, label))
    lines.append("")
    for i, (name, label, annot) in enumerate(be_items):
        x = x_start_be + i * x_gap_be
        lines.append(_annot(x, Y_BE - BOX_H/2 - 0.08, annot))
    lines.append("")
    for i in range(n_be - 1):
        src = be_items[i][0]
        dst = be_items[i+1][0]
        lines.append(_arrow(f"{src}.east", f"{dst}.west"))
    lines.append("")

    # --- Security row ---
    sec_items = [
        ("cg", "Capability\\\\[-1pt]Gating"),
        ("sl", "Step Limit"),
        ("fa", "Fault Audit"),
        ("cv", "Closed-loop\\\\[-1pt]Verify"),
    ]
    n_sec = len(sec_items)
    x_start_sec = 1.8
    x_gap_sec = 3.6
    lines.append("% Security row")
    for i, (name, label) in enumerate(sec_items):
        x = x_start_sec + i * x_gap_sec
        lines.append(_box(name, x, Y_SEC, BOX_W, BOX_H, label))
    lines.append("")

    # Enforcement bracket
    x_left = x_start_sec - BOX_W/2 - 0.3
    x_right = x_start_sec + (n_sec-1)*x_gap_sec + BOX_W/2 + 0.3
    y_bracket = Y_SEC - BOX_H/2 - 0.35
    lines.append("% Enforcement bracket")
    lines.append(f"\\draw[black!40, line width=0.4pt]")
    lines.append(f"  ({x_left:.2f}, {y_bracket:.2f}) -- ({x_right:.2f}, {y_bracket:.2f});")
    lines.append(f"\\draw[black!40, line width=0.4pt]")
    lines.append(f"  ({x_left:.2f}, {y_bracket:.2f}) -- ({x_left:.2f}, {y_bracket - 0.1:.2f});")
    lines.append(f"\\draw[black!40, line width=0.4pt]")
    lines.append(f"  ({x_right:.2f}, {y_bracket:.2f}) -- ({x_right:.2f}, {y_bracket - 0.1:.2f});")
    mid_x = (x_left + x_right) / 2
    lines.append(f"\\node[font=\\sffamily\\tiny, black!50, anchor=north] at ({mid_x:.2f}, {y_bracket - 0.05:.2f})")
    lines.append(f"  {{enforce at runtime}};")
    lines.append("")

    # --- Feedback arrow (orthogonal: fb -> llm) ---
    fb_x = x_start_be + 3 * x_gap_be  # fb x
    llm_x = x_start + 1 * x_gap       # llm x
    lines.append("% Error feedback (orthogonal)")
    lines.append(f"\\draw[darrow, black!70, line width=0.7pt]")
    lines.append(f"  ({fb_x:.2f}, {Y_BE + BOX_H/2 + 0.1:.2f})")
    lines.append(f"  -- ({fb_x:.2f}, {Y_FE - 0.1:.2f})")
    lines.append(f"  -| ({llm_x:.2f}, {Y_FE + BOX_H/2 + 0.1:.2f});")
    lines.append(f"\\node[font=\\sffamily\\tiny, black!50, anchor=south west]")
    lines.append(f"  at ({fb_x + 0.1:.2f}, {Y_FE - 0.1:.2f}) {{error feedback}};")
    lines.append("")

    lines.append("\\end{tikzpicture}")
    return "\n".join(lines)


# ── Fig 2: LIR-to-Bytecode Lowering ────────────────────────────

def gen_fig2():
    lines = []
    lines.append("% Fig.2: LIR-to-Bytecode Lowering — auto-generated")
    lines.append("\\begin{tikzpicture}[scale=0.68, transform shape,")
    lines.append("  >=Stealth, font=\\sffamily\\small,")
    lines.append("  col/.style={draw=black!80, fill=white, line width=0.5pt},")
    lines.append("]")
    lines.append("")

    # Three columns
    col_w, col_h = 4.8, 5.6
    col_gap = 1.2
    col_y = 0  # centered vertically

    col_defs = [
        ("LIR Source",
         [("require cap(relay1)", 2.2),
          ("require cap(water\\_sensor)", 1.7),
          ("set relay1 = 1", 1.2),
          ("wait 500ms", 0.7),
          ("read water\\_sensor", 0.2),
          ("halt", -0.3)],
         [("LLM-generated", -2.3), ("running example", -2.6)]),
        ("Compiler",
         [("cap(5) $\\rightarrow$ GTWAY 5", 2.2),
          ("cap(1) $\\rightarrow$ GTWAY 1", 1.7),
          ("set 1 $\\rightarrow$ LIT 1; IOW 5", 1.2),
          ("wait 500 $\\rightarrow$ WAIT 500", 0.7),
          ("read s $\\rightarrow$ IOR 1", 0.2),
          ("halt $\\rightarrow$ HALT", -0.3)],
         [("O(n) deterministic", -2.3), ("unique output", -2.6)]),
        ("Bytecode",
         [("GTWAY 5", 2.2),
          ("GTWAY 1", 1.7),
          ("LIT 1", 1.2),
          ("IOW 5", 0.7),
          ("WAIT 500", 0.2),
          ("IOR 1", -0.3),
          ("HALT", -0.8)],
         [("12 bytes", -2.3), ("varint encoded", -2.6)]),
    ]

    x_positions = []
    for ci, (title, code_lines, annots) in enumerate(col_defs):
        cx = ci * (col_w + col_gap)
        x_positions.append(cx)
        x_left = cx - col_w/2
        x_right = cx + col_w/2
        y_top = col_y + col_h/2
        y_bot = col_y - col_h/2

        # Column box
        lines.append(f"\\draw[col] ({x_left:.2f},{y_bot:.2f}) rectangle ({x_right:.2f},{y_top:.2f});")
        # Title
        lines.append(f"\\node[font=\\sffamily\\small\\bfseries, black!80] at ({cx:.2f},{y_top - 0.3:.2f}) {{{title}}};")
        # Code lines
        for text, y_off in code_lines:
            lines.append(f"\\node[font=\\ttfamily\\tiny, anchor=north west] at ({x_left + 0.2:.2f},{y_top - 0.6 + (2.2 - y_off):.2f}) {{{text}}};")
        # Annotations
        for text, y_off in annots:
            lines.append(f"\\node[font=\\sffamily\\tiny, black!40] at ({cx:.2f},{y_off:.2f}) {{{text}}};")
        lines.append("")

    # Arrows between columns
    for ci in range(len(col_defs) - 1):
        x1 = x_positions[ci] + col_w/2
        x2 = x_positions[ci+1] - col_w/2
        mid_y = col_y
        lines.append(f"\\draw[-Stealth, thick, black!70] ({x1:.2f},{mid_y:.2f}) -- ({x2:.2f},{mid_y:.2f});")

    # Arrow labels
    for ci in range(len(col_defs) - 1):
        x_mid = (x_positions[ci] + col_w/2 + x_positions[ci+1] - col_w/2) / 2
        label = "lower" if ci == 0 else "encode"
        lines.append(f"\\node[font=\\sffamily\\tiny, black!50] at ({x_mid:.2f},{col_y + 0.35:.2f}) {{{label}}};")

    lines.append("")
    lines.append("\\end{tikzpicture}")
    return "\n".join(lines)


# ── Fig 3: LVM Execution Flow ──────────────────────────────────

def gen_fig3():
    lines = []
    lines.append("% Fig.3: LVM Execution Flow — auto-generated")
    lines.append("\\begin{tikzpicture}[scale=0.72, transform shape,")
    lines.append("  >=Stealth, font=\\sffamily\\small,")
    lines.append("  stage/.style={draw=black!80, fill=white, minimum width=2.0cm,")
    lines.append("                minimum height=1.5cm, align=center, inner sep=3pt,")
    lines.append("                font=\\sffamily\\scriptsize\\bfseries},")
    lines.append("  arr/.style={-Stealth, thick, draw=black!70},")
    lines.append("  darrow/.style={-Stealth, thick, draw=black!70, dashed},")
    lines.append("]")
    lines.append("")

    stages = [
        ("s1", "FETCH",      "Load\\\\[-1pt]Frame",     "fetch bytecode"),
        ("s2", "DECODE",     "Decode\\\\[-1pt]Opcode",  "instruction decode"),
        ("s3", "VALIDATE",   "Static\\\\[-1pt]Checks",  "bounds / encoding"),
        ("s4", "GUARD",      "Runtime\\\\[-1pt]Guards", "cap / step stack"),
        ("s5", "EXECUTE",    "Execute\\\\[-1pt]IOW/IOR","stack-based exec"),
        ("s6", "OUTPUT",     "Emit\\\\[-1pt]Result",    "OK or FAULT"),
    ]

    x_start = 0.0
    x_gap = 2.4
    y_stage = 0.7
    y_label = 1.85
    y_annot = -0.15
    box_h = 1.5

    # Stage labels
    lines.append("% Stage labels")
    for i, (name, label_text, box_text, annot) in enumerate(stages):
        x = x_start + i * x_gap
        lines.append(f"\\node[font=\\sffamily\\tiny\\bfseries, black!50] at ({x:.2f}, {y_label:.2f}) {{{label_text}}};")
    lines.append("")

    # Stage boxes
    lines.append("% Stage boxes")
    for i, (name, label_text, box_text, annot) in enumerate(stages):
        x = x_start + i * x_gap
        lines.append(_box(name, x, y_stage, 2.0, box_h, box_text, "stage"))
    lines.append("")

    # Annotations
    lines.append("% Annotations")
    for i, (name, label_text, box_text, annot) in enumerate(stages):
        x = x_start + i * x_gap
        lines.append(_annot(x, y_annot, annot))
    lines.append("")

    # Arrows
    lines.append("% Pipeline arrows")
    for i in range(len(stages) - 1):
        src = stages[i][0]
        dst = stages[i+1][0]
        lines.append(_arrow(f"{src}.east", f"{dst}.west"))
    lines.append("")

    # Fault branch (below s4 = GUARD)
    fault_x = x_start + 3 * x_gap
    fault_y = y_stage - box_h/2 - 1.3
    lines.append("% Fault branch")
    lines.append(f"\\node[stage, draw=red!70, fill=red!5, minimum height=1.0cm]")
    lines.append(f"  (fault) at ({fault_x:.2f}, {fault_y:.2f}) {{Fault}};")
    lines.append(_annot(fault_x, fault_y - 0.7, "code, pc"))
    lines.append(f"\\draw[darrow, red!70] (s4.south) -- (fault.north);")
    lines.append(f"\\node[font=\\sffamily\\tiny, red!70!black, anchor=west] at ({fault_x + 1.15:.2f}, {fault_y:.2f}) {{violation}};")
    lines.append("")

    lines.append("\\end{tikzpicture}")
    return "\n".join(lines)


# ── Fig 4: Closed-Loop FSM ─────────────────────────────────────

def gen_fig4():
    lines = []
    lines.append("% Fig.4: Closed-Loop FSM — auto-generated")
    lines.append("\\begin{tikzpicture}[scale=0.70, transform shape,")
    lines.append("  >=Stealth, font=\\sffamily\\small,")
    lines.append("  state/.style={draw=black!80, fill=white, minimum width=1.8cm,")
    lines.append("                minimum height=1.0cm, align=center, inner sep=3pt,")
    lines.append("                font=\\sffamily\\scriptsize\\bfseries},")
    lines.append("  arr/.style={-Stealth, thick, draw=black!70},")
    lines.append("  darrow/.style={-Stealth, thick, draw=black!70, dashed},")
    lines.append("]")
    lines.append("")

    states = [
        ("set",  "SET",       "write device",   0.0),
        ("ack",  "ACK",       "confirm write",  2.8),
        ("read", "READBACK",  "read device",    5.8),
        ("cmp",  "COMPARE",   "match check",    8.8),
    ]

    y_state = 0
    y_annot = -0.6
    box_h = 1.0

    # Initial state (filled circle)
    init_x = -2.0
    lines.append("% Initial state")
    lines.append(f"\\fill[black] ({init_x:.2f}, {y_state:.2f}) circle (3pt);")
    lines.append(f"\\draw[arr] ({init_x + 0.15:.2f}, {y_state:.2f}) -- ({states[0][3] - 0.9:.2f}, {y_state:.2f});")
    lines.append("")

    # State boxes
    lines.append("% States")
    for name, label, annot, x in states:
        lines.append(_box(name, x, y_state, 1.8, box_h, label, "state"))
    lines.append("")

    # Annotations
    lines.append("% Annotations")
    for name, label, annot, x in states:
        lines.append(_annot(x, y_annot, annot))
    lines.append("")

    # Arrows between states
    lines.append("% State transitions")
    for i in range(len(states) - 1):
        src = states[i][0]
        dst = states[i+1][0]
        lines.append(_arrow(f"{src}.east", f"{dst}.west"))
    lines.append("")

    # CONVERGED terminal
    term_x = 12.0
    term_y_pos = 1.2
    lines.append("% CONVERGED terminal")
    lines.append(f"\\fill[black] ({term_x:.2f}, {term_y_pos:.2f}) circle (3pt);")
    lines.append(f"\\draw[line width=0.8pt] ({term_x:.2f}, {term_y_pos:.2f}) circle (7pt);")
    lines.append(f"\\draw[arr] (cmp.east) -- ++(0.4, 0) |- ({term_x:.2f}, {term_y_pos:.2f});")
    lines.append(f"\\node[font=\\sffamily\\tiny\\bfseries, black!70, anchor=south] at ({term_x:.2f}, {term_y_pos + 0.75:.2f})")
    lines.append(f"  {{CONVERGED}};")
    lines.append("")

    # SAFE/FAULT terminal
    term_y_neg = -1.2
    lines.append("% SAFE/FAULT terminal")
    lines.append(f"\\fill[black] ({term_x:.2f}, {term_y_neg:.2f}) circle (3pt);")
    lines.append(f"\\draw[line width=0.8pt] ({term_x:.2f}, {term_y_neg:.2f}) circle (7pt);")
    lines.append(f"\\draw[arr] (cmp.east) -- ++(0.4, 0) |- ({term_x:.2f}, {term_y_neg:.2f});")
    lines.append(f"\\node[font=\\sffamily\\tiny\\bfseries, red!70!black, anchor=north] at ({term_x:.2f}, {term_y_neg - 0.75:.2f})")
    lines.append(f"  {{SAFE/FAULT}};")
    lines.append("")

    # Retry loop (orthogonal dashed)
    retry_y = -1.8
    lines.append("% Retry loop")
    lines.append(f"\\draw[darrow]")
    lines.append(f"  ({states[3][3]:.2f}, {y_state - box_h/2 - 0.05:.2f})")
    lines.append(f"  |- ({states[0][3]:.2f}, {retry_y:.2f})")
    lines.append(f"  -| ({states[0][3]:.2f}, {y_state - box_h/2 - 0.05:.2f});")
    lines.append(f"\\node[font=\\sffamily\\tiny, black!50, anchor=north] at ({(states[0][3] + states[3][3])/2:.2f}, {retry_y:.2f})")
    lines.append(f"  {{mismatch $\\rightarrow$ retry}};")
    lines.append("")

    lines.append("\\end{tikzpicture}")
    return "\n".join(lines)


# ── Fig 5: Generation Pipeline with Repair Loop ─────────────────

def gen_fig5():
    lines = []
    lines.append("% Fig.5: Generation Pipeline with Repair Loop — auto-generated")
    lines.append("\\begin{tikzpicture}[scale=0.52, transform shape,")
    lines.append("  >=Stealth, font=\\sffamily\\small,")
    lines.append("  box/.style={draw=black!80, fill=white, minimum width=1.8cm,")
    lines.append("              minimum height=0.9cm, align=center, inner sep=2pt,")
    lines.append("              font=\\sffamily\\scriptsize\\bfseries},")
    lines.append("  arr/.style={-Stealth, thick, draw=black!70},")
    lines.append("  darrow/.style={-Stealth, thick, draw=black!70, dashed},")
    lines.append("]")
    lines.append("")

    # Layout
    Y_MAIN = 3.2
    Y_REP = 0.6
    BOX_W, BOX_H = 1.8, 0.9

    # --- Layer backgrounds ---
    lines.append("% Layer backgrounds")
    lines.append("\\fill[black!3, draw=black!15, line width=0.3pt]")
    lines.append("  (-0.6, 2.1) rectangle (15.8, 4.5);")
    lines.append("\\node[font=\\sffamily\\small\\bfseries, black!60, anchor=north west]")
    lines.append("  at (-0.5, 4.45) {Generation Pipeline};")
    lines.append("")
    lines.append("\\fill[black!3, draw=black!15, line width=0.3pt]")
    lines.append("  (-0.6, -0.6) rectangle (15.8, 1.8);")
    lines.append("\\node[font=\\sffamily\\small\\bfseries, black!60, anchor=north west]")
    lines.append("  at (-0.5, 1.75) {Repair Loop (on failure)};")
    lines.append("")

    # --- Main pipeline ---
    main_items = [
        ("tp",  "Task\\\\[-1pt]Prompt",  "NL goal +"),
        ("llm", "LLM",                  "structured"),
        ("lir", "LIR",                  "textual DSL"),
        ("cmp", "Compiler",             "IR lowering +"),
        ("vfy", "Verifier",             "opcode / varint /"),
        ("lvm", "LVM",                  "bounded exec."),
    ]

    x_start = 0.8
    x_gap = 2.5
    lines.append("% Main pipeline")
    for i, (name, label, annot) in enumerate(main_items):
        x = x_start + i * x_gap
        lines.append(_box(name, x, Y_MAIN, BOX_W, BOX_H, label))
    lines.append("")
    for i, (name, label, annot) in enumerate(main_items):
        x = x_start + i * x_gap
        lines.append(_annot(x, Y_MAIN - BOX_H/2 - 0.08, annot))
    lines.append("")
    for i in range(len(main_items) - 1):
        src = main_items[i][0]
        dst = main_items[i+1][0]
        lines.append(_arrow(f"{src}.east", f"{dst}.west"))
    lines.append("")

    # --- Repair loop ---
    rep_items = [
        ("out", "LVM\\\\[-1pt]Output",     "OK or"),
        ("prs", "Parse\\\\[-1pt]Result",    "stage /"),
        ("err", "Error\\\\[-1pt]Formatter", "stage / code /"),
        ("rep", "LLM\\\\[-1pt]Repair",      "regenerate"),
        ("flt", "Fault\\\\[-1pt]Trace",     "pc / fault /"),
    ]

    x_start_rep = 0.8
    x_gap_rep = 2.6
    lines.append("% Repair loop")
    for i, (name, label, annot) in enumerate(rep_items):
        x = x_start_rep + i * x_gap_rep
        style = "box" if name != "err" else "box, draw=red!70, fill=red!5"
        lines.append(_box(name, x, Y_REP, BOX_W, BOX_H, label, style))
    lines.append("")
    for i, (name, label, annot) in enumerate(rep_items):
        x = x_start_rep + i * x_gap_rep
        lines.append(_annot(x, Y_REP - BOX_H/2 - 0.08, annot))
    lines.append("")
    for i in range(len(rep_items) - 1):
        src = rep_items[i][0]
        dst = rep_items[i+1][0]
        lines.append(_arrow(f"{src}.east", f"{dst}.west"))
    lines.append("")

    # LVM -> LVM Output (vertical)
    lvm_x = x_start + 5 * x_gap
    out_x = x_start_rep
    lines.append("% LVM -> Repair entry")
    lines.append(f"\\draw[arr] (lvm.south) -- ++(0, -0.4) -| (out.north);")
    lines.append("")

    # Accept box
    prs_x = x_start_rep + 1 * x_gap_rep
    lines.append("% Accept box")
    lines.append(f"\\node[draw=black!60, fill=black!5, minimum width=1.4cm, minimum height=0.55cm,")
    lines.append(f"      font=\\sffamily\\tiny\\bfseries, align=center, inner sep=2pt]")
    lines.append(f"  (acc) at ({prs_x:.2f}, -1.1) {{Accept}};")
    lines.append(_annot(prs_x, -1.45, "task done"))
    lines.append(f"\\draw[arr] (prs.south) -- (acc.north);")
    lines.append(f"\\node[font=\\sffamily\\tiny, black!60, anchor=west] at ({prs_x + 0.85:.2f}, -0.85) {{OK}};")
    lines.append("")

    # Re-compile arrow (orthogonal dashed: rep -> cmp)
    rep_x = x_start_rep + 3 * x_gap_rep
    cmp_x = x_start + 3 * x_gap
    lines.append("% Re-compile (orthogonal dashed)")
    lines.append(f"\\draw[darrow, black!70, line width=0.7pt]")
    lines.append(f"  ({rep_x:.2f}, {Y_REP + BOX_H/2 + 0.1:.2f})")
    lines.append(f"  -- ({rep_x:.2f}, {Y_MAIN - 0.1:.2f})")
    lines.append(f"  -| ({cmp_x:.2f}, {Y_MAIN + BOX_H/2 + 0.1:.2f});")
    lines.append(f"\\node[font=\\sffamily\\tiny, black!50, anchor=south west]")
    lines.append(f"  at ({rep_x + 0.1:.2f}, {Y_MAIN - 0.1:.2f}) {{re-compile}};")
    lines.append(f"\\node[font=\\sffamily\\tiny, black!40, anchor=north west]")
    lines.append(f"  at ({rep_x + 0.1:.2f}, {Y_MAIN - 0.35:.2f}) {{(max 3 rounds)}};")
    lines.append("")

    lines.append("\\end{tikzpicture}")
    return "\n".join(lines)


# ── Main ────────────────────────────────────────────────────────

def main():
    os.makedirs(LATEX_DIR, exist_ok=True)

    generators = {
        "fig1_tikz.tex": gen_fig1,
        "fig2_tikz.tex": gen_fig2,
        "fig3_tikz.tex": gen_fig3,
        "fig4_tikz.tex": gen_fig4,
        "fig5_tikz.tex": gen_fig5,
    }

    for fname, gen_fn in generators.items():
        path = os.path.join(LATEX_DIR, fname)
        content = gen_fn()
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"  [OK] {fname}")

    print(f"\nAll 5 TikZ figures generated in {LATEX_DIR}")


if __name__ == "__main__":
    main()
