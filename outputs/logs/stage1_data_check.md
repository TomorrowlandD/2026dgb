# 阶段 1 数据清洗检查

总体结果：通过

- [x] 10 个小区编号完整且顺序一致
- [x] 三类老人初始人数加总等于 60+ 老人数
- [x] 距离矩阵为 10 x 10
- [x] 距离矩阵主对角线为 0
- [x] 距离矩阵对称
- [x] 服务项目为 6 项
- [x] 紧急救助价格为 0
- [x] 消费上限比例正确
- [x] 建设成本、运营成本、容量均非负
- [x] 需求、成本、转移概率和满意度规则无异常空值
- [x] 所有核心数值字段非负

## 输出文件
- `outputs/tables/stage1_communities.csv`
- `outputs/tables/stage1_transition_probabilities.csv`
- `outputs/tables/stage1_service_demand.csv`
- `outputs/tables/stage1_service_costs.csv`
- `outputs/tables/stage1_consumption_limits.csv`
- `outputs/tables/stage1_station_costs.csv`
- `outputs/tables/stage1_satisfaction_rules.csv`
- `outputs/tables/stage1_distance_matrix.csv`
- `outputs/tables/stage1_cleaned_parameters.json`
