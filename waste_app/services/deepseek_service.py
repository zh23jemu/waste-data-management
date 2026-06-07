from __future__ import annotations

import json

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


def ask_deepseek_json(prompt: str, *, api_key: str, base_url: str, model: str) -> dict[str, object]:
    """调用 DeepSeek 并要求返回 JSON 对象。

    该方法用于分类知识检索等结构化场景：后端先拿到本地知识条目，再让
    DeepSeek 生成更自然的类别说明与投放建议，避免前端做文本解析。
    """
    if not api_key:
        raise ExternalApiError("DeepSeek API 密钥未配置，请在 .env 中填写 DEEPSEEK_API_KEY。")
    if not prompt.strip():
        raise ExternalApiError("提示内容不能为空。")
    payload = {
        "model": model,
        "messages": [
            {
                "role": "system",
                "content": (
                    "你是垃圾分类知识助手。请严格只返回 JSON，不要输出 Markdown、代码块或额外说明。"
                    " JSON 字段必须包括：item_name、category_label、disposal_advice、explanation。"
                    " category_label 只能是 可回收物、有害垃圾、厨余垃圾、其他垃圾 之一。"
                ),
            },
            {"role": "user", "content": prompt.strip()},
        ],
        "temperature": 0.2,
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
        content = str(data["choices"][0]["message"]["content"]).strip()
        if content.startswith("```"):
            content = content.strip("`")
            if content.startswith("json"):
                content = content[4:].strip()
        return json.loads(content)
    except Exception as exc:
        raise ExternalApiError(f"DeepSeek 结构化调用失败：{exc}") from exc
