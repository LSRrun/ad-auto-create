from fastapi import HTTPException

from .ai_strategy import suggest
from .repository import load_job, load_plan, save_plan, update_job
from .research_gateway import research
from .schemas import CreateMediaPlanRequest, MediaPlan
from .strategy_generator import generate_plan


async def run_job(
    job_id: str,
    request: CreateMediaPlanRequest,
    image: bytes | None = None,
    mime_type: str | None = None,
) -> None:
    try:
        update_job(job_id, status="running", stage="creative_analysis", progress=12, message="正在读取商品资料和广告创意")
        evidence, research_warnings = await research(request)
        official_count = sum(item.reliability == "official" for item in evidence)
        update_job(
            job_id,
            stage="research",
            progress=52,
            message="已完成公开资料检索，正在综合投放策略",
            source_count=len(evidence),
            official_source_count=official_count,
        )
        suggestion = None
        if request.ai_config:
            try:
                suggestion = await suggest(request, evidence, image, mime_type)
            except HTTPException as exc:
                research_warnings.append(f"AI 策略分析未完成：{exc.detail}；已切换规则模式")
        else:
            research_warnings.append("未配置 AI 策略模型，本次使用规则模式生成可编辑方案")
        update_job(job_id, stage="strategy", progress=78, message="正在生成计划、广告单元和创意")
        plan = generate_plan(request, evidence, suggestion, research_warnings)
        saved = save_plan(plan.model_dump())
        update_job(
            job_id,
            status="completed",
            stage="completed",
            progress=100,
            message="投放方案已生成",
            plan_id=saved["id"],
        )
    except Exception as exc:
        detail = exc.detail if isinstance(exc, HTTPException) else "投放方案生成失败，请检查输入或稍后重试"
        update_job(job_id, status="failed", stage="failed", progress=100, message="任务失败", error=str(detail))


def get_job(job_id: str) -> dict:
    return load_job(job_id)


def get_plan(plan_id: str) -> MediaPlan:
    return MediaPlan.model_validate(load_plan(plan_id))


def replace_plan(plan_id: str, plan: MediaPlan) -> MediaPlan:
    if plan.id != plan_id:
        raise HTTPException(status_code=400, detail="方案 ID 不一致")
    saved = save_plan(plan.model_dump())
    return MediaPlan.model_validate(saved)


def recalculate_saved_plan(plan_id: str) -> MediaPlan:
    from .budget_engine import recalculate

    plan = get_plan(plan_id)
    recalculated = recalculate(plan)
    return replace_plan(plan_id, recalculated)


def export_markdown(plan: MediaPlan) -> str:
    campaign = plan.campaigns[0]
    lines = [
        f"# {plan.name}",
        "",
        f"- 投放目标：{plan.objective}",
        f"- 平台：{plan.platform}",
        f"- 周期：{campaign.duration_days} 天",
        f"- 总预算：{plan.currency} {campaign.total_budget:,.2f}",
        f"- 日预算：{plan.currency} {campaign.daily_budget:,.2f}",
        f"- 主要指标：{campaign.primary_kpi}",
        "",
        "## 策略摘要",
        "",
        plan.strategy_summary,
        "",
        "## 计划与广告单元",
    ]
    for unit in campaign.ad_units:
        lines.extend([
            "",
            f"### {unit.name}",
            "",
            f"- 预算占比：{unit.budget_share * 100:.0f}%",
            f"- 日预算：{plan.currency} {unit.daily_budget:,.2f}",
            f"- 城市：{'、'.join(unit.geo.include)}",
            f"- 年龄：{'、'.join(unit.demographics.age_ranges)}",
            f"- 性别：{'不限' if 'all' in unit.demographics.genders else '、'.join(unit.demographics.genders)}",
            f"- 兴趣：{'、'.join(unit.audiences.interests) or '宽泛'}",
            f"- 测试假设：{unit.hypothesis}",
        ])
    lines.extend(["", "## 风险与假设", ""])
    lines.extend(f"- {item}" for item in [*plan.warnings, *plan.assumptions])
    lines.extend(["", "## 数据来源", ""])
    lines.extend(f"- [{item.title}]({item.url}) — {item.publisher}" for item in plan.sources)
    return "\n".join(lines) + "\n"
