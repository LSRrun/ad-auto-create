from __future__ import annotations

from io import BytesIO
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont, ImageOps

from ..styles import get_style
from .schemas import PageSnapshot


OUTPUT_SIZE = (1024, 1280)
FONT_CANDIDATES = {
    "serif": [
        "/System/Library/Fonts/Supplemental/Songti.ttc",
        "/usr/share/fonts/opentype/noto/NotoSerifCJK-Regular.ttc",
        "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc",
    ],
    "sans": [
        "/System/Library/Fonts/STHeiti Medium.ttc",
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ],
}


def _font(size: int, family: str = "sans") -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    for candidate in FONT_CANDIDATES[family]:
        if Path(candidate).exists():
            return ImageFont.truetype(candidate, size=size)
    return ImageFont.load_default(size=size)


def _hex_color(value: str, fallback: str) -> tuple[int, int, int]:
    try:
        value = value.lstrip("#")
        if len(value) != 6:
            raise ValueError
        return tuple(int(value[index : index + 2], 16) for index in (0, 2, 4))
    except (TypeError, ValueError):
        return _hex_color(fallback, "#000000")


def _fit_background(background_bytes: bytes) -> Image.Image:
    with Image.open(BytesIO(background_bytes)) as source:
        return ImageOps.fit(source.convert("RGB"), OUTPUT_SIZE, method=Image.Resampling.LANCZOS)


def _corner_background(image: Image.Image) -> tuple[tuple[int, int, int], bool]:
    rgb = image.convert("RGB")
    width, height = rgb.size
    inset_x = max(1, min(12, width // 20))
    inset_y = max(1, min(12, height // 20))
    points = [
        rgb.getpixel((inset_x, inset_y)),
        rgb.getpixel((width - inset_x - 1, inset_y)),
        rgb.getpixel((inset_x, height - inset_y - 1)),
        rgb.getpixel((width - inset_x - 1, height - inset_y - 1)),
    ]
    average = tuple(sum(point[channel] for point in points) // len(points) for channel in range(3))
    spread = max(abs(point[channel] - average[channel]) for point in points for channel in range(3))
    return average, spread <= 24


def _extract_product(product_bytes: bytes) -> Image.Image:
    with Image.open(BytesIO(product_bytes)) as source:
        image = ImageOps.exif_transpose(source).convert("RGBA")

    existing_alpha = image.getchannel("A")
    if existing_alpha.getextrema()[0] < 250:
        alpha = existing_alpha
    else:
        background_color, uniform = _corner_background(image)
        if not uniform:
            return image
        rgb = image.convert("RGB")
        background = Image.new("RGB", rgb.size, background_color)
        difference = ImageChops.difference(rgb, background)
        red, green, blue = difference.split()
        strongest = ImageChops.lighter(ImageChops.lighter(red, green), blue)
        alpha = strongest.point(lambda value: 0 if value <= 8 else 255 if value >= 30 else int((value - 8) * 255 / 22))
        alpha = alpha.filter(ImageFilter.GaussianBlur(0.7))
        image.putalpha(alpha)

    bounds = image.getbbox()
    return image.crop(bounds) if bounds else image


def _contain(image: Image.Image, maximum: tuple[int, int]) -> Image.Image:
    copy = image.copy()
    copy.thumbnail(maximum, Image.Resampling.LANCZOS)
    return copy


def _wrap_text(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.ImageFont, max_width: int, max_lines: int) -> list[str]:
    value = text.strip()
    if not value:
        return []
    lines: list[str] = []
    current = ""
    for character in value:
        candidate = current + character
        if current and draw.textlength(candidate, font=font) > max_width:
            if character in "，。！？；：、,.!?;:":
                current = candidate
                continue
            lines.append(current)
            current = character
            if len(lines) == max_lines:
                break
        else:
            current = candidate
    if len(lines) < max_lines and current:
        lines.append(current)
    if sum(len(line) for line in lines) < len(value) and lines:
        last = lines[-1]
        lines[-1] = (last[:-1] + "…") if len(last) > 1 else "…"
    return lines


def _draw_multiline(
    draw: ImageDraw.ImageDraw,
    position: tuple[int, int],
    lines: list[str],
    font: ImageFont.ImageFont,
    fill: tuple[int, int, int] | tuple[int, int, int, int],
    spacing: int,
) -> int:
    x, y = position
    for line in lines:
        draw.text((x, y), line, font=font, fill=fill)
        bbox = draw.textbbox((x, y), line, font=font)
        y = bbox[3] + spacing
    return y


def compose_locked_ad(background_bytes: bytes, product_bytes: bytes, snapshot: PageSnapshot) -> Image.Image:
    base = _fit_background(background_bytes).convert("RGBA")
    style = get_style(snapshot.style_id) or {}
    palette = style.get("palette", {})
    text_color = _hex_color(palette.get("text", "#20211f"), "#20211f")
    accent = _hex_color(palette.get("accent", "#607966"), "#607966")
    surface = _hex_color(palette.get("surface", "#ffffff"), "#ffffff")

    overlay = Image.new("RGBA", OUTPUT_SIZE, (0, 0, 0, 0))
    overlay_draw = ImageDraw.Draw(overlay, "RGBA")
    overlay_draw.rounded_rectangle((48, 48, 976, 1232), radius=18, fill=(*surface, 218))
    overlay_draw.rounded_rectangle((548, 248, 942, 1052), radius=180, fill=(*surface, 205), outline=(*accent, 75), width=2)
    overlay_draw.line((80, 148, 944, 148), fill=(*text_color, 42), width=1)
    base = Image.alpha_composite(base, overlay)

    product = _contain(_extract_product(product_bytes), (420, 610))
    product_x = 745 - product.width // 2
    product_y = 650 - product.height // 2
    shadow_mask = product.getchannel("A").filter(ImageFilter.GaussianBlur(22))
    shadow = Image.new("RGBA", product.size, (18, 20, 18, 0))
    shadow.putalpha(shadow_mask.point(lambda value: int(value * 0.24)))
    base.alpha_composite(shadow, (product_x + 13, product_y + 28))
    base.alpha_composite(product, (product_x, product_y))

    draw = ImageDraw.Draw(base, "RGBA")
    brand_font = _font(27, "serif")
    micro_font = _font(15, "sans")
    eyebrow_font = _font(17, "sans")
    headline_font = _font(58, "serif")
    product_font = _font(25, "serif")
    description_font = _font(19, "sans")
    feature_font = _font(18, "sans")
    price_font = _font(28, "serif")

    brand = snapshot.product.brand.strip() or "MUJING"
    draw.text((82, 91), brand, font=brand_font, fill=text_color)
    collection = "BATHROOM COLLECTION / 2026"
    collection_width = draw.textlength(collection, font=micro_font)
    draw.text((942 - collection_width, 98), collection, font=micro_font, fill=(*text_color, 180))

    eyebrow = snapshot.ad.eyebrow.strip() or style.get("eyebrow", "BATHROOM DESIGN")
    draw.text((84, 246), eyebrow, font=eyebrow_font, fill=accent)
    headline_lines = _wrap_text(draw, snapshot.ad.headline, headline_font, 400, 2)
    cursor_y = _draw_multiline(draw, (82, 287), headline_lines, headline_font, text_color, 14)
    cursor_y += 18
    draw.text((84, cursor_y), snapshot.product.product_name, font=product_font, fill=accent)
    cursor_y += 62

    description_lines = _wrap_text(draw, snapshot.ad.description, description_font, 390, 4)
    cursor_y = _draw_multiline(draw, (84, cursor_y), description_lines, description_font, (*text_color, 190), 12)
    cursor_y += 33

    features = snapshot.ad.features or [item.strip() for item in snapshot.product.selling_points.replace("，", ",").split(",") if item.strip()][:3]
    for feature in features[:3]:
        draw.text((86, cursor_y), "—", font=feature_font, fill=accent)
        draw.text((121, cursor_y), feature[:24], font=feature_font, fill=(*text_color, 220))
        cursor_y += 42

    price = snapshot.product.price.strip().replace("¥", "￥")
    if price:
        draw.text((84, 1052), price, font=price_font, fill=text_color)
    cta = snapshot.ad.cta.strip() or "立即了解"
    draw.text((84, 1128), cta, font=description_font, fill=text_color)
    cta_width = draw.textlength(cta, font=description_font)
    draw.text((105 + cta_width, 1124), "↗", font=product_font, fill=accent)
    draw.line((84, 1162, 118 + cta_width, 1162), fill=accent, width=2)
    draw.text((80, 1195), "01", font=micro_font, fill=(*text_color, 105))
    reconstruction_label = "AI RECONSTRUCTED"
    label_width = draw.textlength(reconstruction_label, font=micro_font)
    draw.text((944 - label_width, 1195), reconstruction_label, font=micro_font, fill=(*text_color, 105))
    return base.convert("RGB")
