"""SQLite repository for skill-build platform data."""

from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator
from uuid import uuid4

from .models import ChatMessage, SkillItem, TaskCategory, TaskItem


def utc_now() -> datetime:
    """Return timezone-aware UTC timestamp."""
    return datetime.now(tz=timezone.utc)


def dt_to_text(value: datetime) -> str:
    """Serialize datetime for SQLite storage."""
    return value.isoformat()


def text_to_dt(value: str) -> datetime:
    """Deserialize datetime text from SQLite."""
    return datetime.fromisoformat(value)


class PlatformRepository:
    """Repository that stores categories, tasks, skills, and chat logs."""

    def __init__(self, db_path: str):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_schema()

    @contextmanager
    def _conn(self) -> Iterator[sqlite3.Connection]:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()

    def _init_schema(self) -> None:
        with self._conn() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS task_categories (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL UNIQUE,
                    description TEXT NOT NULL,
                    default_skill_ids TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS tasks (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    description TEXT NOT NULL,
                    category_id TEXT NOT NULL,
                    selected_skill_ids TEXT NOT NULL,
                    document_name TEXT,
                    document_content TEXT,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (category_id) REFERENCES task_categories(id)
                );

                CREATE TABLE IF NOT EXISTS chat_messages (
                    id TEXT PRIMARY KEY,
                    task_id TEXT NOT NULL,
                    role TEXT NOT NULL,
                    source TEXT NOT NULL,
                    content TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (task_id) REFERENCES tasks(id)
                );

                CREATE TABLE IF NOT EXISTS platform_skills (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    description TEXT NOT NULL,
                    type TEXT NOT NULL,
                    category_bindings TEXT NOT NULL,
                    content TEXT NOT NULL,
                    base_skill_ids TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );
                """
            )

    def list_categories(self) -> list[TaskCategory]:
        with self._conn() as conn:
            rows = conn.execute("SELECT * FROM task_categories ORDER BY created_at DESC").fetchall()
        return [self._row_to_category(row) for row in rows]

    def create_category(self, name: str, description: str, default_skill_ids: list[str]) -> TaskCategory:
        now = utc_now()
        category_id = f"cat_{uuid4().hex[:12]}"
        with self._conn() as conn:
            conn.execute(
                """
                INSERT INTO task_categories (id, name, description, default_skill_ids, created_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (category_id, name, description, json.dumps(default_skill_ids), dt_to_text(now)),
            )
            row = conn.execute("SELECT * FROM task_categories WHERE id = ?", (category_id,)).fetchone()
        return self._row_to_category(row)

    def update_category(self, category_id: str, name: str, description: str, default_skill_ids: list[str]) -> TaskCategory | None:
        with self._conn() as conn:
            row = conn.execute("SELECT id FROM task_categories WHERE id = ?", (category_id,)).fetchone()
            if not row:
                return None
            conn.execute(
                """
                UPDATE task_categories
                SET name = ?, description = ?, default_skill_ids = ?
                WHERE id = ?
                """,
                (name, description, json.dumps(default_skill_ids), category_id),
            )
            updated = conn.execute("SELECT * FROM task_categories WHERE id = ?", (category_id,)).fetchone()
        return self._row_to_category(updated)

    def get_category(self, category_id: str) -> TaskCategory | None:
        with self._conn() as conn:
            row = conn.execute("SELECT * FROM task_categories WHERE id = ?", (category_id,)).fetchone()
        return self._row_to_category(row) if row else None

    def list_tasks(self) -> list[TaskItem]:
        with self._conn() as conn:
            rows = conn.execute("SELECT * FROM tasks ORDER BY created_at DESC").fetchall()
        return [self._row_to_task(row) for row in rows]

    def get_task(self, task_id: str) -> TaskItem | None:
        with self._conn() as conn:
            row = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
        return self._row_to_task(row) if row else None

    def create_task(
        self,
        name: str,
        description: str,
        category_id: str,
        selected_skill_ids: list[str],
        document_name: str | None,
        document_content: str | None,
    ) -> TaskItem:
        now = utc_now()
        task_id = f"task_{uuid4().hex[:12]}"
        with self._conn() as conn:
            conn.execute(
                """
                INSERT INTO tasks (
                    id, name, description, category_id, selected_skill_ids,
                    document_name, document_content, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    task_id,
                    name,
                    description,
                    category_id,
                    json.dumps(selected_skill_ids),
                    document_name,
                    document_content,
                    dt_to_text(now),
                ),
            )
            row = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
        return self._row_to_task(row)

    def list_messages(self, task_id: str) -> list[ChatMessage]:
        with self._conn() as conn:
            rows = conn.execute(
                "SELECT * FROM chat_messages WHERE task_id = ? ORDER BY created_at ASC",
                (task_id,),
            ).fetchall()
        return [self._row_to_message(row) for row in rows]

    def add_message(self, task_id: str, role: str, source: str, content: str) -> ChatMessage:
        now = utc_now()
        msg_id = f"msg_{uuid4().hex[:12]}"
        with self._conn() as conn:
            conn.execute(
                """
                INSERT INTO chat_messages (id, task_id, role, source, content, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (msg_id, task_id, role, source, content, dt_to_text(now)),
            )
            row = conn.execute("SELECT * FROM chat_messages WHERE id = ?", (msg_id,)).fetchone()
        return self._row_to_message(row)

    def list_platform_skills(self) -> list[SkillItem]:
        with self._conn() as conn:
            rows = conn.execute("SELECT * FROM platform_skills ORDER BY updated_at DESC").fetchall()
        return [self._row_to_skill(row) for row in rows]

    def upsert_platform_skill(
        self,
        skill_id: str,
        name: str,
        description: str,
        skill_type: str,
        category_bindings: list[str],
        content: str,
        base_skill_ids: list[str],
    ) -> SkillItem:
        now = utc_now()
        with self._conn() as conn:
            exists = conn.execute("SELECT id FROM platform_skills WHERE id = ?", (skill_id,)).fetchone()
            if exists:
                conn.execute(
                    """
                    UPDATE platform_skills
                    SET name = ?, description = ?, type = ?, category_bindings = ?, content = ?,
                        base_skill_ids = ?, updated_at = ?
                    WHERE id = ?
                    """,
                    (
                        name,
                        description,
                        skill_type,
                        json.dumps(category_bindings),
                        content,
                        json.dumps(base_skill_ids),
                        dt_to_text(now),
                        skill_id,
                    ),
                )
            else:
                conn.execute(
                    """
                    INSERT INTO platform_skills (
                        id, name, description, type, category_bindings, content, base_skill_ids,
                        created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        skill_id,
                        name,
                        description,
                        skill_type,
                        json.dumps(category_bindings),
                        content,
                        json.dumps(base_skill_ids),
                        dt_to_text(now),
                        dt_to_text(now),
                    ),
                )
            row = conn.execute("SELECT * FROM platform_skills WHERE id = ?", (skill_id,)).fetchone()
        return self._row_to_skill(row)

    def get_platform_skill(self, skill_id: str) -> SkillItem | None:
        with self._conn() as conn:
            row = conn.execute("SELECT * FROM platform_skills WHERE id = ?", (skill_id,)).fetchone()
        return self._row_to_skill(row) if row else None

    @staticmethod
    def _json_list(value: Any) -> list[str]:
        try:
            parsed = json.loads(value)
            return parsed if isinstance(parsed, list) else []
        except Exception:
            return []

    def _row_to_category(self, row: sqlite3.Row) -> TaskCategory:
        return TaskCategory(
            id=row["id"],
            name=row["name"],
            description=row["description"],
            default_skill_ids=self._json_list(row["default_skill_ids"]),
            created_at=text_to_dt(row["created_at"]),
        )

    def _row_to_task(self, row: sqlite3.Row) -> TaskItem:
        return TaskItem(
            id=row["id"],
            name=row["name"],
            description=row["description"],
            category_id=row["category_id"],
            selected_skill_ids=self._json_list(row["selected_skill_ids"]),
            document_name=row["document_name"],
            created_at=text_to_dt(row["created_at"]),
        )

    def _row_to_message(self, row: sqlite3.Row) -> ChatMessage:
        return ChatMessage(
            id=row["id"],
            task_id=row["task_id"],
            role=row["role"],
            source=row["source"],
            content=row["content"],
            created_at=text_to_dt(row["created_at"]),
        )

    def _row_to_skill(self, row: sqlite3.Row) -> SkillItem:
        return SkillItem(
            id=row["id"],
            name=row["name"],
            description=row["description"],
            type=row["type"],
            category_bindings=self._json_list(row["category_bindings"]),
            content=row["content"],
            base_skill_ids=self._json_list(row["base_skill_ids"]),
            created_at=text_to_dt(row["created_at"]),
            updated_at=text_to_dt(row["updated_at"]),
        )

