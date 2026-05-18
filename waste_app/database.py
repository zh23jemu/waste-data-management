from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any

from werkzeug.security import generate_password_hash

SCHEMA = """
CREATE TABLE IF NOT EXISTS recognition_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    image_path TEXT NOT NULL,
    predicted_class TEXT NOT NULL,
    confidence REAL NOT NULL,
    probabilities_json TEXT NOT NULL,
    rationale TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT (datetime('now', 'localtime'))
);

CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE,
    email TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    role TEXT NOT NULL DEFAULT 'user',
    status TEXT NOT NULL DEFAULT 'active',
    created_at TEXT NOT NULL DEFAULT (datetime('now', 'localtime'))
);
"""


def init_db(database_path: Path) -> None:
    """初始化 SQLite 数据库。"""
    database_path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(database_path) as conn:
        conn.executescript(SCHEMA)
        # 为本地演示准备一个默认管理员账号。只有 users 表为空时创建，避免覆盖用户修改。
        # 默认密码仅用于毕业设计本地演示，正式部署时应通过环境变量或管理后台修改。
        user_count = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
        if user_count == 0:
            conn.execute(
                """
                INSERT INTO users (username, email, password_hash, role, status)
                VALUES (?, ?, ?, 'admin', 'active')
                """,
                ("admin", "admin@example.com", generate_password_hash("admin123456")),
            )
        conn.commit()


def get_connection(database_path: Path) -> sqlite3.Connection:
    """创建带字典式行访问能力的数据库连接。"""
    conn = sqlite3.connect(database_path)
    conn.row_factory = sqlite3.Row
    return conn


def row_to_dict(row: sqlite3.Row) -> dict[str, Any]:
    """将 SQLite Row 转为普通字典，便于 JSON 序列化。"""
    return {key: row[key] for key in row.keys()}
