#!/usr/bin/env bash
# reproduce_software_only.sh
# ---------------------------------------------------------------------------
# Reproduces the paper's hardware-independent and LLM-independent results using
# only the Python reference implementation. No MCU, no serial port, and no
# Ollama/LLM server are required.
#
# What this DOES reproduce (deterministic, offline):
#   * Compiler + VM unit tests (compiler-VM consistency)
#   * E1 payload-size rows: compact bytecode vs JSON vs MessagePack (Table:encoding)
#   * E2-Fuzz adversarial containment campaign (Table:fuzzing) -> 0 escapes
#
# What this does NOT reproduce (requires external resources, see README):
#   * TSR / generation-reliability numbers   -> need a local Ollama LLM server
#   * On-device RTT and energy               -> need ESP8266 / STM32 + INA219
#
# Usage:
#   bash reproduce_software_only.sh
# ---------------------------------------------------------------------------
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TOOLS="$HERE/tools"
RESULT="$HERE/result"
SEED=42

echo "==========================================================="
echo " LIR + LVM  --  software-only reproduction (seed=$SEED)"
echo "==========================================================="

echo
echo ">>> [1/3] Compiler + VM unit tests (compiler-VM consistency)"
( cd "$TOOLS" && python -m unittest test_mir_compiler -v )

echo
echo ">>> [2/3] E1 payload sizes (compact bytecode vs JSON vs MessagePack)"
echo "        (no --serial: RTT skipped, size rows written to result/E1/)"
( cd "$HERE" && python tools/bench_e1.py --protos M,JSON,MSG --out-dir "$RESULT/E1" --tag repro --write-latest )

echo
echo ">>> [3/3] E2-Fuzz adversarial bytecode fuzzing (8000 payloads)"
( cd "$TOOLS" && python bench_e2_fuzzing.py --n 8000 --seed "$SEED" --out "$RESULT/E2/fuzzing.csv" )

echo
echo "==========================================================="
echo " Done. Key artifacts:"
echo "   $RESULT/E1/   (payload-size CSVs -> Table 'encoding')"
echo "   $RESULT/E2/fuzzing.csv   (per-payload containment -> Table 'fuzzing')"
echo "==========================================================="
echo " Expected fuzzing headline: overall containment 0.9999, escapes = 0."
