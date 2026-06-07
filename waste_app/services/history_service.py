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


def add_search_history(database_path: Path, keyword: str) -> None:
    """保存分类知识检索关键词，并对重复关键词做最近访问更新。

    分类知识页的“历史记录”需要跨浏览器刷新和换设备部署后仍可保留，因此不再依赖
    localStorage，而是写入 SQLite。keyword 以原始展示文本为准，前后空白会被清理；
    已存在的关键词会累加搜索次数并刷新 updated_at，用于按最近搜索排序。
    """
    value = keyword.strip()
    if not value:
        return
    with get_connection(database_path) as conn:
        conn.execute(
            """
            INSERT INTO search_history (keyword, search_count)
            VALUES (?, 1)
            ON CONFLICT(keyword) DO UPDATE SET
                search_count = search_count + 1,
                updated_at = strftime('%Y-%m-%d %H:%M:%f', 'now', 'localtime')
            """,
            (value,),
        )
        conn.commit()


def list_search_history(database_path: Path, limit: int = 8) -> list[str]:
    """读取最近使用的分类知识检索关键词。"""
    limit = min(max(int(limit), 1), 50)
    with get_connection(database_path) as conn:
        rows = conn.execute(
            """
            SELECT keyword
            FROM search_history
            ORDER BY updated_at DESC, id DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
    return [row["keyword"] for row in rows]


def clear_search_history(database_path: Path) -> int:
    """清空分类知识检索关键词历史，返回删除条数。"""
    with get_connection(database_path) as conn:
        cursor = conn.execute("DELETE FROM search_history")
        conn.commit()
        return cursor.rowcount
