import json
from pathlib import Path


DATA_DIR = Path(__file__).resolve().parent.parent / "data"
TEMPLATES_DIR = DATA_DIR / "style_templates"


AD_STYLES = [
    {
        "id": "quiet-luxury",
        "name": "静奢白",
        "description": "大留白与精致排版，适合智能马桶、高端龙头",
        "eyebrow": "QUIET LUXURY",
        "headline": "让日常，更有质感",
        "palette": {"background": "#f3f0ea", "surface": "#ffffff", "text": "#20211f", "accent": "#826b4d"},
        "copy_tone": "克制、高级、简洁，用精准的细节表达质感，避免大声叫卖",
        "headline_limit": 12,
        "visual_direction": "克制的高端静奢风，大面积温暖留白，细腻材质，柔和自然光，精致而安静",
        "aspect_ratio": "4:5",
        "render_mode": "react_builtin",
        "is_builtin": True,
    },
    {
        "id": "natural-spa",
        "name": "自然疗愈",
        "description": "柔和绿色与石材感，适合浴缸、淋浴和浴室柜",
        "eyebrow": "NATURAL RITUAL",
        "headline": "在家，收藏一段自然",
        "palette": {"background": "#dfe7df", "surface": "#f6f4ed", "text": "#24352c", "accent": "#607966"},
        "copy_tone": "自然、舒缓、温暖，具有生活方式和疗愈感",
        "headline_limit": 14,
        "visual_direction": "自然疗愈风，柔和绿色、石材和木质氛围，松弛、干净、具有居家水疗感",
        "aspect_ratio": "4:5",
        "render_mode": "react_builtin",
        "is_builtin": True,
    },
    {
        "id": "midnight-tech",
        "name": "暗夜科技",
        "description": "黑金对比与科技氛围，适合智能镜、数显花洒",
        "eyebrow": "FUTURE OF WATER",
        "headline": "重新定义智能浴室",
        "palette": {"background": "#141718", "surface": "#222728", "text": "#f3f0e8", "accent": "#c9a86a"},
        "copy_tone": "现代、科技、专业，突出智能体验，但不虚构产品功能",
        "headline_limit": 14,
        "visual_direction": "暗夜科技风，黑金对比，克制的光带和现代几何结构，专业、智能、未来感",
        "aspect_ratio": "4:5",
        "render_mode": "react_builtin",
        "is_builtin": True,
    },
]


def _custom_styles() -> list[dict]:
    if not TEMPLATES_DIR.exists():
        return []
    items: list[dict] = []
    for manifest_path in sorted(TEMPLATES_DIR.glob("*/manifest.json")):
        try:
            item = json.loads(manifest_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if isinstance(item, dict) and item.get("id") and item.get("name"):
            items.append(item)
    return sorted(items, key=lambda item: item.get("created_at", ""))


def list_styles() -> list[dict]:
    return [*AD_STYLES, *_custom_styles()]


def get_style(style_id: str) -> dict | None:
    return next((style for style in list_styles() if style["id"] == style_id), None)
