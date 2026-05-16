from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()
BASE_DIR = Path(__file__).resolve().parent.parent


class Config:
    """系统配置集中定义。

    配置值优先来自 `.env` 或系统环境变量，默认值只用于本地开发演示。
    API 密钥不得写入源码，避免毕业设计材料打包或提交时泄露敏感信息。
    """

    BASE_DIR = BASE_DIR
    FRONTEND_DIR = BASE_DIR / "frontend"
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key")
    DATABASE_PATH = BASE_DIR / os.getenv("DATABASE_PATH", "instance/waste_management.sqlite3")
    UPLOAD_FOLDER = BASE_DIR / os.getenv("UPLOAD_FOLDER", "uploads")
    MAX_CONTENT_LENGTH = int(os.getenv("MAX_CONTENT_LENGTH", str(16 * 1024 * 1024)))
    ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg"}

    MODEL_PATH = BASE_DIR / os.getenv("MODEL_PATH", "models/resnet50_waste.pt")
    CLASS_MAP_PATH = BASE_DIR / os.getenv("CLASS_MAP_PATH", "models/class_map.json")

    QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")
    QDRANT_COLLECTION = os.getenv("QDRANT_COLLECTION", "waste_images")
    SIMILARITY_THRESHOLD = float(os.getenv("SIMILARITY_THRESHOLD", "0.65"))

    DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
    DEEPSEEK_BASE_URL = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com/chat/completions")
    DEEPSEEK_MODEL = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")

    XUNFEI_APP_ID = os.getenv("XUNFEI_APP_ID", "")
    XUNFEI_API_KEY = os.getenv("XUNFEI_API_KEY", "")
    XUNFEI_API_SECRET = os.getenv("XUNFEI_API_SECRET", "")
    XUNFEI_VISION_URL = os.getenv("XUNFEI_VISION_URL", "")
