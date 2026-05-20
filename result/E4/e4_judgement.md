# E4 Strict SCR Judgement

- Generated: 2026-02-12 19:48:44
- Variant: guarded
- Repeat per group: 100
- Disturbance probability: 0.3
- G1 parse-noise probability: 0.15
- G3 max retry: 3

| Group | n | converged | SCR | RTT mean(ms) | attempts_mean |
|---|---:|---:|---:|---:|---:|
| G1_text_proxy | 100 | 56 | 0.560000 | 18.389 | 1.000 |
| G2_m_no_o | 100 | 66 | 0.660000 | 18.598 | 1.000 |
| G4_m_with_o_no_retry | 100 | 66 | 0.660000 | 18.572 | 1.000 |
| G3_m_with_o | 100 | 100 | 1.000000 | 24.424 | 1.340 |

- Delta SCR (G4 - G2): 0.000000
- Delta SCR (G3 - G4): 0.340000
- Delta SCR (G3 - G2): 0.340000
- Verdict: PASS (readback-only shows no standalone SCR gain; improvement mainly comes from retry-enabled closed-loop).

## Notes
- G1 is a proxy text baseline (parse-noise simulation), not a full JSON parser execution path.
- Strict SCR uses physical readback comparison of relay target state.
