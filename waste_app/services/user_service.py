from __future__ import annotations

from pathlib import Path
import re

from werkzeug.security import check_password_hash, generate_password_hash

from ..database import get_connection, row_to_dict


USERNAME_RE = re.compile(r"^[A-Za-z0-9_\u4e00-\u9fa5]{2,24}$")


class UserServiceError(ValueError):
    """用户模块业务校验失败时抛出的异常。"""


def public_user(row) -> dict:
    """返回可暴露给前端的用户字段，避免泄露 password_hash。"""
    data = row_to_dict(row)
    data.pop("password_hash", None)
    return data


def validate_user_input(username: str, email: str, password: str) -> None:
    """校验注册字段，保证用户名、邮箱和密码满足本地演示系统的基础要求。"""
    if not USERNAME_RE.match(username):
        raise UserServiceError("用户名需为 2-24 位中文、字母、数字或下划线。")
    if "@" not in email or "." not in email:
        raise UserServiceError("请输入有效邮箱地址。")
    if len(password) < 6:
        raise UserServiceError("密码至少需要 6 位。")


def register_user(database_path: Path, username: str, email: str, password: str) -> dict:
    """注册普通用户，用户名和邮箱均保持唯一。"""
    username = username.strip()
    email = email.strip().lower()
    validate_user_input(username, email, password)
    with get_connection(database_path) as conn:
        exists = conn.execute(
            "SELECT id FROM users WHERE username = ? OR email = ?",
            (username, email),
        ).fetchone()
        if exists:
            raise UserServiceError("用户名或邮箱已存在。")
        cursor = conn.execute(
            """
            INSERT INTO users (username, email, password_hash, role, status)
            VALUES (?, ?, ?, 'user', 'active')
            """,
            (username, email, generate_password_hash(password)),
        )
        row = conn.execute("SELECT * FROM users WHERE id = ?", (cursor.lastrowid,)).fetchone()
        return public_user(row)


def authenticate_user(database_path: Path, username: str, password: str) -> dict:
    """验证用户名和密码，并拒绝已禁用账号登录。"""
    with get_connection(database_path) as conn:
        row = conn.execute("SELECT * FROM users WHERE username = ? OR email = ?", (username, username)).fetchone()
        if row is None or not check_password_hash(row["password_hash"], password):
            raise UserServiceError("用户名或密码错误。")
        if row["status"] != "active":
            raise UserServiceError("账号已被禁用，请联系管理员。")
        return public_user(row)


def get_user(database_path: Path, user_id: int) -> dict | None:
    """按 ID 查询用户公开信息。"""
    with get_connection(database_path) as conn:
        row = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
        return public_user(row) if row else None


def list_users(database_path: Path) -> list[dict]:
    """按创建时间倒序返回全部用户，用于管理员用户管理页面。"""
    with get_connection(database_path) as conn:
        rows = conn.execute(
            "SELECT * FROM users ORDER BY role = 'admin' DESC, id DESC"
        ).fetchall()
        return [public_user(row) for row in rows]


def update_user_status(database_path: Path, user_id: int, status: str) -> dict:
    """启用或禁用用户，管理员账号不可被禁用。"""
    if status not in {"active", "disabled"}:
        raise UserServiceError("用户状态只能是 active 或 disabled。")
    with get_connection(database_path) as conn:
        row = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
        if row is None:
            raise UserServiceError("用户不存在。")
        if row["role"] == "admin" and status == "disabled":
            raise UserServiceError("管理员账号不能禁用。")
        conn.execute("UPDATE users SET status = ? WHERE id = ?", (status, user_id))
        updated = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
        return public_user(updated)
