import json
import re
import shutil
from pathlib import Path
from threading import Lock
from uuid import uuid4

from fastapi import HTTPException


BASE_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = BASE_DIR / "data"
DRAFTS_DIR = DATA_DIR / "style_template_drafts"
TEMPLATES_DIR = DATA_DIR / "style_templates"
_WRITE_LOCK = Lock()
_SAFE_ID = re.compile(r"^(?:draft|custom)-[a-f0-9]{12}$")


def ensure_directories() -> None:
    DRAFTS_DIR.mkdir(parents=True, exist_ok=True)
    TEMPLATES_DIR.mkdir(parents=True, exist_ok=True)


def new_draft_id() -> str:
    return f"draft-{uuid4().hex[:12]}"


def new_style_id() -> str:
    return f"custom-{uuid4().hex[:12]}"


def _safe_dir(root: Path, item_id: str) -> Path:
    if not _SAFE_ID.fullmatch(item_id):
        raise HTTPException(status_code=404, detail="模板不存在")
    return root / item_id


def _write_json(path: Path, data: dict) -> None:
    temporary = path.with_suffix(".tmp")
    temporary.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    temporary.replace(path)


def create_draft(manifest: dict, template_html: str, source_name: str, source_content: bytes) -> dict:
    ensure_directories()
    draft_id = new_draft_id()
    manifest = {**manifest, "draft_id": draft_id, "status": "draft"}
    with _WRITE_LOCK:
        directory = _safe_dir(DRAFTS_DIR, draft_id)
        directory.mkdir()
        (directory / "template.html").write_text(template_html, encoding="utf-8")
        (directory / source_name).write_bytes(source_content)
        _write_json(directory / "manifest.json", manifest)
    return manifest


def load_draft(draft_id: str) -> tuple[dict, Path]:
    directory = _safe_dir(DRAFTS_DIR, draft_id)
    manifest_path = directory / "manifest.json"
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise HTTPException(status_code=404, detail="模板草稿不存在") from exc
    return manifest, directory


def save_draft(draft_id: str, manifest: dict, template_html: str | None = None) -> dict:
    current, directory = load_draft(draft_id)
    updated = {**current, **manifest, "draft_id": draft_id, "status": "draft"}
    with _WRITE_LOCK:
        if template_html is not None:
            (directory / "template.html").write_text(template_html, encoding="utf-8")
        _write_json(directory / "manifest.json", updated)
    return updated


def read_draft_html(draft_id: str) -> str:
    _, directory = load_draft(draft_id)
    try:
        return (directory / "template.html").read_text(encoding="utf-8")
    except OSError as exc:
        raise HTTPException(status_code=500, detail="模板草稿内容缺失") from exc


def publish_draft(draft_id: str, manifest: dict, template_html: str) -> dict:
    _, source_dir = load_draft(draft_id)
    ensure_directories()
    style_id = new_style_id()
    final_manifest = {
        key: value
        for key, value in manifest.items()
        if key not in {"draft_id", "status", "warnings", "nodes"}
    }
    final_manifest.update({"id": style_id, "status": "published", "is_builtin": False})
    temp_dir = TEMPLATES_DIR / f".{style_id}.tmp"
    final_dir = _safe_dir(TEMPLATES_DIR, style_id)
    with _WRITE_LOCK:
        if temp_dir.exists():
            shutil.rmtree(temp_dir)
        temp_dir.mkdir(parents=True)
        (temp_dir / "template.html").write_text(template_html, encoding="utf-8")
        for source_name in ("source.html", "reference.png", "reference.jpg", "reference.webp"):
            source = source_dir / source_name
            if source.exists():
                shutil.copy2(source, temp_dir / source.name)
        _write_json(temp_dir / "manifest.json", final_manifest)
        temp_dir.replace(final_dir)
    return final_manifest


def load_published(style_id: str) -> tuple[dict, str]:
    directory = _safe_dir(TEMPLATES_DIR, style_id)
    try:
        manifest = json.loads((directory / "manifest.json").read_text(encoding="utf-8"))
        template_html = (directory / "template.html").read_text(encoding="utf-8")
    except (OSError, json.JSONDecodeError) as exc:
        raise HTTPException(status_code=404, detail="风格模板不存在") from exc
    return manifest, template_html
