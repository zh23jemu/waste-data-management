from __future__ import annotations

from flask import Flask, jsonify, send_from_directory

from .config import Config
from .database import init_db
from .routes import api_bp


def create_app(config_object: type[Config] = Config) -> Flask:
    """创建 Flask 应用实例。"""
    app = Flask(__name__, static_folder=str(config_object.FRONTEND_DIR), static_url_path="")
    app.config.from_object(config_object)
    init_db(app.config["DATABASE_PATH"])
    app.register_blueprint(api_bp, url_prefix="/api")

    @app.get("/")
    def index():
        """返回前端单页应用入口。"""
        return send_from_directory(app.static_folder, "index.html")

    @app.get("/health")
    def health():
        """提供轻量健康检查，便于测试服务是否可用。"""
        return jsonify({"ok": True, "service": "waste-data-management"})

    return app
