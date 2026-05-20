# E1 Multi-Batch Judgement

- Generated: 2026-02-11 10:17:55
- Tags: 20260211_100520_mb1, 20260211_100603_mb2, 20260211_100645_mb3, 20260211_100728_mb4, 20260211_100810_mb5
- Total batches: 5
- Rule source: `论文分区/ccfc/result/E1/e1_data_rules.md`

## Compression

- R1 bytes_M < bytes_JSON (all tasks): PASS
- R_avg (mean of R_task): 4.409x
- R_weighted (sum JSON / sum M): 4.605x

## Latency (IO Tasks Only)

- R3 median_M < median_JSON for IO tasks: PASS
- relay1_on: median_M=3.589 ms, median_JSON=5.603 ms, delta(JSON-M)=2.014 ms => PASS
- relay1_off: median_M=3.614 ms, median_JSON=5.534 ms, delta(JSON-M)=1.920 ms => PASS
- water_read: median_M=3.458 ms, median_JSON=4.800 ms, delta(JSON-M)=1.342 ms => PASS
- temp_read: median_M=3.450 ms, median_JSON=4.813 ms, delta(JSON-M)=1.363 ms => PASS

## Stability

- relay1_on: outlier_rate(M/JSON)=0.000/0.000, trimmed_std(M/JSON)=0.306/0.305 ms
- relay1_off: outlier_rate(M/JSON)=0.000/0.000, trimmed_std(M/JSON)=0.304/0.316 ms
- water_read: outlier_rate(M/JSON)=0.000/0.000, trimmed_std(M/JSON)=0.310/0.315 ms
- temp_read: outlier_rate(M/JSON)=0.020/0.000, trimmed_std(M/JSON)=0.301/0.298 ms
- temp_read/M outlier-iter histogram: iter=1 -> 5

## Semantic Check

- R5 combo_on_wait_read median_M in [500,520] ms: PASS (observed 504.369 ms)
- combo task is excluded from protocol-overhead speed conclusion by rule.

## Files

- `论文分区/ccfc/result/E1/e1_multibatch_summary.csv`
- `论文分区/ccfc/result/E1/e1_multibatch_compare.csv`
- `论文分区/ccfc/result/E1/e1_multibatch_compression.csv`
- `论文分区/ccfc/result/E1/e1_multibatch_outliers.csv`
- `论文分区/ccfc/result/E1/e1_temp_m_outlier_iter_hist.csv`
- `论文分区/ccfc/result/E1/e1_multibatch_judgement.md`

