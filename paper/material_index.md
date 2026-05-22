# 论文材料索引表

## 方案与写作规范

| 材料类型 | 文件路径 | 服务章节 | 是否可用 | 备注 |
|---|---|---|---|---|
| 最终建模方案 | `docs/revised_modeling_plan.md` | 全文 | 是 | 后续写作主方案 |
| 最终严谨性修订说明 | `docs/final_revision_notes.md` | 全文口径复核 | 是 | 用于避免旧口径残留 |
| 最终一致性审查 | `docs/final_consistency_audit.md` | 全文口径复核 | 是 | 用于步骤 15 一致性检查 |
| 论文关键结果摘要 | `docs/paper_key_results_summary.md` | 结果分析、摘要 | 是 | 结果数值应回溯到表格 |
| 论文撰写指南 | `docs/paper_writing_guide.md` | 全文 | 是 | 写作风格与结构参考 |
| 论文严格规划清单 | `docs/论文撰写严格规划清单.md` | 全流程 | 是 | 当前步骤依据 |
| 正文写作提示词 | `docs/数学建模竞赛论文写作提示词：B 题《嵌入式社区养老服务站的建设与优化问题》.md` | 步骤 2--13 | 是 | 摘要步骤不优先使用 |
| 摘要优化提示词 | `docs/数学建模论文摘要优化提示词：B 题《嵌入式社区养老服务站的建设与优化问题》.md` | 步骤 14 | 是 | 正文主体完成后使用 |
| 提示词使用指导 | `docs/论文撰写提示词使用指导.md` | 全流程 | 是 | 锁定最终口径 |
| 竞赛 Word 模板 | `docs/“电工杯”全国大学生数学建模竞赛论文Word模板.doc` | 版式参考 | 是 | Word 终稿由人工转换 |
| 竞赛 PDF 模板 | `docs/“电工杯”全国大学生数学建模竞赛论文Word模板.pdf` | 版式参考 | 是 | LaTeX 版式参照 |

## 阶段检查日志

| 材料类型 | 文件路径 | 服务章节 | 是否可用 | 备注 |
|---|---|---|---|---|
| 阶段 0 检查 | `outputs/logs/stage0_check.md` | 全文口径 | 是 | 方案冻结 |
| 阶段 1 检查 | `outputs/logs/stage1_data_check.md` | 数据预处理、模型检验 | 是 | 数据清洗与参数表 |
| 阶段 2 检查 | `outputs/logs/stage2_problem1_check.md` | 问题一、模型检验 | 是 | 人口预测和需求修正 |
| 阶段 3 检查 | `outputs/logs/stage3_problem2_check.md` | 问题二、模型检验 | 是 | 选址与规模优化 |
| 阶段 4 检查 | `outputs/logs/stage4_problem3_check.md` | 问题三、模型检验 | 是 | 定价、补贴、利润率和可及性 |
| 阶段 5 检查 | `outputs/logs/stage5_problem4_check.md` | 问题四、模型检验 | 是 | 灵敏度分析 |
| 阶段 6 总检查 | `outputs/logs/stage6_6_final_check.md` | 图表引用、结果分析 | 是 | 图表生成最终检查 |
| 论文步骤 0 检查 | `outputs/logs/paper_step0_writing_check.md` | 写作口径 | 是 | 总约束确认 |

## 核心表格

| 材料类型 | 文件路径 | 服务章节 | 是否可用 | 备注 |
|---|---|---|---|---|
| 数据清洗参数 | `outputs/tables/stage1_cleaned_parameters.json` | 数据预处理、附录 | 是 | 清洗后参数汇总 |
| 小区基础数据 | `outputs/tables/stage1_communities.csv` | 数据预处理 | 是 | 阶段 1 输出 |
| 距离矩阵 | `outputs/tables/stage1_distance_matrix.csv` | 数据预处理、问题二 | 是 | 图 3 也使用 |
| 服务需求参数 | `outputs/tables/stage1_service_demand.csv` | 问题一 | 是 | 理论需求计算 |
| 服务成本参数 | `outputs/tables/stage1_service_costs.csv` | 问题三 | 是 | 价格和成本核算 |
| 站点成本容量参数 | `outputs/tables/stage1_station_costs.csv` | 问题二、问题三 | 是 | 建设成本、固定成本、容量 |
| 问题一人口预测论文表 | `outputs/tables/paper_problem1_population_trend.csv` | 问题一、摘要 | 是 | 论文图表用整理表 |
| 问题一实际需求论文表 | `outputs/tables/paper_problem1_actual_demand_stack.csv` | 问题一、摘要 | 是 | 论文图表用整理表 |
| 问题一完整人口预测 | `outputs/tables/problem1_population_forecast.csv` | 问题一、附录 | 是 | 核心结果表 |
| 问题一理论需求 | `outputs/tables/problem1_theoretical_demand.csv` | 问题一、附录 | 是 | 核心结果表 |
| 问题一实际需求 | `outputs/tables/problem1_actual_demand.csv` | 问题一、附录 | 是 | 核心结果表 |
| 问题一预算检查 | `outputs/tables/problem1_budget_check.csv` | 问题一、模型检验 | 是 | 约束检查 |
| 问题二最优站点方案 | `outputs/tables/problem2_best_station_plan.csv` | 问题二、摘要 | 是 | 目前无 `paper_problem2_*`，直接引用该表 |
| 问题二分配结果 | `outputs/tables/problem2_assignment.csv` | 问题二 | 是 | 图 3 数据来源 |
| 问题二站点利用率 | `outputs/tables/problem2_station_utilization.csv` | 问题二 | 是 | 图 4 数据来源 |
| 问题二覆盖汇总 | `outputs/tables/problem2_coverage_summary.csv` | 问题二、摘要 | 是 | 论文核心指标 |
| 问题二候选方案 | `outputs/tables/problem2_top_candidates.csv` | 问题二、附录 | 是 | 方案优选说明 |
| 问题三价格论文表 | `outputs/tables/paper_problem3_price_comparison.csv` | 问题三 | 是 | 图 5 整理表 |
| 问题三可及性论文表 | `outputs/tables/paper_problem3_accessibility_long.csv` | 问题三 | 是 | 图 6 整理表 |
| 问题三价格结果 | `outputs/tables/problem3_prices.csv` | 问题三、摘要 | 是 | 优化定价结果 |
| 问题三站点财务 | `outputs/tables/problem3_station_finance.csv` | 问题三、模型检验 | 是 | 利润率和净收益 |
| 问题三可及性汇总 | `outputs/tables/problem3_accessibility_summary.csv` | 问题三、摘要 | 是 | 三类老人可及性 |
| 问题四论文图表整理表 | `outputs/tables/paper_problem4_scenario_metrics_for_fig7.csv` | 问题四 | 是 | 图 7 整理表 |
| 问题四情景指标 | `outputs/tables/problem4_scenario_metrics.csv` | 问题四、摘要 | 是 | S0--S4 完整重求解指标 |
| 问题四站点方案 | `outputs/tables/problem4_scenario_station_plans.csv` | 问题四、附录 | 是 | 情景方案对比 |
| 问题四变化度指标 | `outputs/tables/problem4_variation_indices.csv` | 问题四 | 是 | 鲁棒性评价 |
| 问题四鲁棒性汇总 | `outputs/tables/problem4_robustness_summary.csv` | 问题四、模型检验 | 是 | 稳健性说明 |

## 核心图

| 材料类型 | 文件路径 | 服务章节 | 是否可用 | 备注 |
|---|---|---|---|---|
| 图表索引 | `outputs/figures/figure_index.md` | 全文图表引用 | 是 | 图号和正文位置依据 |
| 图 1 | `outputs/figures/fig1_population_forecast.svg` | 问题一 | 是 | 三类老人五年预测趋势 |
| 图 2 | `outputs/figures/fig2_community_demand_stack.svg` | 问题一 | 是 | 第 5 年各小区需求结构 |
| 图 3 | `outputs/figures/fig3_station_assignment.svg` | 问题二 | 是 | 网络分配示意图 |
| 图 4 | `outputs/figures/fig4_station_utilization_capacity.svg` | 问题二 | 是 | 利用率与容量可得系数 |
| 图 5 | `outputs/figures/fig5_price_vs_baseline.svg` | 问题三 | 是 | 优化价格与基准价格对比 |
| 图 6 | `outputs/figures/fig6_accessibility_by_elder_type.svg` | 问题三 | 是 | 三类老人可及性对比 |
| 图 7 | `outputs/figures/fig7_scenario_metrics_compare.svg` | 问题四 | 是 | 灵敏度情景指标对比 |

## 缺失或待整理材料

| 材料 | 状态 | 处理方式 |
|---|---|---|
| `outputs/tables/paper_problem2_*.csv` | 未发现专门论文整理表 | 步骤 6 可直接使用 `problem2_best_station_plan.csv`、`problem2_assignment.csv`、`problem2_station_utilization.csv`、`problem2_coverage_summary.csv`，必要时再整理论文表 |
| 完整参考文献清单 | 尚未整理 | 步骤 13 基于真实使用材料补充，不得编造 |
| 参赛编号 | 尚未提供 | 封面保留占位，最终由人工填写或后续补充 |
