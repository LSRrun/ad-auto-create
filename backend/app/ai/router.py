from fastapi import APIRouter, HTTPException

from ..styles import get_style
from .providers import AI_PROVIDERS
from .schemas import ConnectionRequest, PolishRequest, PolishedCopy
from .service import polish_copy, test_connection

router = APIRouter(prefix="/api/ai", tags=["AI 文案"])


@router.get("/providers")
def list_providers() -> dict:
    return {"items": AI_PROVIDERS}


@router.post("/test-connection")
async def check_connection(body: ConnectionRequest) -> dict:
    return await test_connection(body.config)


@router.post("/polish", response_model=PolishedCopy)
async def polish(body: PolishRequest) -> PolishedCopy:
    if not get_style(body.style_id):
        raise HTTPException(status_code=400, detail="未知的广告样式")
    return await polish_copy(body)

