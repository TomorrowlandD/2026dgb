from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
TABLE_DIR = ROOT / "outputs" / "tables"
LOG_DIR = ROOT / "outputs" / "logs"

COMMUNITY_ORDER = list("ABCDEFGHIJ")
SERVICE_ORDER = ["助餐", "日间照料", "上门护理", "康复理疗", "助浴", "紧急救助"]
ELDER_TYPE_ORDER = ["自理", "半失能", "失能"]

FILES = {
    "base": DATA_DIR / "附件1：小区基础数据.xlsx",
    "demand": DATA_DIR / "附件2：服务需求数据.xlsx",
    "station": DATA_DIR / "附件3：服务站建设与运营成本.xlsx",
    "distance": DATA_DIR / "附件4：小区间距离矩阵.xlsx",
    "satisfaction": DATA_DIR / "附件5：满意度评分规则.xlsx",
}


def _clean_columns(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.columns = [str(col).strip() for col in df.columns]
    return df


def _first_number(value: Any) -> float:
    if pd.isna(value):
        raise ValueError("missing numeric value")
    if isinstance(value, (int, float)):
        return float(value)
    match = re.search(r"-?\d+(?:\.\d+)?", str(value))
    if not match:
        raise ValueError(f"cannot parse numeric value: {value!r}")
    return float(match.group(0))


def _ratio(value: Any) -> float:
    number = _first_number(value)
    return number / 100 if "%" in str(value) or number > 1 else number


def _normalize_elder_type(value: str) -> str:
    text = str(value).strip()
    text = text.replace("半自理", "半失能")
    text = text.replace("老人", "")
    return text


def _write_csv(df: pd.DataFrame, filename: str) -> None:
    TABLE_DIR.mkdir(parents=True, exist_ok=True)
    df.to_csv(TABLE_DIR / filename, index=False, encoding="utf-8-sig")


def load_communities() -> pd.DataFrame:
    df = pd.read_excel(FILES["base"], sheet_name="人口与老人结构", header=1)
    df = _clean_columns(df)
    df = df.rename(
        columns={
            "小区编号": "community",
            "总人口": "total_population",
            "60+老人数": "elderly_total",
            "自理老人": "self_care",
            "半失能老人": "semi_disabled",
            "失能老人": "disabled",
            "人均月收入(元)": "monthly_income",
        }
    )
    df = df[
        [
            "community",
            "total_population",
            "elderly_total",
            "self_care",
            "semi_disabled",
            "disabled",
            "monthly_income",
        ]
    ]
    numeric_cols = df.columns.drop("community")
    df[numeric_cols] = df[numeric_cols].apply(pd.to_numeric)
    return df


def load_transition_probabilities() -> pd.DataFrame:
    df = pd.read_excel(FILES["base"], sheet_name="转移概率", header=1)
    df = _clean_columns(df)
    df = df.rename(columns={"转移类型": "transition", "年度转移概率参考区间": "probability"})
    df["transition"] = df["transition"].astype(str).str.strip()
    df["probability"] = df["probability"].map(_first_number)
    df["parameter"] = df["transition"].map(
        {
            "自理 → 半失能": "p12",
            "半失能 → 失能": "p23",
        }
    )
    return df[["parameter", "transition", "probability"]]


def load_service_demand() -> pd.DataFrame:
    df = pd.read_excel(FILES["demand"], sheet_name="每位老人月均服务需求次数", header=1)
    df = _clean_columns(df)
    df = df.rename(columns={"服务项目": "service", "自理": "self_care", "半自理": "semi_disabled", "失能": "disabled"})
    df["service"] = df["service"].astype(str).str.strip()
    for col in ["self_care", "semi_disabled", "disabled"]:
        df[col] = pd.to_numeric(df[col])
    return df[["service", "self_care", "semi_disabled", "disabled"]]


def load_service_costs() -> pd.DataFrame:
    df = pd.read_excel(FILES["demand"], sheet_name="服务营收及支出", header=1)
    df = _clean_columns(df)
    df = df.rename(
        columns={
            "服务项目": "service",
            "单次服务营收（元）": "base_price",
            "单次服务直接支出（元）（基准价格）": "direct_cost",
        }
    )
    df["service"] = df["service"].astype(str).str.strip()
    df["base_price"] = df["base_price"].map(_first_number)
    df["direct_cost"] = df["direct_cost"].map(_first_number)
    df["is_emergency"] = df["service"].eq("紧急救助")
    return df[["service", "base_price", "direct_cost", "is_emergency"]]


def load_consumption_limits() -> pd.DataFrame:
    df = pd.read_excel(FILES["demand"], sheet_name="月服务消费上限", header=0)
    df = _clean_columns(df)
    df = df.iloc[:3].copy()
    df = df.rename(columns={"老人类型": "elder_type", "月服务消费上限（占月收入比例）": "max_income_share"})
    df["elder_type"] = df["elder_type"].map(_normalize_elder_type)
    df["max_income_share"] = df["max_income_share"].map(_ratio)
    return df[["elder_type", "max_income_share"]]


def load_station_costs() -> pd.DataFrame:
    df = pd.read_excel(FILES["station"], sheet_name="服务站建设与运营成本", header=1)
    df = _clean_columns(df)
    df = df.rename(
        columns={
            "站点规模": "scale",
            "一次性建设成本（万元）": "construction_cost_10k",
            "日均固定管理成本（元/日）": "daily_fixed_cost",
            "日最大服务人次": "daily_capacity",
        }
    )
    df = df[df["scale"].isin(["小型", "中型", "大型"])].copy()
    for col in ["construction_cost_10k", "daily_fixed_cost", "daily_capacity"]:
        df[col] = pd.to_numeric(df[col])
    subsidy_daily_cap = {"小型": 1000, "中型": 1800, "大型": 2600}
    df["subsidy_daily_cap"] = df["scale"].map(subsidy_daily_cap)
    df["annualized_construction_cost"] = df["construction_cost_10k"] * 10000 / 20
    return df[
        [
            "scale",
            "construction_cost_10k",
            "daily_fixed_cost",
            "daily_capacity",
            "subsidy_daily_cap",
            "annualized_construction_cost",
        ]
    ]


def load_distance_matrix() -> pd.DataFrame:
    df = pd.read_excel(FILES["distance"], sheet_name="小区间距离矩阵", header=1, index_col=0)
    df.index = df.index.astype(str).str.strip()
    df.columns = [str(col).strip() for col in df.columns]
    df = df.loc[COMMUNITY_ORDER, COMMUNITY_ORDER]
    return df.apply(pd.to_numeric)


def load_satisfaction_rules() -> pd.DataFrame:
    rows = [
        {"factor": "distance", "score_name": "S1", "condition": "distance <= 300", "score": 1.00},
        {"factor": "distance", "score_name": "S1", "condition": "300 < distance <= 500", "score": 0.90},
        {"factor": "distance", "score_name": "S1", "condition": "500 < distance <= 650", "score": 0.75},
        {"factor": "distance", "score_name": "S1", "condition": "650 < distance <= 1000", "score": 0.60},
        {"factor": "response", "score_name": "S2", "condition": "utilization <= 0.60", "score": 1.00},
        {"factor": "response", "score_name": "S2", "condition": "0.60 < utilization <= 0.75", "score": 0.93},
        {"factor": "response", "score_name": "S2", "condition": "0.75 < utilization <= 0.85", "score": 0.85},
        {"factor": "response", "score_name": "S2", "condition": "0.85 < utilization <= 0.95", "score": 0.72},
        {"factor": "response", "score_name": "S2", "condition": "0.95 < utilization <= 1.00", "score": 0.60},
        {"factor": "price", "score_name": "S3", "condition": "price <= base_price", "score": 1.00},
        {"factor": "price", "score_name": "S3", "condition": "base_price < price <= 1.10*base_price", "score": 0.90},
        {"factor": "price", "score_name": "S3", "condition": "1.10*base_price < price <= 1.20*base_price", "score": 0.75},
        {"factor": "price", "score_name": "S3", "condition": "price > 1.20*base_price", "score": 0.60},
    ]
    return pd.DataFrame(rows)


def load_all_parameters() -> dict[str, pd.DataFrame]:
    return {
        "communities": load_communities(),
        "transition_probabilities": load_transition_probabilities(),
        "service_demand": load_service_demand(),
        "service_costs": load_service_costs(),
        "consumption_limits": load_consumption_limits(),
        "station_costs": load_station_costs(),
        "distance_matrix": load_distance_matrix(),
        "satisfaction_rules": load_satisfaction_rules(),
    }


def build_checks(params: dict[str, pd.DataFrame]) -> list[dict[str, Any]]:
    communities = params["communities"]
    distance = params["distance_matrix"]
    services = params["service_costs"]
    limits = params["consumption_limits"]
    station = params["station_costs"]
    demand = params["service_demand"]
    transition = params["transition_probabilities"]
    satisfaction = params["satisfaction_rules"]

    elderly_sum = communities[["self_care", "semi_disabled", "disabled"]].sum(axis=1)
    checks = [
        {
            "item": "10 个小区编号完整且顺序一致",
            "passed": communities["community"].tolist() == COMMUNITY_ORDER,
            "detail": communities["community"].tolist(),
        },
        {
            "item": "三类老人初始人数加总等于 60+ 老人数",
            "passed": bool((elderly_sum == communities["elderly_total"]).all()),
            "detail": {
                row["community"]: int(elderly_sum.iloc[idx] - row["elderly_total"])
                for idx, row in communities.iterrows()
            },
        },
        {
            "item": "距离矩阵为 10 x 10",
            "passed": distance.shape == (10, 10),
            "detail": list(distance.shape),
        },
        {
            "item": "距离矩阵主对角线为 0",
            "passed": bool((distance.values.diagonal() == 0).all()),
            "detail": distance.values.diagonal().astype(int).tolist(),
        },
        {
            "item": "距离矩阵对称",
            "passed": bool(distance.equals(distance.T)),
            "detail": "symmetric" if distance.equals(distance.T) else "not symmetric",
        },
        {
            "item": "服务项目为 6 项",
            "passed": services["service"].tolist() == SERVICE_ORDER,
            "detail": services["service"].tolist(),
        },
        {
            "item": "紧急救助价格为 0",
            "passed": float(services.loc[services["service"].eq("紧急救助"), "base_price"].iloc[0]) == 0,
            "detail": float(services.loc[services["service"].eq("紧急救助"), "base_price"].iloc[0]),
        },
        {
            "item": "消费上限比例正确",
            "passed": limits["max_income_share"].round(4).tolist() == [0.20, 0.25, 0.30],
            "detail": limits.to_dict(orient="records"),
        },
        {
            "item": "建设成本、运营成本、容量均非负",
            "passed": bool((station[["construction_cost_10k", "daily_fixed_cost", "daily_capacity"]] >= 0).all().all()),
            "detail": station[["scale", "construction_cost_10k", "daily_fixed_cost", "daily_capacity"]].to_dict(orient="records"),
        },
        {
            "item": "需求、成本、转移概率和满意度规则无异常空值",
            "passed": not any(
                df.isna().any().any()
                for df in [demand, services, limits, station, transition, satisfaction]
            ),
            "detail": {
                "service_demand_nulls": int(demand.isna().sum().sum()),
                "service_costs_nulls": int(services.isna().sum().sum()),
                "consumption_limits_nulls": int(limits.isna().sum().sum()),
                "station_costs_nulls": int(station.isna().sum().sum()),
                "transition_nulls": int(transition.isna().sum().sum()),
                "satisfaction_nulls": int(satisfaction.isna().sum().sum()),
            },
        },
        {
            "item": "所有核心数值字段非负",
            "passed": bool(
                (communities.drop(columns=["community"]) >= 0).all().all()
                and (demand.drop(columns=["service"]) >= 0).all().all()
                and (services[["base_price", "direct_cost"]] >= 0).all().all()
                and (transition["probability"] >= 0).all()
                and (distance >= 0).all().all()
                and (satisfaction["score"] >= 0).all()
            ),
            "detail": "nonnegative core numeric fields",
        },
    ]
    return checks


def export_outputs(params: dict[str, pd.DataFrame], checks: list[dict[str, Any]]) -> None:
    TABLE_DIR.mkdir(parents=True, exist_ok=True)
    LOG_DIR.mkdir(parents=True, exist_ok=True)

    csv_names = {
        "communities": "stage1_communities.csv",
        "transition_probabilities": "stage1_transition_probabilities.csv",
        "service_demand": "stage1_service_demand.csv",
        "service_costs": "stage1_service_costs.csv",
        "consumption_limits": "stage1_consumption_limits.csv",
        "station_costs": "stage1_station_costs.csv",
        "satisfaction_rules": "stage1_satisfaction_rules.csv",
    }
    for key, filename in csv_names.items():
        _write_csv(params[key], filename)

    distance = params["distance_matrix"].reset_index().rename(columns={"index": "community"})
    _write_csv(distance, "stage1_distance_matrix.csv")

    parameter_payload = {
        key: df.reset_index().to_dict(orient="records") if key == "distance_matrix" else df.to_dict(orient="records")
        for key, df in params.items()
    }
    (TABLE_DIR / "stage1_cleaned_parameters.json").write_text(
        json.dumps(parameter_payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    check_payload = {"all_passed": all(item["passed"] for item in checks), "checks": checks}
    (LOG_DIR / "stage1_data_check.json").write_text(
        json.dumps(check_payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    lines = ["# 阶段 1 数据清洗检查", "", f"总体结果：{'通过' if check_payload['all_passed'] else '未通过'}", ""]
    for item in checks:
        mark = "x" if item["passed"] else " "
        lines.append(f"- [{mark}] {item['item']}")
    lines.append("")
    lines.append("## 输出文件")
    for filename in list(csv_names.values()) + ["stage1_distance_matrix.csv", "stage1_cleaned_parameters.json"]:
        lines.append(f"- `outputs/tables/{filename}`")
    (LOG_DIR / "stage1_data_check.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    params = load_all_parameters()
    checks = build_checks(params)
    export_outputs(params, checks)
    print(json.dumps({"all_passed": all(item["passed"] for item in checks), "checks": checks}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
