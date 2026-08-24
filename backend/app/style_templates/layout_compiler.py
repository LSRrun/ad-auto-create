import html

from .schemas import ReferenceStyleSpec


DEFAULT_VALUES = {
    "brand": "MUJING",
    "eyebrow": "CURATED STYLE",
    "headline": "让好设计，被看见",
    "productName": "智能卫浴新品",
    "description": "用精准的细节与舒适体验，为日常空间带来更完整的质感。",
    "price": "¥1,299 起",
    "feature1": "精工品质",
    "feature2": "舒适体验",
    "feature3": "简洁设计",
    "cta": "立即了解",
}


def _box_style(item) -> str:
    return (
        f"left:{item.x / 10:.2f}%;top:{item.y / 10:.2f}%;"
        f"width:{item.width / 10:.2f}%;height:{item.height / 10:.2f}%;"
    )


def _ratio_value(value: str) -> str:
    left, right = value.split(":", 1)
    return f"{left} / {right}"


def compile_reference_style(spec: ReferenceStyleSpec) -> tuple[str, dict[str, str]]:
    bindings: dict[str, str] = {"productImage": "slot-product-image"}
    decoration_html = []
    for index, decoration in enumerate(spec.decorations, start=1):
        node_id = f"decoration-{index}"
        border_radius = "50%" if decoration.type == "circle" else f"{decoration.radius}px"
        height = "1px" if decoration.type == "line" else f"{decoration.height / 10:.2f}%"
        decoration_html.append(
            f'<span class="template-decoration" data-template-node="{node_id}" '
            f'style="{_box_style(decoration)}height:{height};background:{decoration.fill};'
            f'border:1px solid {decoration.stroke};border-radius:{border_radius}"></span>'
        )

    slot_html = []
    for index, slot in enumerate(spec.text_slots, start=1):
        node_id = f"slot-{slot.field}-{index}"
        bindings.setdefault(slot.field, node_id)
        value = spec.headline if slot.field == "headline" else spec.eyebrow if slot.field == "eyebrow" else DEFAULT_VALUES.get(slot.field, slot.field)
        transform = "uppercase" if slot.uppercase else "none"
        line_height = max(int(slot.font_size * 1.25), slot.font_size + 4)
        slot_html.append(
            f'<div class="template-text template-{slot.field}" data-template-node="{node_id}" '
            f'data-ad-field="{slot.field}" style="{_box_style(slot)}font-size:{slot.font_size}px;'
            f'font-weight:{slot.weight};line-height:{line_height}px;text-align:{slot.align};color:{slot.color};'
            f'text-transform:{transform};-webkit-line-clamp:{slot.max_lines}">{html.escape(value)}</div>'
        )

    palette = spec.palette
    template = f"""
<article class="imported-ad" style="--template-ratio:{_ratio_value(spec.aspect_ratio)};--template-bg:{palette.background};--template-surface:{palette.surface};--template-text:{palette.text};--template-accent:{palette.accent}">
  {''.join(decoration_html)}
  <div class="template-product" data-template-node="slot-product-image" data-ad-field="productImage" style="{_box_style(spec.product_slot)}background:{palette.surface}">
    <img src="{{{{productImage}}}}" alt="{{{{productName}}}}" style="object-fit:{spec.product_slot.fit}">
    <span class="template-product-placeholder">上传商品图</span>
  </div>
  {''.join(slot_html)}
</article>
<style>
  *{{box-sizing:border-box}}
  html,body{{margin:0;width:100%;height:100%;overflow:hidden;background:transparent}}
  body{{display:grid;place-items:center;font-family:Arial,"PingFang SC","Microsoft YaHei",sans-serif;color:var(--template-text)}}
  .imported-ad{{position:relative;width:100%;aspect-ratio:var(--template-ratio);overflow:hidden;background:var(--template-bg)}}
  .template-decoration{{position:absolute;pointer-events:none}}
  .template-product{{position:absolute;display:grid;place-items:center;overflow:hidden}}
  .template-product img{{position:relative;z-index:2;width:100%;height:100%;display:block}}
  .template-product img:not([src]),.template-product img[src=""]{{display:none}}
  .template-product-placeholder{{position:absolute;z-index:1;color:var(--template-accent);font-size:18px;letter-spacing:.08em}}
  .template-product:has(img[src]:not([src=""])) .template-product-placeholder{{display:none}}
  .template-text{{position:absolute;z-index:3;display:-webkit-box;-webkit-box-orient:vertical;overflow:hidden;overflow-wrap:anywhere}}
</style>
""".strip()
    return template, bindings
