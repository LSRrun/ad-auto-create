import base64
import binascii
import json
from datetime import datetime
from io import BytesIO
from pathlib import Path
from urllib.parse import urlparse
from uuid import uuid4

import httpx
from fastapi import HTTPException
from PIL import Image, ImageOps, UnidentifiedImageError

from .prompts import build_reconstruction_prompt
from .providers import (
    dashscope_generation_url,
    dashscope_models_url,
    image_edits_url,
    is_dashscope_wan,
    models_url,
)
from .schemas import ImageModelConfig, PageSnapshot


REQUEST_TIMEOUT = httpx.Timeout(120.0, connect=15.0)
MAX_GENERATED_IMAGE_SIZE = 30 * 1024 * 1024


def _headers(config: ImageModelConfig) -> dict[str, str]:
    return {"Authorization": f"Bearer {config.api_key.strip()}"}


def _provider_error(response: httpx.Response) -> HTTPException:
    messages = {
        400: "图片模型拒绝了请求，请检查模型名称、图片格式和 Base URL",
        401: "图片模型 API Key 无效或已过期",
        403: "当前 API Key 没有使用该图片模型的权限",
        404: "未找到图片模型接口，请检查 Base URL 和模型名称",
        429: "图片模型请求过于频繁、额度不足或达到用量限制",
    }
    return HTTPException(status_code=400, detail=messages.get(response.status_code, f"图片模型请求失败（{response.status_code}）"))


def validate_product_image(content: bytes) -> None:
    try:
        with Image.open(BytesIO(content)) as image:
            image.verify()
    except (UnidentifiedImageError, OSError) as exc:
        raise HTTPException(status_code=400, detail="商品图片内容无效") from exc


async def test_image_connection(config: ImageModelConfig) -> dict:
    if not config.api_key.strip():
        raise HTTPException(status_code=400, detail="请填写图片模型 API Key")
    is_wan = is_dashscope_wan(config.model, config.base_url)
    url = dashscope_models_url(config.base_url) if is_wan else models_url(config.base_url)
    try:
        async with httpx.AsyncClient(timeout=20.0, follow_redirects=False) as client:
            response = await client.get(url, headers=_headers(config))
    except httpx.TimeoutException as exc:
        raise HTTPException(status_code=504, detail="图片模型连接测试超时") from exc
    except httpx.RequestError as exc:
        raise HTTPException(status_code=502, detail="无法连接图片模型服务，请检查 Base URL 和网络") from exc
    if not response.is_success:
        raise _provider_error(response)
    if is_wan:
        return {"success": True, "message": "百炼鉴权成功；AI 重构将自动使用万相原生图片接口"}
    return {"success": True, "message": "连接成功；实际重构时会调用图片编辑接口并可能产生费用"}


async def _request_openai_ad(config: ImageModelConfig, product_bytes: bytes, content_type: str, prompt: str) -> bytes:
    data = {
        "model": config.model,
        "prompt": prompt,
        "size": config.size,
        "quality": config.quality,
        "output_format": "png",
        "n": "1",
    }
    files = {"image[]": ("product-reference.png", product_bytes, content_type)}
    try:
        async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT, follow_redirects=False) as client:
            response = await client.post(image_edits_url(config.base_url), headers=_headers(config), data=data, files=files)
    except httpx.TimeoutException as exc:
        raise HTTPException(status_code=504, detail="图片重构超时，请稍后重试或降低输出质量") from exc
    except httpx.RequestError as exc:
        raise HTTPException(status_code=502, detail="无法连接图片模型服务，请检查 Base URL 和网络") from exc
    if not response.is_success:
        raise _provider_error(response)
    try:
        payload = response.json()
        item = payload["data"][0]
    except (json.JSONDecodeError, KeyError, IndexError, TypeError) as exc:
        raise HTTPException(status_code=502, detail="图片模型返回了无效响应") from exc

    encoded = item.get("b64_json") if isinstance(item, dict) else None
    if encoded:
        try:
            return base64.b64decode(encoded, validate=True)
        except (binascii.Error, ValueError) as exc:
            raise HTTPException(status_code=502, detail="图片模型返回的图片无法解析") from exc

    # The OpenAI Image API returns base64 for GPT Image models. Do not follow an
    # arbitrary URL supplied by a custom provider, which would create an SSRF path.
    raise HTTPException(status_code=502, detail="图片模型没有返回可用的 Base64 图片")


def _wan_input_data_url(product_bytes: bytes) -> str:
    """Wan2.7 does not accept PNG alpha channels, so flatten every input to RGB."""
    try:
        with Image.open(BytesIO(product_bytes)) as source:
            image = ImageOps.exif_transpose(source).convert("RGBA")
            width, height = image.size
            if max(width / height, height / width) > 8:
                raise HTTPException(status_code=400, detail="百炼要求商品图片宽高比在 1:8 到 8:1 之间")
            scale = max(240 / width, 240 / height, 1)
            if max(width * scale, height * scale) > 8000:
                scale = min(scale, 8000 / max(width, height))
            target_size = (max(1, round(width * scale)), max(1, round(height * scale)))
            if target_size != image.size:
                image = image.resize(target_size, Image.Resampling.LANCZOS)
            background = Image.new("RGBA", image.size, "white")
            background.alpha_composite(image)
            flattened = background.convert("RGB")
            output = BytesIO()
            flattened.save(output, format="PNG", optimize=True)
    except (UnidentifiedImageError, OSError) as exc:
        raise HTTPException(status_code=400, detail="商品图片无法转换为百炼支持的格式") from exc
    return f"data:image/png;base64,{base64.b64encode(output.getvalue()).decode('ascii')}"


def _dashscope_result_url(payload: dict) -> str:
    try:
        choices = payload["output"]["choices"]
    except (KeyError, TypeError) as exc:
        raise HTTPException(status_code=502, detail="百炼图片模型返回了无效响应") from exc
    for choice in choices if isinstance(choices, list) else []:
        content = choice.get("message", {}).get("content", []) if isinstance(choice, dict) else []
        for item in content if isinstance(content, list) else []:
            image_url = item.get("image") if isinstance(item, dict) else None
            if image_url:
                return image_url
    raise HTTPException(status_code=502, detail="百炼图片模型没有返回图片")


def _validate_dashscope_result_url(image_url: str) -> str:
    parsed = urlparse(image_url)
    hostname = (parsed.hostname or "").lower()
    if parsed.scheme != "https" or not hostname.endswith(".aliyuncs.com"):
        raise HTTPException(status_code=502, detail="百炼返回了不受信任的图片地址")
    try:
        port = parsed.port
    except ValueError as exc:
        raise HTTPException(status_code=502, detail="百炼返回了无效的图片地址") from exc
    if parsed.username or parsed.password or port not in {None, 443}:
        raise HTTPException(status_code=502, detail="百炼返回了无效的图片地址")
    return image_url


async def _download_dashscope_image(image_url: str) -> bytes:
    safe_url = _validate_dashscope_result_url(image_url)
    try:
        async with httpx.AsyncClient(timeout=45.0, follow_redirects=False) as client:
            async with client.stream("GET", safe_url) as response:
                if not response.is_success:
                    raise HTTPException(status_code=502, detail="无法下载百炼生成的图片")
                content_type = response.headers.get("content-type", "").lower()
                if content_type and not content_type.startswith("image/"):
                    raise HTTPException(status_code=502, detail="百炼生成结果不是有效图片")
                chunks: list[bytes] = []
                total = 0
                async for chunk in response.aiter_bytes():
                    total += len(chunk)
                    if total > MAX_GENERATED_IMAGE_SIZE:
                        raise HTTPException(status_code=502, detail="百炼生成的图片超过 30MB")
                    chunks.append(chunk)
    except httpx.TimeoutException as exc:
        raise HTTPException(status_code=504, detail="下载百炼生成图片超时") from exc
    except httpx.RequestError as exc:
        raise HTTPException(status_code=502, detail="无法下载百炼生成的图片") from exc
    content = b"".join(chunks)
    if not content:
        raise HTTPException(status_code=502, detail="百炼返回了空图片")
    return content


async def _request_wan_ad(config: ImageModelConfig, product_bytes: bytes, prompt: str) -> bytes:
    payload = {
        "model": config.model,
        "input": {
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"image": _wan_input_data_url(product_bytes)},
                        {"text": prompt},
                    ],
                }
            ]
        },
        "parameters": {
            "size": config.size.replace("x", "*"),
            "n": 1,
            "watermark": False,
        },
    }
    try:
        async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT, follow_redirects=False) as client:
            response = await client.post(
                dashscope_generation_url(config.base_url),
                headers=_headers(config),
                json=payload,
            )
    except httpx.TimeoutException as exc:
        raise HTTPException(status_code=504, detail="百炼图片重构超时，请稍后重试") from exc
    except httpx.RequestError as exc:
        raise HTTPException(status_code=502, detail="无法连接百炼图片接口，请检查网络和地域配置") from exc
    if not response.is_success:
        raise _provider_error(response)
    try:
        image_url = _dashscope_result_url(response.json())
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=502, detail="百炼图片模型返回了无效响应") from exc
    return await _download_dashscope_image(image_url)


async def _request_generated_ad(config: ImageModelConfig, product_bytes: bytes, content_type: str, prompt: str) -> bytes:
    if is_dashscope_wan(config.model, config.base_url):
        return await _request_wan_ad(config, product_bytes, prompt)
    return await _request_openai_ad(config, product_bytes, content_type, prompt)


def _normalize_generated_ad(content: bytes) -> tuple[Image.Image, int, int]:
    """Decode the model's final poster without imposing the old fixed template."""
    try:
        with Image.open(BytesIO(content)) as source:
            image = ImageOps.exif_transpose(source).convert("RGB")
            image.load()
    except (UnidentifiedImageError, OSError, ValueError) as exc:
        raise HTTPException(status_code=502, detail="图片模型返回的广告图无法解析") from exc
    width, height = image.size
    if width < 256 or height < 256:
        raise HTTPException(status_code=502, detail="图片模型返回的广告图尺寸过小")
    return image, width, height


async def reconstruct_ad(
    config: ImageModelConfig,
    snapshot: PageSnapshot,
    product_bytes: bytes,
    product_content_type: str,
    output_dir: Path,
    public_base_url: str,
    user_prompt: str = "",
) -> dict:
    if not config.api_key.strip():
        raise HTTPException(status_code=400, detail="请先配置图片模型 API Key")
    cleaned_user_prompt = user_prompt.strip()
    if len(cleaned_user_prompt) > 1000:
        raise HTTPException(status_code=400, detail="AI 重构提示词不能超过 1000 个字符")
    validate_product_image(product_bytes)
    prompt = build_reconstruction_prompt(snapshot, cleaned_user_prompt)
    generated_bytes = await _request_generated_ad(config, product_bytes, product_content_type, prompt)
    generated_ad, width, height = _normalize_generated_ad(generated_bytes)

    output_dir.mkdir(parents=True, exist_ok=True)
    reconstruction_id = uuid4().hex
    filename = f"{reconstruction_id}.png"
    generated_ad.save(output_dir / filename, format="PNG", optimize=True)
    created_at = datetime.now().astimezone().isoformat()
    return {
        "id": reconstruction_id,
        "imageUrl": f"{public_base_url.rstrip('/')}/uploads/reconstructions/{filename}",
        "mode": "ai_redesigned",
        "provider": config.provider,
        "model": config.model,
        "width": width,
        "height": height,
        "createdAt": created_at,
    }
