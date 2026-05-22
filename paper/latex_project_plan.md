# LaTeX 工程文件规划表

## 工程结构

| 文件或目录 | 用途 | 当前状态 | 后续步骤 |
|---|---|---|---|
| `paper/main.tex` | 论文主入口，设置页面、页码、宏包、图片路径和章节输入顺序 | 已建立 | 定稿前编译检查 |
| `paper/refs.bib` | 参考文献数据库占位 | 已建立 | 步骤 13 补充真实参考文献 |
| `paper/sections/00_cover.tex` | 封面页，仅含参赛编号占位和赛题题目 | 已建立 | 步骤 14 最终确认 |
| `paper/sections/01_abstract.tex` | 论文题目、摘要和关键词 | 已建立占位 | 步骤 14 撰写 |
| `paper/sections/02_problem_restatement.tex` | 一、问题重述 | 已建立占位 | 步骤 12 撰写 |
| `paper/sections/03_problem_analysis.tex` | 二、问题分析 | 已建立占位 | 步骤 12 撰写 |
| `paper/sections/04_assumptions_symbols.tex` | 三、模型假设；四、符号说明 | 已建立占位 | 步骤 3 撰写 |
| `paper/sections/05_model_solution.tex` | 五、模型建立与求解，含问题 1--4 和数据预处理 | 已建立占位 | 步骤 4--9 分段撰写 |
| `paper/sections/06_model_validation.tex` | 六、模型检验 | 已建立占位 | 步骤 10 撰写 |
| `paper/sections/07_model_evaluation.tex` | 七、模型优缺点评价 | 已建立占位 | 步骤 11 撰写 |
| `paper/sections/08_references_appendix.tex` | 参考文献和附录 | 已建立占位 | 步骤 13 撰写 |

## `main.tex` 结构确认

| 要求 | 实现情况 |
|---|---|
| 使用中文 LaTeX 文档类 | `ctexart` |
| A4 纸 | `a4paper` |
| 四边页边距 2.5 cm | `\usepackage[margin=2.5cm]{geometry}` |
| 正文小四号 | `zihao=-4` |
| 不生成目录 | 未使用 `\tableofcontents` |
| 封面页无页码 | `sections/00_cover.tex` 中使用 `\thispagestyle{empty}` |
| 摘要页起页码为 1 | `main.tex` 中封面后执行 `\setcounter{page}{1}` |
| 页码位于页脚中部 | `fancyhdr` 中使用 `\cfoot{\thepage}` |
| 图像路径 | `\graphicspath{{../outputs/figures/}}` |

## 论文结构映射

| 模板章节 | LaTeX 文件 | 写作步骤 |
|---|---|---|
| 封面信息 | `sections/00_cover.tex` | 步骤 14 |
| 论文题目、摘要、关键词 | `sections/01_abstract.tex` | 步骤 14 |
| 一、问题重述 | `sections/02_problem_restatement.tex` | 步骤 12 |
| 二、问题分析 | `sections/03_problem_analysis.tex` | 步骤 12 |
| 三、模型假设 | `sections/04_assumptions_symbols.tex` | 步骤 3 |
| 四、符号说明 | `sections/04_assumptions_symbols.tex` | 步骤 3 |
| 五、模型建立与求解 | `sections/05_model_solution.tex` | 步骤 4--9 |
| 六、模型检验 | `sections/06_model_validation.tex` | 步骤 10 |
| 七、模型优缺点评价 | `sections/07_model_evaluation.tex` | 步骤 11 |
| 参考文献 | `sections/08_references_appendix.tex` | 步骤 13 |
| 附录 | `sections/08_references_appendix.tex` | 步骤 13 |

## 正文核心图引用规划

| 图号 | 文件 | 推荐位置 | 用途 |
|---|---|---|---|
| 图 1 | `outputs/figures/fig1_population_forecast.svg` | 问题一结果分析 | 展示三类老人五年预测趋势 |
| 图 2 | `outputs/figures/fig2_community_demand_stack.svg` | 问题一结果分析 | 展示第 5 年各小区实际服务需求结构 |
| 图 3 | `outputs/figures/fig3_station_assignment.svg` | 问题二结果分析 | 展示服务站与小区分配关系 |
| 图 4 | `outputs/figures/fig4_station_utilization_capacity.svg` | 问题二结果分析 | 展示利用率与容量可得系数 |
| 图 5 | `outputs/figures/fig5_price_vs_baseline.svg` | 问题三定价结果分析 | 展示优化价格与基准价格对比 |
| 图 6 | `outputs/figures/fig6_accessibility_by_elder_type.svg` | 问题三可及性分析 | 展示三类老人可及性差异 |
| 图 7 | `outputs/figures/fig7_scenario_metrics_compare.svg` | 问题四灵敏度分析 | 展示 S0--S4 情景主要指标对比 |

## 正文页数控制

后续写作时正文控制在 25 页以内。附录页数不限。步骤 15 和步骤 16 需要通过编译后的 PDF 检查实际页数、图表位置和引用状态。
