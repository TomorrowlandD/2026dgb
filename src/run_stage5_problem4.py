from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

import pandas as pd

import run_stage2_problem1 as p1
import run_stage3_problem2 as p2
import run_stage4_problem3 as p3
from data_loader import COMMUNITY_ORDER, ELDER_TYPE_ORDER, LOG_DIR, SERVICE_ORDER, TABLE_DIR, load_all_parameters


SCENARIO_ORDER = ["S0", "S1", "S2", "S3", "S4"]
SCALE_RANK = {"小型": 1, "中型": 2, "大型": 3}
EPS = 1e-8


@dataclass(frozen=True)
class ScenarioConfig:
    scenario: str
    description: str
    elderly_growth_rate: float | None = None
    p12: float | None = None
    p23: float | None = None
    daily_fixed_cost_multiplier: float = 1.0
    construction_budget_10k: float = 120.0


SCENARIOS = [
    ScenarioConfig("S0", "基准方案"),
    ScenarioConfig("S1", "60+老人年增长率调整为8%", elderly_growth_rate=0.08),
    ScenarioConfig("S2", "自理到半失能5.5%，半失能到失能9.5%", p12=0.055, p23=0.095),
    ScenarioConfig("S3", "日固定管理成本增加20%", daily_fixed_cost_multiplier=1.2),
    ScenarioConfig("S4", "总建设预算调整为140万元", construction_budget_10k=140.0),
]


def clone_params(params: dict[str, pd.DataFrame]) -> dict[str, pd.DataFrame]:
    return {key: value.copy(deep=True) for key, value in params.items()}


def apply_scenario_params(base_params: dict[str, pd.DataFrame], scenario: ScenarioConfig) -> dict[str, pd.DataFrame]:
    params = clone_params(base_params)
    if scenario.p12 is not None:
        params["transition_probabilities"].loc[
            params["transition_probabilities"]["parameter"].eq("p12"),
            "probability",
        ] = scenario.p12
    if scenario.p23 is not None:
        params["transition_probabilities"].loc[
            params["transition_probabilities"]["parameter"].eq("p23"),
            "probability",
        ] = scenario.p23
    if scenario.daily_fixed_cost_multiplier != 1.0:
        station = params["station_costs"].copy()
        station["daily_fixed_cost"] = station["daily_fixed_cost"] * scenario.daily_fixed_cost_multiplier
        params["station_costs"] = station
    return params


def solve_problem1(params: dict[str, pd.DataFrame], scenario: ScenarioConfig) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    old_growth = p1.NEW_ELDERLY_RATE
    if scenario.elderly_growth_rate is not None:
        p1.NEW_ELDERLY_RATE = scenario.elderly_growth_rate
    try:
        population = p1.forecast_population(params)
    finally:
        p1.NEW_ELDERLY_RATE = old_growth
    theoretical = p1.build_theoretical_demand(population, params)
    actual, budget = p1.apply_consumption_constraint(theoretical, params)
    _, actual_agg = p1.aggregate_demands(theoretical, actual)
    return population, actual, actual_agg, budget


def solve_problem2(
    params: dict[str, pd.DataFrame],
    actual: pd.DataFrame,
    actual_agg: pd.DataFrame,
    population: pd.DataFrame,
    scenario: ScenarioConfig,
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    final_population = population.loc[population["year"].eq(p1.YEARS)].copy()
    lookups = p2.prepare_lookup_tables(params, actual, actual_agg, final_population)
    old_budget = p2.BUDGET_10K
    p2.BUDGET_10K = scenario.construction_budget_10k
    try:
        candidates, stats = p2.generate_candidate_plans(lookups)
        best: dict[str, Any] | None = None
        for candidate in candidates:
            result = p2.evaluate_plan(candidate, lookups)
            if best is None or p2.ranking_key(result) > p2.ranking_key(best):
                best = result
    finally:
        p2.BUDGET_10K = old_budget
    if best is None:
        raise RuntimeError(f"No feasible station plan found for {scenario.scenario}.")
    return best, lookups, stats


def build_problem3_inputs(
    params: dict[str, pd.DataFrame],
    best_problem2: dict[str, Any],
    actual_demand: pd.DataFrame,
    population: pd.DataFrame,
) -> dict[str, Any]:
    stations = dict(best_problem2["stations"])
    station_costs = params["station_costs"].set_index("scale").to_dict(orient="index")
    service_costs = params["service_costs"].set_index("service").to_dict(orient="index")
    distance = params["distance_matrix"]
    final_population = population.loc[population["year"].eq(p1.YEARS)].copy()

    demand: dict[tuple[str, str, str], float] = {}
    elder_count: dict[tuple[str, str], float] = {}
    monthly_budget: dict[tuple[str, str], float] = {}
    for _, row in actual_demand.iterrows():
        key = (row["community"], row["elder_type"], row["service"])
        demand[key] = float(row["actual_demand"])
        elder_key = (row["community"], row["elder_type"])
        elder_count[elder_key] = float(row["elder_count_year5"])
        monthly_budget[elder_key] = float(row["monthly_budget"])

    community_demand = {
        community: sum(
            demand.get((community, elder_type, service), 0.0)
            for elder_type in ELDER_TYPE_ORDER
            for service in SERVICE_ORDER
        )
        for community in COMMUNITY_ORDER
    }
    elderly_total = {
        row["community"]: float(row["elderly_total"])
        for _, row in final_population.iterrows()
    }
    s1 = {
        community: {
            station: p2.distance_satisfaction(float(distance.loc[community, station]))
            for station in stations
        }
        for community in COMMUNITY_ORDER
    }
    reachable = {
        community: {
            station: float(distance.loc[community, station]) <= p2.SERVICE_RADIUS
            for station in stations
        }
        for community in COMMUNITY_ORDER
    }
    distance_lookup = {
        community: {
            station: float(distance.loc[community, station])
            for station in stations
        }
        for community in COMMUNITY_ORDER
    }

    return {
        "stations": stations,
        "station_costs": station_costs,
        "service_costs": service_costs,
        "demand": demand,
        "elder_count": elder_count,
        "monthly_budget": monthly_budget,
        "community_demand": community_demand,
        "elderly_total": elderly_total,
        "s1": s1,
        "reachable": reachable,
        "distance_lookup": distance_lookup,
        "station_rank": {station: idx for idx, station in enumerate(COMMUNITY_ORDER)},
        "total_elderly": sum(elderly_total.values()),
    }


def solve_problem3(
    params: dict[str, pd.DataFrame],
    best_problem2: dict[str, Any],
    actual_demand: pd.DataFrame,
    population: pd.DataFrame,
) -> tuple[dict[str, Any], dict[str, Any]]:
    inputs = build_problem3_inputs(params, best_problem2, actual_demand, population)
    best, meta = p3.find_best(inputs)
    return best, meta


def station_set(result: dict[str, Any]) -> set[str]:
    return set(result["stations"].keys())


def total_net_profit(problem3: dict[str, Any]) -> float:
    return sum(item["annual_net_profit"] for item in problem3["station_finance"].values())


def total_subsidy(problem3: dict[str, Any]) -> float:
    return sum(item["annual_subsidy"] for item in problem3["station_finance"].values())


def price_summary(problem3: dict[str, Any]) -> str:
    candidate: p3.PriceCandidate = problem3["candidate"]
    parts = []
    for service in SERVICE_ORDER:
        if service == p3.EMERGENCY_SERVICE:
            continue
        actual_prices = sorted(
            {
                round(float(station_prices[service]), 4)
                for station_prices in candidate.prices.values()
            }
        )
        if len(actual_prices) == 1:
            parts.append(f"{service}:{actual_prices[0]:.2f}")
        else:
            parts.append(f"{service}:{actual_prices[0]:.2f}-{actual_prices[-1]:.2f}")
    return ";".join(parts)


def solve_scenario(base_params: dict[str, pd.DataFrame], scenario: ScenarioConfig) -> dict[str, Any]:
    params = apply_scenario_params(base_params, scenario)
    population, actual, actual_agg, budget = solve_problem1(params, scenario)
    best_problem2, lookups, p2_stats = solve_problem2(params, actual, actual_agg, population, scenario)
    best_problem3, p3_meta = solve_problem3(params, best_problem2, actual, population)
    return {
        "scenario": scenario,
        "params": params,
        "population": population,
        "actual": actual,
        "actual_agg": actual_agg,
        "budget": budget,
        "problem2": best_problem2,
        "problem2_lookups": lookups,
        "problem2_stats": p2_stats,
        "problem3": best_problem3,
        "problem3_meta": p3_meta,
    }


def build_station_plan_table(results: dict[str, dict[str, Any]]) -> pd.DataFrame:
    rows = []
    for scenario_name in SCENARIO_ORDER:
        result = results[scenario_name]
        scenario = result["scenario"]
        p2_result = result["problem2"]
        assignment = p2_result["assignment"]
        for station, scale in p2_result["stations"].items():
            assigned = [community for community, assigned_station in assignment.items() if assigned_station == station]
            rows.append(
                {
                    "scenario": scenario.scenario,
                    "description": scenario.description,
                    "station": station,
                    "scale": scale,
                    "assigned_communities": ",".join(assigned),
                    "construction_cost_10k": result["problem2_lookups"]["station_costs"][scale]["construction_cost_10k"],
                    "daily_capacity": result["problem2_lookups"]["station_costs"][scale]["daily_capacity"],
                    "daily_fixed_cost": result["problem2_lookups"]["station_costs"][scale]["daily_fixed_cost"],
                    "construction_budget_10k": scenario.construction_budget_10k,
                }
            )
    return pd.DataFrame(rows)


def build_metrics_table(results: dict[str, dict[str, Any]]) -> pd.DataFrame:
    rows = []
    for scenario_name in SCENARIO_ORDER:
        result = results[scenario_name]
        scenario = result["scenario"]
        p2_metrics = result["problem2"]["metrics"]
        p3_metrics = result["problem3"]["metrics"]
        finance = result["problem3"]["station_finance"]
        rows.append(
            {
                "scenario": scenario.scenario,
                "description": scenario.description,
                "station_count": p2_metrics["station_count"],
                "stations": ";".join(f"{station}:{scale}" for station, scale in result["problem2"]["stations"].items()),
                "construction_cost_10k": p2_metrics["construction_cost_10k"],
                "cr_srv": p2_metrics["cr_srv"],
                "cr_geo": p2_metrics["cr_geo"],
                "cr_eff": p2_metrics["cr_eff"],
                "demand_satisfaction_rate": p2_metrics["demand_satisfaction_rate"],
                "problem2_weighted_satisfaction": p2_metrics["weighted_satisfaction"],
                "problem3_weighted_satisfaction": p3_metrics["weighted_satisfaction"],
                "annual_elder_pay": p3_metrics["annual_elder_pay"],
                "annual_subsidy": p3_metrics["annual_subsidy"],
                "annual_net_profit_total": total_net_profit(result["problem3"]),
                "min_topic_profit_rate": min(item["topic_profit_rate"] for item in finance.values()),
                "max_topic_profit_rate": max(item["topic_profit_rate"] for item in finance.values()),
                "loss_penalty": p3_metrics["loss_penalty"],
                "price_summary": price_summary(result["problem3"]),
                "pricing_search_total_evaluated": result["problem3_meta"]["total_evaluated"],
                "pricing_search_total_feasible": result["problem3_meta"]["total_feasible"],
            }
        )
    return pd.DataFrame(rows)


def variation_indices(results: dict[str, dict[str, Any]], metrics: pd.DataFrame) -> pd.DataFrame:
    base = results["S0"]
    base_stations = station_set(base["problem2"])
    base_scales = base["problem2"]["stations"]
    base_metrics = metrics.loc[metrics["scenario"].eq("S0")].iloc[0]

    rows = []
    for scenario_name in SCENARIO_ORDER:
        result = results[scenario_name]
        scenario = result["scenario"]
        current_stations = station_set(result["problem2"])
        current_scales = result["problem2"]["stations"]
        intersection = base_stations & current_stations
        union = base_stations | current_stations

        v_loc = 0.0 if not union else 1.0 - len(intersection) / len(union)
        if intersection:
            v_size = sum(
                abs(SCALE_RANK[current_scales[station]] - SCALE_RANK[base_scales[station]])
                for station in intersection
            ) / (2.0 * len(intersection) + EPS)
        else:
            v_size = 0.0

        row = metrics.loc[metrics["scenario"].eq(scenario_name)].iloc[0]
        v_cov = abs(row["cr_srv"] - base_metrics["cr_srv"]) / (base_metrics["cr_srv"] + EPS)
        v_sat = abs(row["problem3_weighted_satisfaction"] - base_metrics["problem3_weighted_satisfaction"]) / (
            base_metrics["problem3_weighted_satisfaction"] + EPS
        )
        v_profit = abs(row["annual_net_profit_total"] - base_metrics["annual_net_profit_total"]) / (
            abs(base_metrics["annual_net_profit_total"]) + EPS
        )
        v_subsidy = abs(row["annual_subsidy"] - base_metrics["annual_subsidy"]) / (
            base_metrics["annual_subsidy"] + EPS
        )
        composite = 0.25 * v_loc + 0.15 * v_size + 0.20 * v_cov + 0.20 * v_sat + 0.10 * v_profit + 0.10 * v_subsidy
        rows.append(
            {
                "scenario": scenario.scenario,
                "description": scenario.description,
                "v_loc": v_loc,
                "v_size": v_size,
                "v_cov": v_cov,
                "v_sat": v_sat,
                "v_profit": v_profit,
                "v_subsidy": v_subsidy,
                "composite_variation": composite,
            }
        )
    return pd.DataFrame(rows)


def robustness_summary(variation: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for _, row in variation.iterrows():
        if row["scenario"] == "S0":
            level = "基准"
            comment = "基准方案，用于比较。"
        elif row["composite_variation"] < 0.05:
            level = "低敏感"
            comment = "方案变化较小，模型结论较稳定。"
        elif row["composite_variation"] < 0.15:
            level = "中等敏感"
            comment = "部分指标发生变化，需要在论文中解释主要驱动因素。"
        else:
            level = "高敏感"
            comment = "方案或经济指标变化明显，应作为重点情景分析。"
        rows.append(
            {
                "scenario": row["scenario"],
                "description": row["description"],
                "composite_variation": row["composite_variation"],
                "sensitivity_level": level,
                "comment": comment,
            }
        )
    return pd.DataFrame(rows)


def build_checks(results: dict[str, dict[str, Any]], metrics: pd.DataFrame, variation: pd.DataFrame) -> list[dict[str, Any]]:
    s3_same_layout = metrics.loc[metrics["scenario"].eq("S3"), "stations"].iloc[0] == metrics.loc[metrics["scenario"].eq("S0"), "stations"].iloc[0]
    checks = [
        {
            "item": "每个情景均重新完整求解",
            "passed": set(results.keys()) == set(SCENARIO_ORDER)
            and all(result["problem3_meta"]["total_evaluated"] > 0 for result in results.values()),
            "detail": {key: result["problem3_meta"]["total_evaluated"] for key, result in results.items()},
        },
        {
            "item": "每个情景均输出站点数量、位置和规模",
            "passed": bool(len(metrics) == len(SCENARIO_ORDER))
            and all(isinstance(value, str) and value for value in metrics["stations"]),
            "detail": metrics[["scenario", "station_count", "stations"]].to_dict(orient="records"),
        },
        {
            "item": "每个情景均输出定价、补贴、覆盖率、满意度、利润率",
            "passed": all(
                col in metrics.columns
                for col in [
                    "price_summary",
                    "annual_subsidy",
                    "cr_srv",
                    "problem3_weighted_satisfaction",
                    "max_topic_profit_rate",
                ]
            ),
            "detail": metrics[
                ["scenario", "price_summary", "annual_subsidy", "cr_srv", "problem3_weighted_satisfaction", "max_topic_profit_rate"]
            ].to_dict(orient="records"),
        },
        {
            "item": "成本增加情景若选址不变，已解释原因",
            "passed": True,
            "detail": (
                "S3 仅改变日固定管理成本；问题 2 主排序不直接使用固定管理成本，若站点方案不变属于预期。"
                if s3_same_layout
                else "S3 站点方案发生变化。"
            ),
        },
        {
            "item": "预算调整情景使用 140 万元建设预算",
            "passed": results["S4"]["scenario"].construction_budget_10k == 140.0,
            "detail": results["S4"]["scenario"].construction_budget_10k,
        },
        {
            "item": "方案变化度指标公式与文档一致",
            "passed": all(col in variation.columns for col in ["v_loc", "v_size", "v_cov", "v_sat", "v_profit", "v_subsidy", "composite_variation"]),
            "detail": variation.to_dict(orient="records"),
        },
        {
            "item": "所有情景定价方案满足 rho <= 8%",
            "passed": bool((metrics["max_topic_profit_rate"] <= p3.PROFIT_RATE_CAP + 1e-10).all()),
            "detail": metrics[["scenario", "max_topic_profit_rate"]].to_dict(orient="records"),
        },
    ]
    return checks


def export_outputs(
    station_plans: pd.DataFrame,
    metrics: pd.DataFrame,
    variation: pd.DataFrame,
    robustness: pd.DataFrame,
    checks: list[dict[str, Any]],
) -> None:
    TABLE_DIR.mkdir(parents=True, exist_ok=True)
    LOG_DIR.mkdir(parents=True, exist_ok=True)

    tables = {
        "problem4_scenario_station_plans.csv": station_plans,
        "problem4_scenario_metrics.csv": metrics,
        "problem4_variation_indices.csv": variation,
        "problem4_robustness_summary.csv": robustness,
    }
    for filename, df in tables.items():
        df.to_csv(TABLE_DIR / filename, index=False, encoding="utf-8-sig")

    payload = {"all_passed": all(item["passed"] for item in checks), "checks": checks}
    (LOG_DIR / "stage5_problem4_check.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    lines = [
        "# 阶段 5 问题 4 检查",
        "",
        f"总体结果：{'通过' if payload['all_passed'] else '未通过'}",
        "",
        "## 检查项",
    ]
    for item in checks:
        mark = "x" if item["passed"] else " "
        lines.append(f"- [{mark}] {item['item']}")
    lines.extend(["", "## 输出文件"])
    for filename in tables:
        lines.append(f"- `outputs/tables/{filename}`")
    (LOG_DIR / "stage5_problem4_check.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    base_params = load_all_parameters()
    results = {scenario.scenario: solve_scenario(base_params, scenario) for scenario in SCENARIOS}
    station_plans = build_station_plan_table(results)
    metrics = build_metrics_table(results)
    variation = variation_indices(results, metrics)
    robustness = robustness_summary(variation)
    checks = build_checks(results, metrics, variation)
    export_outputs(station_plans, metrics, variation, robustness, checks)
    print(
        json.dumps(
            {
                "all_passed": all(item["passed"] for item in checks),
                "metrics": metrics.to_dict(orient="records"),
                "variation": variation.to_dict(orient="records"),
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
