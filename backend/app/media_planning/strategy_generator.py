from datetime import datetime, timezone

from .ai_strategy import AIStrategySuggestion
from .budget_engine import recalculate
from .repository import new_plan_id
from .schemas import (
    AdUnit,
    AudienceTargeting,
    CampaignPlan,
    CreativePlan,
    CreateMediaPlanRequest,
    Demographics,
    GeoTargeting,
    MediaPlan,
    ResearchEvidence,
)


OBJECTIVE_LABELS = {
    "sales": ("商品成交", "purchase", "ROAS"),
    "lead_generation": ("获取咨询", "lead_submit", "CPA"),
    "store_visit": ("到店咨询", "store_visit", "CPA"),
    "awareness": ("品牌曝光", "impression", "CPM"),
}


def _default_interests(product_name: str) -> list[str]:
    common = ["家居装修", "品质生活"]
    if any(word in product_name for word in ("花洒", "卫浴", "浴室", "龙头")):
        return ["卫浴产品", "智能家居", *common]
    return [product_name, *common]


def _creative(unit_id: str, request: CreateMediaPlanRequest, angle: str, index: int) -> CreativePlan:
    product = request.product
    headline = product.headline or f"重新认识{product.name}"
    return CreativePlan(
        id=f"creative-{unit_id}-{index}",
        name=f"{angle}创意",
        angle=angle,
        headline=headline,
        body=product.description,
        cta="立即咨询" if request.business.objective != "awareness" else "了解更多",
    )


def _build_units(request: CreateMediaPlanRequest, suggestion: AIStrategySuggestion | None, evidence: list[ResearchEvidence]) -> list[AdUnit]:
    daily = request.business.budget_cap / request.business.duration_days
    use_three = daily >= 600
    shares = [0.5, 0.3, 0.2] if use_three else [0.65, 0.35]
    official_ids = [item.id for item in evidence if item.reliability == "official"][:4]
    interests = suggestion.interests if suggestion and suggestion.interests else _default_interests(request.product.name)
    behaviors = suggestion.behaviors if suggestion else []
    intents = suggestion.purchase_intents if suggestion else [f"主动了解{request.product.name}"]
    angles = suggestion.creative_angles if suggestion else ["核心功能", "生活方式", "价格与行动"]
    definitions = [
        (
            "core-intent",
            "核心｜高意向人群",
            suggestion.core_hypothesis if suggestion else "正在装修或主动了解相关产品的人群，更可能完成当前转化目标",
            interests,
            behaviors,
            intents,
            "以业务覆盖范围内的高意向兴趣和购买意图作为第一轮验证",
        ),
        (
            "scenario-expansion",
            "拓量｜场景兴趣人群",
            suggestion.expansion_hypothesis if suggestion else "关注家居改善和品质生活场景的人群，可能被当前创意的体验表达吸引",
            ["家居装修", "品质生活", "智能家居"],
            [],
            [],
            "减少产品词限制，验证更宽的使用场景需求",
        ),
        (
            "broad-explore",
            "探索｜宽泛人群",
            "在服务地区和成年人范围内减少手动标签，让平台寻找新的转化人群",
            [],
            [],
            [],
            "宽泛探索用于发现增量，不代表平台一定能够达到目标成本",
        ),
    ]
    units = []
    for index, (unit_id, name, hypothesis, unit_interests, unit_behaviors, unit_intents, reason) in enumerate(definitions[: len(shares)]):
        angle = angles[min(index, len(angles) - 1)]
        units.append(AdUnit(
            id=f"unit-{unit_id}",
            name=name,
            hypothesis=hypothesis,
            budget_share=shares[index],
            daily_budget=0,
            geo=GeoTargeting(include=request.business.service_areas),
            demographics=Demographics(age_ranges=["25-34", "35-44", "45-54"], genders=["all"]),
            audiences=AudienceTargeting(
                interests=unit_interests,
                behaviors=unit_behaviors,
                purchase_intents=unit_intents,
                exclusions=["已完成当前转化目标的人群"],
            ),
            optimization_event=OBJECTIVE_LABELS[request.business.objective][1],
            creatives=[_creative(unit_id, request, angle, index + 1)],
            reason=reason,
            evidence_ids=official_ids,
            confidence="medium" if index < 2 else "low",
        ))
    return units


def generate_plan(
    request: CreateMediaPlanRequest,
    evidence: list[ResearchEvidence],
    suggestion: AIStrategySuggestion | None,
    research_warnings: list[str],
) -> MediaPlan:
    timestamp = datetime.now(timezone.utc).isoformat()
    objective_label, event, kpi = OBJECTIVE_LABELS[request.business.objective]
    product_category = suggestion.product_category if suggestion else request.product.name
    positioning = suggestion.creative_positioning if suggestion else "根据当前商品卖点与广告文案形成的测试定位"
    summary = suggestion.strategy_summary if suggestion else (
        f"围绕“{request.product.name}”建立核心意向与场景拓量测试，在{request.business.duration_days}天内"
        f"以{objective_label}为目标，先验证素材与人群组合，再依据真实 {kpi} 决定扩量。"
    )
    warnings = [
        "本方案是投放测试建议，不构成效果保证；具体成本需以真实广告账户数据校准",
        "性别默认不限，未根据广告画面推断敏感或人口属性",
        *research_warnings,
    ]
    assumptions = [
        "用户填写的预算、服务地区、价格和目标为真实业务约束",
        "当前没有导入广告账户历史数据，预算预估仅使用目标 CPA 或利润约束",
        "城市只从用户可服务地区中选择，未把公开信息转化为伪精确城市排名",
    ]
    if suggestion:
        warnings.extend(suggestion.compliance_observations)
        assumptions.extend(suggestion.uncertainties)
    units = _build_units(request, suggestion, evidence)
    plan = MediaPlan(
        id=new_plan_id(),
        name=f"{request.product.name}｜{request.business.duration_days}天投放方案",
        status="ready",
        currency=request.business.currency,
        platform=" / ".join(request.business.platforms),
        objective=request.business.objective,
        product=request.product,
        creative_source=request.creative_source,
        business_inputs=request.business,
        creative_analysis={
            "product_category": product_category,
            "creative_positioning": positioning,
            "analysis_mode": "ai" if suggestion else "rule_fallback",
        },
        strategy_summary=summary,
        campaigns=[CampaignPlan(
            id="campaign-01",
            name=f"{request.product.name}｜{objective_label}测试",
            objective=request.business.objective,
            optimization_event=event,
            total_budget=request.business.budget_cap,
            daily_budget=request.business.budget_cap / request.business.duration_days,
            duration_days=request.business.duration_days,
            primary_kpi=kpi,
            ad_units=units,
        )],
        assumptions=list(dict.fromkeys(item for item in assumptions if item)),
        warnings=list(dict.fromkeys(item for item in warnings if item)),
        sources=evidence,
        created_at=timestamp,
        updated_at=timestamp,
    )
    return recalculate(plan)

