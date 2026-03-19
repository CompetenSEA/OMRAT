"""Stateful API-facing helpers for task-oriented workbench interactions.

This module provides stable function boundaries that can be wrapped by Django/DRF
views without exposing controller instance management details to web handlers.
"""

from __future__ import annotations

from typing import Any

from omrat_api.api.workbench_controller import WorkbenchController

_CONTROLLER = WorkbenchController()


def create_route_segment(payload: dict[str, Any]) -> dict[str, Any]:
    return _CONTROLLER.create_route_segment(payload)


def enqueue_run(payload: dict[str, Any]) -> dict[str, Any]:
    return _CONTROLLER.enqueue_run(payload)


def execute_run(task_id: str) -> dict[str, Any]:
    return _CONTROLLER.execute_run(task_id)


def execute_run_async(task_id: str) -> dict[str, Any]:
    return _CONTROLLER.execute_run_async(task_id)


def process_queue_once() -> dict[str, Any]:
    return _CONTROLLER.process_queue_once()


def get_task(task_id: str) -> dict[str, Any]:
    return _CONTROLLER.get_task(task_id)


def sync_layers(payload: dict[str, Any]) -> dict[str, Any]:
    return _CONTROLLER.sync_layers(payload)


def preview_corridor_overlaps(payload: dict[str, Any]) -> dict[str, Any]:
    return _CONTROLLER.preview_corridor_overlaps(payload)
