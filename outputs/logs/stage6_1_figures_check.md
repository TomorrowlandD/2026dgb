# 阶段 6.1 图表检查记录

## 生成方式

- 数据型图表均使用 Python 绘制。
- 阶段 6.1 保留 SVG 主文件，并额外生成 PNG 备用格式以便 LaTeX 驱动和排版软件兼容。
- 图 1 已标注各年份三类老人数量：蓝线标注在线段下方，绿线标注在线段上方，红线标注位于红线上方且向下微调以避开绿线标注，并已移除图内顶部标题；图 2 已标注各小区总服务需求。堆叠柱各分段不逐一标注，避免图面拥挤。
- 未使用大模型生图。

## 生成文件

- 图1 三类老人五年数量预测趋势（SVG 主文件）: `outputs\figures\fig1_population_forecast.svg`
- 图1 三类老人五年数量预测趋势（PNG 备用格式）: `outputs\figures\fig1_population_forecast.png`
- 图2 第5年各小区实际服务需求结构（SVG 主文件）: `outputs\figures\fig2_community_demand_stack.svg`
- 图2 第5年各小区实际服务需求结构（PNG 备用格式）: `outputs\figures\fig2_community_demand_stack.png`

## 配套论文表格

- `outputs/tables/paper_problem1_population_trend.csv`
- `outputs/tables/paper_problem1_actual_demand_stack.csv`

## 检查项

- [x] 图 1 数据来自问题 1 老人数量预测表。
- [x] 图 2 数据来自消费约束后的实际需求表。
- [x] 图 1 横轴为年份，纵轴为人数，图例为老人类型。
- [x] 图 2 横轴为小区，纵轴为月服务需求次数，图例为服务项目。
- [x] 图中服务需求展示值与论文表格取整规则一致。
- [x] 图形能支持“需求规模和结构”的文字结论。
- [x] 图 1 已添加各点取整人数标注：蓝线位于线段下方，绿线位于线段上方，红线在保持位于线上方的前提下向下微调且不与绿线标注重合，图内顶部标题已移除；图 2 已添加各小区总量标注，未添加会造成拥挤的分段标签。
