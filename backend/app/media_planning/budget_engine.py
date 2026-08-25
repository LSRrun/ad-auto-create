from decimal import Decimal, ROUND_HALF_UP

from .schemas import BudgetScenario, MediaPlan


def money(value: float | Decimal) -> float:
    return float(Decimal(str(value)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))


def _conversion_range(total: float, target_cpa: float | None) -> tuple[float | None, float | None]:
    if not target_cpa:
        return None, None
    optimistic = max(target_cpa * 0.8, 0.01)
    conservative = target_cpa * 1.25
    return money(total / conservative), money(total / optimistic)


def build_scenarios(total: float, days: int, target_cpa: float | None) -> list[BudgetScenario]:
    definitions = [
        ("conservative", "保守测试", 0.6, "控制风险，先验证素材与核心人群方向"),
        ("standard", "标准测试", 1.0, "按当前总预算并行测试核心、拓量和宽泛单元"),
        ("scale", "扩量参考", 1.5, "仅在真实 CPA 和转化量达到目标后使用"),
    ]
    scenarios = []
    for scenario_id, name, factor, note in definitions:
        scenario_total = money(total * factor)
        low, high = _conversion_range(scenario_total, target_cpa)
        scenarios.append(BudgetScenario(
            id=scenario_id,
            name=name,
            total_budget=scenario_total,
            daily_budget=money(scenario_total / days),
            estimated_conversions_low=low,
            estimated_conversions_high=high,
            note=note,
        ))
    return scenarios


def resolve_target_cpa(plan: MediaPlan) -> float | None:
    business = plan.business_inputs
    if business.target_cpa_cap:
        return money(business.target_cpa_cap)
    if business.actual_price and business.gross_margin_rate is not None:
        return money(business.actual_price * business.gross_margin_rate * 0.5)
    return None


def recalculate(plan: MediaPlan) -> MediaPlan:
    total = money(plan.business_inputs.budget_cap)
    days = plan.business_inputs.duration_days
    daily = money(total / days)
    target_cpa = resolve_target_cpa(plan)
    for campaign in plan.campaigns:
        campaign.total_budget = total
        campaign.daily_budget = daily
        campaign.duration_days = days
        campaign.target_kpi = target_cpa
        for unit in campaign.ad_units:
            unit.daily_budget = money(daily * unit.budget_share)
    plan.budget_scenarios = build_scenarios(total, days, target_cpa)
    return plan

