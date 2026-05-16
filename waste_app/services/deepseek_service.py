from __future__ import annotations

import requests


class ExternalApiError(RuntimeError):
    """外部大模型 API 调用失败时抛出的业务异常。"""


def ask_deepseek(question: str, *, api_key: str, base_url: str, model: str) -> str:
    """调用 DeepSeek Chat API 回答垃圾分类问题。"""
    if not api_key:
        raise ExternalApiError("DeepSeek API 密钥未配置，请在 .env 中填写 DEEPSEEK_API_KEY。")
    if not question.strip():
        raise ExternalApiError("问题不能为空。")
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": "你是垃圾分类助手，请用简洁、准确的中文回答，并给出分类依据。"},
            {"role": "user", "content": question.strip()},
        ],
        "temperature": 0.3,
    }
    try:
        response = requests.post(
            base_url,
            json=payload,
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            timeout=30,
        )
        response.raise_for_status()
        data = response.json()
        return data["choices"][0]["message"]["content"]
    except Exception as exc:
        raise ExternalApiError(f"DeepSeek API 调用失败：{exc}") from exc
