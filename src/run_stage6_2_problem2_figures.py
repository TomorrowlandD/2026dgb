from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib import font_manager
from matplotlib.patches import FancyBboxPatch


ROOT = Path(__file__).resolve().parents[1]
TABLE_DIR = ROOT / "outputs" / "tables"
FIG_DIR = ROOT / "outputs" / "figures"


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


def classical_mds(distance_matrix: pd.DataFrame) -> pd.DataFrame:
    labels = list(distance_matrix.index)
    d = distance_matrix.to_numpy(dtype=float)
    n = d.shape[0]
    h = np.eye(n) - np.ones((n, n)) / n
    b = -0.5 * h @ (d ** 2) @ h
    eigenvalues, eigenvectors = np.linalg.eigh(b)
    order = np.argsort(eigenvalues)[::-1]
    eigenvalues = eigenvalues[order]
    eigenvectors = eigenvectors[:, order]
    coords = eigenvectors[:, :2] * np.sqrt(np.maximum(eigenvalues[:2], 0))
    return pd.DataFrame(coords, index=labels, columns=["x", "y"])


def scale_label_to_size(scale: str) -> int:
    return {"小型": 360, "中型": 520, "大型": 700}.get(scale, 420)


def plot_station_assignment() -> None:
    assignments = pd.read_csv(TABLE_DIR / "problem2_assignment.csv")
    plan = pd.read_csv(TABLE_DIR / "problem2_best_station_plan.csv")
    stations = set(plan["station"])
    station_scale = dict(zip(plan["station"], plan["scale"]))

    # Hand-tuned cluster layout for a clear service-relationship diagram.
    # The original MDS layout preserves relative distances, but it creates label and edge collisions.
    coords = pd.DataFrame(
        {
            "x": {
                "G": -2.3,
                "E": -3.15,
                "F": -3.35,
                "I": -1.35,
                "D": 1.45,
                "H": 1.75,
                "A": 3.55,
                "B": 2.45,
                "J": 2.52,
                "C": -0.15,
            },
            "y": {
                "G": 0.25,
                "E": -0.55,
                "F": 1.25,
                "I": 1.05,
                "D": 0.38,
                "H": 1.55,
                "A": 0.05,
                "B": -1.30,
                "J": -0.50,
                "C": -2.35,
            },
        }
    )

    fig, ax = plt.subplots(figsize=(11.5, 7.6))

    for _, row in assignments.iterrows():
        community = row["community"]
        station = row["assigned_station"]
        x0, y0 = coords.loc[community, ["x", "y"]]
        x1, y1 = coords.loc[station, ["x", "y"]]
        if community == station:
            continue
        ax.plot([x0, x1], [y0, y1], color="#9CA3AF", linewidth=1.4, alpha=0.72, zorder=1)
        mid_x, mid_y = (x0 + x1) / 2, (y0 + y1) / 2
        label_offsets = {
            ("E", "G"): (-0.04, -0.10),
            ("F", "G"): (0.03, 0.12),
            ("I", "G"): (0.00, 0.12),
            ("H", "D"): (0.08, 0.08),
            ("J", "D"): (0.08, -0.08),
            ("B", "D"): (0.10, -0.12),
            ("A", "D"): (0.02, 0.12),
        }
        dx, dy = label_offsets.get((community, station), (0, 0))
        ax.text(
            mid_x + dx,
            mid_y + dy,
            f"{int(row['distance'])}m",
            fontsize=8,
            color="#6B7280",
            ha="center",
            va="center",
            bbox={"boxstyle": "round,pad=0.15", "facecolor": "white", "edgecolor": "none", "alpha": 0.78},
            zorder=2,
        )

    for community, point in coords.iterrows():
        if community in stations:
            scale = station_scale[community]
            width = {"小型": 0.54, "中型": 0.66, "大型": 0.74}.get(scale, 0.64)
            height = 0.46
            rect = FancyBboxPatch(
                (point["x"] - width / 2, point["y"] - height / 2),
                width,
                height,
                boxstyle="round,pad=0.06,rounding_size=0.035",
                facecolor="#2563EB",
                edgecolor="#1E3A8A",
                linewidth=1.6,
                zorder=3,
            )
            ax.add_patch(rect)
            ax.text(
                point["x"],
                point["y"],
                f"{community}\n{scale}",
                fontsize=10.5,
                ha="center",
                va="center",
                color="#111827",
                linespacing=1.22,
                zorder=4,
            )
        else:
            ax.scatter(
                point["x"],
                point["y"],
                s=360,
                marker="o",
                c="#E5E7EB",
                edgecolors="#6B7280",
                linewidths=1.5,
                zorder=3,
            )
            ax.text(point["x"], point["y"], community, fontsize=11, ha="center", va="center", color="#111827", zorder=4)

    summary = pd.read_csv(TABLE_DIR / "problem2_coverage_summary.csv").iloc[0]
    subtitle = (
        f"站点数 {int(summary['station_count'])} | 建设成本 {summary['construction_cost_10k']:.0f} 万元 | "
        f"服务覆盖率 {summary['cr_srv'] * 100:.1f}%"
    )
    fig.text(
        0.5,
        0.950,
        subtitle,
        ha="center",
        fontsize=11,
        color="#374151",
        bbox={"boxstyle": "round,pad=0.25", "facecolor": "#F9FAFB", "edgecolor": "#E5E7EB"},
    )
    ax.text(
        0.5,
        -0.04,
        "说明：布局依据服务分配关系和标注距离进行示意调整，仅表示服务关系与距离量级，不代表真实地图位置。",
        transform=ax.transAxes,
        ha="center",
        fontsize=9,
        color="#6B7280",
    )
    ax.set_axis_off()
    ax.set_xlim(-3.95, 4.05)
    ax.set_ylim(-2.95, 2.05)
    fig.subplots_adjust(top=0.89, bottom=0.12, left=0.03, right=0.97)

    for ext in ("png", "svg"):
        fig.savefig(FIG_DIR / f"fig3_station_assignment.{ext}", bbox_inches="tight")
    plt.close(fig)


def plot_station_utilization_capacity() -> None:
    util = pd.read_csv(TABLE_DIR / "problem2_station_utilization.csv")
    plan = pd.read_csv(TABLE_DIR / "problem2_best_station_plan.csv")
    util = util.merge(plan[["station", "construction_cost_10k"]], on="station", how="left")
    util["label"] = util["station"] + "\n" + util["scale"]

    x = np.arange(len(util))
    width = 0.34

    fig, ax = plt.subplots(figsize=(9.6, 6.2))
    bars1 = ax.bar(
        x - width / 2,
        util["utilization"],
        width,
        label="利用率",
        color="#2563EB",
        edgecolor="#1E40AF",
        linewidth=0.8,
    )
    bars2 = ax.bar(
        x + width / 2,
        util["capacity_gamma"],
        width,
        label="容量可得系数",
        color="#F59E0B",
        edgecolor="#B45309",
        linewidth=0.8,
    )

    for y, label in [(0.60, "S2=1.00上限"), (0.75, "S2=0.93"), (0.85, "S2=0.85"), (0.95, "S2=0.72")]:
        ax.axhline(y, color="#D1D5DB", linewidth=0.8, linestyle="--", zorder=0)
        ax.text(len(util) - 0.12, y + 0.008, label, fontsize=8, color="#6B7280", ha="right")

    for bars in (bars1, bars2):
        for bar in bars:
            value = bar.get_height()
            ax.text(
                bar.get_x() + bar.get_width() / 2,
                value + 0.015,
                f"{value * 100:.1f}%",
                ha="center",
                va="bottom",
                fontsize=9,
                color="#111827",
            )

    for idx, row in util.iterrows():
        communities = str(row["assigned_communities"]).replace(",", ", ")
        ax.text(
            idx,
            -0.16,
            f"覆盖：{communities}",
            ha="center",
            va="top",
            fontsize=8,
            color="#4B5563",
            transform=ax.get_xaxis_transform(),
        )

    ax.set_ylabel("比例")
    ax.set_ylim(0, 1.18)
    ax.set_xlim(-0.55, len(util) - 0.02)
    ax.set_xticks(x)
    ax.set_xticklabels(util["label"], fontsize=10)
    ax.legend(loc="upper left", bbox_to_anchor=(0.0, 1.13), frameon=False, ncol=2)
    ax.grid(axis="y", color="#E5E7EB", linewidth=0.8)
    ax.spines[["top", "right"]].set_visible(False)
    fig.subplots_adjust(top=0.82, bottom=0.20, left=0.08, right=0.92)

    for ext in ("png", "svg"):
        fig.savefig(FIG_DIR / f"fig4_station_utilization_capacity.{ext}", bbox_inches="tight")
    plt.close(fig)


def main() -> None:
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    configure_plot_style()
    plot_station_assignment()
    plot_station_utilization_capacity()
    print("Generated:")
    print(FIG_DIR / "fig3_station_assignment.png")
    print(FIG_DIR / "fig3_station_assignment.svg")
    print(FIG_DIR / "fig4_station_utilization_capacity.png")
    print(FIG_DIR / "fig4_station_utilization_capacity.svg")


if __name__ == "__main__":
    main()
