AD_STYLES = [
    {
        "id": "quiet-luxury",
        "name": "静奢白",
        "description": "大留白与精致排版，适合智能马桶、高端龙头",
        "eyebrow": "QUIET LUXURY",
        "palette": {"background": "#f3f0ea", "surface": "#ffffff", "text": "#20211f", "accent": "#826b4d"},
    },
    {
        "id": "natural-spa",
        "name": "自然疗愈",
        "description": "柔和绿色与石材感，适合浴缸、淋浴和浴室柜",
        "eyebrow": "NATURAL RITUAL",
        "palette": {"background": "#dfe7df", "surface": "#f6f4ed", "text": "#24352c", "accent": "#607966"},
    },
    {
        "id": "midnight-tech",
        "name": "暗夜科技",
        "description": "黑金对比与科技氛围，适合智能镜、数显花洒",
        "eyebrow": "FUTURE OF WATER",
        "palette": {"background": "#141718", "surface": "#222728", "text": "#f3f0e8", "accent": "#c9a86a"},
    },
]


def get_style(style_id: str) -> dict | None:
    return next((style for style in AD_STYLES if style["id"] == style_id), None)

