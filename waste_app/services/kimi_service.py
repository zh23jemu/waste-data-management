from __future__ import annotations

import base64
import mimetypes
from pathlib import Path

import requests

from .deepseek_service import ExternalApiError


def analyze_image_with_kimi(image_path: Path, *, api_key: str, base_url: str, model: str) -> str:
    """调用 Kimi 多模态接口分析废弃物图片。

    Kimi API 兼容 OpenAI Chat Completions 格式，图片通过 base64 data URL
    放入 `image_url` 消息片段。这里仅封装图片理解模块需要的最小能力：
    上传本地图片，要求模型用中文描述物品、材质、状态、可能类别和分类依据。
    """
    if not api_key:
        raise ExternalApiError("Kimi API 密钥未配置，请在 .env 中填写 KIMI_API_KEY。")
    if not base_url:
        raise ExternalApiError("Kimi API 地址未配置，请在 .env 中填写 KIMI_BASE_URL。")
    if not model:
        raise ExternalApiError("Kimi 多模态模型未配置，请在 .env 中填写 KIMI_MODEL。")

    mime_type = mimetypes.guess_type(image_path.name)[0] or "image/jpeg"
    image_b64 = base64.b64encode(image_path.read_bytes()).decode("utf-8")
    image_url = f"data:{mime_type};base64,{image_b64}"
    payload = {
        "model": model,
        "messages": [
            {
                "role": "system",
                "content": "你是废弃物图片理解助手，请用简洁准确的中文回答，并优先给出垃圾分类相关判断。",
            },
            {
                "role": "user",
                "content": [
                    {"type": "image_url", "image_url": {"url": image_url}},
                    {
                        "type": "text",
                        "text": "请分析图片中的废弃物，说明可见物品、材质或状态、可能所属垃圾类别，并给出分类依据。",
                    },
                ],
            },
        ],
        "max_tokens": 500,
    }
    try:
        response = requests.post(
            base_url,
            json=payload,
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            timeout=90,
        )
        response.raise_for_status()
        data = response.json()
        message = data["choices"][0]["message"]
        return message.get("content") or message.get("reasoning_content") or str(data)
    except Exception as exc:
        raise ExternalApiError(f"Kimi 多模态 API 调用失败：{exc}") from exc
