# E10 Deploy Metrics

| 平台 | 场景 | 指标 | 数值 | 单位 | n | 结果文件 | 备注 |
|---|---|---|---:|---|---:|---|---|
| ESP8266 | E2 guarded | 平均功耗 | [待填] | mA | [待填] | `论文分区/ccfc/result/E10_deploy/power_manual.csv` | 需外接功耗仪采样并填写 power_manual.csv |
| ESP8266 | E2 guarded | 单任务能耗 | [待填] | mWh/task | [待填] | `论文分区/ccfc/result/E10_deploy/power_manual.csv` | 需外接功耗仪采样并填写 power_manual.csv |
| ESP8266 | E2 guarded | 吞吐 | 96.530 | cmd/s | 1000 | `论文分区/ccfc/result/E10_deploy/throughput_summary.csv` | 串口端到端实测 |
| ESP8266 | E2 guarded | 峰值 stack 水位 | 144.000 | B | 55 | `论文分区/ccfc/result/E10_deploy/e3_mem_summary.csv` | 以 free_stack(max-min) 作为水位代理 |
| ESP8266 | E2 guarded | 峰值 heap 水位 | 0.000 | B | 55 | `论文分区/ccfc/result/E10_deploy/e3_mem_summary.csv` | 以 free_heap(max-min) 作为水位代理 |
| ESP8266 | E4 guarded | P95 RTT | 38.960 | ms | 100 | `论文分区/ccfc/result/E4/e4_trials.csv` | G3_m_with_o 的 rtt_total_ms 分位数 |
