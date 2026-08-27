import json
import re

import httpx
from fastapi import HTTPException
from pydantic import ValidationError

from .prompts import build_messages
from .providers import chat_completions_url
from .schemas import ModelConfig, PolishedCopy, PolishRequest

REQUEST_TIMEOUT = httpx.Timeout(35.0, connect=10.0)
CONNECTION_MAX_TOKENS = 256
POLISH_MAX_TOKENS = 4096


def _headers(config: ModelConfig) -> dict[str, str]:
    headers = {"Content-Type": "application/json"}
    if config.api_key.strip():
        headers["Authorization"] = f"Bearer {config.api_key.strip()}"
    return headers


def _provider_error(response: httpx.Response) -> HTTPException:
    messages = {
        400: "模型拒绝了当前请求，请检查模型名称和 Base URL",
        401: "API Key 无效或已过期",
        403: "当前 API Key 没有访问该模型的权限",
        404: "未找到模型接口，请检查 Base URL 和模型名称",
        429: "模型请求过于频繁或额度不足",
    }
    return HTTPException(status_code=400, detail=messages.get(response.status_code, f"模型服务请求失败（{response.status_code}）"))


async def _request_completion(config: ModelConfig, payload: dict) -> dict:
    url = chat_completions_url(config.base_url)
    try:
        async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT, follow_redirects=False) as client:
            response = await client.post(url, headers=_headers(config), json=payload)
            # Some OpenAI-compatible services do not implement response_format.
            # The prompt still requires JSON, so retry once without that optional field.
            if response.status_code == 400 and "response_format" in payload:
                compatible_payload = {key: value for key, value in payload.items() if key != "response_format"}
                response = await client.post(url, headers=_headers(config), json=compatible_payload)
    except httpx.TimeoutException as exc:
        raise HTTPException(status_code=504, detail="模型请求超时，请稍后重试") from exc
    except httpx.RequestError as exc:
        raise HTTPException(status_code=502, detail="无法连接模型服务，请检查 Base URL 和网络") from exc
    if not response.is_success:
        raise _provider_error(response)
    try:
        return response.json()
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=502, detail="模型服务返回了无效响应") from exc


def _message_content(response: dict) -> str:
    try:
        content = response["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as exc:
        raise HTTPException(status_code=502, detail="模型响应中没有可用文案") from exc
    if not isinstance(content, str) or not content.strip():
        raise HTTPException(status_code=502, detail="模型返回了空文案")
    return content.strip()


def _is_deepseek_model(config: ModelConfig) -> bool:
    provider = config.provider.strip().lower()
    model = config.model.strip().lower()
    return provider == "deepseek" or model.startswith("deepseek-")


def parse_polished_copy(content: str) -> PolishedCopy:
    cleaned = re.sub(r"^```(?:json)?\s*|\s*```$", "", content.strip(), flags=re.IGNORECASE)
    try:
        data = json.loads(cleaned)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", cleaned, flags=re.DOTALL)
        if not match:
            raise HTTPException(status_code=502, detail="AI 未按要求返回 JSON 文案")
        try:
            data = json.loads(match.group(0))
        except json.JSONDecodeError as exc:
            raise HTTPException(status_code=502, detail="AI 返回的文案格式无法解析") from exc
    if isinstance(data, dict) and isinstance(data.get("features"), str):
        data["features"] = [item.strip() for item in re.split(r"[，,；;\n]", data["features"]) if item.strip()]
    try:
        return PolishedCopy.model_validate(data)
    except ValidationError as exc:
        raise HTTPException(status_code=502, detail="AI 返回的文案字段不完整或过长") from exc


async def test_connection(config: ModelConfig) -> dict:
    if not config.api_key.strip() and config.provider != "ollama":
        raise HTTPException(status_code=400, detail="请填写 API Key")
    token_field = "max_completion_tokens" if config.provider == "openai" else "max_tokens"
    payload = {
        "model": config.model,
        "messages": [{"role": "user", "content": "只回复 OK"}],
        "stream": False,
        token_field: CONNECTION_MAX_TOKENS,
    }
    if _is_deepseek_model(config):
        # DeepSeek V4 enables reasoning by default. A tiny connection probe can
        # otherwise spend its whole output budget on reasoning_content and
        # return an empty final content even though authentication succeeded.
        payload["enable_thinking"] = False
    response = await _request_completion(config, payload)
    _message_content(response)
    return {"success": True, "message": "连接成功"}


async def polish_copy(request: PolishRequest) -> PolishedCopy:
    if not request.config.api_key.strip() and request.config.provider != "ollama":
        raise HTTPException(status_code=400, detail="请先配置 API Key")
    messages = build_messages(
        request.style_id,
        request.product.model_dump(),
        request.current_copy.model_dump(),
    )
    token_field = "max_completion_tokens" if request.config.provider == "openai" else "max_tokens"
    payload = {
        "model": request.config.model,
        "messages": messages,
        "stream": False,
        "temperature": 0.7,
        token_field: POLISH_MAX_TOKENS,
        "response_format": {"type": "json_object"},
    }
    response = await _request_completion(request.config, payload)
    content = _message_content(response)
    try:
        return parse_polished_copy(content)
    except HTTPException as exc:
        if exc.status_code != 502:
            raise

    repair_messages = [
        *messages,
        {"role": "assistant", "content": content},
        {
            "role": "user",
            "content": (
                "上一次返回不符合要求。请重新输出严格 JSON，必须完整包含 headline、eyebrow、"
                "description、features、cta 五个字段，并对五个字段都进行润色；不要解释，不要使用 Markdown。"
            ),
        },
    ]
    retry_payload = {
        **payload,
        "messages": repair_messages,
        "temperature": 0.3,
    }
    retry_response = await _request_completion(request.config, retry_payload)
    return parse_polished_copy(_message_content(retry_response))
