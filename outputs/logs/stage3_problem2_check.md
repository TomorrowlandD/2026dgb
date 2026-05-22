# 阶段 3 问题 2 检查

总体结果：通过

## 枚举统计
- total_enumerated: 1048576
- empty_plans: 1
- over_budget_pruned: 1033368
- budget_feasible: 15207

## 检查项
- [x] 枚举方案总数为 4^10，并记录剪枝数量
- [x] 最优方案建设成本不超过 120 万元
- [x] 所有被分配小区均有服务站
- [x] 每个被分配小区与服务站距离不超过 1000 米
- [x] 容量可得系数在 [0, 1] 内
- [x] 服务站利用率非负且不超过 1
- [x] 主覆盖率使用 CR_srv 且在 [0, 1] 内
- [x] 保留了 E_{i,r,k} 以支持三类老人可及性
- [x] 迭代收敛或记录最大迭代近似解
- [x] 预计年度利润使用基准价格测算

## 输出文件
- `outputs/tables/problem2_best_station_plan.csv`
- `outputs/tables/problem2_assignment.csv`
- `outputs/tables/problem2_station_utilization.csv`
- `outputs/tables/problem2_coverage_summary.csv`
- `outputs/tables/problem2_top_candidates.csv`
- `outputs/tables/problem2_effective_service_by_community_service.csv`
- `outputs/tables/problem2_effective_service_by_community_elder_service.csv`
