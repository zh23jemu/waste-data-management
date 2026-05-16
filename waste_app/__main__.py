from __future__ import annotations

from . import create_app

app = create_app()

if __name__ == "__main__":
    # 本地毕业设计演示默认使用 Flask 开发服务器；正式部署时可换成 waitress/gunicorn。
    app.run(host="127.0.0.1", port=5000, debug=True)
