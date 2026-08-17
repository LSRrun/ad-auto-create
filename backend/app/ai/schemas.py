from pydantic import BaseModel, Field, field_validator


class ModelConfig(BaseModel):
    provider: str = Field(min_length=1, max_length=40)
    model: str = Field(min_length=1, max_length=120)
    base_url: str = Field(min_length=1, max_length=500)
    api_key: str = Field(default="", max_length=500)


class ConnectionRequest(BaseModel):
    config: ModelConfig


class ProductInput(BaseModel):
    brand: str = Field(default="", max_length=80)
    product_name: str = Field(min_length=1, max_length=80)
    price: str = Field(default="", max_length=40)
    selling_points: str = Field(default="", max_length=500)


class CurrentCopy(BaseModel):
    headline: str = Field(default="", max_length=60)
    eyebrow: str = Field(default="", max_length=60)
    description: str = Field(default="", max_length=500)
    features: list[str] = Field(default_factory=list, max_length=3)
    cta: str = Field(default="", max_length=30)


class PolishRequest(BaseModel):
    config: ModelConfig
    style_id: str
    product: ProductInput
    current_copy: CurrentCopy


class PolishedCopy(BaseModel):
    headline: str = Field(min_length=1, max_length=28)
    eyebrow: str = Field(min_length=1, max_length=40)
    description: str = Field(min_length=1, max_length=140)
    features: list[str] = Field(min_length=1, max_length=3)
    cta: str = Field(min_length=1, max_length=16)

    @field_validator("headline", "eyebrow", "description", "cta")
    @classmethod
    def clean_text(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("文案不能为空")
        return cleaned

    @field_validator("features")
    @classmethod
    def clean_features(cls, value: list[str]) -> list[str]:
        cleaned = [item.strip()[:24] for item in value if item.strip()]
        if not cleaned:
            raise ValueError("至少需要一个卖点")
        return cleaned[:3]

