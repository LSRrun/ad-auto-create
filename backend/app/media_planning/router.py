import asyncio
import json

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from fastapi.responses import JSONResponse, PlainTextResponse
from pydantic import ValidationError

from .repository import create_job, update_job
from .schemas import CreateMediaPlanRequest, MediaPlan
from .service import export_markdown, get_job, get_plan, recalculate_saved_plan, replace_plan, run_job


router = APIRouter(prefix="/api/media-plans", tags=["AI 投放策划"])
MAX_CREATIVE_IMAGE_SIZE = 10 * 1024 * 1024
ALLOWED_IMAGES = {"image/jpeg", "image/png", "image/webp"}
_RUNNING_TASKS: set[asyncio.Task] = set()


@router.post("/jobs", status_code=202)
async def create_media_plan_job(
    payload: str = Form(...),
    creative_image: UploadFile | None = File(None),
) -> dict:
    try:
        request = CreateMediaPlanRequest.model_validate(json.loads(payload))
    except (json.JSONDecodeError, ValidationError) as exc:
        raise HTTPException(status_code=400, detail="投放策划参数不完整或格式不正确") from exc
    image = None
    mime_type = None
    if creative_image:
        if creative_image.content_type not in ALLOWED_IMAGES:
            raise HTTPException(status_code=400, detail="广告图仅支持 JPG、PNG 或 WebP")
        image = await creative_image.read(MAX_CREATIVE_IMAGE_SIZE + 1)
        if len(image) > MAX_CREATIVE_IMAGE_SIZE:
            raise HTTPException(status_code=400, detail="广告图不能超过 10 MB")
        mime_type = creative_image.content_type
    persisted_request = request.model_dump(exclude={"ai_config"})
    job = create_job(persisted_request)
    task = asyncio.create_task(run_job(job["id"], request, image, mime_type))
    _RUNNING_TASKS.add(task)
    task.add_done_callback(_RUNNING_TASKS.discard)
    job.pop("request_snapshot", None)
    return job


@router.get("/jobs/{job_id}")
def read_job(job_id: str) -> dict:
    return get_job(job_id)


@router.post("/jobs/{job_id}/cancel")
def cancel_job(job_id: str) -> dict:
    job = get_job(job_id)
    if job["status"] in {"completed", "failed"}:
        return job
    return update_job(job_id, status="cancelled", stage="cancelled", message="任务已取消")


@router.get("/{plan_id}")
def read_plan(plan_id: str) -> dict:
    return get_plan(plan_id).model_dump()


@router.patch("/{plan_id}")
def update_plan(plan_id: str, body: MediaPlan) -> dict:
    return replace_plan(plan_id, body).model_dump()


@router.post("/{plan_id}/recalculate")
def recalculate_plan(plan_id: str) -> dict:
    return recalculate_saved_plan(plan_id).model_dump()


@router.get("/{plan_id}/export")
def export_plan(plan_id: str, format: str = "markdown"):
    plan = get_plan(plan_id)
    if format == "json":
        return JSONResponse(
            plan.model_dump(),
            headers={"Content-Disposition": f'attachment; filename="{plan.id}.json"'},
        )
    if format not in {"markdown", "md"}:
        raise HTTPException(status_code=400, detail="当前仅支持 JSON 或 Markdown 导出")
    return PlainTextResponse(
        export_markdown(plan),
        media_type="text/markdown; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{plan.id}.md"'},
    )
