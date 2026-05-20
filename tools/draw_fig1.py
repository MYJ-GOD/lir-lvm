#!/usr/bin/env python3
"""Generate Fig.1 system architecture SVG."""
from __future__ import annotations

SVG_TEMPLATE = '''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 960 620" width="960" height="620">
  <defs>
    <marker id="arrow" viewBox="0 0 10 6" refX="10" refY="3"
            markerWidth="10" markerHeight="6" orient="auto-start-reverse">
      <path d="M 0 0 L 10 3 L 0 6 z" fill="#333"/>
    </marker>
    <marker id="arrow-blue" viewBox="0 0 10 6" refX="10" refY="3"
            markerWidth="10" markerHeight="6" orient="auto-start-reverse">
      <path d="M 0 0 L 10 3 L 0 6 z" fill="#2563eb"/>
    </marker>
    <marker id="arrow-red" viewBox="0 0 10 6" refX="10" refY="3"
            markerWidth="10" markerHeight="6" orient="auto-start-reverse">
      <path d="M 0 0 L 10 3 L 0 6 z" fill="#dc2626"/>
    </marker>
    <style>
      .box { rx: 8; ry: 8; stroke-width: 1.5; }
      .box-frontend { fill: #dbeafe; stroke: #2563eb; }
      .box-backend  { fill: #fce7f3; stroke: #db2777; }
      .box-hw       { fill: #fef3c7; stroke: #d97706; }
      .box-security { fill: #fee2e2; stroke: #dc2626; }
      .box-io       { fill: #e0e7ff; stroke: #4f46e5; }
      .label { font-family: "Segoe UI", Arial, sans-serif; font-size: 13px; fill: #1e293b; text-anchor: middle; dominant-baseline: central; }
      .label-sm { font-family: "Segoe UI", Arial, sans-serif; font-size: 11px; fill: #475569; text-anchor: middle; dominant-baseline: central; }
      .title { font-family: "Segoe UI", Arial, sans-serif; font-size: 15px; font-weight: bold; fill: #0f172a; text-anchor: middle; }
      .section-title { font-family: "Segoe UI", Arial, sans-serif; font-size: 13px; font-weight: bold; fill: #334155; text-anchor: start; }
      .arrow-line { stroke: #333; stroke-width: 1.5; fill: none; marker-end: url(#arrow); }
      .arrow-blue { stroke: #2563eb; stroke-width: 1.5; fill: none; marker-end: url(#arrow-blue); stroke-dasharray: 6,3; }
      .arrow-red  { stroke: #dc2626; stroke-width: 1.5; fill: none; marker-end: url(#arrow-red); stroke-dasharray: 4,3; }
      .brace { stroke: #94a3b8; stroke-width: 1; fill: none; }
      .brace-label { font-family: "Segoe UI", Arial, sans-serif; font-size: 11px; fill: #64748b; }
    </style>
  </defs>

  <!-- Background -->
  <rect width="960" height="620" fill="#fafbfc" rx="12"/>

  <!-- Title -->
  <text x="480" y="32" class="title">M-IR + MVM System Architecture</text>

  <!-- ==================== FRONTEND (top half) ==================== -->
  <text x="30" y="62" class="section-title">Frontend: LLM Generation Pipeline</text>

  <!-- NL -->
  <rect class="box box-io" x="30" y="80" width="120" height="48"/>
  <text class="label" x="90" y="104">Natural Language</text>

  <!-- Arrow: NL -> LLM -->
  <line class="arrow-line" x1="150" y1="104" x2="195" y2="104"/>

  <!-- LLM -->
  <rect class="box box-frontend" x="200" y="80" width="100" height="48"/>
  <text class="label" x="250" y="98">LLM</text>
  <text class="label-sm" x="250" y="114">(llama / qwen)</text>

  <!-- Arrow: LLM -> M-IR -->
  <line class="arrow-line" x1="300" y1="104" x2="345" y2="104"/>

  <!-- M-IR -->
  <rect class="box box-frontend" x="350" y="72" width="110" height="64"/>
  <text class="label" x="405" y="94">M-IR</text>
  <text class="label-sm" x="405" y="112">structured DSL</text>
  <text class="label-sm" x="405" y="126">v0.1 syntax</text>

  <!-- Arrow: M-IR -> Compiler -->
  <line class="arrow-line" x1="460" y1="104" x2="505" y2="104"/>

  <!-- Compiler -->
  <rect class="box box-frontend" x="510" y="80" width="100" height="48"/>
  <text class="label" x="560" y="98">Compiler</text>
  <text class="label-sm" x="560" y="114">deterministic</text>

  <!-- Arrow: Compiler -> Verifier -->
  <line class="arrow-line" x1="610" y1="104" x2="655" y2="104"/>

  <!-- Verifier -->
  <rect class="box box-security" x="660" y="80" width="100" height="48"/>
  <text class="label" x="710" y="98">Verifier</text>
  <text class="label-sm" x="710" y="114">static check</text>

  <!-- Arrow: Verifier -> M-bytecode -->
  <line class="arrow-line" x1="760" y1="104" x2="805" y2="104"/>

  <!-- M-bytecode (bridge between frontend and backend) -->
  <rect class="box box-io" x="810" y="80" width="120" height="48"/>
  <text class="label" x="870" y="98">M-bytecode</text>
  <text class="label-sm" x="870" y="114">compact payload</text>

  <!-- ==================== BACKEND (bottom half) ==================== -->
  <text x="30" y="210" class="section-title">Backend: MCU Execution &amp; Safety</text>

  <!-- Transmission -->
  <rect class="box box-io" x="30" y="230" width="100" height="48"/>
  <text class="label" x="80" y="248">Transmission</text>
  <text class="label-sm" x="80" y="264">serial / WiFi</text>

  <!-- Arrow: Transmission -> MVM -->
  <line class="arrow-line" x1="130" y1="254" x2="175" y2="254"/>

  <!-- MVM -->
  <rect class="box box-backend" x="180" y="218" width="160" height="72"/>
  <text class="label" x="260" y="244">MVM (Virtual Machine)</text>
  <text class="label-sm" x="260" y="262">ESP8266 / MCU</text>
  <text class="label-sm" x="260" y="278">stack-based execution</text>

  <!-- Arrow: MVM -> Hardware -->
  <line class="arrow-line" x1="340" y1="254" x2="385" y2="254"/>

  <!-- Hardware -->
  <rect class="box box-hw" x="390" y="230" width="140" height="48"/>
  <text class="label" x="460" y="248">Hardware I/O</text>
  <text class="label-sm" x="460" y="264">relay / sensor</text>

  <!-- Arrow: Hardware -> Feedback -->
  <line class="arrow-line" x1="530" y1="254" x2="575" y2="254"/>

  <!-- Feedback -->
  <rect class="box box-io" x="580" y="230" width="120" height="48"/>
  <text class="label" x="640" y="248">Feedback</text>
  <text class="label-sm" x="640" y="264">fault / readback</text>

  <!-- Arrow: Feedback -> Repair -->
  <line class="arrow-line" x1="700" y1="254" x2="745" y2="254"/>

  <!-- Repair -->
  <rect class="box box-frontend" x="750" y="230" width="100" height="48"/>
  <text class="label" x="800" y="248">Repair Loop</text>
  <text class="label-sm" x="800" y="264">structured fix</text>

  <!-- ==================== Security annotations ==================== -->
  <text x="30" y="340" class="section-title">Security Mechanisms (runtime)</text>

  <!-- Capability gating -->
  <rect class="box box-security" x="30" y="355" width="140" height="40"/>
  <text class="label" x="100" y="375">Capability Gating</text>

  <!-- Step limit -->
  <rect class="box box-security" x="190" y="355" width="120" height="40"/>
  <text class="label" x="250" y="375">Step Limit</text>

  <!-- Fault audit -->
  <rect class="box box-security" x="330" y="355" width="120" height="40"/>
  <text class="label" x="390" y="375">Fault Audit</text>

  <!-- Closed-loop -->
  <rect class="box box-security" x="470" y="355" width="140" height="40"/>
  <text class="label" x="540" y="375">Closed-loop Verify</text>

  <!-- Arrow from security to MVM -->
  <line class="arrow-red" x1="100" y1="355" x2="220" y2="290"/>
  <line class="arrow-red" x1="250" y1="355" x2="260" y2="290"/>
  <line class="arrow-red" x1="390" y1="355" x2="300" y2="290"/>
  <line class="arrow-red" x1="540" y1="355" x2="320" y2="290"/>

  <!-- ==================== Data flow annotations ==================== -->
  <!-- Dotted blue arrow: feedback back to LLM -->
  <path class="arrow-blue" d="M 640,230 C 640,180 300,180 250,128"/>
  <text class="label-sm" fill="#2563eb" x="440" y="172">error feedback for repair</text>

  <!-- ==================== Legend ==================== -->
  <rect x="660" y="340" width="280" height="100" fill="#f8fafc" stroke="#cbd5e1" rx="6"/>
  <text class="label-sm" x="680" y="360" text-anchor="start" font-weight="bold">Legend</text>
  <rect x="680" y="370" width="12" height="12" class="box box-frontend" stroke-width="1"/>
  <text class="label-sm" x="700" y="380" text-anchor="start">Frontend (generation)</text>
  <rect x="680" y="390" width="12" height="12" class="box box-backend" stroke-width="1"/>
  <text class="label-sm" x="700" y="400" text-anchor="start">Backend (execution)</text>
  <rect x="680" y="410" width="12" height="12" class="box box-security" stroke-width="1"/>
  <text class="label-sm" x="700" y="420" text-anchor="start">Security mechanism</text>
  <rect x="810" y="370" width="12" height="12" class="box box-hw" stroke-width="1"/>
  <text class="label-sm" x="830" y="380" text-anchor="start">Hardware</text>
  <rect x="810" y="390" width="12" height="12" class="box box-io" stroke-width="1"/>
  <text class="label-sm" x="830" y="400" text-anchor="start">Data / I/O</text>
  <line x1="810" y1="418" x2="840" y2="418" class="arrow-blue" stroke-width="1"/>
  <text class="label-sm" x="848" y="418" text-anchor="start">Feedback path</text>

</svg>'''

def main():
    out = Path(__file__).resolve().parent.parent / "figures" / "Fig1_architecture.svg"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(SVG_TEMPLATE, encoding="utf-8")
    print(f"Written: {out}")

if __name__ == "__main__":
    from pathlib import Path
    main()
