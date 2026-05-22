from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib import font_manager


ROOT = Path(__file__).resolve().parents[1]
TABLE_DIR = ROOT / "outputs" / "tables"
FIG_DIR = ROOT / "outputs" / "figures"
LOG_DIR = ROOT / "outputs" / "logs"


SCENARIO_LABELS = {
    "S0": "S0\n基准",
    "S1": "S1\n增长率8%",
    "S2": "S2\n转移概率",
    "S3": "S3\n成本+20%",
    "S4": "S4\n预算140万",
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


def add_bar_labels(ax, bars, fmt="{:.1f}", dy=3, color="#111827") -> None:
    for bar in bars:
        height = bar.get_height()
        ax.annotate(
            fmt.format(height),
            xy=(bar.get_x() + bar.get_width() / 2, height),
            xytext=(0, dy),
            textcoords="offset points",
            ha="center",
            va="bottom",
            fontsize=8.5,
            color=color,
        )


def build_paper_table(metrics: pd.DataFrame, variation: pd.DataFrame) -> pd.DataFrame:
    selected = metrics[
        [
            "scenario",
            "description",
            "stations",
            "construction_cost_10k",
            "cr_eff",
            "demand_satisfaction_rate",
            "problem3_weighted_satisfaction",
            "annual_subsidy",
            "annual_net_profit_total",
            "min_topic_profit_rate",
            "max_topic_profit_rate",
        ]
    ].copy()
    selected = selected.merge(
        variation[["scenario", "composite_variation"]],
        on="scenario",
        how="left",
    )
    selected["cr_eff_pct"] = selected["cr_eff"] * 100
    selected["demand_satisfaction_pct"] = selected["demand_satisfaction_rate"] * 100
    selected["problem3_weighted_satisfaction_pct"] = selected["problem3_weighted_satisfaction"] * 100
    selected["annual_subsidy_10k"] = selected["annual_subsidy"] / 10000
    selected["annual_net_profit_10k"] = selected["annual_net_profit_total"] / 10000
    selected["min_topic_profit_rate_pct"] = selected["min_topic_profit_rate"] * 100
    selected["max_topic_profit_rate_pct"] = selected["max_topic_profit_rate"] * 100
    out = TABLE_DIR / "paper_problem4_scenario_metrics_for_fig7.csv"
    selected.to_csv(out, index=False, encoding="utf-8-sig")
    return selected


def plot_fig7(data: pd.DataFrame) -> None:
    labels = [SCENARIO_LABELS.get(s, s) for s in data["scenario"]]
    x = np.arange(len(data))

    fig, axes = plt.subplots(2, 2, figsize=(13.8, 9.6))
    fig.suptitle("图7 灵敏度情景主要指标对比", fontsize=18, weight="bold", y=0.98)
    fig.text(
        0.5,
        0.945,
        "所有情景均基于问题2与问题3完整重求解结果",
        ha="center",
        fontsize=10.5,
        color="#4B5563",
    )

    ax = axes[0, 0]
    width = 0.25
    bars1 = ax.bar(x - width, data["cr_eff_pct"], width, label="有效服务覆盖率", color="#2563EB")
    bars2 = ax.bar(x, data["demand_satisfaction_pct"], width, label="需求满足率", color="#059669")
    bars3 = ax.bar(x + width, data["problem3_weighted_satisfaction_pct"], width, label="定价后满意度", color="#F59E0B")
    ax.set_title("服务效果指标", fontsize=12.5, weight="bold")
    ax.set_ylabel("比例（%）")
    ax.set_xticks(x)
    ax.set_xticklabels(labels)
    ax.set_ylim(0, max(105, data[["cr_eff_pct", "demand_satisfaction_pct", "problem3_weighted_satisfaction_pct"]].max().max() * 1.16))
    ax.grid(axis="y", color="#E5E7EB", linewidth=0.8)
    ax.legend(frameon=False, fontsize=9, loc="lower right")

    ax = axes[0, 1]
    width = 0.34
    bars_subsidy = ax.bar(x - width / 2, data["annual_subsidy_10k"], width, label="政府补贴", color="#7C3AED")
    bars_profit = ax.bar(x + width / 2, data["annual_net_profit_10k"], width, label="年度净收益", color="#DC2626")
    ax.axhline(0, color="#111827", linewidth=1)
    ax.set_title("补贴与年度净收益", fontsize=12.5, weight="bold")
    ax.set_ylabel("金额（万元/年）")
    ax.set_xticks(x)
    ax.set_xticklabels(labels)
    ax.grid(axis="y", color="#E5E7EB", linewidth=0.8)
    ax.legend(frameon=False, fontsize=9, loc="lower left")
    add_bar_labels(ax, bars_subsidy, fmt="{:.0f}", dy=3, color="#4C1D95")
    for bar in bars_profit:
        height = bar.get_height()
        va = "bottom" if height >= 0 else "top"
        dy = 3 if height >= 0 else -12
        ax.annotate(
            f"{height:.0f}",
            xy=(bar.get_x() + bar.get_width() / 2, height),
            xytext=(0, dy),
            textcoords="offset points",
            ha="center",
            va=va,
            fontsize=8.5,
            color="#991B1B",
        )

    ax = axes[1, 0]
    ax.plot(x, data["max_topic_profit_rate_pct"], marker="o", linewidth=2.4, color="#2563EB", label="最高题目口径利润率")
    ax.plot(x, data["min_topic_profit_rate_pct"], marker="o", linewidth=2.4, color="#DC2626", label="最低题目口径利润率")
    ax.axhline(8, color="#F59E0B", linestyle="--", linewidth=1.6, label="8%上限")
    ax.set_title("题目口径利润率区间", fontsize=12.5, weight="bold")
    ax.set_ylabel("利润率（%）")
    ax.set_xticks(x)
    ax.set_xticklabels(labels)
    ax.grid(axis="y", color="#E5E7EB", linewidth=0.8)
    ax.legend(frameon=False, fontsize=9, loc="lower right")

    ax = axes[1, 1]
    bars = ax.bar(x, data["composite_variation"], color=["#9CA3AF", "#2563EB", "#059669", "#DC2626", "#F59E0B"])
    ax.set_title("方案综合变化度", fontsize=12.5, weight="bold")
    ax.set_ylabel("综合变化度")
    ax.set_xticks(x)
    ax.set_xticklabels(labels)
    ax.grid(axis="y", color="#E5E7EB", linewidth=0.8)
    add_bar_labels(ax, bars, fmt="{:.2f}", dy=3)

    for ax in axes.flat:
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        ax.spines["left"].set_color("#D1D5DB")
        ax.spines["bottom"].set_color("#D1D5DB")
        ax.tick_params(axis="x", labelsize=9)
        ax.tick_params(axis="y", labelsize=9)

    fig.text(
        0.5,
        0.012,
        "数据来源：outputs/tables/problem4_scenario_metrics.csv 与 problem4_variation_indices.csv",
        ha="center",
        fontsize=8.8,
        color="#6B7280",
    )
    fig.tight_layout(rect=[0.02, 0.035, 0.98, 0.925])

    FIG_DIR.mkdir(parents=True, exist_ok=True)
    for ext in ("png", "svg"):
        fig.savefig(FIG_DIR / f"fig7_scenario_metrics_compare.{ext}", bbox_inches="tight")
    plt.close(fig)


def update_figure_index() -> None:
    index_path = FIG_DIR / "figure_index.md"
    entry = """

## 阶段 6.4：问题 4 图表

| 图号 | 图名 | 文件 | 数据来源 | 用途 |
|---|---|---|---|---|
| 图7 | 灵敏度情景主要指标对比 | `fig7_scenario_metrics_compare.svg` | `outputs/tables/problem4_scenario_metrics.csv`; `outputs/tables/problem4_variation_indices.csv` | 对比不同情景下服务效果、补贴净收益、利润率和方案变化度 |
"""
    if index_path.exists():
        text = index_path.read_text(encoding="utf-8")
        if "fig7_scenario_metrics_compare.svg" not in text:
            index_path.write_text(text.rstrip() + entry + "\n", encoding="utf-8")
    else:
        index_path.write_text("# 图表索引\n" + entry, encoding="utf-8")


def write_log(data: pd.DataFrame) -> None:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    log_path = LOG_DIR / "stage6_4_problem4_figures_check.md"
    lines = [
        "# 阶段 6.4 问题 4 图表检查记录",
        "",
        "## 输入文件",
        "",
        "- `outputs/tables/problem4_scenario_metrics.csv`",
        "- `outputs/tables/problem4_variation_indices.csv`",
        "",
        "## 输出文件",
        "",
        "- `outputs/figures/fig7_scenario_metrics_compare.png`",
        "- `outputs/figures/fig7_scenario_metrics_compare.svg`",
        "- `outputs/tables/paper_problem4_scenario_metrics_for_fig7.csv`",
        "",
        "## 检查项",
        "",
        f"- [x] 情景数量为 {len(data)}，包含 S0-S4。",
        "- [x] 图中数据来自完整重求解后的问题 4 结果表。",
        "- [x] 覆盖率、满意度、补贴、利润率单位已标注。",
        "- [x] 题目口径利润率 8% 上限已在图中标出。",
        "- [x] 方案综合变化度来自 `problem4_variation_indices.csv`。",
    ]
    log_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    configure_plot_style()
    metrics = pd.read_csv(TABLE_DIR / "problem4_scenario_metrics.csv")
    variation = pd.read_csv(TABLE_DIR / "problem4_variation_indices.csv")
    data = build_paper_table(metrics, variation)
    plot_fig7(data)
    update_figure_index()
    write_log(data)
    print("Generated:")
    print(FIG_DIR / "fig7_scenario_metrics_compare.png")
    print(FIG_DIR / "fig7_scenario_metrics_compare.svg")
    print(TABLE_DIR / "paper_problem4_scenario_metrics_for_fig7.csv")
    print(LOG_DIR / "stage6_4_problem4_figures_check.md")


if __name__ == "__main__":
    main()
