from typing import Literal

from pydantic import BaseModel, Field, field_validator, model_validator

from ..ai.schemas import ModelConfig


Objective = Literal["sales", "lead_generation", "store_visit", "awareness"]
Confidence = Literal["high", "medium", "low"]


class ProductSnapshot(BaseModel):
    brand: str = Field(default="", max_length=80)
    name: str = Field(min_length=1, max_length=80)
    price_text: str = Field(default="", max_length=60)
    selling_points: list[str] = Field(default_factory=list, max_length=8)
    headline: str = Field(default="", max_length=80)
    description: str = Field(default="", max_length=300)


class CreativeSource(BaseModel):
    type: Literal["original", "reconstructed"] = "original"
    source_url: str = Field(default="", max_length=1000)
    style_id: str = Field(default="", max_length=80)
    version: str = Field(default="current", max_length=80)


class BusinessInput(BaseModel):
    objective: Objective
    platforms: list[str] = Field(min_length=1, max_length=4)
    duration_days: int = Field(ge=1, le=180)
    budget_cap: float = Field(gt=0, le=100_000_000)
    currency: Literal["CNY", "USD"] = "CNY"
    service_areas: list[str] = Field(min_length=1, max_length=100)
    conversion_destination: str = Field(default="lead_form", max_length=80)
    actual_price: float | None = Field(default=None, gt=0, le=100_000_000)
    gross_margin_rate: float | None = Field(default=None, ge=0, le=1)
    target_cpa_cap: float | None = Field(default=None, gt=0, le=10_000_000)

    @field_validator("service_areas")
    @classmethod
    def clean_areas(cls, value: list[str]) -> list[str]:
        cleaned = list(dict.fromkeys(item.strip()[:40] for item in value if item.strip()))
        if not cleaned:
            raise ValueError("至少需要一个可服务地区")
        return cleaned


class ResearchConfig(BaseModel):
    enabled: bool = True
    max_queries: int = Field(default=4, ge=1, le=8)
    max_pages: int = Field(default=6, ge=1, le=16)
    freshness_days: int = Field(default=365, ge=7, le=1825)


class CreateMediaPlanRequest(BaseModel):
    product: ProductSnapshot
    creative_source: CreativeSource
    business: BusinessInput
    research: ResearchConfig = Field(default_factory=ResearchConfig)
    model_config: ModelConfig | None = None


class ResearchEvidence(BaseModel):
    id: str
    topic: str
    title: str
    url: str
    publisher: str
    published_at: str = ""
    retrieved_at: str
    summary: str
    reliability: Literal["official", "industry", "public_web", "user_input"]
    supports: list[str] = Field(default_factory=list)


class CreativePlan(BaseModel):
    id: str
    name: str
    angle: str
    headline: str
    body: str = ""
    cta: str
    source_type: str = "current_ad"
    landing_page: str = ""
    compliance_status: Literal["needs_review", "reviewed"] = "needs_review"


class GeoTargeting(BaseModel):
    include: list[str] = Field(default_factory=list, max_length=100)
    exclude: list[str] = Field(default_factory=list, max_length=100)
    presence_mode: Literal["physical_or_regular", "platform_default"] = "physical_or_regular"


class Demographics(BaseModel):
    age_ranges: list[str] = Field(default_factory=list)
    genders: list[Literal["all", "female", "male"]] = Field(default_factory=lambda: ["all"])
    unknown_gender: Literal["include", "exclude"] = "include"


class AudienceTargeting(BaseModel):
    interests: list[str] = Field(default_factory=list)
    behaviors: list[str] = Field(default_factory=list)
    purchase_intents: list[str] = Field(default_factory=list)
    first_party: list[str] = Field(default_factory=list)
    exclusions: list[str] = Field(default_factory=list)


class AdUnit(BaseModel):
    id: str
    name: str
    hypothesis: str
    budget_share: float = Field(gt=0, le=1)
    daily_budget: float = Field(ge=0)
    geo: GeoTargeting
    demographics: Demographics
    audiences: AudienceTargeting
    placements: list[str] = Field(default_factory=lambda: ["automatic"])
    bid_strategy: str = "lowest_cost"
    optimization_event: str = "lead_submit"
    creatives: list[CreativePlan] = Field(min_length=1)
    reason: str
    evidence_ids: list[str] = Field(default_factory=list)
    confidence: Confidence = "medium"


class CampaignPlan(BaseModel):
    id: str
    name: str
    objective: Objective
    optimization_event: str
    budget_type: Literal["lifetime", "daily"] = "lifetime"
    total_budget: float = Field(gt=0)
    daily_budget: float = Field(gt=0)
    duration_days: int = Field(ge=1, le=180)
    primary_kpi: str
    target_kpi: float | None = None
    ad_units: list[AdUnit] = Field(min_length=1)

    @model_validator(mode="after")
    def validate_budget_shares(self):
        total = sum(unit.budget_share for unit in self.ad_units)
        if abs(total - 1) > 0.011:
            raise ValueError("广告单元预算占比合计必须为 100%")
        return self


class BudgetScenario(BaseModel):
    id: Literal["conservative", "standard", "scale"]
    name: str
    total_budget: float
    daily_budget: float
    estimated_conversions_low: float | None = None
    estimated_conversions_high: float | None = None
    note: str


class MediaPlan(BaseModel):
    schema_version: int = 1
    id: str
    name: str
    status: Literal["draft", "ready"] = "draft"
    currency: Literal["CNY", "USD"]
    platform: str
    objective: Objective
    product: ProductSnapshot
    creative_source: CreativeSource
    business_inputs: BusinessInput
    creative_analysis: dict = Field(default_factory=dict)
    strategy_summary: str
    campaigns: list[CampaignPlan] = Field(min_length=1)
    budget_scenarios: list[BudgetScenario] = Field(default_factory=list)
    assumptions: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    sources: list[ResearchEvidence] = Field(default_factory=list)
    created_at: str
    updated_at: str


class JobStatus(BaseModel):
    id: str
    status: Literal["queued", "running", "completed", "failed", "cancelled"]
    stage: str
    progress: int = Field(ge=0, le=100)
    message: str
    plan_id: str | None = None
    error: str | None = None
    source_count: int = 0
    official_source_count: int = 0
    created_at: str
    updated_at: str

