from typing import Literal

from pydantic import BaseModel, Field, field_validator, model_validator


StyleField = Literal[
    "brand",
    "eyebrow",
    "headline",
    "productName",
    "productImage",
    "description",
    "price",
    "feature1",
    "feature2",
    "feature3",
    "cta",
]


class Palette(BaseModel):
    background: str = "#F3F0EA"
    surface: str = "#FFFFFF"
    text: str = "#20211F"
    accent: str = "#826B4D"

    @field_validator("background", "surface", "text", "accent")
    @classmethod
    def validate_hex(cls, value: str) -> str:
        cleaned = value.strip().upper()
        if len(cleaned) != 7 or not cleaned.startswith("#"):
            raise ValueError("颜色必须使用 #RRGGBB 格式")
        try:
            int(cleaned[1:], 16)
        except ValueError as exc:
            raise ValueError("颜色必须使用 #RRGGBB 格式") from exc
        return cleaned


class DraftUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=40)
    description: str | None = Field(default=None, min_length=1, max_length=120)
    eyebrow: str | None = Field(default=None, min_length=1, max_length=40)
    headline: str | None = Field(default=None, min_length=1, max_length=28)
    copy_tone: str | None = Field(default=None, min_length=1, max_length=300)
    headline_limit: int | None = Field(default=None, ge=8, le=28)
    visual_direction: str | None = Field(default=None, min_length=1, max_length=800)
    aspect_ratio: Literal["1:1", "4:5", "3:4", "16:9", "9:16"] | None = None
    palette: Palette | None = None
    bindings: dict[StyleField, str] | None = None

    @field_validator("name", "description", "eyebrow", "headline", "copy_tone", "visual_direction")
    @classmethod
    def clean_text(cls, value: str | None) -> str | None:
        return value.strip() if value is not None else None

    @model_validator(mode="after")
    def unique_binding_targets(self):
        if self.bindings and len(set(self.bindings.values())) != len(self.bindings):
            raise ValueError("同一个 HTML 元素不能同时映射多个广告字段")
        return self


class Box(BaseModel):
    x: int = Field(ge=0, le=1000)
    y: int = Field(ge=0, le=1000)
    width: int = Field(gt=0, le=1000)
    height: int = Field(gt=0, le=1000)

    @model_validator(mode="after")
    def inside_canvas(self):
        if self.x + self.width > 1000 or self.y + self.height > 1000:
            raise ValueError("容器不能超出画布")
        return self


class ProductSlot(Box):
    fit: Literal["contain", "cover"] = "contain"


class TextSlot(Box):
    field: StyleField
    font_size: int = Field(default=36, ge=10, le=120)
    weight: int = Field(default=500, ge=300, le=800)
    align: Literal["left", "center", "right"] = "left"
    color: str = "#20211F"
    max_lines: int = Field(default=2, ge=1, le=8)
    uppercase: bool = False

    _validate_color = field_validator("color")(Palette.validate_hex.__func__)


class Decoration(Box):
    type: Literal["rectangle", "circle", "line"]
    fill: str = "#00000000"
    stroke: str = "#00000000"
    radius: int = Field(default=0, ge=0, le=500)

    @field_validator("fill", "stroke")
    @classmethod
    def validate_color(cls, value: str) -> str:
        cleaned = value.strip().upper()
        if len(cleaned) not in {7, 9} or not cleaned.startswith("#"):
            raise ValueError("图形颜色格式不正确")
        try:
            int(cleaned[1:], 16)
        except ValueError as exc:
            raise ValueError("图形颜色格式不正确") from exc
        return cleaned


class ReferenceStyleSpec(BaseModel):
    name: str = Field(min_length=1, max_length=40)
    description: str = Field(min_length=1, max_length=120)
    eyebrow: str = Field(default="CURATED STYLE", min_length=1, max_length=40)
    headline: str = Field(default="让好设计，被看见", min_length=1, max_length=28)
    aspect_ratio: Literal["1:1", "4:5", "3:4", "16:9", "9:16"] = "4:5"
    palette: Palette
    product_slot: ProductSlot
    text_slots: list[TextSlot] = Field(min_length=2, max_length=12)
    decorations: list[Decoration] = Field(default_factory=list, max_length=12)
    copy_tone: str = Field(min_length=1, max_length=300)
    headline_limit: int = Field(default=16, ge=8, le=28)
    visual_direction: str = Field(min_length=1, max_length=800)

    @model_validator(mode="after")
    def required_slots(self):
        fields = {slot.field for slot in self.text_slots}
        if "headline" not in fields or "productName" not in fields:
            raise ValueError("布局必须包含 headline 和 productName")
        return self
