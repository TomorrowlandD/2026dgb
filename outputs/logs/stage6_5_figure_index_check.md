# 阶段 6.5 图表编号、索引和统一风格检查记录

## 输入文件

- `outputs/figures/figure_plan.md`
- `outputs/figures/fig1_population_forecast.svg`
- `outputs/figures/fig2_community_demand_stack.svg`
- `outputs/figures/fig3_station_assignment.svg`
- `outputs/figures/fig4_station_utilization_capacity.svg`
- `outputs/figures/fig5_price_vs_baseline.svg`
- `outputs/figures/fig6_accessibility_by_elder_type.svg`
- `outputs/figures/fig7_scenario_metrics_compare.svg`

## 输出文件

- `outputs/figures/figure_index.md`

## 核心图文件状态

| 图号 | SVG | PNG | 状态 |
|---|---|---|---|
| 图 1 | 已存在 | 无 | 可用于正文主引用 |
| 图 2 | 已存在 | 无 | 可用于正文主引用 |
| 图 3 | 已存在 | 已存在 | 可用于正文主引用，PNG 可作备用 |
| 图 4 | 已存在 | 已存在 | 可用于正文主引用，PNG 可作备用 |
| 图 5 | 已存在 | 已存在 | 可用于正文主引用，PNG 可作备用 |
| 图 6 | 已存在 | 已存在 | 可用于正文主引用，PNG 可作备用 |
| 图 7 | 已存在 | 已存在 | 可用于正文主引用，PNG 可作备用 |

## 检查项

- [x] 图表编号和当前 7 张核心图一致。
- [x] 每张核心图均有明确数据来源。
- [x] 每张核心图均有推荐正文位置。
- [x] 文件名均以 `fig数字_英文描述` 开头。
- [x] 当前正文核心图范围仍限定为图 1 至图 7。
- [x] 备用图未进入当前正文核心编号。
- [x] `figure_index.md` 已补充图 7。
- [x] `figure_index.md` 已补充统一风格要求和正文引用建议。

## 备注

当前图 1 和图 2 仅有 SVG 格式。SVG 为矢量格式，可作为正文主引用；若后续排版软件不支持 SVG，再单独转换为 PNG，不在阶段 6.5 中强制新增位图版本。

