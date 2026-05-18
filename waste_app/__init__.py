from __future__ import annotations

from pathlib import Path

from flask import Flask, abort, jsonify, send_from_directory
from werkzeug.exceptions import RequestEntityTooLarge

from .config import Config
from .database import init_db
from . import routes
from .routes import api_bp


def create_app(config_object: type[Config] = Config) -> Flask:
    """创建 Flask 应用实例。"""
    app = Flask(__name__, static_folder=str(config_object.FRONTEND_DIR), static_url_path="")
    app.config.from_object(config_object)
    # 测试或多实例运行时可能传入不同配置，这里重置懒加载分类器缓存，
    # 避免上一个应用实例的模型路径、类别映射路径影响当前实例。
    routes._classifier_cache = None
    init_db(app.config["DATABASE_PATH"])
    app.register_blueprint(api_bp, url_prefix="/api")

    @app.get("/")
    def index():
        """返回前端单页应用入口。"""
        return send_from_directory(app.static_folder, "index.html")

    @app.get("/media/<path:relative_path>")
    def media_file(relative_path: str):
        """安全返回系统产生或数据集中已有的图片，用于前端预览。

        前端需要展示上传图片、历史记录图片和 Qdrant 返回的相似图片。接口只允许读取
        uploads、data/raw 和 data/processed 三类项目内目录，避免把任意本地文件暴露给浏览器。
        """
        base_dir: Path = app.config["BASE_DIR"]
        candidate = (base_dir / relative_path).resolve()
        allowed_roots = [
            app.config["UPLOAD_FOLDER"].resolve(),
            (base_dir / "data/raw").resolve(),
            (base_dir / "data/processed").resolve(),
        ]
        if not any(candidate == root or root in candidate.parents for root in allowed_roots):
            abort(404)
        if not candidate.is_file():
            abort(404)
        return send_from_directory(candidate.parent, candidate.name)

    @app.get("/health")
    def health():
        """提供轻量健康检查，便于测试服务是否可用。"""
        return jsonify({"ok": True, "service": "waste-data-management"})

    @app.errorhandler(RequestEntityTooLarge)
    def handle_large_upload(exc: RequestEntityTooLarge):
        """将 Flask 默认的上传超限 HTML 响应转换为前端可读 JSON。"""
        max_mb = app.config["MAX_CONTENT_LENGTH"] // 1024 // 1024
        return jsonify({"ok": False, "message": f"上传文件不能超过 {max_mb}MB。"}), 413

    return app
