# 阶段 6.0 图表计划检查记录

## 输入文件

- `outputs/tables/problem1_population_forecast.csv`
- `outputs/tables/problem1_actual_demand_by_community_service.csv`
- `outputs/tables/problem2_assignment.csv`
- `outputs/tables/problem2_best_station_plan.csv`
- `outputs/tables/problem2_station_utilization.csv`
- `outputs/tables/problem2_coverage_summary.csv`
- `outputs/tables/problem3_prices.csv`
- `outputs/tables/problem3_station_finance.csv`
- `outputs/tables/problem3_accessibility_summary.csv`
- `outputs/tables/problem4_scenario_metrics.csv`
- `outputs/tables/problem4_variation_indices.csv`
- `outputs/tables/stage1_distance_matrix.csv`

## 输出文件

- `outputs/figures/figure_plan.md`

## 检查结果

- [x] 每张候选图都有对应输入表。
- [x] 每张核心图都能支撑一个明确结论。
- [x] 没有把同一结论重复画成多张相似图。
- [x] 图表计划中区分了核心图和可选图。
- [x] 明确数据型图表使用 Python 绘制，不使用大模型生图。
- [x] 明确后续按阶段 6.1 至 6.4 分批生成图片。
- [x] 当前生成范围限定为 7 张核心图，备用图仅记录、不执行。

## 结论

阶段 6.0 已完成，可以进入阶段 6.1。
