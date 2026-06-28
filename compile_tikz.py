#!/usr/bin/env python3
"""Compile TikZ files to standalone PDFs."""
import subprocess
import os
import shutil

# TikZ files to compile
tikz_files = [
    "fig_intro_pipeline.tex",
    "fig1_tikz.tex",
    "fig2_tikz.tex",
    "fig3_tikz.tex",
    "fig4_tikz.tex",
    "fig5_tikz.tex",
]

# Mapping from TikZ filename to output PDF name
name_mapping = {
    "fig_intro_pipeline.tex": "fig_intro_pipeline.pdf",
    "fig1_tikz.tex": "fig1_tikz.pdf",
    "fig2_tikz.tex": "fig2_tikz.pdf",
    "fig3_tikz.tex": "fig3_tikz.pdf",
    "fig4_tikz.tex": "fig4_tikz.pdf",
    "fig5_tikz.tex": "fig5_tikz.pdf",
}

def create_standalone_tex(tikz_content, output_name):
    """Create a standalone LaTeX document wrapping TikZ content."""
    return r"""\documentclass[border=2pt]{standalone}
\usepackage{tikz}
\usetikzlibrary{arrows.meta,positioning,calc}
\usepackage{amssymb}
\begin{document}
""" + tikz_content + r"""
\end{document}
"""

def compile_tikz_to_pdf(tikz_file, output_pdf):
    """Compile a TikZ file to PDF."""
    print(f"Compiling {tikz_file}...")

    # Read TikZ content
    with open(tikz_file, 'r', encoding='utf-8') as f:
        tikz_content = f.read()

    # Create standalone LaTeX file
    standalone_tex = create_standalone_tex(tikz_content, output_pdf)
    temp_tex = "temp_standalone.tex"

    with open(temp_tex, 'w', encoding='utf-8') as f:
        f.write(standalone_tex)

    # Compile with pdflatex
    try:
        result = subprocess.run(
            ["pdflatex", "-interaction=nonstopmode", temp_tex],
            capture_output=True,
            text=True,
            timeout=60
        )

        if result.returncode == 0:
            # Move PDF to output location
            temp_pdf = "temp_standalone.pdf"
            if os.path.exists(temp_pdf):
                shutil.move(temp_pdf, output_pdf)
                print(f"  [OK] Created {output_pdf}")
                return True
            else:
                print(f"  [FAIL] PDF not generated for {tikz_file}")
                return False
        else:
            print(f"  [FAIL] Compilation failed for {tikz_file}")
            print(f"    Error: {result.stderr[:200]}")
            return False
    except subprocess.TimeoutExpired:
        print(f"  [FAIL] Timeout compiling {tikz_file}")
        return False
    finally:
        # Cleanup temp files
        for ext in ['.tex', '.aux', '.log']:
            if os.path.exists(f"temp_standalone{ext}"):
                os.remove(f"temp_standalone{ext}")

def main():
    os.chdir("latex")

    success_count = 0
    for tikz_file in tikz_files:
        if os.path.exists(tikz_file):
            output_pdf = name_mapping[tikz_file]
            if compile_tikz_to_pdf(tikz_file, output_pdf):
                success_count += 1
        else:
            print(f"  [FAIL] {tikz_file} not found")

    print(f"\nCompiled {success_count}/{len(tikz_files)} TikZ files successfully.")

    # Move PDFs to figures directory
    print("\nMoving PDFs to figures/ directory...")
    for tikz_file in tikz_files:
        output_pdf = name_mapping[tikz_file]
        if os.path.exists(output_pdf):
            dest = f"../figures/{output_pdf}"
            shutil.copy2(output_pdf, dest)
            print(f"  [OK] {output_pdf} -> figures/")

if __name__ == "__main__":
    main()
