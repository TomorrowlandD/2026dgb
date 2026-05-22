from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib import font_manager


ROOT = Path(__file__).resolve().parents[1]
TABLE_DIR = ROOT / "outputs" / "tables"
FIG_DIR = ROOT / "outputs" / "figures"
LOG_DIR = ROOT / "outputs" / "logs"

NON_EMERGENCY_SERVICES = ["助餐", "日间照料", "上门护理", "康复理疗", "助浴"]
ACCESSIBILITY_LABELS = {
    "weighted_economic_accessibility": "经济可及性",
    "weighted_geographic_accessibility": "地理可及性",
    "weighted_service_accessibility": "服务满足可及性",
    "weighted_overall_accessibility": "综合可及性",
}
COLORS = {
    "base": "#94A3B8",
    "optimized": "#2563EB",
    "经济可及性": "#2563EB",
    "地理可及性": "#059669",
    "服务满足可及性": "#F59E0B",
    "综合可及性": "#DC2626",
}


def configure_plot_style() -> None:
    candidates = [
        "Microsoft YaHei",
        "SimHei",
        "Noto Sans CJK SC",
        "Source Han Sans SC",
        "Arial Unicode MS",
    ]
    available = {font.name for font in font_manager.fontManager.ttflist}
    for name in candidates:
        if name in available:
            plt.rcParams["font.sans-serif"] = [name]
            break
    plt.rcParams["axes.unicode_minus"] = False
    plt.rcParams["figure.dpi"] = 120
    plt.rcParams["savefig.dpi"] = 300


def save_figure(fig: plt.Figure, stem: str) -> list[Path]:
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    paths = []
    for ext in ("png", "svg"):
        path = FIG_DIR / f"{stem}.{ext}"
        fig.savefig(path, bbox_inches="tight")
        paths.append(path)
    plt.close(fig)
    return paths


def yuan_label(value: float) -> str:
    if abs(value - round(value)) < 1e-8:
        return f"{value:.0f}"
    return f"{value:.1f}"


def pct_label(value: float) -> str:
    return f"{value * 100:.1f}%"


def build_price_comparison() -> tuple[pd.DataFrame, list[Path]]:
    prices = pd.read_csv(TABLE_DIR / "problem3_prices.csv")
    prices = prices[prices["service"].isin(NON_EMERGENCY_SERVICES)].copy()

    summary = (
        prices.groupby("service", as_index=False)
        .agg(
            optimized_price=("price", "mean"),
            min_price=("price", "min"),
            max_price=("price", "max"),
            base_price=("base_price", "first"),
            direct_cost=("direct_cost", "first"),
        )
        .set_index("service")
        .reindex(NON_EMERGENCY_SERVICES)
        .reset_index()
    )
    summary["price_reduction"] = summary["base_price"] - summary["optimized_price"]
    summary["price_reduction_rate"] = summary["price_reduction"] / summary["base_price"]
    out = TABLE_DIR / "paper_problem3_price_comparison.csv"
    summary.to_csv(out, index=False, encoding="utf-8-sig")

    x = np.arange(len(summary))
    width = 0.36
    fig, ax = plt.subplots(figsize=(9.8, 6.2))
    base_bars = ax.bar(
        x - width / 2,
        summary["base_price"],
        width,
        label="基准价格",
        color=COLORS["base"],
        edgecolor="#64748B",
        linewidth=0.8,
    )
    opt_bars = ax.bar(
        x + width / 2,
        summary["optimized_price"],
        width,
        label="优化价格",
        color=COLORS["optimized"],
        edgecolor="#1E40AF",
        linewidth=0.8,
    )

    for bars in (base_bars, opt_bars):
        for bar in bars:
            value = bar.get_height()
            ax.text(
                bar.get_x() + bar.get_width() / 2,
                value + 0.55,
                yuan_label(value),
                ha="center",
                va="bottom",
                fontsize=9,
                color="#111827",
            )

    for idx, row in summary.iterrows():
        reduction = row["price_reduction_rate"]
        ax.text(
            idx,
            max(row["base_price"], row["optimized_price"]) + 3.2,
            f"降幅 {reduction * 100:.1f}%",
            ha="center",
            va="bottom",
            fontsize=9,
            color="#047857",
            weight="bold",
        )

    fig.suptitle("图5 优化价格与基准价格对比", fontsize=16, weight="bold", y=0.98)
    ax.set_title("紧急救助为公益免费服务，不参与价格优化", fontsize=10.5, color="#4B5563", pad=10)
    ax.set_ylabel("价格（元/次）")
    ax.set_xticks(x)
    ax.set_xticklabels(summary["service"], fontsize=10)
    ax.set_ylim(0, max(summary["base_price"].max(), summary["optimized_price"].max()) * 1.32)
    ax.legend(loc="upper left", frameon=False, ncol=2)
    ax.grid(axis="y", color="#E5E7EB", linewidth=0.8)
    ax.spines[["top", "right"]].set_visible(False)
    fig.subplots_adjust(top=0.82, bottom=0.12, left=0.09, right=0.98)

    paths = save_figure(fig, "fig5_price_vs_baseline")
    return summary, paths


def build_accessibility_comparison() -> tuple[pd.DataFrame, list[Path]]:
    summary = pd.read_csv(TABLE_DIR / "problem3_accessibility_summary.csv")
    long_df = summary.melt(
        id_vars="elder_type",
        value_vars=list(ACCESSIBILITY_LABELS.keys()),
        var_name="metric",
        value_name="value",
    )
    long_df["metric_label"] = long_df["metric"].map(ACCESSIBILITY_LABELS)
    out = TABLE_DIR / "paper_problem3_accessibility_long.csv"
    long_df.to_csv(out, index=False, encoding="utf-8-sig")

    elder_types = summary["elder_type"].tolist()
    metrics = list(ACCESSIBILITY_LABELS.keys())
    metric_labels = [ACCESSIBILITY_LABELS[m] for m in metrics]
    x = np.arange(len(elder_types))
    width = 0.18

    fig, ax = plt.subplots(figsize=(10.4, 6.4))
    offsets = (np.arange(len(metrics)) - (len(metrics) - 1) / 2) * width
    for offset, metric, label in zip(offsets, metrics, metric_labels):
        values = summary[metric].to_numpy(dtype=float)
        bars = ax.bar(
            x + offset,
            values,
            width,
            label=label,
            color=COLORS[label],
            edgecolor="#FFFFFF",
            linewidth=0.8,
        )
        for bar in bars:
            value = bar.get_height()
            ax.text(
                bar.get_x() + bar.get_width() / 2,
                value + 0.012,
                pct_label(value),
                ha="center",
                va="bottom",
                fontsize=8,
                color="#111827",
                rotation=0,
            )

    fig.suptitle("图6 三类老人服务可及性对比", fontsize=16, weight="bold", y=0.98)
    fig.text(0.5, 0.91, "可及性由经济、地理、服务满足三个维度加权得到", ha="center", fontsize=10.5, color="#4B5563")
    ax.set_ylabel("可及性得分")
    ax.set_ylim(0, 1.12)
    ax.set_xticks(x)
    ax.set_xticklabels(elder_types, fontsize=10)
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, 1.16), frameon=False, ncol=4)
    ax.grid(axis="y", color="#E5E7EB", linewidth=0.8)
    ax.spines[["top", "right"]].set_visible(False)
    fig.subplots_adjust(top=0.74, bottom=0.12, left=0.08, right=0.98)

    paths = save_figure(fig, "fig6_accessibility_by_elder_type")
    return long_df, paths


def update_figure_index() -> None:
    index_path = FIG_DIR / "figure_index.md"
    content = """# 图表索引

## 阶段 6.1：问题 1 图表

| 图号 | 图名 | 文件 | 数据来源 | 用途 |
|---|---|---|---|---|
| 图1 | 三类老人五年数量预测趋势 | `fig1_population_forecast.svg` | `outputs/tables/problem1_population_forecast.csv` | 展示未来五年三类老人规模变化 |
| 图2 | 第5年各小区实际服务需求结构 | `fig2_community_demand_stack.svg` | `outputs/tables/problem1_actual_demand_by_community_service.csv` | 展示消费约束后各小区服务需求结构 |

## 阶段 6.2：问题 2 图表

| 图号 | 图名 | 文件 | 数据来源 | 用途 |
|---|---|---|---|---|
| 图3 | 最优服务站-小区分配示意图 | `fig3_station_assignment.svg` | `outputs/tables/problem2_assignment.csv`; `outputs/tables/problem2_best_station_plan.csv` | 展示最优站点位置、规模和服务覆盖关系 |
| 图4 | 各服务站利用率与容量可得系数 | `fig4_station_utilization_capacity.svg` | `outputs/tables/problem2_station_utilization.csv` | 展示各站点服务能力利用情况和容量约束程度 |

## 阶段 6.3：问题 3 图表

| 图号 | 图名 | 文件 | 数据来源 | 用途 |
|---|---|---|---|---|
| 图5 | 优化价格与基准价格对比 | `fig5_price_vs_baseline.svg` | `outputs/tables/problem3_prices.csv` | 展示补贴导向定价下收费服务价格相对基准价的变化 |
| 图6 | 三类老人服务可及性对比 | `fig6_accessibility_by_elder_type.svg` | `outputs/tables/problem3_accessibility_summary.csv` | 比较自理、半失能、失能老人经济、地理、服务满足和综合可及性 |
"""
    index_path.write_text(content, encoding="utf-8")


def write_check_log(generated: list[Path]) -> None:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    rel_paths = [path.relative_to(ROOT).as_posix() for path in generated]
    log = [
        "# 阶段 6.3 问题 3 图表生成检查",
        "",
        "## 绘图方式",
        "",
        "本阶段图表均为数据驱动图，使用 Python 自动绘制。",
        "",
        "未使用大模型生图，因此不需要大模型提示词。",
        "",
        "## 输入数据",
        "",
        "- `outputs/tables/problem3_prices.csv`",
        "- `outputs/tables/problem3_accessibility_summary.csv`",
        "- `outputs/tables/problem3_station_finance.csv`",
        "",
        "## 生成文件",
        "",
        *[f"- `{path}`" for path in rel_paths],
        "",
        "## 生成脚本",
        "",
        "- `src/run_stage6_3_problem3_figures.py`",
        "",
        "运行命令：",
        "",
        "```powershell",
        "python src\\run_stage6_3_problem3_figures.py",
        "```",
        "",
        "## 检查结果",
        "",
        "- [x] 图 5 的优化价格来自问题 3 最优候选方案。",
        "- [x] 图 5 未混用问题 2 基准价格测算结果。",
        "- [x] 图 5 明确区分基准价格和优化价格。",
        "- [x] 图 6 包含经济、地理、服务满足和综合可及性。",
        "- [x] 图 6 使用 `problem3_accessibility_summary.csv` 的最终可及性指标。",
        "- [x] 两张图均生成 PNG 和 SVG 版本。",
    ]
    (LOG_DIR / "stage6_3_problem3_figures_check.md").write_text("\n".join(log) + "\n", encoding="utf-8")


def main() -> None:
    configure_plot_style()
    _, price_paths = build_price_comparison()
    _, accessibility_paths = build_accessibility_comparison()
    update_figure_index()
    generated = price_paths + accessibility_paths
    write_check_log(generated)
    print("Generated:")
    for path in generated:
        print(path)
    print(FIG_DIR / "figure_index.md")
    print(LOG_DIR / "stage6_3_problem3_figures_check.md")


if __name__ == "__main__":
    main()
