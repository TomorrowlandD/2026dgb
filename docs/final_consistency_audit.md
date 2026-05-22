# 最终一致性审查

## 审查结论

当前阶段 0-6 的主模型结果可以继续使用，不需要推倒重算，也不需要重画核心图。当前主要任务是统一方案文档和论文解释口径，并进入论文正文写作。

已修复的问题：基准问题 3 的最终价格与问题 4 中 S0 的 `price_summary` 已统一，均为“助餐 7 元、日间照料 18 元、上门护理 29 元、康复理疗 27 元、助浴 21 元、紧急救助 0 元”。该修复只统一并列候选定价的输出口径，不改变核心覆盖率、满意度、补贴、利润率和年度净收益结果。

## 检查清单

| 检查项 | 当前状态 | 依据 | 结论 |
|---|---|---|---|
| Q1 是否采用等比例削减 | 已满足 | `outputs/logs/stage2_problem1_check.md`；`src/run_stage2_problem1.py` | 通过 |
| 紧急救助是否未被消费约束削减 | 已满足 | `problem1_actual_demand_by_community_service.csv` 中紧急救助保留率为 1 | 通过 |
| Q2 排序目标是否不含年化利润 | 已满足 | `src/run_stage3_problem2.py` 的 `ranking_key` 为 `CR_srv, CR_eff, weighted_satisfaction, DR, -construction_cost` | 通过 |
| Q3 是否每组价格重新计算 `S3` | 已满足 | `outputs/logs/stage4_problem3_check.md` | 通过 |
| Q3 是否每组价格重新计算有效服务人次 `E` | 已满足 | `outputs/logs/stage4_problem3_check.md` | 通过 |
| 紧急救助是否不计补贴 | 已满足 | `outputs/logs/stage4_problem3_check.md` | 通过 |
| 紧急救助是否计入直接服务成本 | 已满足 | `outputs/logs/stage4_problem3_check.md` | 通过 |
| 利润率是否为题目口径 | 已满足 | `rho=(ServiceProfit+G-OC)/OC` | 通过 |
| 年度净收益是否单独输出 | 已满足 | `outputs/tables/problem3_station_finance.csv`、`problem4_scenario_metrics.csv` | 通过 |
| 是否未将 `rho >= 0` 作为硬约束 | 已满足 | `outputs/logs/stage4_problem3_check.md` | 通过 |
| Q4 是否完整重求解 | 已满足 | `outputs/logs/stage5_problem4_check.md` | 通过 |
| 是否存在亏损站点 | 存在 | 基准方案 C 站年度净收益为 -98068.66 元 | 需要论文解释 |
| 是否存在亏损情景 | 存在 | S2、S3、S4 年度净收益总额为负 | 需要论文解释 |
| 对亏损结果的解释是否准备充分 | 已在方案中要求 | `docs/revised_modeling_plan.md`、`docs/final_revision_notes.md` | 通过但写作时需执行 |
| Q3价格表与Q4价格摘要是否一致 | 已满足 | `problem3_prices.csv` 与 `problem4_scenario_metrics.csv` 的 S0 `price_summary` 均为 7/18/29/27/21/0 | 通过 |

## 亏损风险记录

### 基准问题 3

基准问题 3 中：

- C 站年度净收益为 `-98,068.66` 元；
- D 站年度净收益为 `95,130.46` 元；
- G 站年度净收益为 `101,423.23` 元；
- 三站合计年度净收益为 `98,485.03` 元；
- 最低题目口径利润率为 `-12.20%`；
- 最高题目口径利润率为 `7.72%`，满足 `rho <= 8%`。

解释要求：

```text
基准方案满足题目利润率上限约束，但小型 C 站存在年度净收益为负的保本风险。该风险不应被回避，论文中应说明需要通过区域统筹、财政兜底、专项补贴或运营规模调整缓解。
```

### 情景分析

根据 `problem4_scenario_metrics.csv`：

| 情景 | 年度净收益总额 | 解释要求 |
|---|---:|---|
| S0 | 98,485.03 元 | 基准方案总体为正，但 C 站亏损 |
| S1 | 85,784.33 元 | 总体仍为正，但存在局部亏损风险 |
| S2 | -1,489,044.51 元 | 转移概率变化导致财务压力显著增大 |
| S3 | -1,835,917.33 元 | 固定管理成本上升后财务可持续性恶化 |
| S4 | -705,388.29 元 | 预算提高带来扩张和服务改善，但年度净收益为负 |

论文中不能把 S2、S3、S4 写成单纯更优方案。尤其 S4 应表述为：

```text
预算提高使站点扩张并改善有效覆盖和满意度，但同时提高运营与建设摊销压力，导致年度净收益为负。因此预算扩张方案需要结合运营可持续性和财政补贴能力综合判断。
```

## 是否需要重跑

当前不需要重跑阶段 0-6。

只有在以下情况下重跑：

1. 将硬约束改为 `0 <= rho <= 8%`；
2. 引入 Q2-Q3 联动筛选站点；
3. 发现财务或有效服务量计算存在实质错误。

此前 `problem4_scenario_metrics.csv` 的 S0 `price_summary` 与问题 3 价格表不一致的问题已经修复，不再构成重跑条件。
