from __future__ import annotations

from html import escape
from math import ceil
import os
from pathlib import Path

MPL_CONFIG_DIR = Path(__file__).resolve().parents[1] / "paper" / "build" / "mplconfig"
MPL_CONFIG_DIR.mkdir(parents=True, exist_ok=True)
os.environ.setdefault("MPLCONFIGDIR", str(MPL_CONFIG_DIR))

import matplotlib.pyplot as plt
import pandas as pd
from matplotlib import font_manager


ROOT = Path(__file__).resolve().parents[1]
TABLE_DIR = ROOT / "outputs" / "tables"
FIGURE_DIR = ROOT / "outputs" / "figures"
LOG_DIR = ROOT / "outputs" / "logs"

SERVICE_ORDER = ["助餐", "日间照料", "上门护理", "康复理疗", "助浴", "紧急救助"]
ELDER_TYPE_COLUMNS = {
    "self_care": "自理老人",
    "semi_disabled": "半失能老人",
    "disabled": "失能老人",
}

COLORS_ELDER = {
    "自理老人": "#2563EB",
    "半失能老人": "#059669",
    "失能老人": "#DC2626",
}

COLORS_SERVICE = {
    "助餐": "#2563EB",
    "日间照料": "#059669",
    "上门护理": "#DC2626",
    "康复理疗": "#7C3AED",
    "助浴": "#F59E0B",
    "紧急救助": "#64748B",
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


def fmt_num(value: float) -> str:
    return f"{value:,.0f}"


def nice_max(value: float) -> int:
    if value <= 0:
        return 1
    magnitude = 10 ** (len(str(int(value))) - 1)
    return int(ceil(value / magnitude) * magnitude)


def svg_text(x: float, y: float, text: str, size: int = 14, anchor: str = "middle", weight: str = "400",
             fill: str = "#111827", rotate: float | None = None) -> str:
    transform = f' transform="rotate({rotate} {x} {y})"' if rotate is not None else ""
    return (
        f'<text x="{x:.1f}" y="{y:.1f}" font-size="{size}" font-weight="{weight}" '
        f'text-anchor="{anchor}" fill="{fill}" font-family="Microsoft YaHei, SimHei, Arial, sans-serif"{transform}>'
        f"{escape(str(text))}</text>"
    )


def write_svg(path: Path, width: int, height: int, body: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    svg = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<rect width="100%" height="100%" fill="#FFFFFF"/>',
        *body,
        "</svg>",
    ]
    path.write_text("\n".join(svg), encoding="utf-8")


def write_population_png(trend: pd.DataFrame) -> Path:
    configure_plot_style()
    fig, ax = plt.subplots(figsize=(9.8, 6.0))
    years = trend["year"].tolist()
    label_offsets = {
        "自理老人": -18,
        "半失能老人": 14,
        "失能老人": 7,
    }
    for label in ELDER_TYPE_COLUMNS.values():
        values = trend[label].tolist()
        ax.plot(years, values, marker="o", linewidth=2.4, markersize=5.5, label=label, color=COLORS_ELDER[label])
        for year, value in zip(years, values):
            offset = label_offsets[label]
            ax.annotate(
                fmt_num(value),
                (year, value),
                xytext=(0, offset),
                textcoords="offset points",
                ha="center",
                va="top" if offset < 0 else "bottom",
                fontsize=8.5,
                color=COLORS_ELDER[label],
                fontweight="bold",
            )

    ax.set_xlabel("年份 $t$")
    ax.set_ylabel("老人数量（人）")
    ax.set_xticks(years)
    ax.grid(axis="y", alpha=0.26)
    ax.legend(frameon=False, ncol=3, loc="upper center", bbox_to_anchor=(0.5, -0.13))
    fig.tight_layout()

    path = FIGURE_DIR / "fig1_population_forecast.png"
    fig.savefig(path, bbox_inches="tight")
    plt.close(fig)
    return path


def write_demand_stack_png(pivot: pd.DataFrame) -> Path:
    configure_plot_style()
    fig, ax = plt.subplots(figsize=(11.2, 6.6))
    bottom = pd.Series(0.0, index=pivot.index)
    for service in SERVICE_ORDER:
        values = pivot[service].astype(float)
        ax.bar(
            pivot.index,
            values,
            bottom=bottom,
            label=service,
            color=COLORS_SERVICE[service],
            linewidth=0.5,
            edgecolor="white",
        )
        bottom += values

    for community, total in bottom.items():
        ax.annotate(
            fmt_num(total),
            (community, total),
            xytext=(0, 5),
            textcoords="offset points",
            ha="center",
            va="bottom",
            fontsize=8.5,
            fontweight="bold",
        )

    ax.set_xlabel("小区")
    ax.set_ylabel("实际月服务需求（次/月）")
    ax.grid(axis="y", alpha=0.24)
    ax.legend(frameon=False, bbox_to_anchor=(1.01, 1), loc="upper left")
    fig.tight_layout()

    path = FIGURE_DIR / "fig2_community_demand_stack.png"
    fig.savefig(path, bbox_inches="tight")
    plt.close(fig)
    return path


def build_population_trend() -> tuple[pd.DataFrame, Path]:
    src = TABLE_DIR / "problem1_population_forecast.csv"
    df = pd.read_csv(src)

    trend = (
        df.groupby("year", as_index=False)[list(ELDER_TYPE_COLUMNS.keys())]
        .sum()
        .rename(columns=ELDER_TYPE_COLUMNS)
    )
    trend["老人总数"] = trend[list(ELDER_TYPE_COLUMNS.values())].sum(axis=1)
    trend_out = TABLE_DIR / "paper_problem1_population_trend.csv"
    trend.to_csv(trend_out, index=False, encoding="utf-8-sig")

    width, height = 980, 600
    left, right, top, bottom = 92, 62, 42, 118
    plot_w = width - left - right
    plot_h = height - top - bottom
    years = trend["year"].tolist()
    y_max = nice_max(float(trend[list(ELDER_TYPE_COLUMNS.values())].max().max()) * 1.08)
    y_ticks = [0, y_max * 0.25, y_max * 0.50, y_max * 0.75, y_max]

    def x_scale(year: float) -> float:
        return left + (year - min(years)) / (max(years) - min(years)) * plot_w

    def y_scale(value: float) -> float:
        return top + plot_h - value / y_max * plot_h

    body: list[str] = []

    for tick in y_ticks:
        y = y_scale(tick)
        body.append(f'<line x1="{left}" y1="{y:.1f}" x2="{width-right}" y2="{y:.1f}" stroke="#E5E7EB" stroke-width="1"/>')
        body.append(svg_text(left - 12, y + 5, fmt_num(tick), 12, anchor="end", fill="#4B5563"))

    body.append(f'<line x1="{left}" y1="{top}" x2="{left}" y2="{height-bottom}" stroke="#111827" stroke-width="1.2"/>')
    body.append(f'<line x1="{left}" y1="{height-bottom}" x2="{width-right}" y2="{height-bottom}" stroke="#111827" stroke-width="1.2"/>')

    for year in years:
        x = x_scale(year)
        body.append(svg_text(x, height - bottom + 28, str(year), 13, fill="#374151"))
        body.append(f'<line x1="{x:.1f}" y1="{height-bottom}" x2="{x:.1f}" y2="{height-bottom+5}" stroke="#111827"/>')

    label_offsets = {
        "自理老人": 18,
        "半失能老人": -12,
        "失能老人": -6,
    }
    for label in ELDER_TYPE_COLUMNS.values():
        points = [(x_scale(row["year"]), y_scale(row[label])) for _, row in trend.iterrows()]
        point_attr = " ".join(f"{x:.1f},{y:.1f}" for x, y in points)
        body.append(f'<polyline points="{point_attr}" fill="none" stroke="{COLORS_ELDER[label]}" stroke-width="3"/>')
        for idx, (x, y) in enumerate(points):
            body.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="4.2" fill="#FFFFFF" stroke="{COLORS_ELDER[label]}" stroke-width="2"/>')
            value = trend.iloc[idx][label]
            body.append(
                svg_text(
                    x,
                    y + label_offsets[label],
                    fmt_num(value),
                    11,
                    fill=COLORS_ELDER[label],
                    weight="700",
                )
            )

    legend_x = left + 170
    legend_y = height - 44
    for idx, label in enumerate(ELDER_TYPE_COLUMNS.values()):
        x = legend_x + idx * 180
        body.append(f'<circle cx="{x}" cy="{legend_y}" r="6" fill="{COLORS_ELDER[label]}"/>')
        body.append(svg_text(x + 16, legend_y + 5, label, 13, anchor="start", fill="#374151"))

    body.append(svg_text(width / 2, height - 18, "年份 t", 13, fill="#374151"))
    body.append(svg_text(28, top + plot_h / 2, "老人数量（人）", 13, fill="#374151", rotate=-90))

    path = FIGURE_DIR / "fig1_population_forecast.svg"
    write_svg(path, width, height, body)
    write_population_png(trend)
    return trend, path


def build_demand_stack() -> tuple[pd.DataFrame, Path]:
    src = TABLE_DIR / "problem1_actual_demand_by_community_service.csv"
    df = pd.read_csv(src)

    value_col = "actual_demand_rounded" if "actual_demand_rounded" in df.columns else "actual_demand"
    pivot = (
        df.pivot_table(index="community", columns="service", values=value_col, aggfunc="sum")
        .reindex(columns=SERVICE_ORDER)
        .fillna(0)
    )
    pivot = pivot.sort_index()
    pivot_out = TABLE_DIR / "paper_problem1_actual_demand_stack.csv"
    pivot.to_csv(pivot_out, encoding="utf-8-sig")

    width, height = 1120, 660
    left, right, top, bottom = 92, 260, 84, 92
    plot_w = width - left - right
    plot_h = height - top - bottom
    communities = pivot.index.tolist()
    totals = pivot.sum(axis=1)
    y_max = nice_max(float(totals.max()))
    y_ticks = [0, y_max * 0.25, y_max * 0.50, y_max * 0.75, y_max]
    bar_gap = 14
    bar_w = (plot_w - bar_gap * (len(communities) - 1)) / len(communities)

    def y_scale(value: float) -> float:
        return top + plot_h - value / y_max * plot_h

    body: list[str] = []
    body.append(svg_text(width / 2, 64, "按服务项目堆叠，单位：次/月", 13, fill="#4B5563"))

    for tick in y_ticks:
        y = y_scale(tick)
        body.append(f'<line x1="{left}" y1="{y:.1f}" x2="{width-right}" y2="{y:.1f}" stroke="#E5E7EB" stroke-width="1"/>')
        body.append(svg_text(left - 12, y + 5, fmt_num(tick), 12, anchor="end", fill="#4B5563"))

    body.append(f'<line x1="{left}" y1="{top}" x2="{left}" y2="{height-bottom}" stroke="#111827" stroke-width="1.2"/>')
    body.append(f'<line x1="{left}" y1="{height-bottom}" x2="{width-right}" y2="{height-bottom}" stroke="#111827" stroke-width="1.2"/>')

    for i, community in enumerate(communities):
        x = left + i * (bar_w + bar_gap)
        cumulative = 0.0
        for service in SERVICE_ORDER:
            value = float(pivot.loc[community, service])
            y_top = y_scale(cumulative + value)
            y_bottom = y_scale(cumulative)
            rect_h = y_bottom - y_top
            if rect_h > 0:
                body.append(
                    f'<rect x="{x:.1f}" y="{y_top:.1f}" width="{bar_w:.1f}" height="{rect_h:.1f}" '
                    f'fill="{COLORS_SERVICE[service]}" stroke="#FFFFFF" stroke-width="0.6"/>'
                )
            cumulative += value
        body.append(
            svg_text(
                x + bar_w / 2,
                y_scale(cumulative) - 8,
                fmt_num(cumulative),
                11,
                fill="#111827",
                weight="700",
            )
        )
        body.append(svg_text(x + bar_w / 2, height - bottom + 28, community, 13, fill="#374151"))

    legend_x = width - right + 42
    legend_y = top + 20
    for idx, service in enumerate(SERVICE_ORDER):
        y = legend_y + idx * 30
        body.append(f'<rect x="{legend_x}" y="{y-10}" width="14" height="14" rx="2" fill="{COLORS_SERVICE[service]}"/>')
        body.append(svg_text(legend_x + 22, y + 2, service, 13, anchor="start", fill="#374151"))

    body.append(svg_text((left + width - right) / 2, height - 18, "小区", 13, fill="#374151"))
    body.append(svg_text(28, top + plot_h / 2, "实际月服务需求（次/月）", 13, fill="#374151", rotate=-90))

    path = FIGURE_DIR / "fig2_community_demand_stack.svg"
    write_svg(path, width, height, body)
    write_demand_stack_png(pivot)
    return pivot, path


def write_index_and_log(generated: dict[str, Path]) -> None:
    FIGURE_DIR.mkdir(parents=True, exist_ok=True)
    LOG_DIR.mkdir(parents=True, exist_ok=True)

    index_path = FIGURE_DIR / "figure_index.md"
    if not index_path.exists():
        index_text = """# 图表索引

## 阶段 6.1：问题 1 图表

| 图号 | 图名 | 主文件 | 备用格式 | 数据来源 | 用途 |
|---|---|---|---|---|---|
| 图1 | 三类老人五年数量预测趋势 | `fig1_population_forecast.svg` | `fig1_population_forecast.png` | `outputs/tables/problem1_population_forecast.csv` | 展示未来五年三类老人规模变化 |
| 图2 | 第5年各小区实际服务需求结构 | `fig2_community_demand_stack.svg` | `fig2_community_demand_stack.png` | `outputs/tables/problem1_actual_demand_by_community_service.csv` | 展示消费约束后各小区服务需求结构 |
"""
        index_path.write_text(index_text, encoding="utf-8")

    log_path = LOG_DIR / "stage6_1_figures_check.md"
    generated_lines = [f"- {fig_name}: `{path.relative_to(ROOT)}`" for fig_name, path in generated.items()]
    log_text = f"""# 阶段 6.1 图表检查记录

## 生成方式

- 数据型图表均使用 Python 绘制。
- 阶段 6.1 保留 SVG 主文件，并额外生成 PNG 备用格式以便 LaTeX 驱动和排版软件兼容。
- 图 1 已标注各年份三类老人数量：蓝线标注在线段下方，绿线标注在线段上方，红线标注位于红线上方且向下微调以避开绿线标注，并已移除图内顶部标题；图 2 已标注各小区总服务需求。堆叠柱各分段不逐一标注，避免图面拥挤。
- 未使用大模型生图。

## 生成文件

{chr(10).join(generated_lines)}

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
"""
    log_path.write_text(log_text, encoding="utf-8")


def main() -> None:
    FIGURE_DIR.mkdir(parents=True, exist_ok=True)
    TABLE_DIR.mkdir(parents=True, exist_ok=True)
    LOG_DIR.mkdir(parents=True, exist_ok=True)

    generated: dict[str, Path] = {}
    _, fig1_path = build_population_trend()
    generated["图1 三类老人五年数量预测趋势（SVG 主文件）"] = fig1_path
    generated["图1 三类老人五年数量预测趋势（PNG 备用格式）"] = FIGURE_DIR / "fig1_population_forecast.png"
    _, fig2_path = build_demand_stack()
    generated["图2 第5年各小区实际服务需求结构（SVG 主文件）"] = fig2_path
    generated["图2 第5年各小区实际服务需求结构（PNG 备用格式）"] = FIGURE_DIR / "fig2_community_demand_stack.png"
    write_index_and_log(generated)

    print("Stage 6.1 figures generated:")
    for fig_name, path in generated.items():
        print(f"{fig_name}: {path}")


if __name__ == "__main__":
    main()
