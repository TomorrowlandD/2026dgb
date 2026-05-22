# 阶段 6.5 图表索引与统一风格记录

## 当前图表生成范围

当前只使用 7 张核心图。备用图仅记录在 `AGENTS.md` 中，当前不生成、不编号进正文。

## 核心图索引

| 图号 | 图名 | 推荐正文位置 | 主文件 | 备用格式 | 数据来源 | 论文用途 |
|---|---|---|---|---|---|---|
| 图 1 | 三类老人五年预测趋势图 | 6.1 老人数量与需求预测结果 | `fig1_population_forecast.svg` | `fig1_population_forecast.png` | `outputs/tables/problem1_population_forecast.csv` | 展示未来五年自理、半失能、失能老人规模变化 |
| 图 2 | 第 5 年各小区实际服务需求结构图 | 6.1 老人数量与需求预测结果 | `fig2_community_demand_stack.svg` | `fig2_community_demand_stack.png` | `outputs/tables/problem1_actual_demand_by_community_service.csv` | 展示消费约束后各小区服务需求结构 |
| 图 3 | 最优服务站-小区分配示意图 | 6.2 服务站选址与规模优化结果 | `fig3_station_assignment.svg` | `fig3_station_assignment.png` | `outputs/tables/problem2_assignment.csv`; `outputs/tables/problem2_best_station_plan.csv`; `outputs/tables/stage1_distance_matrix.csv` | 展示最优站点位置、规模和服务覆盖关系 |
| 图 4 | 各服务站利用率与容量可得系数图 | 6.2 服务站选址与规模优化结果 | `fig4_station_utilization_capacity.svg` | `fig4_station_utilization_capacity.png` | `outputs/tables/problem2_station_utilization.csv` | 展示各站点服务能力利用情况和容量约束程度 |
| 图 5 | 优化价格与基准价格对比图 | 6.3 定价与补贴优化结果 | `fig5_price_vs_baseline.svg` | `fig5_price_vs_baseline.png` | `outputs/tables/problem3_prices.csv` | 展示补贴导向定价下各服务价格相对基准价格的变化 |
| 图 6 | 三类老人服务可及性对比图 | 6.4 三类老人可及性结果 | `fig6_accessibility_by_elder_type.svg` | `fig6_accessibility_by_elder_type.png` | `outputs/tables/problem3_accessibility_summary.csv` | 比较自理、半失能、失能老人经济、地理、服务满足和综合可及性 |
| 图 7 | 灵敏度情景主要指标对比图 | 6.5 情景灵敏度分析结果 | `fig7_scenario_metrics_compare.svg` | `fig7_scenario_metrics_compare.png` | `outputs/tables/problem4_scenario_metrics.csv`; `outputs/tables/problem4_variation_indices.csv` | 比较不同情景下覆盖率、满意度、补贴、净收益、利润率和方案变化度 |

## 正文引用建议

- 图 1 和图 2 放在问题 1 结果分析部分，用于说明未来需求规模和结构。
- 图 3 和图 4 放在问题 2 结果分析部分，用于说明站点布局、服务覆盖和容量配置。
- 图 5 放在问题 3 定价结果部分，用于说明补贴导向定价效果。
- 图 6 放在问题 3.3 可及性分析部分，用于比较三类老人服务可及性。
- 图 7 放在问题 4 灵敏度分析部分，用于说明模型鲁棒性和敏感参数影响。

## 文件命名规则

核心图统一采用：

```text
fig数字_英文描述.svg
```

若同时保留位图格式，则采用同名 `.png`：

```text
fig数字_英文描述.png
```

当前正文主引用优先使用 `.svg`，因为 SVG 为矢量图，适合论文排版和后续无损缩放；若排版软件不支持 SVG，则使用同名 PNG。

## 统一风格要求

- 图中文字、标题、坐标轴、图例使用中文。
- 坐标轴必须标明单位，例如“人数”“次/月”“万元”“比例”。
- 覆盖率、满意度、可及性和利润率的显示口径必须与正文一致。
- 财务类图必须区分题目口径利润率和年度净收益。
- 图 3 只能称为“网络分配示意图”或“服务关系示意图”，不能称为真实地图。
- 每张图应有明确结论，不为装饰目的生成。
- 后续若新增备用图，必须先更新本索引，再在正文中引用。

## 阶段 6.5 检查

- [x] 图表编号与 7 张核心图一致。
- [x] 图 1 至图 7 均有明确数据来源。
- [x] 图 1 至图 7 均有推荐正文位置。
- [x] 图 1 至图 7 文件名遵循 `fig数字_英文描述` 规则。
- [x] SVG 主文件均已记录。
- [x] PNG 备用文件仅在已存在时记录，没有强制新增。
- [x] 备用图未进入当前正文核心图编号。

