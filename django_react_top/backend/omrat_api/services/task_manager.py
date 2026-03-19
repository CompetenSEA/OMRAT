"""Task manager with pluggable persistence backends for standalone web backend."""

from __future__ import annotations

import json
import os
import sqlite3
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4


@dataclass
class TaskRecord:
    task_id: str
    state: str
    created_at: str
    updated_at: str
    progress: int = 0
    message: str = ""
    payload: dict[str, Any] = field(default_factory=dict)
    result: dict[str, Any] | None = None
    error: str | None = None
    attempts: int = 0
    max_attempts: int = 3
    next_retry_at: str | None = None

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


class TaskManagerService:
    """Task manager supporting in-memory, SQLite, and PostgreSQL persistence."""

    def __init__(self, db_path: str | None = None, db_url: str | None = None):
        self._tasks: dict[str, TaskRecord] = {}
        self._db_url = db_url or os.getenv("OMRAT_DATABASE_URL", "").strip() or None
        self._db_path = db_path
        self._backend = "memory"

        if self._db_url:
            self._configure_from_db_url(self._db_url)
        elif db_path:
            self._backend = "sqlite"
            self._initialize_sqlite()

    def _configure_from_db_url(self, db_url: str) -> None:
        if db_url.startswith("sqlite:///"):
            self._db_path = db_url.replace("sqlite:///", "", 1)
            self._backend = "sqlite"
            self._initialize_sqlite()
            return
        if db_url.startswith("postgresql://") or db_url.startswith("postgres://"):
            self._backend = "postgres"
            self._initialize_postgres()
            return
        raise ValueError(f"Unsupported OMRAT_DATABASE_URL scheme: {db_url}")

    @staticmethod
    def _now() -> str:
        return datetime.now(tz=timezone.utc).isoformat()

    def _initialize_sqlite(self) -> None:
        db_parent = Path(self._db_path).expanduser().resolve().parent
        db_parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(self._db_path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS task_records (
                    task_id TEXT PRIMARY KEY,
                    state TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    progress INTEGER NOT NULL,
                    message TEXT NOT NULL,
                    payload_json TEXT NOT NULL,
                    result_json TEXT,
                    error TEXT,
                    attempts INTEGER NOT NULL DEFAULT 0,
                    max_attempts INTEGER NOT NULL DEFAULT 3,
                    next_retry_at TEXT
                )
                """
            )
            conn.commit()

    def _initialize_postgres(self) -> None:
        conn = self._connect_postgres()
        with conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    CREATE TABLE IF NOT EXISTS omrat_task_records (
                        task_id TEXT PRIMARY KEY,
                        state TEXT NOT NULL,
                        created_at TEXT NOT NULL,
                        updated_at TEXT NOT NULL,
                        progress INTEGER NOT NULL,
                        message TEXT NOT NULL,
                        payload_json JSONB NOT NULL,
                        result_json JSONB,
                        error TEXT,
                        attempts INTEGER NOT NULL DEFAULT 0,
                        max_attempts INTEGER NOT NULL DEFAULT 3,
                        next_retry_at TEXT
                    )
                    """
                )
        conn.close()

    @staticmethod
    def _connect_psycopg_module():
        try:
            import psycopg  # type: ignore

            return psycopg, "psycopg"
        except Exception:
            try:
                import psycopg2  # type: ignore

                return psycopg2, "psycopg2"
            except Exception as exc:
                raise RuntimeError(
                    "PostgreSQL persistence requires psycopg/psycopg2 to be installed"
                ) from exc

    def _connect_postgres(self):
        module, _name = self._connect_psycopg_module()
        return module.connect(self._db_url)

    def _write_sqlite(self, record: TaskRecord) -> None:
        if self._backend != "sqlite":
            return
        with sqlite3.connect(self._db_path) as conn:
            conn.execute(
                """
                INSERT INTO task_records(task_id, state, created_at, updated_at, progress, message, payload_json, result_json, error, attempts, max_attempts, next_retry_at)
                VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(task_id) DO UPDATE SET
                    state = excluded.state,
                    updated_at = excluded.updated_at,
                    progress = excluded.progress,
                    message = excluded.message,
                    payload_json = excluded.payload_json,
                    result_json = excluded.result_json,
                    error = excluded.error,
                    attempts = excluded.attempts,
                    max_attempts = excluded.max_attempts,
                    next_retry_at = excluded.next_retry_at
                """,
                (
                    record.task_id,
                    record.state,
                    record.created_at,
                    record.updated_at,
                    record.progress,
                    record.message,
                    json.dumps(record.payload),
                    json.dumps(record.result) if record.result is not None else None,
                    record.error,
                    record.attempts,
                    record.max_attempts,
                    record.next_retry_at,
                ),
            )
            conn.commit()

    def _read_sqlite(self, task_id: str) -> TaskRecord | None:
        if self._backend != "sqlite":
            return None
        with sqlite3.connect(self._db_path) as conn:
            row = conn.execute(
                """
                SELECT task_id, state, created_at, updated_at, progress, message, payload_json, result_json, error, attempts, max_attempts, next_retry_at
                FROM task_records
                WHERE task_id = ?
                """,
                (task_id,),
            ).fetchone()
        if row is None:
            return None
        payload = json.loads(row[6]) if row[6] else {}
        result = json.loads(row[7]) if row[7] else None
        return TaskRecord(
            task_id=row[0],
            state=row[1],
            created_at=row[2],
            updated_at=row[3],
            progress=int(row[4]),
            message=row[5],
            payload=payload,
            result=result,
            error=row[8],
            attempts=int(row[9]),
            max_attempts=int(row[10]),
            next_retry_at=row[11],
        )

    def _write_postgres(self, record: TaskRecord) -> None:
        if self._backend != "postgres":
            return None
        conn = self._connect_postgres()
        with conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO omrat_task_records(task_id, state, created_at, updated_at, progress, message, payload_json, result_json, error, attempts, max_attempts, next_retry_at)
                    VALUES(%s, %s, %s, %s, %s, %s, %s::jsonb, %s::jsonb, %s, %s, %s, %s)
                    ON CONFLICT(task_id) DO UPDATE SET
                        state = EXCLUDED.state,
                        updated_at = EXCLUDED.updated_at,
                        progress = EXCLUDED.progress,
                        message = EXCLUDED.message,
                        payload_json = EXCLUDED.payload_json,
                        result_json = EXCLUDED.result_json,
                        error = EXCLUDED.error,
                        attempts = EXCLUDED.attempts,
                        max_attempts = EXCLUDED.max_attempts,
                        next_retry_at = EXCLUDED.next_retry_at
                    """,
                    (
                        record.task_id,
                        record.state,
                        record.created_at,
                        record.updated_at,
                        record.progress,
                        record.message,
                        json.dumps(record.payload),
                        json.dumps(record.result) if record.result is not None else None,
                        record.error,
                        record.attempts,
                        record.max_attempts,
                        record.next_retry_at,
                    ),
                )
        conn.close()
        return None

    def _read_postgres(self, task_id: str) -> TaskRecord | None:
        if self._backend != "postgres":
            return None
        conn = self._connect_postgres()
        with conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT task_id, state, created_at, updated_at, progress, message, payload_json, result_json, error, attempts, max_attempts, next_retry_at
                    FROM omrat_task_records
                    WHERE task_id = %s
                    """,
                    (task_id,),
                )
                row = cur.fetchone()
        conn.close()
        if row is None:
            return None
        payload = row[6] if isinstance(row[6], dict) else json.loads(row[6]) if row[6] else {}
        result = row[7] if isinstance(row[7], dict) else json.loads(row[7]) if row[7] else None
        return TaskRecord(
            task_id=row[0],
            state=row[1],
            created_at=row[2],
            updated_at=row[3],
            progress=int(row[4]),
            message=row[5],
            payload=payload,
            result=result,
            error=row[8],
            attempts=int(row[9]),
            max_attempts=int(row[10]),
            next_retry_at=row[11],
        )

    def _persist_record(self, record: TaskRecord) -> None:
        if self._backend == "sqlite":
            self._write_sqlite(record)
        elif self._backend == "postgres":
            self._write_postgres(record)

    def _load_record(self, task_id: str) -> TaskRecord | None:
        if self._backend == "sqlite":
            return self._read_sqlite(task_id)
        if self._backend == "postgres":
            return self._read_postgres(task_id)
        return None

    def create_task(
        self,
        payload: dict[str, Any],
        *,
        message: str = "Queued",
        max_attempts: int = 3,
    ) -> TaskRecord:
        task_id = str(uuid4())
        now = self._now()
        record = TaskRecord(
            task_id=task_id,
            state="queued",
            created_at=now,
            updated_at=now,
            message=message,
            payload=payload,
            max_attempts=max(1, int(max_attempts)),
        )
        self._tasks[task_id] = record
        self._persist_record(record)
        return record

    def get_task(self, task_id: str) -> TaskRecord:
        record = self._tasks.get(task_id)
        if record is not None:
            return record
        db_record = self._load_record(task_id)
        if db_record is None:
            raise KeyError(task_id)
        self._tasks[task_id] = db_record
        return db_record

    def start_task(self, task_id: str, *, message: str = "Running") -> TaskRecord:
        record = self.get_task(task_id)
        record.state = "running"
        record.progress = max(record.progress, 5)
        record.message = message
        record.updated_at = self._now()
        self._persist_record(record)
        return record

    def update_progress(self, task_id: str, progress: int, *, message: str = "") -> TaskRecord:
        record = self.get_task(task_id)
        record.progress = min(max(progress, 0), 100)
        if message:
            record.message = message
        record.updated_at = self._now()
        self._persist_record(record)
        return record

    def complete_task(self, task_id: str, result: dict[str, Any]) -> TaskRecord:
        record = self.get_task(task_id)
        record.state = "completed"
        record.progress = 100
        record.result = result
        record.message = "Completed"
        record.updated_at = self._now()
        self._persist_record(record)
        return record

    def fail_task(self, task_id: str, error: str) -> TaskRecord:
        record = self.get_task(task_id)
        record.attempts += 1
        record.state = "failed"
        record.error = error
        record.message = "Failed"
        record.updated_at = self._now()
        self._persist_record(record)
        return record

    def schedule_retry(self, task_id: str, *, error: str, retry_in_seconds: int = 10) -> TaskRecord:
        record = self.get_task(task_id)
        record.attempts += 1
        if record.attempts >= record.max_attempts:
            record.state = "failed"
            record.error = error
            record.message = "Failed (max retries reached)"
            record.next_retry_at = None
        else:
            record.state = "queued"
            record.error = error
            record.message = f"Retry scheduled after error: {error}"
            retry_at = datetime.now(tz=timezone.utc).timestamp() + max(retry_in_seconds, 1)
            record.next_retry_at = datetime.fromtimestamp(retry_at, tz=timezone.utc).isoformat()
        record.updated_at = self._now()
        self._persist_record(record)
        return record

    def claim_next_queued_task(self) -> TaskRecord | None:
        now_ts = datetime.now(tz=timezone.utc).timestamp()
        queued = sorted(
            (
                task
                for task in self._tasks.values()
                if task.state == "queued"
                and (not task.next_retry_at or datetime.fromisoformat(task.next_retry_at).timestamp() <= now_ts)
            ),
            key=lambda item: item.created_at,
        )
        if not queued:
            return None
        record = queued[0]
        record.state = "running"
        record.message = "Claimed by worker"
        record.updated_at = self._now()
        self._persist_record(record)
        return record
