from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd

from data_loader import (
    ELDER_TYPE_ORDER,
    LOG_DIR,
    SERVICE_ORDER,
    TABLE_DIR,
    load_all_parameters,
)


YEARS = 5
MORTALITY_RATE = 0.05
NEW_ELDERLY_RATE = 0.07
CHARGED_SERVICES = [service for service in SERVICE_ORDER if service != "紧急救助"]
EMERGENCY_SERVICE = "紧急救助"

ELDER_COLS = {
    "自理": "self_care",
    "半失能": "semi_disabled",
    "失能": "disabled",
}


def _write_csv(df: pd.DataFrame, filename: str) -> Path:
    TABLE_DIR.mkdir(parents=True, exist_ok=True)
    path = TABLE_DIR / filename
    df.to_csv(path, index=False, encoding="utf-8-sig")
    return path


def _transition_value(params: dict[str, pd.DataFrame], parameter: str) -> float:
    transition = params["transition_probabilities"]
    row = transition.loc[transition["parameter"].eq(parameter)]
    if row.empty:
        raise ValueError(f"Missing transition parameter: {parameter}")
    return float(row["probability"].iloc[0])


def forecast_population(params: dict[str, pd.DataFrame]) -> pd.DataFrame:
    communities = params["communities"].copy()
    p12 = _transition_value(params, "p12")
    p23 = _transition_value(params, "p23")

    state = communities[
        ["community", "self_care", "semi_disabled", "disabled", "monthly_income"]
    ].copy()
    records: list[dict[str, Any]] = []

    for year in range(YEARS + 1):
        current = state.copy()
        current["year"] = year
        current["elderly_total"] = (
            current["self_care"] + current["semi_disabled"] + current["disabled"]
        )
        records.extend(
            current[
                [
                    "year",
                    "community",
                    "self_care",
                    "semi_disabled",
                    "disabled",
                    "elderly_total",
                    "monthly_income",
                ]
            ].to_dict(orient="records")
        )

        if year == YEARS:
            break

        total = current["elderly_total"]
        next_state = state[["community", "monthly_income"]].copy()
        next_state["self_care"] = (
            (1 - MORTALITY_RATE) * (1 - p12) * state["self_care"]
            + NEW_ELDERLY_RATE * total
        )
        next_state["semi_disabled"] = (1 - MORTALITY_RATE) * (
            p12 * state["self_care"] + (1 - p23) * state["semi_disabled"]
        )
        next_state["disabled"] = (1 - MORTALITY_RATE) * (
            p23 * state["semi_disabled"] + state["disabled"]
        )
        state = next_state

    population = pd.DataFrame(records)
    return population


def build_theoretical_demand(
    population: pd.DataFrame, params: dict[str, pd.DataFrame]
) -> pd.DataFrame:
    final_population = population.loc[population["year"].eq(YEARS)].copy()
    service_demand = params["service_demand"].copy()

    records: list[dict[str, Any]] = []
    for _, pop_row in final_population.iterrows():
        for elder_type in ELDER_TYPE_ORDER:
            elder_count = float(pop_row[ELDER_COLS[elder_type]])
            for _, demand_row in service_demand.iterrows():
                service = str(demand_row["service"])
                monthly_times = float(demand_row[ELDER_COLS[elder_type]])
                demand = elder_count * monthly_times
                records.append(
                    {
                        "community": pop_row["community"],
                        "elder_type": elder_type,
                        "service": service,
                        "elder_count_year5": elder_count,
                        "monthly_times_per_person": monthly_times,
                        "theoretical_demand": demand,
                        "theoretical_demand_rounded": round(demand),
                    }
                )

    return pd.DataFrame(records)


def apply_consumption_constraint(
    theoretical: pd.DataFrame, params: dict[str, pd.DataFrame]
) -> tuple[pd.DataFrame, pd.DataFrame]:
    communities = params["communities"][["community", "monthly_income"]].copy()
    costs = params["service_costs"][["service", "base_price", "is_emergency"]].copy()
    limits = params["consumption_limits"].copy()

    demand = theoretical.merge(costs, on="service", how="left")
    demand = demand.merge(communities, on="community", how="left")
    demand = demand.merge(limits, on="elder_type", how="left")
    demand["theoretical_fee"] = demand["theoretical_demand"] * demand["base_price"]

    charged = demand.loc[~demand["is_emergency"]].copy()
    group_cols = ["community", "elder_type"]
    charged_fee = (
        charged.groupby(group_cols, as_index=False)["theoretical_fee"]
        .sum()
        .rename(columns={"theoretical_fee": "charged_theoretical_fee"})
    )
    base_budget = (
        demand[group_cols + ["elder_count_year5", "monthly_income", "max_income_share"]]
        .drop_duplicates(group_cols)
        .copy()
    )
    budget = base_budget.merge(charged_fee, on=group_cols, how="left")
    budget["charged_theoretical_fee"] = budget["charged_theoretical_fee"].fillna(0)
    budget["monthly_budget"] = (
        budget["elder_count_year5"] * budget["monthly_income"] * budget["max_income_share"]
    )
    budget["reduction_alpha"] = 1.0
    over_budget = budget["charged_theoretical_fee"] > budget["monthly_budget"]
    budget.loc[over_budget, "reduction_alpha"] = (
        budget.loc[over_budget, "monthly_budget"]
        / budget.loc[over_budget, "charged_theoretical_fee"]
    )

    demand = demand.merge(
        budget[group_cols + ["monthly_budget", "charged_theoretical_fee", "reduction_alpha"]],
        on=group_cols,
        how="left",
    )
    demand["actual_demand"] = demand["theoretical_demand"]
    charged_mask = ~demand["is_emergency"]
    demand.loc[charged_mask, "actual_demand"] = (
        demand.loc[charged_mask, "theoretical_demand"]
        * demand.loc[charged_mask, "reduction_alpha"]
    )
    demand["actual_demand_rounded"] = demand["actual_demand"].round().astype(int)
    demand["satisfaction_rate_budget"] = (
        demand["actual_demand"] / demand["theoretical_demand"].replace(0, pd.NA)
    ).fillna(1.0)
    demand["actual_fee"] = demand["actual_demand"] * demand["base_price"]

    budget_actual_fee = (
        demand.loc[~demand["is_emergency"]]
        .groupby(group_cols, as_index=False)["actual_fee"]
        .sum()
        .rename(columns={"actual_fee": "charged_actual_fee"})
    )
    budget = budget.merge(budget_actual_fee, on=group_cols, how="left")
    budget["charged_actual_fee"] = budget["charged_actual_fee"].fillna(0)
    budget["budget_utilization"] = (
        budget["charged_actual_fee"] / budget["monthly_budget"].replace(0, pd.NA)
    ).fillna(0.0)

    actual_cols = [
        "community",
        "elder_type",
        "service",
        "elder_count_year5",
        "monthly_times_per_person",
        "base_price",
        "is_emergency",
        "theoretical_demand",
        "theoretical_demand_rounded",
        "actual_demand",
        "actual_demand_rounded",
        "satisfaction_rate_budget",
        "theoretical_fee",
        "actual_fee",
        "monthly_budget",
        "charged_theoretical_fee",
        "reduction_alpha",
    ]
    return demand[actual_cols].copy(), budget.copy()


def aggregate_demands(theoretical: pd.DataFrame, actual: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    theoretical_agg = (
        theoretical.groupby(["community", "service"], as_index=False)["theoretical_demand"]
        .sum()
        .assign(theoretical_demand_rounded=lambda df: df["theoretical_demand"].round().astype(int))
    )
    actual_agg = (
        actual.groupby(["community", "service"], as_index=False)[["theoretical_demand", "actual_demand"]]
        .sum()
    )
    actual_agg["actual_demand_rounded"] = actual_agg["actual_demand"].round().astype(int)
    actual_agg["demand_retention_rate"] = (
        actual_agg["actual_demand"] / actual_agg["theoretical_demand"].replace(0, pd.NA)
    ).fillna(1.0)
    return theoretical_agg, actual_agg


def build_checks(
    population: pd.DataFrame,
    theoretical: pd.DataFrame,
    actual: pd.DataFrame,
    budget: pd.DataFrame,
) -> list[dict[str, Any]]:
    final_population = population.loc[population["year"].eq(YEARS)].copy()
    charged_actual = actual.loc[~actual["is_emergency"]].copy()
    emergency = actual.loc[actual["service"].eq(EMERGENCY_SERVICE)].copy()
    over_budget = budget["charged_theoretical_fee"] > budget["monthly_budget"]

    alpha_check = True
    if over_budget.any():
        expected_alpha = (
            budget.loc[over_budget, "monthly_budget"]
            / budget.loc[over_budget, "charged_theoretical_fee"]
        )
        alpha_check = bool(
            (budget.loc[over_budget, "reduction_alpha"].round(10) == expected_alpha.round(10)).all()
        )

    budget_usage_ok = bool((budget["budget_utilization"] <= 1 + 1e-8).all())
    if over_budget.any():
        budget_usage_ok = budget_usage_ok and bool(
            (budget.loc[over_budget, "budget_utilization"].round(8) == 1.0).all()
        )

    checks = [
        {
            "item": "五年递推逐年输出 0 至 5 年",
            "passed": sorted(population["year"].unique().tolist()) == list(range(YEARS + 1)),
            "detail": sorted(population["year"].unique().tolist()),
        },
        {
            "item": "老人数量均非负",
            "passed": bool((population[["self_care", "semi_disabled", "disabled", "elderly_total"]] >= 0).all().all()),
            "detail": "nonnegative population",
        },
        {
            "item": "老人总数等于三类老人加总",
            "passed": bool(
                (
                    population["elderly_total"].round(8)
                    == (
                        population["self_care"]
                        + population["semi_disabled"]
                        + population["disabled"]
                    ).round(8)
                ).all()
            ),
            "detail": "elderly_total matches type sum",
        },
        {
            "item": "第 5 年理论需求均非负",
            "passed": bool((theoretical["theoretical_demand"] >= 0).all()),
            "detail": "nonnegative theoretical demand",
        },
        {
            "item": "实际需求不超过理论需求",
            "passed": bool((actual["actual_demand"] <= actual["theoretical_demand"] + 1e-8).all()),
            "detail": "actual demand <= theoretical demand",
        },
        {
            "item": "紧急救助未被消费约束削减",
            "passed": bool((emergency["actual_demand"].round(10) == emergency["theoretical_demand"].round(10)).all()),
            "detail": "emergency actual demand equals theoretical demand",
        },
        {
            "item": "预算不足时收费服务按同一比例削减",
            "passed": alpha_check,
            "detail": budget[["community", "elder_type", "charged_theoretical_fee", "monthly_budget", "reduction_alpha"]].to_dict(orient="records"),
        },
        {
            "item": "收费服务实际费用不超过预算，预算不足时使用率接近 1",
            "passed": budget_usage_ok,
            "detail": budget[["community", "elder_type", "monthly_budget", "charged_actual_fee", "budget_utilization"]].to_dict(orient="records"),
        },
        {
            "item": "计算过程保留小数并另有取整展示列",
            "passed": "actual_demand_rounded" in actual.columns and "theoretical_demand_rounded" in theoretical.columns,
            "detail": "rounded columns are present while continuous columns are preserved",
        },
        {
            "item": "第 5 年预测小区数为 10",
            "passed": len(final_population["community"].unique()) == 10,
            "detail": final_population["community"].tolist(),
        },
    ]
    return checks


def export_outputs(
    population: pd.DataFrame,
    theoretical: pd.DataFrame,
    actual: pd.DataFrame,
    budget: pd.DataFrame,
    theoretical_agg: pd.DataFrame,
    actual_agg: pd.DataFrame,
    checks: list[dict[str, Any]],
) -> None:
    TABLE_DIR.mkdir(parents=True, exist_ok=True)
    LOG_DIR.mkdir(parents=True, exist_ok=True)

    outputs = {
        "problem1_population_forecast.csv": population,
        "problem1_population_forecast_display.csv": population.assign(
            self_care_rounded=population["self_care"].round().astype(int),
            semi_disabled_rounded=population["semi_disabled"].round().astype(int),
            disabled_rounded=population["disabled"].round().astype(int),
            elderly_total_rounded=population["elderly_total"].round().astype(int),
        ),
        "problem1_theoretical_demand.csv": theoretical,
        "problem1_theoretical_demand_by_community_service.csv": theoretical_agg,
        "problem1_actual_demand.csv": actual,
        "problem1_actual_demand_by_community_service.csv": actual_agg,
        "problem1_budget_check.csv": budget,
    }
    for filename, df in outputs.items():
        _write_csv(df, filename)

    check_payload = {"all_passed": all(item["passed"] for item in checks), "checks": checks}
    (LOG_DIR / "stage2_problem1_check.json").write_text(
        json.dumps(check_payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    lines = [
        "# 阶段 2 问题 1 检查",
        "",
        f"总体结果：{'通过' if check_payload['all_passed'] else '未通过'}",
        "",
        "## 检查项",
    ]
    for item in checks:
        mark = "x" if item["passed"] else " "
        lines.append(f"- [{mark}] {item['item']}")
    lines.extend(["", "## 输出文件"])
    for filename in outputs:
        lines.append(f"- `outputs/tables/{filename}`")
    (LOG_DIR / "stage2_problem1_check.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    params = load_all_parameters()
    population = forecast_population(params)
    theoretical = build_theoretical_demand(population, params)
    actual, budget = apply_consumption_constraint(theoretical, params)
    theoretical_agg, actual_agg = aggregate_demands(theoretical, actual)
    checks = build_checks(population, theoretical, actual, budget)
    export_outputs(population, theoretical, actual, budget, theoretical_agg, actual_agg, checks)
    print(json.dumps({"all_passed": all(item["passed"] for item in checks)}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
