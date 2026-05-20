# JSON Baseline Eval Summary

- total: 3
- json_valid_rate: 1.000 (95% CI [0.439, 1.000])
- structural_ok_rate: 1.000
- execution_pass_rate: 1.000
- task_success_rate: 1.000 (95% CI [0.439, 1.000])

## Size Comparison (structurally valid JSON only)

- n: 3
- Avg raw JSON (LLM output):  92.0 bytes
- Avg compact JSON:           92.0 bytes
- Avg zlib (level 9):         84.3 bytes
- Avg CBOR:                   63.0 bytes
- Avg M-bytecode (golden):    7.0 bytes
- M vs raw JSON:      13.1x compression
- M vs compact JSON:  13.1x compression
- M vs zlib JSON:     12.0x compression
- M vs CBOR:          9.0x compression

## Error Breakdown

- none

## Comparison to Direct Hex Baseline

| Metric | Direct Hex | JSON + Schema | M-IR (golden) |
|---|---|---|---|
| ir_valid_rate | 0.000 | 1.000 | 1.000 |
| task_success_rate | 0.000 | 1.000 | 1.000 |
| Avg payload bytes | N/A | 84.3 (zlib) | 7.0 |
