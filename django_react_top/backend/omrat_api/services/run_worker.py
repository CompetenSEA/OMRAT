"""Queue worker for processing enqueued run tasks with retry semantics."""

from __future__ import annotations

from typing import Any, Protocol

from omrat_api.services.task_manager import TaskManagerService


class _ControllerProtocol(Protocol):
    def execute_run(self, task_id: str) -> dict[str, Any]: ...


class RunQueueWorker:
    """Processes queued run tasks one-by-one."""

    def __init__(self, controller: _ControllerProtocol, task_manager: TaskManagerService):
        self._controller = controller
        self._task_manager = task_manager

    def poll_once(self) -> dict[str, Any]:
        task = self._task_manager.claim_next_queued_task()
        if task is None:
            return {"processed": False, "message": "No queued task ready"}

        try:
            result = self._controller.execute_run(task.task_id)
            return {"processed": True, "task_id": task.task_id, "state": result["state"]}
        except Exception as exc:  # pragma: no cover - safety boundary
            retried = self._task_manager.schedule_retry(task.task_id, error=str(exc))
            return {"processed": True, "task_id": task.task_id, "state": retried.state}
