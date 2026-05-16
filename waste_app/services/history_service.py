from __future__ import annotations

import json
from pathlib import Path

from ..database import get_connection, row_to_dict


def add_history(database_path: Path, image_path: str, result: dict) -> int:
    """保存一次图像识别历史记录。"""
    with get_connection(database_path) as conn:
        cursor = conn.execute(
            """
            INSERT INTO recognition_history
            (image_path, predicted_class, confidence, probabilities_json, rationale)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                image_path,
                result["predicted_class"],
                float(result["confidence"]),
                json.dumps(result.get("probabilities", {}), ensure_ascii=False),
                result.get("rationale", ""),
            ),
        )
        conn.commit()
        return int(cursor.lastrowid)


def list_history(database_path: Path, page: int, page_size: int) -> dict:
    """分页读取历史记录。"""
    page = max(page, 1)
    page_size = min(max(page_size, 1), 100)
    offset = (page - 1) * page_size
    with get_connection(database_path) as conn:
        total = conn.execute("SELECT COUNT(*) AS total FROM recognition_history").fetchone()["total"]
        rows = conn.execute(
            """
            SELECT id, image_path, predicted_class, confidence, probabilities_json, rationale, created_at
            FROM recognition_history
            ORDER BY id DESC
            LIMIT ? OFFSET ?
            """,
            (page_size, offset),
        ).fetchall()
    items = []
    for row in rows:
        item = row_to_dict(row)
        item["probabilities"] = json.loads(item.pop("probabilities_json") or "{}")
        items.append(item)
    return {"items": items, "total": total, "page": page, "page_size": page_size}


def delete_history(database_path: Path, record_id: int) -> bool:
    """删除单条历史记录，返回是否实际删除。"""
    with get_connection(database_path) as conn:
        cursor = conn.execute("DELETE FROM recognition_history WHERE id = ?", (record_id,))
        conn.commit()
        return cursor.rowcount > 0


def clear_history(database_path: Path) -> int:
    """清空历史记录，返回删除条数。"""
    with get_connection(database_path) as conn:
        cursor = conn.execute("DELETE FROM recognition_history")
        conn.commit()
        return cursor.rowcount
