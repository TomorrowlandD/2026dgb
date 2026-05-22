# 阶段 6.3 问题 3 图表生成检查

## 绘图方式

本阶段图表均为数据驱动图，使用 Python 自动绘制。

未使用大模型生图，因此不需要大模型提示词。

## 输入数据

- `outputs/tables/problem3_prices.csv`
- `outputs/tables/problem3_accessibility_summary.csv`
- `outputs/tables/problem3_station_finance.csv`

## 生成文件

- `outputs/figures/fig5_price_vs_baseline.png`
- `outputs/figures/fig5_price_vs_baseline.svg`
- `outputs/figures/fig6_accessibility_by_elder_type.png`
- `outputs/figures/fig6_accessibility_by_elder_type.svg`

## 生成脚本

- `src/run_stage6_3_problem3_figures.py`

运行命令：

```powershell
python src\run_stage6_3_problem3_figures.py
```

## 检查结果

- [x] 图 5 的优化价格来自问题 3 最优候选方案。
- [x] 图 5 未混用问题 2 基准价格测算结果。
- [x] 图 5 明确区分基准价格和优化价格。
- [x] 图 6 包含经济、地理、服务满足和综合可及性。
- [x] 图 6 使用 `problem3_accessibility_summary.csv` 的最终可及性指标。
- [x] 两张图均生成 PNG 和 SVG 版本。
