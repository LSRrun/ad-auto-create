from urllib.parse import urlparse, urlunparse

from fastapi import HTTPException


IMAGE_PROVIDERS = [
    {
        "id": "openai-image",
        "name": "OpenAI Images",
        "model": "gpt-image-2",
        "baseUrl": "https://api.openai.com/v1",
        "requiresApiKey": True,
        "capabilities": {"imageInput": True, "imageEdit": True, "asyncJob": False},
    },
    {
        "id": "custom-image",
        "name": "自定义 OpenAI 图片接口",
        "model": "gpt-image-2",
        "baseUrl": "",
        "requiresApiKey": True,
        "capabilities": {"imageInput": True, "imageEdit": True, "asyncJob": False},
    },
]


def validate_image_base_url(base_url: str) -> str:
    value = base_url.strip().rstrip("/")
    parsed = urlparse(value)
    if parsed.username or parsed.password or parsed.query or parsed.fragment:
        raise HTTPException(status_code=400, detail="Base URL 不能包含账号、查询参数或片段")
    if parsed.scheme == "https" and parsed.hostname:
        return value
    if parsed.scheme == "http" and parsed.hostname in {"127.0.0.1", "localhost", "::1"}:
        return value
    raise HTTPException(status_code=400, detail="Base URL 必须使用 HTTPS；本地接口可使用 localhost HTTP")


def image_edits_url(base_url: str) -> str:
    base = validate_image_base_url(base_url)
    if base.endswith("/images/edits"):
        return base
    return f"{base}/images/edits"


def models_url(base_url: str) -> str:
    base = validate_image_base_url(base_url)
    if base.endswith("/models"):
        return base
    return f"{base}/models"


def is_dashscope_wan(model: str, base_url: str) -> bool:
    parsed = urlparse(base_url.strip())
    hostname = (parsed.hostname or "").lower()
    return model.strip().lower().startswith("wan2.7-image") and hostname.endswith(".aliyuncs.com")


def dashscope_generation_url(base_url: str) -> str:
    """Convert compatible-mode or native DashScope roots to the Wan sync endpoint."""
    base = validate_image_base_url(base_url)
    parsed = urlparse(base)
    path = parsed.path.rstrip("/")
    endpoint = "/services/aigc/multimodal-generation/generation"
    if path.endswith(endpoint):
        native_path = path
    elif "/compatible-mode/v1" in path:
        prefix = path.split("/compatible-mode/v1", 1)[0]
        native_path = f"{prefix}/api/v1{endpoint}"
    elif path.endswith("/api/v1"):
        native_path = f"{path}{endpoint}"
    elif not path:
        native_path = f"/api/v1{endpoint}"
    else:
        raise HTTPException(status_code=400, detail="百炼 Base URL 应以 /compatible-mode/v1 或 /api/v1 结尾")
    return urlunparse((parsed.scheme, parsed.netloc, native_path, "", "", ""))


def dashscope_models_url(base_url: str) -> str:
    """Use the compatible models endpoint for a no-cost credential check."""
    base = validate_image_base_url(base_url)
    parsed = urlparse(base)
    path = parsed.path.rstrip("/")
    if "/compatible-mode/v1" in path:
        prefix = path.split("/compatible-mode/v1", 1)[0]
    elif "/api/v1" in path:
        prefix = path.split("/api/v1", 1)[0]
    else:
        prefix = path
    models_path = f"{prefix}/compatible-mode/v1/models"
    return urlunparse((parsed.scheme, parsed.netloc, models_path, "", "", ""))
