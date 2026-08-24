import io
import json

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from PIL import Image, UnidentifiedImageError
from pydantic import ValidationError

from ..ai.schemas import ModelConfig
from .schemas import DraftUpdate
from .service import (
    get_draft,
    get_render_source,
    import_html_template,
    import_reference_template,
    publish,
    update_draft,
)


router = APIRouter(prefix="/api/style-templates", tags=["广告风格模板"])
HTML_LIMIT = 1024 * 1024
IMAGE_LIMIT = 10 * 1024 * 1024
ALLOWED_IMAGES = {"image/jpeg", "image/png", "image/webp"}


@router.post("/drafts/html")
async def create_html_draft(file: UploadFile = File(...)) -> dict:
    content = await file.read(HTML_LIMIT + 1)
    return import_html_template(file.filename or "template.html", content)


@router.post("/drafts/reference")
async def create_reference_draft(
    file: UploadFile = File(...),
    analysis_config: str = Form(...),
    user_direction: str = Form(""),
) -> dict:
    if file.content_type not in ALLOWED_IMAGES:
        raise HTTPException(status_code=400, detail="参考图仅支持 JPG、PNG 或 WebP")
    content = await file.read(IMAGE_LIMIT + 1)
    if not content:
        raise HTTPException(status_code=400, detail="参考图不能为空")
    if len(content) > IMAGE_LIMIT:
        raise HTTPException(status_code=400, detail="参考图不能超过 10 MB")
    try:
        with Image.open(io.BytesIO(content)) as image:
            image.verify()
    except (UnidentifiedImageError, OSError) as exc:
        raise HTTPException(status_code=400, detail="参考图内容无法解码") from exc
    try:
        config = ModelConfig.model_validate(json.loads(analysis_config))
    except (json.JSONDecodeError, ValidationError) as exc:
        raise HTTPException(status_code=400, detail="视觉分析模型配置格式不正确") from exc
    if len(user_direction.strip()) > 500:
        raise HTTPException(status_code=400, detail="风格分析要求不能超过 500 个字符")
    return await import_reference_template(
        file.filename or "reference.png",
        content,
        file.content_type,
        config,
        user_direction,
    )


@router.get("/drafts/{draft_id}")
def read_draft(draft_id: str) -> dict:
    return get_draft(draft_id)


@router.patch("/drafts/{draft_id}")
def patch_draft(draft_id: str, body: DraftUpdate) -> dict:
    return update_draft(draft_id, body)


@router.post("/drafts/{draft_id}/publish", status_code=201)
def publish_template(draft_id: str) -> dict:
    return publish(draft_id)


@router.get("/{style_id}/render-source")
def render_source(style_id: str) -> dict:
    return get_render_source(style_id)
