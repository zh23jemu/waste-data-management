from __future__ import annotations

import base64
from pathlib import Path

import requests

from .deepseek_service import ExternalApiError


def analyze_image_with_xunfei(image_path: Path, *, app_id: str, api_key: str, api_secret: str, vision_url: str) -> str:
    """调用星火图片理解接口分析图片。

    星火不同版本的视觉接口签名和网关地址可能随账号能力变化，因此本项目将接口地址
    作为 `.env` 配置项。若学校演示环境使用特定签名规范，可只替换本函数内部请求构造。
    """
    missing = [name for name, value in {
        "XUNFEI_APP_ID": app_id,
        "XUNFEI_API_KEY": api_key,
        "XUNFEI_API_SECRET": api_secret,
        "XUNFEI_VISION_URL": vision_url,
    }.items() if not value]
    if missing:
        raise ExternalApiError(f"星火图片理解配置不完整，请在 .env 中填写：{', '.join(missing)}。")

    image_b64 = base64.b64encode(image_path.read_bytes()).decode("utf-8")
    payload = {
        "app_id": app_id,
        "prompt": "请识别图片中的废弃物，说明可能的材质、状态、垃圾类别和分类依据。",
        "image": image_b64,
    }
    headers = {
        "Content-Type": "application/json",
        "X-Appid": app_id,
        "X-Api-Key": api_key,
        "X-Api-Secret": api_secret,
    }
    try:
        response = requests.post(vision_url, json=payload, headers=headers, timeout=45)
        response.raise_for_status()
        data = response.json()
        return data.get("answer") or data.get("content") or data.get("text") or str(data)
    except Exception as exc:
        raise ExternalApiError(f"星火图片理解 API 调用失败：{exc}") from exc
