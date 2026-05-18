from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any

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
"""


def init_db(database_path: Path) -> None:
    """初始化 SQLite 数据库。"""
    database_path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(database_path) as conn:
        conn.executescript(SCHEMA)
        conn.commit()


def get_connection(database_path: Path) -> sqlite3.Connection:
    """创建带字典式行访问能力的数据库连接。"""
    conn = sqlite3.connect(database_path)
    conn.row_factory = sqlite3.Row
    return conn


def row_to_dict(row: sqlite3.Row) -> dict[str, Any]:
    """将 SQLite Row 转为普通字典，便于 JSON 序列化。"""
    return {key: row[key] for key in row.keys()}
