import json
import re
from datetime import datetime, timezone
from pathlib import Path
from threading import Lock
from uuid import uuid4

from fastapi import HTTPException


BASE_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = BASE_DIR / "data" / "media_plans"
JOBS_DIR = DATA_DIR / "jobs"
PLANS_DIR = DATA_DIR / "plans"
_LOCK = Lock()
_SAFE_JOB_ID = re.compile(r"^job-[a-f0-9]{12}$")
_SAFE_PLAN_ID = re.compile(r"^plan-[a-f0-9]{12}$")


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def ensure_directories() -> None:
    JOBS_DIR.mkdir(parents=True, exist_ok=True)
    PLANS_DIR.mkdir(parents=True, exist_ok=True)


def new_job_id() -> str:
    return f"job-{uuid4().hex[:12]}"


def new_plan_id() -> str:
    return f"plan-{uuid4().hex[:12]}"


def _path(root: Path, item_id: str, pattern: re.Pattern[str]) -> Path:
    if not pattern.fullmatch(item_id):
        raise HTTPException(status_code=404, detail="投放方案不存在")
    return root / f"{item_id}.json"


def _atomic_write(path: Path, data: dict) -> None:
    temporary = path.with_suffix(".tmp")
    temporary.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    temporary.replace(path)


def create_job(payload: dict) -> dict:
    ensure_directories()
    timestamp = now_iso()
    job = {
        "id": new_job_id(),
        "status": "queued",
        "stage": "queued",
        "progress": 0,
        "message": "投放策划任务已创建",
        "plan_id": None,
        "error": None,
        "source_count": 0,
        "official_source_count": 0,
        "created_at": timestamp,
        "updated_at": timestamp,
        "request_snapshot": payload,
    }
    with _LOCK:
        _atomic_write(_path(JOBS_DIR, job["id"], _SAFE_JOB_ID), job)
    return job


def update_job(job_id: str, **changes) -> dict:
    job = load_job(job_id, include_snapshot=True)
    job.update(changes)
    job["updated_at"] = now_iso()
    with _LOCK:
        _atomic_write(_path(JOBS_DIR, job_id, _SAFE_JOB_ID), job)
    return job


def load_job(job_id: str, include_snapshot: bool = False) -> dict:
    ensure_directories()
    try:
        job = json.loads(_path(JOBS_DIR, job_id, _SAFE_JOB_ID).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise HTTPException(status_code=404, detail="投放策划任务不存在") from exc
    if not include_snapshot:
        job.pop("request_snapshot", None)
    return job


def save_plan(plan: dict) -> dict:
    ensure_directories()
    plan_id = plan.get("id") or new_plan_id()
    saved = {**plan, "id": plan_id, "updated_at": now_iso()}
    with _LOCK:
        _atomic_write(_path(PLANS_DIR, plan_id, _SAFE_PLAN_ID), saved)
    return saved


def load_plan(plan_id: str) -> dict:
    ensure_directories()
    try:
        return json.loads(_path(PLANS_DIR, plan_id, _SAFE_PLAN_ID).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise HTTPException(status_code=404, detail="投放方案不存在") from exc

