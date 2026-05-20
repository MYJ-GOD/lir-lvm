# E1 数据判定与报告规则（规范版）

## 1. 目标与基准

- 本规则用于 E1（M vs JSON）复测的数据判定与论文报告口径统一。
- 语义基准：`m_vm.c` 的执行语义为唯一基准。
- 原始数据必须完整保留，不允许删除或手工改写单个样本点。

## 2. 采样设计

- 每批次：每个 task/proto 采样 `repeat=50`。
- 批次数：`5` 批。
- 总样本：每个 task/proto 共 `250` 个 RTT 点。
- 比较协议：`M` 与 `JSON`（均走 fw-proto）。

## 3. 指标定义

- 逐任务压缩率：`R_task = bytes_JSON / bytes_M`。
- 平均压缩率（论文主口径）：`R_avg = mean(R_task)`（对任务做等权平均）。
- 加权压缩率（附录可选）：`R_weighted = sum(bytes_JSON) / sum(bytes_M)`。
- RTT 报告项：`mean`、`std`、`median`、`p95`、`min`、`max`。
- 鲁棒离群判定（MAD）：
  - `MAD = median(|x_i - median(x)|)`；
  - `robust_z = 0.6745 * (x_i - median) / MAD`（`MAD=0` 时不判离群）；
  - `|robust_z| > 3.5` 记为离群点。
- 修剪统计（trimmed）：去除离群点后计算 `trimmed_mean`、`trimmed_std`。

## 4. 判定规则

- R1（压缩优势）：所有任务必须满足 `bytes_M < bytes_JSON`（即 `R_task > 1`）。
- R2（时延主比较范围）：只在无显式等待语义任务上比较协议开销：
  - `relay1_on`、`relay1_off`、`water_read`、`temp_read`。
- R3（时延优势）：对 R2 的每个任务，要求 `median_M < median_JSON`。
- R4（稳定性）：对 R2 的每个任务，记录离群率 `outlier_rate = outliers / n`；
  - 论文主文报告 `median/p95/trimmed_std`；
  - `std` 保留但不单独作为否决项（避免被单点抖动主导）。
- R5（语义一致性检查）：`combo_on_wait_read` 含 `WAIT(500ms)`，应单独解释：
  - M 侧 RTT 需体现等待语义（约 `500ms + 固定开销`）；
  - 不把该任务纳入“协议开销快慢”结论。

## 5. 论文报告要求

- 主文必须并列报告：`median`、`p95`、`trimmed_std` 与离群率。
- 附录保留：完整原始样本 CSV 与批次级统计。
- 若出现单点尖峰，不删原始点；在文中说明其频度、幅度与对均值/方差的影响。
