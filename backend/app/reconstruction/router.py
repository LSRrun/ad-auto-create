from pathlib import Path

from fastapi import APIRouter, File, Form, HTTPException, Request, UploadFile
from pydantic import ValidationError

from ..styles import get_style
from .providers import IMAGE_PROVIDERS
from .schemas import ImageConnectionRequest, ImageModelConfig, PageSnapshot, ReconstructionResult
from .service import reconstruct_ad, test_image_connection


router = APIRouter(prefix="/api/reconstruction", tags=["AI 图片重构"])
OUTPUT_DIR = Path(__file__).resolve().parents[2] / "uploads" / "reconstructions"
ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp"}
MAX_IMAGE_SIZE = 8 * 1024 * 1024


@router.get("/providers")
def list_image_providers() -> dict:
    return {"items": IMAGE_PROVIDERS}


@router.post("/test-connection")
async def check_image_connection(body: ImageConnectionRequest) -> dict:
    return await test_image_connection(body.config)


def _parse_form_json(model_type, value: str, label: str):
    try:
        return model_type.model_validate_json(value)
    except ValidationError as exc:
        raise HTTPException(status_code=400, detail=f"{label}格式不正确") from exc


@router.post("/generate", response_model=ReconstructionResult)
async def generate_reconstruction(
    request: Request,
    config: str = Form(...),
    snapshot: str = Form(...),
    product_image: UploadFile = File(...),
) -> ReconstructionResult:
    parsed_config = _parse_form_json(ImageModelConfig, config, "图片模型配置")
    parsed_snapshot = _parse_form_json(PageSnapshot, snapshot, "广告页面快照")
    if not get_style(parsed_snapshot.style_id):
        raise HTTPException(status_code=400, detail="未知的广告样式")
    if product_image.content_type not in ALLOWED_IMAGE_TYPES:
        raise HTTPException(status_code=400, detail="商品图片仅支持 JPG、PNG 或 WebP")
    content = await product_image.read(MAX_IMAGE_SIZE + 1)
    if len(content) > MAX_IMAGE_SIZE:
        raise HTTPException(status_code=400, detail="商品图片不能超过 8MB")
    if not content:
        raise HTTPException(status_code=400, detail="商品图片不能为空")

    result = await reconstruct_ad(
        parsed_config,
        parsed_snapshot,
        content,
        product_image.content_type,
        OUTPUT_DIR,
        str(request.base_url),
    )
    return ReconstructionResult.model_validate(result)
