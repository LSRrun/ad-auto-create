from .styles import get_style


def generate_ad_copy(
    product_name: str,
    brand: str,
    price: str,
    selling_points: str,
    style_id: str,
) -> dict:
    """Generate predictable copy now; replace this function with an AI call later."""
    style = get_style(style_id)
    points = [point.strip() for point in selling_points.replace("，", ",").split(",") if point.strip()]
    points = points[:3] or ["精工品质", "舒适体验", "轻松打理"]

    headline_prefix = {
        "quiet-luxury": "让日常，更有质感",
        "natural-spa": "在家，收藏一段自然",
        "midnight-tech": "重新定义智能浴室",
    }.get(style_id, "焕新你的浴室体验")

    return {
        "brand": brand.strip() or "MUJING",
        "eyebrow": style["eyebrow"],
        "headline": headline_prefix,
        "productName": product_name.strip(),
        "description": f"{product_name.strip()}，用更克制的设计和更贴心的细节，让每一次使用都成为享受。",
        "price": price.strip() or "到店咨询",
        "features": points,
        "cta": "立即了解",
        "style": style,
    }

