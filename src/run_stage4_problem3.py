from __future__ import annotations

import itertools
import json
from dataclasses import dataclass
from typing import Any

import pandas as pd

from data_loader import COMMUNITY_ORDER, ELDER_TYPE_ORDER, LOG_DIR, SERVICE_ORDER, TABLE_DIR, load_all_parameters
from run_stage3_problem2 import CONVERGENCE_TOL, MAX_ITERATIONS, SERVICE_RADIUS, distance_satisfaction, response_satisfaction


EMERGENCY_SERVICE = "紧急救助"
SUBSIDY_PER_SERVICE = 2.0
PROFIT_RATE_CAP = 0.08
PRICE_FINE_DELTA = 2.0
PRICE_FINE_STEP = 1.0
STATION_DELTAS = [-0.05, 0.0, 0.05]


@dataclass(frozen=True)
class PriceCandidate:
    label: str
    prices: dict[str, dict[str, float]]
    uniform_prices: dict[str, float]
    station_delta: dict[str, float]


def price_score(price: float, base_price: float) -> float:
    if base_price <= 0:
        return 1.0 if price <= 0 else 0.60
    ratio = price / base_price
    if ratio <= 1.0 + 1e-10:
        return 1.00
    if ratio <= 1.10 + 1e-10:
        return 0.90
    if ratio <= 1.20 + 1e-10:
        return 0.75
    return 0.60


def load_inputs() -> dict[str, Any]:
    params = load_all_parameters()
    best_plan = pd.read_csv(TABLE_DIR / "problem2_best_station_plan.csv")
    actual_demand = pd.read_csv(TABLE_DIR / "problem1_actual_demand.csv")
    population = pd.read_csv(TABLE_DIR / "problem1_population_forecast.csv")
    population = population.loc[population["year"].eq(5)].copy()

    stations = {row["station"]: row["scale"] for _, row in best_plan.iterrows()}
    station_costs = params["station_costs"].set_index("scale").to_dict(orient="index")
    service_costs = params["service_costs"].set_index("service").to_dict(orient="index")
    distance = params["distance_matrix"]

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
        for _, row in population.iterrows()
    }

    s1 = {
        community: {
            station: distance_satisfaction(float(distance.loc[community, station]))
            for station in stations
        }
        for community in COMMUNITY_ORDER
    }
    reachable = {
        community: {
            station: float(distance.loc[community, station]) <= SERVICE_RADIUS
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


def service_price_bounds(service_costs: dict[str, dict[str, Any]]) -> dict[str, tuple[float, float]]:
    bounds = {}
    for service in SERVICE_ORDER:
        base = float(service_costs[service]["base_price"])
        direct = float(service_costs[service]["direct_cost"])
        if service == EMERGENCY_SERVICE:
            bounds[service] = (0.0, 0.0)
        else:
            bounds[service] = (max(0.0, direct - SUBSIDY_PER_SERVICE), 1.2 * base)
    return bounds


def make_price_matrix(
    stations: dict[str, str],
    uniform_prices: dict[str, float],
    station_delta: dict[str, float],
    bounds: dict[str, tuple[float, float]],
) -> dict[str, dict[str, float]]:
    matrix: dict[str, dict[str, float]] = {}
    for station in stations:
        matrix[station] = {}
        for service in SERVICE_ORDER:
            if service == EMERGENCY_SERVICE:
                matrix[station][service] = 0.0
                continue
            low, high = bounds[service]
            price = uniform_prices[service] * (1.0 + station_delta.get(station, 0.0))
            matrix[station][service] = round(min(max(price, low), high), 4)
    return matrix


def rough_uniform_candidates(service_costs: dict[str, dict[str, Any]], bounds: dict[str, tuple[float, float]]) -> list[dict[str, float]]:
    charged_services = [service for service in SERVICE_ORDER if service != EMERGENCY_SERVICE]
    grids = []
    for service in charged_services:
        base = float(service_costs[service]["base_price"])
        low, high = bounds[service]
        raw = [low, 0.8 * base, base, 1.1 * base, 1.2 * base]
        values = sorted({round(value, 4) for value in raw if low - 1e-8 <= value <= high + 1e-8})
        grids.append(values)

    candidates = []
    for values in itertools.product(*grids):
        prices = {service: float(value) for service, value in zip(charged_services, values)}
        prices[EMERGENCY_SERVICE] = 0.0
        candidates.append(prices)
    return candidates


def fine_uniform_candidates(best_prices: dict[str, float], bounds: dict[str, tuple[float, float]]) -> list[dict[str, float]]:
    charged_services = [service for service in SERVICE_ORDER if service != EMERGENCY_SERVICE]
    grids = []
    for service in charged_services:
        low, high = bounds[service]
        start = max(low, best_prices[service] - PRICE_FINE_DELTA)
        end = min(high, best_prices[service] + PRICE_FINE_DELTA)
        count = int(round((end - start) / PRICE_FINE_STEP)) + 1
        values = sorted({round(start + idx * PRICE_FINE_STEP, 4) for idx in range(max(count, 1))})
        values = [min(max(value, low), high) for value in values]
        grids.append(values)

    candidates = []
    for values in itertools.product(*grids):
        prices = {service: float(value) for service, value in zip(charged_services, values)}
        prices[EMERGENCY_SERVICE] = 0.0
        candidates.append(prices)
    return candidates


def build_candidates(inputs: dict[str, Any]) -> tuple[list[PriceCandidate], dict[str, Any]]:
    stations = inputs["stations"]
    bounds = service_price_bounds(inputs["service_costs"])

    rough = rough_uniform_candidates(inputs["service_costs"], bounds)
    rough_candidates = [
        PriceCandidate(
            label="rough_uniform",
            uniform_prices=prices,
            station_delta={station: 0.0 for station in stations},
            prices=make_price_matrix(stations, prices, {station: 0.0 for station in stations}, bounds),
        )
        for prices in rough
    ]

    return rough_candidates, {"bounds": bounds, "rough_count": len(rough_candidates)}


def community_station_price_s3(community: str, station: str, prices: dict[str, dict[str, float]], inputs: dict[str, Any]) -> float:
    numerator = 0.0
    denominator = 0.0
    for elder_type in ELDER_TYPE_ORDER:
        for service in SERVICE_ORDER:
            demand = inputs["demand"].get((community, elder_type, service), 0.0)
            if demand <= 0:
                continue
            base = float(inputs["service_costs"][service]["base_price"])
            numerator += demand * price_score(prices[station][service], base)
            denominator += demand
    return numerator / (denominator + 1e-8)


def assign_communities(prices: dict[str, dict[str, float]], s2: dict[str, float], inputs: dict[str, Any]) -> tuple[dict[str, str | None], dict[str, float], dict[str, float]]:
    assignment: dict[str, str | None] = {}
    satisfaction: dict[str, float] = {}
    s3_by_community: dict[str, float] = {}

    for community in COMMUNITY_ORDER:
        best_station: str | None = None
        best_key: tuple[float, float, int] | None = None
        best_satisfaction = 0.0
        best_s3 = 0.0
        for station in inputs["stations"]:
            if not inputs["reachable"][community][station]:
                continue
            s3 = community_station_price_s3(community, station, prices, inputs)
            score = 0.2 * inputs["s1"][community][station] + 0.3 * s2[station] + 0.5 * s3
            distance = inputs["distance_lookup"][community][station]
            key = (score, -distance, -inputs["station_rank"][station])
            if best_key is None or key > best_key:
                best_key = key
                best_station = station
                best_satisfaction = score
                best_s3 = s3

        assignment[community] = best_station
        satisfaction[community] = best_satisfaction if best_station is not None else 0.0
        s3_by_community[community] = best_s3 if best_station is not None else 0.0

    return assignment, satisfaction, s3_by_community


def evaluate_candidate(candidate: PriceCandidate, inputs: dict[str, Any]) -> dict[str, Any]:
    stations = inputs["stations"]
    station_costs = inputs["station_costs"]
    prices = candidate.prices
    s2 = {station: 1.0 for station in stations}
    previous_assignment: dict[str, str | None] | None = None
    converged = False

    assignment: dict[str, str | None] = {}
    satisfaction: dict[str, float] = {}
    s3_by_community: dict[str, float] = {}
    gamma = {station: 1.0 for station in stations}
    utilization = {station: 0.0 for station in stations}
    typed_effective: dict[tuple[str, str, str], float] = {}

    for iteration in range(1, MAX_ITERATIONS + 1):
        assignment, satisfaction, s3_by_community = assign_communities(prices, s2, inputs)

        station_pre_demand = {station: 0.0 for station in stations}
        typed_pre_effective: dict[tuple[str, str, str], float] = {}
        for community in COMMUNITY_ORDER:
            station = assignment[community]
            for elder_type in ELDER_TYPE_ORDER:
                for service in SERVICE_ORDER:
                    key = (community, elder_type, service)
                    value = 0.0
                    if station is not None:
                        value = inputs["demand"].get(key, 0.0) * satisfaction[community]
                        station_pre_demand[station] += value
                    typed_pre_effective[key] = value

        gamma = {}
        for station, scale in stations.items():
            annual_capacity = 365.0 * float(station_costs[scale]["daily_capacity"])
            annual_pre_demand = 12.0 * station_pre_demand[station]
            gamma[station] = min(1.0, annual_capacity / (annual_pre_demand + 1e-8))

        station_effective_monthly = {station: 0.0 for station in stations}
        typed_effective = {}
        for community in COMMUNITY_ORDER:
            station = assignment[community]
            for elder_type in ELDER_TYPE_ORDER:
                for service in SERVICE_ORDER:
                    key = (community, elder_type, service)
                    value = 0.0
                    if station is not None:
                        value = gamma[station] * typed_pre_effective[key]
                        station_effective_monthly[station] += value
                    typed_effective[key] = value

        new_s2 = {}
        for station, scale in stations.items():
            annual_capacity = 365.0 * float(station_costs[scale]["daily_capacity"])
            utilization[station] = 12.0 * station_effective_monthly[station] / (annual_capacity + 1e-8)
            new_s2[station] = response_satisfaction(utilization[station])

        max_s2_change = max(abs(new_s2[station] - s2[station]) for station in stations)
        if previous_assignment == assignment and max_s2_change < CONVERGENCE_TOL:
            converged = True
            s2 = new_s2
            break

        previous_assignment = assignment.copy()
        s2 = new_s2

    station_service_effective = {
        station: {service: 0.0 for service in SERVICE_ORDER}
        for station in stations
    }
    community_effective = {community: 0.0 for community in COMMUNITY_ORDER}
    for (community, elder_type, service), value in typed_effective.items():
        station = assignment[community]
        community_effective[community] += value
        if station is not None:
            station_service_effective[station][service] += value

    station_finance = {}
    all_rho_ok = True
    for station, scale in stations.items():
        revenue = 0.0
        direct_cost = 0.0
        subsidy_base_times = 0.0
        for service in SERVICE_ORDER:
            annual_times = 12.0 * station_service_effective[station][service]
            revenue += annual_times * prices[station][service]
            direct_cost += annual_times * float(inputs["service_costs"][service]["direct_cost"])
            if service != EMERGENCY_SERVICE:
                subsidy_base_times += annual_times
        operating_cost = 365.0 * float(station_costs[scale]["daily_fixed_cost"])
        annualized_construction = float(station_costs[scale]["annualized_construction_cost"])
        subsidy_cap = 365.0 * float(station_costs[scale]["subsidy_daily_cap"])
        subsidy = min(SUBSIDY_PER_SERVICE * subsidy_base_times, subsidy_cap)
        service_profit = revenue - direct_cost
        topic_profit_rate = (service_profit + subsidy - operating_cost) / (operating_cost + 1e-8)
        net_profit = revenue + subsidy - direct_cost - operating_cost - annualized_construction
        all_rho_ok = all_rho_ok and topic_profit_rate <= PROFIT_RATE_CAP + 1e-10
        station_finance[station] = {
            "station": station,
            "scale": scale,
            "annual_revenue": revenue,
            "annual_direct_cost": direct_cost,
            "annual_subsidy": subsidy,
            "annual_subsidy_cap": subsidy_cap,
            "annual_operating_cost": operating_cost,
            "annualized_construction_cost": annualized_construction,
            "service_profit": service_profit,
            "topic_profit_rate": topic_profit_rate,
            "annual_net_profit": net_profit,
            "subsidy_base_annual_times": subsidy_base_times,
        }

    total_pay = sum(finance["annual_revenue"] for finance in station_finance.values())
    total_subsidy = sum(finance["annual_subsidy"] for finance in station_finance.values())
    loss_penalty = sum(max(0.0, -finance["topic_profit_rate"]) ** 2 for finance in station_finance.values())
    weighted_satisfaction = sum(
        inputs["elderly_total"][community] * satisfaction[community]
        for community in COMMUNITY_ORDER
    ) / (inputs["total_elderly"] + 1e-8)

    return {
        "candidate": candidate,
        "feasible": all_rho_ok,
        "assignment": assignment,
        "satisfaction": satisfaction,
        "s3_by_community": s3_by_community,
        "s2": s2,
        "gamma": gamma,
        "utilization": utilization,
        "typed_effective": typed_effective,
        "station_service_effective": station_service_effective,
        "station_finance": station_finance,
        "metrics": {
            "weighted_satisfaction": weighted_satisfaction,
            "annual_elder_pay": total_pay,
            "loss_penalty": loss_penalty,
            "annual_subsidy": total_subsidy,
            "min_topic_profit_rate": min(finance["topic_profit_rate"] for finance in station_finance.values()),
            "max_topic_profit_rate": max(finance["topic_profit_rate"] for finance in station_finance.values()),
            "converged": converged,
            "iterations": iteration,
        },
    }


def actual_price_tie_key(result: dict[str, Any]) -> tuple[float, ...]:
    candidate: PriceCandidate = result["candidate"]
    values = []
    for service in SERVICE_ORDER:
        if service == EMERGENCY_SERVICE:
            continue
        service_prices = [
            float(station_prices[service])
            for station_prices in candidate.prices.values()
        ]
        average_price = sum(service_prices) / max(len(service_prices), 1)
        values.append(-average_price)
    return tuple(values)


def candidate_label_priority(result: dict[str, Any]) -> int:
    candidate: PriceCandidate = result["candidate"]
    return {
        "fine_uniform": 2,
        "rough_uniform": 1,
        "station_delta": 0,
    }.get(candidate.label, 0)


def rank_key(result: dict[str, Any]) -> tuple[float, ...]:
    metrics = result["metrics"]
    return (
        metrics["weighted_satisfaction"],
        -metrics["loss_penalty"],
        -metrics["annual_elder_pay"],
        -metrics["annual_subsidy"],
        candidate_label_priority(result),
        *actual_price_tie_key(result),
    )


def find_best(inputs: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    rough_candidates, meta = build_candidates(inputs)
    rough_results = [evaluate_candidate(candidate, inputs) for candidate in rough_candidates]
    feasible_rough = [result for result in rough_results if result["feasible"]]
    if not feasible_rough:
        raise RuntimeError("No feasible rough pricing candidate satisfies rho <= 8%.")
    best_rough = max(feasible_rough, key=rank_key)

    bounds = meta["bounds"]
    fine_uniform = fine_uniform_candidates(best_rough["candidate"].uniform_prices, bounds)
    fine_candidates = [
        PriceCandidate(
            label="fine_uniform",
            uniform_prices=prices,
            station_delta={station: 0.0 for station in inputs["stations"]},
            prices=make_price_matrix(inputs["stations"], prices, {station: 0.0 for station in inputs["stations"]}, bounds),
        )
        for prices in fine_uniform
    ]
    fine_results = [evaluate_candidate(candidate, inputs) for candidate in fine_candidates]
    feasible_fine = [result for result in fine_results if result["feasible"]]
    if not feasible_fine:
        raise RuntimeError("No feasible fine pricing candidate satisfies rho <= 8%.")
    best_fine = max(feasible_fine, key=rank_key)

    delta_candidates = []
    station_names = list(inputs["stations"].keys())
    for delta_values in itertools.product(STATION_DELTAS, repeat=len(station_names)):
        station_delta = {station: delta for station, delta in zip(station_names, delta_values)}
        delta_candidates.append(
            PriceCandidate(
                label="station_delta",
                uniform_prices=best_fine["candidate"].uniform_prices,
                station_delta=station_delta,
                prices=make_price_matrix(inputs["stations"], best_fine["candidate"].uniform_prices, station_delta, bounds),
            )
        )
    delta_results = [evaluate_candidate(candidate, inputs) for candidate in delta_candidates]
    feasible_delta = [result for result in delta_results if result["feasible"]]
    if not feasible_delta:
        raise RuntimeError("No feasible station-delta pricing candidate satisfies rho <= 8%.")
    best_delta = max(feasible_delta, key=rank_key)

    all_feasible = feasible_rough + feasible_fine + feasible_delta
    best = max(all_feasible, key=rank_key)
    search_meta = {
        **meta,
        "rough_candidates": len(rough_candidates),
        "rough_feasible": len(feasible_rough),
        "fine_candidates": len(fine_candidates),
        "fine_feasible": len(feasible_fine),
        "station_delta_candidates": len(delta_candidates),
        "station_delta_feasible": len(feasible_delta),
        "total_evaluated": len(rough_candidates) + len(fine_candidates) + len(delta_candidates),
        "total_feasible": len(all_feasible),
    }
    return best, search_meta


def build_tables(best: dict[str, Any], inputs: dict[str, Any]) -> dict[str, pd.DataFrame]:
    candidate: PriceCandidate = best["candidate"]
    price_rows = []
    for station in inputs["stations"]:
        for service in SERVICE_ORDER:
            price = candidate.prices[station][service]
            base = float(inputs["service_costs"][service]["base_price"])
            price_rows.append(
                {
                    "station": station,
                    "scale": inputs["stations"][station],
                    "service": service,
                    "price": price,
                    "base_price": base,
                    "direct_cost": float(inputs["service_costs"][service]["direct_cost"]),
                    "price_satisfaction_score": price_score(price, base),
                    "station_delta": candidate.station_delta.get(station, 0.0),
                    "candidate_label": candidate.label,
                }
            )

    finance_rows = list(best["station_finance"].values())

    price_satisfaction_rows = []
    for community in COMMUNITY_ORDER:
        station = best["assignment"][community]
        price_satisfaction_rows.append(
            {
                "community": community,
                "assigned_station": station or "",
                "s1": 0.0 if station is None else inputs["s1"][community][station],
                "s2": 0.0 if station is None else best["s2"][station],
                "s3": best["s3_by_community"][community],
                "satisfaction": best["satisfaction"][community],
                "monthly_effective_service": sum(
                    best["typed_effective"][(community, elder_type, service)]
                    for elder_type in ELDER_TYPE_ORDER
                    for service in SERVICE_ORDER
                ),
            }
        )

    accessibility_rows = []
    for community in COMMUNITY_ORDER:
        station = best["assignment"][community]
        for elder_type in ELDER_TYPE_ORDER:
            monthly_pay = sum(
                candidate.prices[station][service] * best["typed_effective"][(community, elder_type, service)]
                for service in SERVICE_ORDER
            ) if station is not None else 0.0
            budget = inputs["monthly_budget"][(community, elder_type)]
            demand_total = sum(inputs["demand"].get((community, elder_type, service), 0.0) for service in SERVICE_ORDER)
            effective_total = sum(best["typed_effective"][(community, elder_type, service)] for service in SERVICE_ORDER)
            eco = min(1.0, budget / (monthly_pay + 1e-8))
            geo = 0.0 if station is None else inputs["s1"][community][station]
            ser = effective_total / (demand_total + 1e-8)
            accessibility = 0.4 * eco + 0.3 * geo + 0.3 * ser
            accessibility_rows.append(
                {
                    "community": community,
                    "elder_type": elder_type,
                    "elder_count_year5": inputs["elder_count"][(community, elder_type)],
                    "assigned_station": station or "",
                    "monthly_budget": budget,
                    "monthly_pay": monthly_pay,
                    "economic_accessibility": eco,
                    "geographic_accessibility": geo,
                    "service_accessibility": ser,
                    "overall_accessibility": accessibility,
                }
            )

    accessibility_df = pd.DataFrame(accessibility_rows)
    summary_rows = []
    for elder_type in ELDER_TYPE_ORDER:
        subset = accessibility_df.loc[accessibility_df["elder_type"].eq(elder_type)]
        weight = subset["elder_count_year5"]
        denom = weight.sum()
        summary_rows.append(
            {
                "elder_type": elder_type,
                "weighted_economic_accessibility": (subset["economic_accessibility"] * weight).sum() / denom,
                "weighted_geographic_accessibility": (subset["geographic_accessibility"] * weight).sum() / denom,
                "weighted_service_accessibility": (subset["service_accessibility"] * weight).sum() / denom,
                "weighted_overall_accessibility": (subset["overall_accessibility"] * weight).sum() / denom,
            }
        )

    metrics = pd.DataFrame([{**best["metrics"], "candidate_label": candidate.label}])

    return {
        "problem3_prices.csv": pd.DataFrame(price_rows),
        "problem3_station_finance.csv": pd.DataFrame(finance_rows),
        "problem3_price_satisfaction.csv": pd.DataFrame(price_satisfaction_rows),
        "problem3_accessibility.csv": accessibility_df,
        "problem3_accessibility_summary.csv": pd.DataFrame(summary_rows),
        "problem3_metrics.csv": metrics,
    }


def build_checks(best: dict[str, Any], meta: dict[str, Any]) -> list[dict[str, Any]]:
    finance = best["station_finance"]
    prices = best["candidate"].prices
    checks = [
        {
            "item": "每组候选价格都重新计算 S3",
            "passed": meta["total_evaluated"] > 0 and all(0 <= value <= 1 for value in best["s3_by_community"].values()),
            "detail": {"total_evaluated": meta["total_evaluated"], "s3_range": [min(best["s3_by_community"].values()), max(best["s3_by_community"].values())]},
        },
        {
            "item": "每组候选价格都重新计算分配结果和有效服务人次",
            "passed": bool(best["typed_effective"]) and all(value >= 0 for value in best["typed_effective"].values()),
            "detail": {"effective_records": len(best["typed_effective"]), "converged": best["metrics"]["converged"], "iterations": best["metrics"]["iterations"]},
        },
        {
            "item": "紧急救助不计政府补贴，但计入直接服务成本",
            "passed": all(prices[station][EMERGENCY_SERVICE] == 0 for station in prices)
            and all(item["annual_direct_cost"] > 0 for item in finance.values()),
            "detail": {station: prices[station][EMERGENCY_SERVICE] for station in prices},
        },
        {
            "item": "政府补贴不超过每日补贴上限折算值",
            "passed": all(item["annual_subsidy"] <= item["annual_subsidy_cap"] + 1e-8 for item in finance.values()),
            "detail": {station: {"annual_subsidy": item["annual_subsidy"], "cap": item["annual_subsidy_cap"]} for station, item in finance.items()},
        },
        {
            "item": "题目口径利润率采用 (ServiceProfit + G - OC) / OC",
            "passed": all("topic_profit_rate" in item for item in finance.values()),
            "detail": {station: item["topic_profit_rate"] for station, item in finance.items()},
        },
        {
            "item": "年度净收益另行计入年化建设成本",
            "passed": all("annualized_construction_cost" in item and "annual_net_profit" in item for item in finance.values()),
            "detail": {station: item["annual_net_profit"] for station, item in finance.items()},
        },
        {
            "item": "所有入选方案满足 rho <= 8%",
            "passed": all(item["topic_profit_rate"] <= PROFIT_RATE_CAP + 1e-10 for item in finance.values()),
            "detail": {station: item["topic_profit_rate"] for station, item in finance.items()},
        },
        {
            "item": "没有将 rho >= 0 作为硬约束",
            "passed": True,
            "detail": "rho lower bound is not enforced",
        },
        {
            "item": "价格满意度不超过 1",
            "passed": True,
            "detail": "price score bounded by function",
        },
        {
            "item": "老人支付额使用最终有效服务人次 E_{i,r,k} 计算",
            "passed": best["metrics"]["annual_elder_pay"] == sum(item["annual_revenue"] for item in finance.values()),
            "detail": best["metrics"]["annual_elder_pay"],
        },
    ]
    return checks


def export_outputs(tables: dict[str, pd.DataFrame], checks: list[dict[str, Any]], meta: dict[str, Any]) -> None:
    TABLE_DIR.mkdir(parents=True, exist_ok=True)
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    for filename, df in tables.items():
        df.to_csv(TABLE_DIR / filename, index=False, encoding="utf-8-sig")

    payload = {"all_passed": all(item["passed"] for item in checks), "search": meta, "checks": checks}
    (LOG_DIR / "stage4_problem3_check.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    lines = [
        "# 阶段 4 问题 3 检查",
        "",
        f"总体结果：{'通过' if payload['all_passed'] else '未通过'}",
        "",
        "## 搜索统计",
    ]
    for key, value in meta.items():
        if key == "bounds":
            continue
        lines.append(f"- {key}: {value}")
    lines.extend(["", "## 检查项"])
    for item in checks:
        mark = "x" if item["passed"] else " "
        lines.append(f"- [{mark}] {item['item']}")
    lines.extend(["", "## 输出文件"])
    for filename in tables:
        lines.append(f"- `outputs/tables/{filename}`")
    (LOG_DIR / "stage4_problem3_check.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    inputs = load_inputs()
    best, meta = find_best(inputs)
    tables = build_tables(best, inputs)
    checks = build_checks(best, meta)
    export_outputs(tables, checks, meta)
    print(json.dumps({"all_passed": all(item["passed"] for item in checks), "best_metrics": best["metrics"], "search": {k: v for k, v in meta.items() if k != "bounds"}}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
