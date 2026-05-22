from __future__ import annotations

import json
from typing import Any

import pandas as pd

from data_loader import COMMUNITY_ORDER, LOG_DIR, SERVICE_ORDER, TABLE_DIR, load_all_parameters


BUDGET_10K = 120.0
SERVICE_RADIUS = 1000.0
SERVICE_COVERAGE_THRESHOLD = 1.0
MAX_ITERATIONS = 30
CONVERGENCE_TOL = 1e-6
PRICE_SATISFACTION_STAGE2 = 1.0

NO_STATION = "不建"
SCALE_ORDER = [NO_STATION, "小型", "中型", "大型"]


def distance_satisfaction(distance: float) -> float:
    if distance <= 300:
        return 1.00
    if distance <= 500:
        return 0.90
    if distance <= 650:
        return 0.75
    if distance <= 1000:
        return 0.60
    return 0.0


def response_satisfaction(utilization: float) -> float:
    if utilization <= 0.60:
        return 1.00
    if utilization <= 0.75:
        return 0.93
    if utilization <= 0.85:
        return 0.85
    if utilization <= 0.95:
        return 0.72
    return 0.60


def load_stage2_demands() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    actual = pd.read_csv(TABLE_DIR / "problem1_actual_demand.csv")
    demand_by_service = pd.read_csv(TABLE_DIR / "problem1_actual_demand_by_community_service.csv")
    population = pd.read_csv(TABLE_DIR / "problem1_population_forecast.csv")
    population = population.loc[population["year"].eq(5)].copy()
    return actual, demand_by_service, population


def prepare_lookup_tables(
    params: dict[str, pd.DataFrame],
    actual: pd.DataFrame,
    demand_by_service: pd.DataFrame,
    population: pd.DataFrame,
) -> dict[str, Any]:
    station_costs = params["station_costs"].set_index("scale").to_dict(orient="index")
    service_costs = params["service_costs"].set_index("service").to_dict(orient="index")
    distance = params["distance_matrix"]
    distance_lookup = {
        i: {j: float(distance.loc[i, j]) for j in COMMUNITY_ORDER}
        for i in COMMUNITY_ORDER
    }

    elderly_total = {
        row["community"]: float(row["elderly_total"])
        for _, row in population.iterrows()
    }
    demand = {
        community: {service: 0.0 for service in SERVICE_ORDER}
        for community in COMMUNITY_ORDER
    }
    for _, row in demand_by_service.iterrows():
        demand[row["community"]][row["service"]] = float(row["actual_demand"])

    typed_demand = {}
    for _, row in actual.iterrows():
        typed_demand[(row["community"], row["elder_type"], row["service"])] = float(row["actual_demand"])

    total_elderly = sum(elderly_total.values())
    total_demand = sum(sum(values.values()) for values in demand.values())

    s1 = {
        i: {
            j: distance_satisfaction(float(distance.loc[i, j]))
            for j in COMMUNITY_ORDER
        }
        for i in COMMUNITY_ORDER
    }
    reachable = {
        i: {
            j: distance_lookup[i][j] <= SERVICE_RADIUS
            for j in COMMUNITY_ORDER
        }
        for i in COMMUNITY_ORDER
    }

    return {
        "station_costs": station_costs,
        "service_costs": service_costs,
        "distance": distance,
        "distance_lookup": distance_lookup,
        "station_rank": {community: idx for idx, community in enumerate(COMMUNITY_ORDER)},
        "elderly_total": elderly_total,
        "demand": demand,
        "typed_demand": typed_demand,
        "total_elderly": total_elderly,
        "total_demand": total_demand,
        "s1": s1,
        "reachable": reachable,
    }


def generate_candidate_plans(lookups: dict[str, Any]) -> tuple[list[dict[str, Any]], dict[str, int]]:
    station_costs = lookups["station_costs"]
    candidates: list[dict[str, Any]] = []
    empty = 1

    def walk(index: int, stations: dict[str, str], construction_cost: float) -> None:
        if construction_cost > BUDGET_10K:
            return
        if index == len(COMMUNITY_ORDER):
            if stations:
                candidates.append(
                    {
                        "stations": stations.copy(),
                        "construction_cost_10k": float(construction_cost),
                    }
                )
            return

        community = COMMUNITY_ORDER[index]
        walk(index + 1, stations, construction_cost)
        for scale in SCALE_ORDER[1:]:
            stations[community] = scale
            walk(index + 1, stations, construction_cost + float(station_costs[scale]["construction_cost_10k"]))
            del stations[community]

    walk(0, {}, 0.0)

    total = len(SCALE_ORDER) ** len(COMMUNITY_ORDER)
    over_budget = total - empty - len(candidates)

    stats = {
        "total_enumerated": total,
        "empty_plans": empty,
        "over_budget_pruned": over_budget,
        "budget_feasible": len(candidates),
    }
    return candidates, stats


def assign_communities(stations: dict[str, str], s2: dict[str, float], lookups: dict[str, Any]) -> tuple[dict[str, str | None], dict[str, float]]:
    assignment: dict[str, str | None] = {}
    satisfaction: dict[str, float] = {}

    for community in COMMUNITY_ORDER:
        best_station: str | None = None
        best_key: tuple[float, float, int] | None = None
        best_satisfaction = 0.0
        for station in stations:
            if not lookups["reachable"][community][station]:
                continue
            score = (
                0.2 * lookups["s1"][community][station]
                + 0.3 * s2[station]
                + 0.5 * PRICE_SATISFACTION_STAGE2
            )
            distance = lookups["distance_lookup"][community][station]
            key = (score, -distance, -lookups["station_rank"][station])
            if best_key is None or key > best_key:
                best_key = key
                best_station = station
                best_satisfaction = score

        assignment[community] = best_station
        satisfaction[community] = best_satisfaction if best_station is not None else 0.0

    return assignment, satisfaction


def evaluate_plan(plan: dict[str, Any], lookups: dict[str, Any]) -> dict[str, Any]:
    stations = plan["stations"]
    station_costs = lookups["station_costs"]
    demand = lookups["demand"]
    elderly_total = lookups["elderly_total"]
    service_costs = lookups["service_costs"]

    s2 = {station: 1.0 for station in stations}
    previous_assignment: dict[str, str | None] | None = None
    converged = False
    assignment: dict[str, str | None] = {}
    satisfaction: dict[str, float] = {}
    gamma = {station: 1.0 for station in stations}
    utilization = {station: 0.0 for station in stations}
    effective_by_community_service: dict[tuple[str, str], float] = {}
    pre_effective_by_community_service: dict[tuple[str, str], float] = {}

    for iteration in range(1, MAX_ITERATIONS + 1):
        assignment, satisfaction = assign_communities(stations, s2, lookups)

        station_pre_demand = {station: 0.0 for station in stations}
        pre_effective_by_community_service = {}
        for community in COMMUNITY_ORDER:
            station = assignment[community]
            for service in SERVICE_ORDER:
                value = 0.0
                if station is not None:
                    value = demand[community][service] * satisfaction[community]
                    station_pre_demand[station] += value
                pre_effective_by_community_service[(community, service)] = value

        gamma = {}
        utilization = {}
        effective_by_community_service = {}
        station_effective_demand = {station: 0.0 for station in stations}

        for station, scale in stations.items():
            annual_capacity = 365.0 * float(station_costs[scale]["daily_capacity"])
            annual_pre_demand = 12.0 * station_pre_demand[station]
            gamma[station] = min(1.0, annual_capacity / (annual_pre_demand + 1e-8))

        for community in COMMUNITY_ORDER:
            station = assignment[community]
            for service in SERVICE_ORDER:
                value = 0.0
                if station is not None:
                    value = gamma[station] * pre_effective_by_community_service[(community, service)]
                    station_effective_demand[station] += value
                effective_by_community_service[(community, service)] = value

        new_s2 = {}
        for station, scale in stations.items():
            annual_capacity = 365.0 * float(station_costs[scale]["daily_capacity"])
            utilization[station] = 12.0 * station_effective_demand[station] / (annual_capacity + 1e-8)
            new_s2[station] = response_satisfaction(utilization[station])

        max_s2_change = max(abs(new_s2[station] - s2[station]) for station in stations) if stations else 0.0
        if previous_assignment == assignment and max_s2_change < CONVERGENCE_TOL:
            converged = True
            s2 = new_s2
            break

        previous_assignment = assignment.copy()
        s2 = new_s2

    community_effective = {
        community: sum(effective_by_community_service[(community, service)] for service in SERVICE_ORDER)
        for community in COMMUNITY_ORDER
    }
    community_demand = {
        community: sum(demand[community].values())
        for community in COMMUNITY_ORDER
    }

    service_covered_elderly = sum(
        elderly_total[community]
        for community in COMMUNITY_ORDER
        if community_effective[community] > SERVICE_COVERAGE_THRESHOLD
    )
    geo_covered_elderly = sum(
        elderly_total[community]
        for community in COMMUNITY_ORDER
        if any(lookups["reachable"][community][station] for station in stations)
    )
    cr_eff_numerator = sum(
        elderly_total[community]
        * min(1.0, community_effective[community] / (community_demand[community] + 1e-8))
        for community in COMMUNITY_ORDER
    )

    total_effective = sum(community_effective.values())
    weighted_satisfaction = sum(
        elderly_total[community] * satisfaction[community]
        for community in COMMUNITY_ORDER
    ) / (lookups["total_elderly"] + 1e-8)

    station_finance = {}
    effective_by_community_elder_service = {}
    station_service_effective = {
        station: {service: 0.0 for service in SERVICE_ORDER}
        for station in stations
    }
    for community in COMMUNITY_ORDER:
        station = assignment[community]
        for (row_community, elder_type, service), demand_value in lookups["typed_demand"].items():
            if row_community != community:
                continue
            typed_effective = 0.0
            if station is not None:
                typed_effective = gamma[station] * demand_value * satisfaction[community]
            effective_by_community_elder_service[(community, elder_type, service)] = typed_effective
        if station is None:
            continue
        for service in SERVICE_ORDER:
            station_service_effective[station][service] += effective_by_community_service[(community, service)]

    for station, scale in stations.items():
        annual_revenue = 0.0
        annual_direct_cost = 0.0
        for service in SERVICE_ORDER:
            annual_times = 12.0 * station_service_effective[station][service]
            annual_revenue += annual_times * float(service_costs[service]["base_price"])
            annual_direct_cost += annual_times * float(service_costs[service]["direct_cost"])
        annual_operating_cost = 365.0 * float(station_costs[scale]["daily_fixed_cost"])
        annualized_construction_cost = float(station_costs[scale]["annualized_construction_cost"])
        station_finance[station] = {
            "annual_revenue_base": annual_revenue,
            "annual_direct_cost": annual_direct_cost,
            "annual_operating_cost": annual_operating_cost,
            "annualized_construction_cost": annualized_construction_cost,
            "annual_net_profit_base_no_subsidy": (
                annual_revenue
                - annual_direct_cost
                - annual_operating_cost
                - annualized_construction_cost
            ),
            "topic_profit_rate_base_no_subsidy": (
                (annual_revenue - annual_direct_cost - annual_operating_cost)
                / (annual_operating_cost + 1e-8)
            ),
        }

    return {
        "stations": stations,
        "construction_cost_10k": plan["construction_cost_10k"],
        "assignment": assignment,
        "satisfaction": satisfaction,
        "s2": s2,
        "gamma": gamma,
        "utilization": utilization,
        "effective_by_community_service": effective_by_community_service,
        "effective_by_community_elder_service": effective_by_community_elder_service,
        "community_effective": community_effective,
        "community_demand": community_demand,
        "station_service_effective": station_service_effective,
        "station_finance": station_finance,
        "metrics": {
            "station_count": len(stations),
            "cr_srv": service_covered_elderly / (lookups["total_elderly"] + 1e-8),
            "cr_geo": geo_covered_elderly / (lookups["total_elderly"] + 1e-8),
            "cr_eff": cr_eff_numerator / (lookups["total_elderly"] + 1e-8),
            "demand_satisfaction_rate": total_effective / (lookups["total_demand"] + 1e-8),
            "weighted_satisfaction": weighted_satisfaction,
            "construction_cost_10k": plan["construction_cost_10k"],
            "converged": converged,
            "iterations": iteration,
        },
    }


def ranking_key(result: dict[str, Any]) -> tuple[float, float, float, float, float]:
    metrics = result["metrics"]
    return (
        metrics["cr_srv"],
        metrics["cr_eff"],
        metrics["weighted_satisfaction"],
        metrics["demand_satisfaction_rate"],
        -metrics["construction_cost_10k"],
    )


def build_output_tables(best: dict[str, Any], top_results: list[dict[str, Any]], stats: dict[str, int], lookups: dict[str, Any]) -> dict[str, pd.DataFrame]:
    best_plan_rows = []
    for station, scale in best["stations"].items():
        finance = best["station_finance"][station]
        best_plan_rows.append(
            {
                "station": station,
                "scale": scale,
                "construction_cost_10k": lookups["station_costs"][scale]["construction_cost_10k"],
                "daily_capacity": lookups["station_costs"][scale]["daily_capacity"],
                **finance,
            }
        )

    assignment_rows = []
    for community in COMMUNITY_ORDER:
        station = best["assignment"][community]
        distance = None if station is None else lookups["distance_lookup"][community][station]
        assignment_rows.append(
            {
                "community": community,
                "assigned_station": station or "",
                "assigned_scale": "" if station is None else best["stations"][station],
                "distance": distance,
                "s1": 0.0 if station is None else lookups["s1"][community][station],
                "s2": 0.0 if station is None else best["s2"][station],
                "s3": PRICE_SATISFACTION_STAGE2 if station is not None else 0.0,
                "satisfaction": best["satisfaction"][community],
                "monthly_demand": best["community_demand"][community],
                "monthly_effective_service": best["community_effective"][community],
                "effective_ratio": best["community_effective"][community] / (best["community_demand"][community] + 1e-8),
                "service_covered": best["community_effective"][community] > SERVICE_COVERAGE_THRESHOLD,
            }
        )

    utilization_rows = []
    for station, scale in best["stations"].items():
        monthly_effective = sum(best["station_service_effective"][station].values())
        utilization_rows.append(
            {
                "station": station,
                "scale": scale,
                "assigned_communities": ",".join(
                    community for community, assigned in best["assignment"].items() if assigned == station
                ),
                "monthly_effective_service": monthly_effective,
                "annual_effective_service": 12.0 * monthly_effective,
                "annual_capacity": 365.0 * lookups["station_costs"][scale]["daily_capacity"],
                "utilization": best["utilization"][station],
                "capacity_gamma": best["gamma"][station],
                "response_satisfaction_s2": best["s2"][station],
            }
        )

    coverage = pd.DataFrame(
        [
            {
                **best["metrics"],
                **stats,
            }
        ]
    )

    top_rows = []
    for rank, result in enumerate(top_results, start=1):
        top_rows.append(
            {
                "rank": rank,
                "stations": ";".join(f"{station}:{scale}" for station, scale in result["stations"].items()),
                **result["metrics"],
            }
        )

    effective_rows = []
    for community in COMMUNITY_ORDER:
        for service in SERVICE_ORDER:
            effective_rows.append(
                {
                    "community": community,
                    "service": service,
                    "actual_demand": lookups["demand"][community][service],
                    "effective_service": best["effective_by_community_service"][(community, service)],
                }
            )

    typed_effective_rows = []
    for (community, elder_type, service), effective_value in best["effective_by_community_elder_service"].items():
        typed_effective_rows.append(
            {
                "community": community,
                "elder_type": elder_type,
                "service": service,
                "actual_demand": lookups["typed_demand"][(community, elder_type, service)],
                "effective_service": effective_value,
            }
        )

    return {
        "problem2_best_station_plan.csv": pd.DataFrame(best_plan_rows),
        "problem2_assignment.csv": pd.DataFrame(assignment_rows),
        "problem2_station_utilization.csv": pd.DataFrame(utilization_rows),
        "problem2_coverage_summary.csv": coverage,
        "problem2_top_candidates.csv": pd.DataFrame(top_rows),
        "problem2_effective_service_by_community_service.csv": pd.DataFrame(effective_rows),
        "problem2_effective_service_by_community_elder_service.csv": pd.DataFrame(typed_effective_rows),
    }


def build_checks(best: dict[str, Any], stats: dict[str, int], lookups: dict[str, Any]) -> list[dict[str, Any]]:
    assignments_with_station = [station for station in best["assignment"].values() if station is not None]
    assigned_distances = {
        community: None if station is None else lookups["distance_lookup"][community][station]
        for community, station in best["assignment"].items()
    }
    checks = [
        {
            "item": "枚举方案总数为 4^10，并记录剪枝数量",
            "passed": stats["total_enumerated"] == 4 ** 10 and stats["over_budget_pruned"] >= 0,
            "detail": stats,
        },
        {
            "item": "最优方案建设成本不超过 120 万元",
            "passed": best["construction_cost_10k"] <= BUDGET_10K + 1e-8,
            "detail": best["construction_cost_10k"],
        },
        {
            "item": "所有被分配小区均有服务站",
            "passed": len(assignments_with_station) == len(COMMUNITY_ORDER),
            "detail": best["assignment"],
        },
        {
            "item": "每个被分配小区与服务站距离不超过 1000 米",
            "passed": all(distance is not None and distance <= SERVICE_RADIUS for distance in assigned_distances.values()),
            "detail": assigned_distances,
        },
        {
            "item": "容量可得系数在 [0, 1] 内",
            "passed": all(0 <= value <= 1 for value in best["gamma"].values()),
            "detail": best["gamma"],
        },
        {
            "item": "服务站利用率非负且不超过 1",
            "passed": all(0 <= value <= 1 + 1e-8 for value in best["utilization"].values()),
            "detail": best["utilization"],
        },
        {
            "item": "主覆盖率使用 CR_srv 且在 [0, 1] 内",
            "passed": 0 <= best["metrics"]["cr_srv"] <= 1,
            "detail": best["metrics"]["cr_srv"],
        },
        {
            "item": "保留了 E_{i,r,k} 以支持三类老人可及性",
            "passed": bool(best["effective_by_community_elder_service"]),
            "detail": len(best["effective_by_community_elder_service"]),
        },
        {
            "item": "迭代收敛或记录最大迭代近似解",
            "passed": True,
            "detail": {"converged": best["metrics"]["converged"], "iterations": best["metrics"]["iterations"]},
        },
        {
            "item": "预计年度利润使用基准价格测算",
            "passed": all("annual_net_profit_base_no_subsidy" in finance for finance in best["station_finance"].values()),
            "detail": best["station_finance"],
        },
    ]
    return checks


def export_outputs(tables: dict[str, pd.DataFrame], checks: list[dict[str, Any]], stats: dict[str, int]) -> None:
    TABLE_DIR.mkdir(parents=True, exist_ok=True)
    LOG_DIR.mkdir(parents=True, exist_ok=True)

    for filename, df in tables.items():
        df.to_csv(TABLE_DIR / filename, index=False, encoding="utf-8-sig")

    payload = {"all_passed": all(item["passed"] for item in checks), "enumeration_stats": stats, "checks": checks}
    (LOG_DIR / "stage3_problem2_check.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    lines = [
        "# 阶段 3 问题 2 检查",
        "",
        f"总体结果：{'通过' if payload['all_passed'] else '未通过'}",
        "",
        "## 枚举统计",
    ]
    for key, value in stats.items():
        lines.append(f"- {key}: {value}")
    lines.extend(["", "## 检查项"])
    for item in checks:
        mark = "x" if item["passed"] else " "
        lines.append(f"- [{mark}] {item['item']}")
    lines.extend(["", "## 输出文件"])
    for filename in tables:
        lines.append(f"- `outputs/tables/{filename}`")
    (LOG_DIR / "stage3_problem2_check.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    params = load_all_parameters()
    actual, demand_by_service, population = load_stage2_demands()
    lookups = prepare_lookup_tables(params, actual, demand_by_service, population)
    candidates, stats = generate_candidate_plans(lookups)

    best: dict[str, Any] | None = None
    top_results: list[dict[str, Any]] = []

    for candidate in candidates:
        result = evaluate_plan(candidate, lookups)
        if best is None or ranking_key(result) > ranking_key(best):
            best = result
        top_results.append(result)
        top_results.sort(key=ranking_key, reverse=True)
        if len(top_results) > 5:
            top_results = top_results[:5]

    if best is None:
        raise RuntimeError("No feasible station plan found.")

    tables = build_output_tables(best, top_results, stats, lookups)
    checks = build_checks(best, stats, lookups)
    export_outputs(tables, checks, stats)
    print(json.dumps({"all_passed": all(item["passed"] for item in checks), "best_metrics": best["metrics"], "enumeration_stats": stats}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
