# 阶段 6.2 问题 2 图表生成检查

## 绘图方式

本阶段图表均为数据驱动图，使用 Python 自动绘制。

未使用大模型生图，因此不需要大模型提示词。

## 输入数据

- `outputs/tables/problem2_assignment.csv`
- `outputs/tables/problem2_best_station_plan.csv`
- `outputs/tables/problem2_station_utilization.csv`
- `outputs/tables/problem2_coverage_summary.csv`
- `outputs/tables/stage1_distance_matrix.csv`

## 生成文件

- `outputs/figures/fig3_station_assignment.png`
- `outputs/figures/fig3_station_assignment.svg`
- `outputs/figures/fig4_station_utilization_capacity.png`
- `outputs/figures/fig4_station_utilization_capacity.svg`

## 生成脚本

- `src/run_stage6_2_problem2_figures.py`

运行命令：

```powershell
python src\run_stage6_2_problem2_figures.py
```

说明：本机系统 Python 已具备 `pandas`、`numpy`、`matplotlib`。Codex bundled Python 中未安装 `matplotlib`，因此本阶段使用系统 Python 运行绘图脚本。

## 检查结果

- [x] 图 3 中所有分配关系来自问题 2 最优分配结果。
- [x] 图 3 明确区分服务站规模。
- [x] 图 3 标注为示意图，不作为真实地图。
- [x] 图 3 主标题、副标题和图主体之间留白充足，无文字挤压。
- [x] 图 4 的利用率和容量可得系数来自最终迭代结果。
- [x] 图 4 中容量可得系数位于 `[0,1]`。
- [x] 图 4 显示了服务响应满意度阈值参考线。
- [x] 图 4 图例、柱顶数值和右侧阈值标注无重叠或裁切。
- [x] 两张图均生成 PNG 和 SVG 版本。

## 重新生成记录

用户指出旧版图 3 的副标题与主标题距离过近，旧版图 4 的图例和柱顶数值存在挤压风险。已调整 `src/run_stage6_2_problem2_figures.py` 的标题区、图例位置、顶部留白和右侧留白，并重新生成同名图片。

尝试按单文件路径删除旧图时系统返回访问拒绝，随后使用同名输出覆盖生成新版图片。

用户进一步指出图 3 中站点框过小、连线与站点框/文字连接不自然、副标题仍显拥挤。已将图 3 从距离矩阵降维布局改为按服务站簇排布的服务关系示意图，扩大站点框，隐藏穿过站点框的连线部分，偏移距离标签，并将副标题放入独立信息条。已重新覆盖生成 `fig3_station_assignment.png` 和 `fig3_station_assignment.svg`。
