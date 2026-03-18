"""In-memory task manager that mimics QGIS task lifecycle in web backend."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
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

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


class TaskManagerService:
    """Minimal task manager to mirror plugin background-run UX semantics."""

    def __init__(self):
        self._tasks: dict[str, TaskRecord] = {}

    @staticmethod
    def _now() -> str:
        return datetime.now(tz=timezone.utc).isoformat()

    def create_task(self, payload: dict[str, Any], *, message: str = "Queued") -> TaskRecord:
        task_id = str(uuid4())
        now = self._now()
        record = TaskRecord(
            task_id=task_id,
            state="queued",
            created_at=now,
            updated_at=now,
            message=message,
            payload=payload,
        )
        self._tasks[task_id] = record
        return record

    def get_task(self, task_id: str) -> TaskRecord:
        return self._tasks[task_id]

    def start_task(self, task_id: str, *, message: str = "Running") -> TaskRecord:
        record = self.get_task(task_id)
        record.state = "running"
        record.progress = max(record.progress, 5)
        record.message = message
        record.updated_at = self._now()
        return record

    def update_progress(self, task_id: str, progress: int, *, message: str = "") -> TaskRecord:
        record = self.get_task(task_id)
        record.progress = min(max(progress, 0), 100)
        if message:
            record.message = message
        record.updated_at = self._now()
        return record

    def complete_task(self, task_id: str, result: dict[str, Any]) -> TaskRecord:
        record = self.get_task(task_id)
        record.state = "completed"
        record.progress = 100
        record.result = result
        record.message = "Completed"
        record.updated_at = self._now()
        return record

    def fail_task(self, task_id: str, error: str) -> TaskRecord:
        record = self.get_task(task_id)
        record.state = "failed"
        record.error = error
        record.message = "Failed"
        record.updated_at = self._now()
        return record
