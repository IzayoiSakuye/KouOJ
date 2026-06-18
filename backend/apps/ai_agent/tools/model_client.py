from __future__ import annotations

import time
from typing import Any

import requests
from django.conf import settings


def _safe_float(value: Any, default: float) -> float:
    """把环境变量中的温度配置转成浮点数，写错时使用稳定默认值。"""
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _safe_timeout(value: Any, default: float) -> float:
    """把模型超时时间转成安全数字，避免配置过小或非法导致请求立刻失败。"""
    try:
        timeout = float(value)
    except (TypeError, ValueError):
        return default
    return max(5.0, min(timeout, 120.0))


def call_chat_completion(messages: list[dict[str, str]]) -> dict[str, Any]:
    """
    按 OpenAI Chat Completions 规范调用模型。

    这里不绑定具体厂商，只依赖 base_url + api_key + model 这三个配置。函数返回统一
    结构，让 LangGraph 节点可以判断“模型可用就用模型输出，不可用就降级到规则提示”。
    """
    base_url = getattr(settings, "KOUOJ_AI_MODEL_BASE_URL", "").rstrip("/")
    api_key = getattr(settings, "KOUOJ_AI_MODEL_API_KEY", "")
    model = getattr(settings, "KOUOJ_AI_MODEL_NAME", "")

    if not base_url or not api_key or not model:
        return {
            "available": False,
            "reason": "模型配置不完整，已降级为规则提示。",
            "content": "",
        }

    payload = {
        "model": model,
        "messages": messages,
        "temperature": _safe_float(getattr(settings, "KOUOJ_AI_MODEL_TEMPERATURE", 0), 0.0),
        "max_tokens": 10000,
    }
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    retry_status_codes = {429, 500, 502, 503, 504}
    timeout = _safe_timeout(getattr(settings, "KOUOJ_AI_MODEL_TIMEOUT", 30), 30.0)
    last_error: str | None = None

    for attempt in range(3):
        try:
            response = requests.post(
                f"{base_url}/chat/completions",
                headers=headers,
                json=payload,
                timeout=timeout,
            )
            data = response.json()
        except Exception as exc:
            last_error = str(exc)
            if attempt < 2:
                time.sleep(0.8 * (attempt + 1))
                continue
            return {
                "available": False,
                "reason": f"模型调用失败，已降级为规则提示：{last_error}",
                "content": "",
            }

        if response.status_code not in retry_status_codes:
            break

        last_error = f"模型服务返回 {response.status_code}：{data}"
        if attempt < 2:
            time.sleep(0.8 * (attempt + 1))
            continue
    else:
        return {
            "available": False,
            "reason": f"{last_error}，已降级为规则提示。",
            "content": "",
        }

    if response.status_code >= 400:
        return {
            "available": False,
            "reason": f"模型服务返回 {response.status_code}，已降级为规则提示：{data}",
            "content": "",
        }

    choices = data.get("choices") or []
    content = ""
    if choices:
        content = choices[0].get("message", {}).get("content", "").strip()

    if not content:
        return {
            "available": False,
            "reason": "模型没有返回有效内容，已降级为规则提示。",
            "content": "",
        }

    return {
        "available": True,
        "reason": "",
        "content": content,
        "model": data.get("model", model),
    }
