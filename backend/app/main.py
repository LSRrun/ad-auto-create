from pathlib import Path
from uuid import uuid4

from fastapi import FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from .generator import generate_ad_copy
from .styles import AD_STYLES, get_style

BASE_DIR = Path(__file__).resolve().parent.parent
UPLOAD_DIR = BASE_DIR / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)
ALLOWED_IMAGE_TYPES = {"image/jpeg": ".jpg", "image/png": ".png", "image/webp": ".webp"}
MAX_IMAGE_SIZE = 8 * 1024 * 1024

app = FastAPI(title="沐境·卫浴广告生成器 API", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")


@app.get("/api/health")
def health() -> dict:
    return {"status": "ok"}


@app.get("/api/styles")
def list_styles() -> dict:
    return {"items": AD_STYLES}


@app.post("/api/ads/generate")
async def generate_ad(
    request: Request,
    product_name: str = Form(..., min_length=1, max_length=80),
    style_id: str = Form(...),
    selling_points: str = Form(""),
    brand: str = Form(""),
    price: str = Form(""),
    image: UploadFile | None = File(None),
) -> dict:
    if not get_style(style_id):
        raise HTTPException(status_code=400, detail="未知的广告样式")

    image_url = None
    if image:
        extension = ALLOWED_IMAGE_TYPES.get(image.content_type or "")
        if not extension:
            raise HTTPException(status_code=400, detail="仅支持 JPG、PNG 或 WebP 图片")
        content = await image.read(MAX_IMAGE_SIZE + 1)
        if len(content) > MAX_IMAGE_SIZE:
            raise HTTPException(status_code=400, detail="图片不能超过 8MB")
        filename = f"{uuid4().hex}{extension}"
        (UPLOAD_DIR / filename).write_bytes(content)
        image_url = f"{str(request.base_url).rstrip('/')}/uploads/{filename}"

    ad = generate_ad_copy(product_name, brand, price, selling_points, style_id)
    return {"id": uuid4().hex, "imageUrl": image_url, **ad}

