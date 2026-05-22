# 阶段 4 问题 3 检查

总体结果：通过

## 搜索统计
- rough_count: 3125
- rough_candidates: 3125
- rough_feasible: 545
- fine_candidates: 3125
- fine_feasible: 1569
- station_delta_candidates: 27
- station_delta_feasible: 8
- total_evaluated: 6277
- total_feasible: 2122

## 检查项
- [x] 每组候选价格都重新计算 S3
- [x] 每组候选价格都重新计算分配结果和有效服务人次
- [x] 紧急救助不计政府补贴，但计入直接服务成本
- [x] 政府补贴不超过每日补贴上限折算值
- [x] 题目口径利润率采用 (ServiceProfit + G - OC) / OC
- [x] 年度净收益另行计入年化建设成本
- [x] 所有入选方案满足 rho <= 8%
- [x] 没有将 rho >= 0 作为硬约束
- [x] 价格满意度不超过 1
- [x] 老人支付额使用最终有效服务人次 E_{i,r,k} 计算

## 输出文件
- `outputs/tables/problem3_prices.csv`
- `outputs/tables/problem3_station_finance.csv`
- `outputs/tables/problem3_price_satisfaction.csv`
- `outputs/tables/problem3_accessibility.csv`
- `outputs/tables/problem3_accessibility_summary.csv`
- `outputs/tables/problem3_metrics.csv`
