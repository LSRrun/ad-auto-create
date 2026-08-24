from datetime import datetime, timezone
from pathlib import Path

from fastapi import HTTPException

from ..ai.schemas import ModelConfig
from ..styles import list_styles
from .html_sanitizer import apply_bindings, sanitize_html
from .layout_compiler import compile_reference_style
from .reference_analyzer import analyze_reference
from .repository import (
    create_draft,
    load_draft,
    load_published,
    publish_draft,
    read_draft_html,
    save_draft,
)
from .schemas import DraftUpdate, Palette


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _draft_payload(manifest: dict, template_html: str) -> dict:
    return {**manifest, "templateHtml": template_html}


def import_html_template(filename: str, content: bytes) -> dict:
    if not content:
        raise HTTPException(status_code=400, detail="HTML 文件不能为空")
    if len(content) > 1024 * 1024:
        raise HTTPException(status_code=400, detail="HTML 文件不能超过 1 MB")
    if Path(filename).suffix.lower() not in {".html", ".htm"}:
        raise HTTPException(status_code=400, detail="请上传 .html 文件")
    try:
        source = content.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise HTTPException(status_code=400, detail="HTML 文件必须使用 UTF-8 编码") from exc
    sanitized = sanitize_html(source)
    stem = Path(filename).stem.strip()[:30] or "导入风格"
    timestamp = _now()
    manifest = {
        "schema_version": 1,
        "name": stem,
        "description": "从 HTML 文件导入的可复用广告风格",
        "source_type": "html",
        "render_mode": "sandbox_html",
        "aspect_ratio": "4:5",
        "bindings": sanitized.bindings,
        "palette": Palette.model_validate(sanitized.palette).model_dump(),
        "eyebrow": "IMPORTED TEMPLATE",
        "headline": "让好设计，被看见",
        "copy_tone": "简洁、准确、符合当前广告版式的品牌文案",
        "headline_limit": 16,
        "visual_direction": "延续导入 HTML 的配色、布局、留白和文字层级",
        "nodes": sanitized.nodes,
        "warnings": sanitized.warnings,
        "created_at": timestamp,
        "updated_at": timestamp,
    }
    draft = create_draft(manifest, sanitized.html, "source.html", content)
    return _draft_payload(draft, sanitized.html)


async def import_reference_template(
    filename: str,
    content: bytes,
    mime_type: str,
    config: ModelConfig,
    user_direction: str,
) -> dict:
    spec = await analyze_reference(config, content, mime_type, user_direction)
    template_html, bindings = compile_reference_style(spec)
    timestamp = _now()
    manifest = {
        "schema_version": 1,
        "name": spec.name,
        "description": spec.description,
        "source_type": "reference_image",
        "render_mode": "sandbox_html",
        "aspect_ratio": spec.aspect_ratio,
        "bindings": bindings,
        "palette": spec.palette.model_dump(),
        "eyebrow": spec.eyebrow,
        "headline": spec.headline,
        "copy_tone": spec.copy_tone,
        "headline_limit": spec.headline_limit,
        "visual_direction": spec.visual_direction,
        "nodes": [],
        "warnings": ["参考图为 AI 近似还原，请在发布前检查文字溢出和商品位置"],
        "created_at": timestamp,
        "updated_at": timestamp,
    }
    extension = {"image/png": ".png", "image/jpeg": ".jpg", "image/webp": ".webp"}[mime_type]
    draft = create_draft(manifest, template_html, f"reference{extension}", content)
    return _draft_payload(draft, template_html)


def get_draft(draft_id: str) -> dict:
    manifest, _ = load_draft(draft_id)
    return _draft_payload(manifest, read_draft_html(draft_id))


def update_draft(draft_id: str, update: DraftUpdate) -> dict:
    manifest, _ = load_draft(draft_id)
    changes = update.model_dump(exclude_none=True)
    template_html = read_draft_html(draft_id)
    if "bindings" in changes:
        template_html = apply_bindings(template_html, changes["bindings"])
    changes["updated_at"] = _now()
    updated = save_draft(draft_id, changes, template_html)
    return _draft_payload(updated, template_html)


def publish(draft_id: str) -> dict:
    manifest, _ = load_draft(draft_id)
    bindings = manifest.get("bindings") or {}
    missing = [field for field in ("headline", "productImage") if field not in bindings]
    if missing:
        labels = {"headline": "广告大标题", "productImage": "商品图"}
        raise HTTPException(status_code=400, detail=f"发布前请映射：{'、'.join(labels[item] for item in missing)}")
    normalized_name = str(manifest.get("name", "")).strip().casefold()
    if not normalized_name:
        raise HTTPException(status_code=400, detail="请填写风格名称")
    if any(str(item.get("name", "")).strip().casefold() == normalized_name for item in list_styles()):
        raise HTTPException(status_code=400, detail="已存在同名广告风格")
    template_html = apply_bindings(read_draft_html(draft_id), bindings)
    final_manifest = {**manifest, "updated_at": _now()}
    return publish_draft(draft_id, final_manifest, template_html)


def get_render_source(style_id: str) -> dict:
    manifest, template_html = load_published(style_id)
    return {
        "id": manifest["id"],
        "aspectRatio": manifest.get("aspect_ratio", "4:5"),
        "bindings": manifest.get("bindings", {}),
        "templateHtml": template_html,
    }
