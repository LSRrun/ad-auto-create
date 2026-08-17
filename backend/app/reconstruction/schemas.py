from typing import Literal

from pydantic import BaseModel, Field, field_validator


class ImageModelConfig(BaseModel):
    provider: str = Field(min_length=1, max_length=40)
    model: str = Field(min_length=1, max_length=120)
    base_url: str = Field(min_length=1, max_length=500)
    api_key: str = Field(default="", max_length=500)
    size: Literal["1024x1024", "1024x1536", "1536x1024"] = "1024x1536"
    quality: Literal["low", "medium", "high"] = "medium"


class ImageConnectionRequest(BaseModel):
    config: ImageModelConfig


class SnapshotProduct(BaseModel):
    brand: str = Field(default="", max_length=80)
    product_name: str = Field(min_length=1, max_length=80)
    price: str = Field(default="", max_length=40)
    selling_points: str = Field(default="", max_length=500)


class SnapshotAd(BaseModel):
    eyebrow: str = Field(default="", max_length=60)
    headline: str = Field(min_length=1, max_length=60)
    description: str = Field(default="", max_length=500)
    features: list[str] = Field(default_factory=list, max_length=3)
    cta: str = Field(default="", max_length=30)

    @field_validator("features")
    @classmethod
    def clean_features(cls, value: list[str]) -> list[str]:
        return [item.strip()[:40] for item in value if item.strip()][:3]


class PageSnapshot(BaseModel):
    style_id: str = Field(min_length=1, max_length=60)
    product: SnapshotProduct
    ad: SnapshotAd


class ReconstructionResult(BaseModel):
    id: str
    imageUrl: str
    mode: Literal["product_locked"] = "product_locked"
    provider: str
    model: str
    width: int
    height: int
    createdAt: str
