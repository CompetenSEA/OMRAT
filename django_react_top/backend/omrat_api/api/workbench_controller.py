"""Stateful workbench controller for Django/DRF endpoints.

This layer provides web-native long-running task tracking semantics.
"""

from __future__ import annotations

import os
from concurrent.futures import ThreadPoolExecutor
from typing import Any

from omrat_api.api.workbench_api import (
    build_osm_scene,
    create_route_segment,
    evaluate_land_crossings,
    ingest_ais,
    import_project,
    load_project,
    preview_corridor_overlaps,
    start_analysis,
    sync_layers,
)
from omrat_api.errors import TaskExecutionError
from omrat_api.services.run_worker import RunQueueWorker
from omrat_api.services.task_manager import TaskManagerService

_TASK_MANAGER = TaskManagerService(
    db_path=os.getenv("OMRAT_TASK_DB_PATH"),
    db_url=os.getenv("OMRAT_DATABASE_URL"),
)
_RUN_EXECUTOR = ThreadPoolExecutor(max_workers=2, thread_name_prefix="omrat-runner")


class WorkbenchController:
    """Unified stateful façade for frontend polling workflows."""

    def load_project(self, payload: dict[str, Any]) -> dict[str, Any]:
        return load_project(payload)

    def import_project(
        self, current_state: dict[str, Any], incoming_payload: dict[str, Any], *, merge: bool
    ) -> dict[str, Any]:
        return import_project(current_state, incoming_payload, merge=merge)

    def ingest_ais(self, rows: list[dict[str, Any]]) -> dict[str, Any]:
        return ingest_ais(rows)

    def build_osm_scene(self, osm_context: dict[str, Any]) -> dict[str, Any]:
        return build_osm_scene(osm_context)

    def evaluate_land_crossings(
        self, payload: dict[str, Any], osm_context: dict[str, Any]
    ) -> dict[str, Any]:
        return evaluate_land_crossings(payload, osm_context)


    def create_route_segment(self, payload: dict[str, Any]) -> dict[str, Any]:
        return create_route_segment(payload)

    def sync_layers(self, payload: dict[str, Any]) -> dict[str, Any]:
        return sync_layers(payload)

    def preview_corridor_overlaps(self, payload: dict[str, Any]) -> dict[str, Any]:
        return preview_corridor_overlaps(payload)

    def enqueue_run(self, payload: dict[str, Any]) -> dict[str, Any]:
        task = _TASK_MANAGER.create_task(payload, message="Run queued", max_attempts=payload.get("max_attempts", 3))
        return task.as_dict()

    def execute_run(self, task_id: str) -> dict[str, Any]:
        task = _TASK_MANAGER.start_task(task_id, message="Preparing run")
        try:
            _TASK_MANAGER.update_progress(task_id, 25, message="Building OSM scene")
            if task.payload.get("osm_context"):
                _TASK_MANAGER.update_progress(task_id, 45, message="Evaluating land crossings")
                evaluate_land_crossings(task.payload, task.payload["osm_context"])

            _TASK_MANAGER.update_progress(task_id, 70, message="Computing overlaps")
            result = start_analysis(task.payload)
            _TASK_MANAGER.update_progress(task_id, 90, message="Preparing report metadata")
            completed = _TASK_MANAGER.complete_task(task_id, result)
            return completed.as_dict()
        except Exception as exc:
            _TASK_MANAGER.fail_task(task_id, str(exc))
            raise TaskExecutionError(f"Task {task_id} failed") from exc

    def get_task(self, task_id: str) -> dict[str, Any]:
        return _TASK_MANAGER.get_task(task_id).as_dict()

    def execute_run_async(self, task_id: str) -> dict[str, Any]:
        """Schedule run execution on a background worker thread."""
        _RUN_EXECUTOR.submit(self.execute_run, task_id)
        task = _TASK_MANAGER.get_task(task_id)
        return task.as_dict()

    def process_queue_once(self) -> dict[str, Any]:
        worker = RunQueueWorker(controller=self, task_manager=_TASK_MANAGER)
        return worker.poll_once()
