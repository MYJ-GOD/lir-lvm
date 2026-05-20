# JSON Baseline Eval Summary

- total: 113
- json_valid_rate: 1.000 (95% CI [0.967, 1.000])
- structural_ok_rate: 1.000
- execution_pass_rate: 1.000
- task_success_rate: 0.965 (95% CI [0.913, 0.986])

## Size Comparison (structurally valid JSON only)

- n: 113
- Avg raw JSON (LLM output):  156.4 bytes
- Avg compact JSON:           147.4 bytes
- Avg zlib (level 9):         106.7 bytes
- Avg CBOR:                   105.2 bytes
- Avg M-bytecode (golden):    10.9 bytes
- M vs raw JSON:      14.3x compression
- M vs compact JSON:  13.5x compression
- M vs zlib JSON:     9.8x compression
- M vs CBOR:          9.6x compression

## Error Breakdown

- TASK_SIGNATURE_MISMATCH: 4

## Comparison to Direct Hex Baseline

| Metric | Direct Hex | JSON + Schema | M-IR (golden) |
|---|---|---|---|
| ir_valid_rate | 0.000 | 1.000 | 1.000 |
| task_success_rate | 0.000 | 0.965 | 1.000 |
| Avg payload bytes | N/A | 106.7 (zlib) | 10.9 |
