from urllib.parse import urlparse

from fastapi import HTTPException

AI_PROVIDERS = [
    {
        "id": "deepseek",
        "name": "DeepSeek",
        "model": "deepseek-chat",
        "baseUrl": "https://api.deepseek.com",
        "requiresApiKey": True,
    },
    {
        "id": "qwen",
        "name": "通义千问",
        "model": "qwen-plus",
        "baseUrl": "https://dashscope.aliyuncs.com/compatible-mode/v1",
        "requiresApiKey": True,
    },
    {
        "id": "openai",
        "name": "OpenAI",
        "model": "gpt-5-mini",
        "baseUrl": "https://api.openai.com/v1",
        "requiresApiKey": True,
    },
    {
        "id": "ollama",
        "name": "Ollama 本地模型",
        "model": "qwen3:8b",
        "baseUrl": "http://127.0.0.1:11434/v1",
        "requiresApiKey": False,
    },
    {
        "id": "custom",
        "name": "自定义兼容接口",
        "model": "",
        "baseUrl": "",
        "requiresApiKey": True,
    },
]


def validate_base_url(base_url: str) -> str:
    """Allow HTTPS providers and explicit loopback HTTP URLs for local models."""
    value = base_url.strip().rstrip("/")
    parsed = urlparse(value)
    if parsed.username or parsed.password or parsed.query or parsed.fragment:
        raise HTTPException(status_code=400, detail="Base URL 不能包含账号、查询参数或片段")
    if parsed.scheme == "https" and parsed.hostname:
        return value
    if parsed.scheme == "http" and parsed.hostname in {"127.0.0.1", "localhost", "::1"}:
        return value
    raise HTTPException(status_code=400, detail="Base URL 必须使用 HTTPS；本地模型可使用 localhost HTTP")


def chat_completions_url(base_url: str) -> str:
    base = validate_base_url(base_url)
    if base.endswith("/chat/completions"):
        return base
    return f"{base}/chat/completions"

