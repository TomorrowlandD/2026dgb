from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd

from data_loader import COMMUNITY_ORDER, LOG_DIR, SERVICE_ORDER, TABLE_DIR


EPS = 1e-6


def read_csv(name: str) -> pd.DataFrame:
    return pd.read_csv(TABLE_DIR / name)


def check(condition: bool, item: str, detail: Any) -> dict[str, Any]:
    return {"item": item, "passed": bool(condition), "detail": detail}


def json_all_passed(name: str) -> bool:
    path = LOG_DIR / name
    payload = json.loads(path.read_text(encoding="utf-8"))
    return bool(payload.get("all_passed"))


def main() -> None:
    checks: list[dict[str, Any]] = []

    required_files = [
        LOG_DIR / "stage0_check.md",
        LOG_DIR / "stage1_data_check.json",
        LOG_DIR / "stage2_problem1_check.json",
        LOG_DIR / "stage3_problem2_check.json",
        LOG_DIR / "stage4_problem3_check.json",
        LOG_DIR / "stage5_problem4_check.json",
        TABLE_DIR / "problem1_actual_demand.csv",
        TABLE_DIR / "problem2_best_station_plan.csv",
        TABLE_DIR / "problem2_assignment.csv",
        TABLE_DIR / "problem2_effective_service_by_community_service.csv",
        TABLE_DIR / "problem2_effective_service_by_community_elder_service.csv",
        TABLE_DIR / "problem3_prices.csv",
        TABLE_DIR / "problem3_station_finance.csv",
        TABLE_DIR / "problem3_metrics.csv",
        TABLE_DIR / "problem4_scenario_metrics.csv",
        TABLE_DIR / "problem4_variation_indices.csv",
    ]
    missing = [str(path) for path in required_files if not path.exists()]
    checks.append(check(not missing, "阶段 0-5 必要日志和结果文件存在", missing))

    stage0_text = (LOG_DIR / "stage0_check.md").read_text(encoding="utf-8")
    checks.append(check("阶段 0 已通过" in stage0_text, "阶段 0 日志显示已通过", "stage0_check.md"))
    for filename in [
        "stage1_data_check.json",
        "stage2_problem1_check.json",
        "stage3_problem2_check.json",
        "stage4_problem3_check.json",
        "stage5_problem4_check.json",
    ]:
        checks.append(check(json_all_passed(filename), f"{filename} all_passed=true", filename))

    communities = read_csv("stage1_communities.csv")
    checks.append(
        check(
            communities["community"].tolist() == COMMUNITY_ORDER,
            "阶段 1 小区顺序保持 A-J",
            communities["community"].tolist(),
        )
    )
    type_sum = communities[["self_care", "semi_disabled", "disabled"]].sum(axis=1)
    checks.append(
        check(
            bool((type_sum == communities["elderly_total"]).all()),
            "阶段 1 三类老人初始人数等于 60+ 人数",
            (type_sum - communities["elderly_total"]).tolist(),
        )
    )

    actual = read_csv("problem1_actual_demand.csv")
    checks.append(
        check(
            bool((actual["actual_demand"] <= actual["theoretical_demand"] + EPS).all()),
            "阶段 2 实际需求不超过理论需求",
            "actual_demand <= theoretical_demand",
        )
    )
    emergency = actual.loc[actual["service"].eq("紧急救助")]
    checks.append(
        check(
            bool((emergency["actual_demand"].round(8) == emergency["theoretical_demand"].round(8)).all()),
            "阶段 2 紧急救助未被消费约束削减",
            "emergency demand equality",
        )
    )

    best_plan = read_csv("problem2_best_station_plan.csv")
    assignment = read_csv("problem2_assignment.csv")
    coverage = read_csv("problem2_coverage_summary.csv").iloc[0]
    checks.append(
        check(
            float(best_plan["construction_cost_10k"].sum()) <= 120 + EPS,
            "阶段 3 最优方案建设成本不超过 120 万元",
            float(best_plan["construction_cost_10k"].sum()),
        )
    )
    checks.append(
        check(
            bool((assignment["distance"] <= 1000 + EPS).all()),
            "阶段 3 所有分配距离不超过 1000 米",
            assignment[["community", "assigned_station", "distance"]].to_dict(orient="records"),
        )
    )
    checks.append(
        check(
            0 <= float(coverage["cr_srv"]) <= 1 and 0 <= float(coverage["cr_eff"]) <= 1,
            "阶段 3 覆盖率指标在 [0,1] 内",
            {"cr_srv": float(coverage["cr_srv"]), "cr_eff": float(coverage["cr_eff"])},
        )
    )

    eff_service = read_csv("problem2_effective_service_by_community_service.csv")
    eff_typed = read_csv("problem2_effective_service_by_community_elder_service.csv")
    typed_agg = (
        eff_typed.groupby(["community", "service"], as_index=False)["effective_service"]
        .sum()
        .sort_values(["community", "service"])
        .reset_index(drop=True)
    )
    service_sorted = eff_service[["community", "service", "effective_service"]].sort_values(["community", "service"]).reset_index(drop=True)
    max_eff_diff = (typed_agg["effective_service"] - service_sorted["effective_service"]).abs().max()
    checks.append(
        check(
            max_eff_diff <= EPS,
            "阶段 3 E_{i,r,k} 汇总等于 E_{i,k}",
            float(max_eff_diff),
        )
    )

    prices = read_csv("problem3_prices.csv")
    finance = read_csv("problem3_station_finance.csv")
    metrics = read_csv("problem3_metrics.csv").iloc[0]
    checks.append(
        check(
            bool((prices.loc[prices["service"].eq("紧急救助"), "price"] == 0).all()),
            "阶段 4 紧急救助价格为 0",
            prices.loc[prices["service"].eq("紧急救助"), ["station", "price"]].to_dict(orient="records"),
        )
    )
    checks.append(
        check(
            bool((finance["annual_subsidy"] <= finance["annual_subsidy_cap"] + EPS).all()),
            "阶段 4 政府补贴不超过上限",
            finance[["station", "annual_subsidy", "annual_subsidy_cap"]].to_dict(orient="records"),
        )
    )
    checks.append(
        check(
            bool((finance["topic_profit_rate"] <= 0.08 + EPS).all()),
            "阶段 4 所有站点满足 rho <= 8%",
            finance[["station", "topic_profit_rate"]].to_dict(orient="records"),
        )
    )
    checks.append(
        check(
            abs(float(metrics["annual_elder_pay"]) - float(finance["annual_revenue"].sum())) <= EPS,
            "阶段 4 老人支付额等于站点年收入合计",
            {
                "annual_elder_pay": float(metrics["annual_elder_pay"]),
                "annual_revenue_sum": float(finance["annual_revenue"].sum()),
            },
        )
    )

    scenario_metrics = read_csv("problem4_scenario_metrics.csv")
    variation = read_csv("problem4_variation_indices.csv")
    checks.append(
        check(
            scenario_metrics["scenario"].tolist() == ["S0", "S1", "S2", "S3", "S4"],
            "阶段 5 输出 S0-S4 五个情景",
            scenario_metrics["scenario"].tolist(),
        )
    )
    checks.append(
        check(
            bool((scenario_metrics["max_topic_profit_rate"] <= 0.08 + EPS).all()),
            "阶段 5 所有情景满足 rho <= 8%",
            scenario_metrics[["scenario", "max_topic_profit_rate"]].to_dict(orient="records"),
        )
    )
    s4_budget = float(scenario_metrics.loc[scenario_metrics["scenario"].eq("S4"), "construction_cost_10k"].iloc[0])
    checks.append(check(s4_budget <= 140 + EPS, "阶段 5 S4 使用 140 万元预算", s4_budget))
    checks.append(
        check(
            variation["scenario"].tolist() == ["S0", "S1", "S2", "S3", "S4"]
            and abs(float(variation.loc[variation["scenario"].eq("S0"), "composite_variation"].iloc[0])) <= EPS,
            "阶段 5 方案变化度以 S0 为基准",
            variation[["scenario", "composite_variation"]].to_dict(orient="records"),
        )
    )

    payload = {"all_passed": all(item["passed"] for item in checks), "checks": checks}
    (LOG_DIR / "stage0_5_recheck.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    lines = [
        "# 阶段 0-5 复核记录",
        "",
        f"总体结果：{'通过' if payload['all_passed'] else '未通过'}",
        "",
        "## 检查项",
    ]
    for item in checks:
        mark = "x" if item["passed"] else " "
        lines.append(f"- [{mark}] {item['item']}")
    (LOG_DIR / "stage0_5_recheck.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(json.dumps(payload, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
