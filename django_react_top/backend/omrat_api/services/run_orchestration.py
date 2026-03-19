"""Run-task orchestration for Django API endpoints."""

from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import datetime, timezone
from uuid import uuid4

from omrat_api.adapters.execution_adapter import (
    ExecutionAdapter,
    PluginEquivalentExecutionAdapter,
    ShadowCascadeExecutionAdapter,
    SimulationExecutionAdapter,
)
from omrat_api.contracts import normalize_payload, serialize_payload
from omrat_api.errors import TaskExecutionError
from omrat_api.services.osm_scene_service import OSMSceneService


@dataclass(frozen=True)
class RunSummary:
    run_id: str
    status: str
    started_at: str
    report_path: str
    powered_summary: dict
    drifting_summary: dict
    osm_summary: dict


class RunOrchestrationService:
    """Coordinates normalization + execution adapter calls."""

    def __init__(self, adapter: ExecutionAdapter | None = None):
        self._adapter_mode = os.getenv("OMRAT_EXECUTION_ADAPTER", "auto").strip().lower()
        self.adapter = adapter or self._default_adapter()

    @staticmethod
    def _default_adapter() -> ExecutionAdapter:
        mode = os.getenv("OMRAT_EXECUTION_ADAPTER", "auto").strip().lower()
        if mode in {"plugin", "plugin-equivalent", "legacy"}:
            return PluginEquivalentExecutionAdapter()
        if mode == "simulation":
            return SimulationExecutionAdapter()
        if mode == "shadow-cascade":
            return ShadowCascadeExecutionAdapter()
        # auto mode defaults to plugin-equivalent; runtime fallback happens in start_run().
        return PluginEquivalentExecutionAdapter()

    def start_run(self, payload: dict) -> RunSummary:
        try:
            osm_context = payload.get("osm_context", {})
            enriched_payload = OSMSceneService.merge_objects_with_scene(payload, osm_context)
            land_crossings = OSMSceneService.compute_land_crossings(payload, osm_context)

            normalized = normalize_payload(enriched_payload)
            run_id = payload.get("run_id") or str(uuid4())
            started_at = datetime.now(tz=timezone.utc).isoformat()
            serialized = serialize_payload(normalized)
            try:
                artifacts = self.adapter.run_model(run_id=run_id, payload=serialized)
            except Exception:
                if self._adapter_mode != "auto":
                    raise
                try:
                    artifacts = ShadowCascadeExecutionAdapter().run_model(run_id=run_id, payload=serialized)
                except Exception:
                    artifacts = SimulationExecutionAdapter().run_model(run_id=run_id, payload=serialized)
            return RunSummary(
                run_id=artifacts.run_id,
                status="completed",
                started_at=started_at,
                report_path=artifacts.report_path,
                powered_summary=artifacts.powered_summary,
                drifting_summary=artifacts.drifting_summary,
                osm_summary={
                    "land_crossing_count": land_crossings["count"],
                    "osm_fixed_objects_added": max(
                        len(enriched_payload.get("objects", [])) - len(payload.get("objects", [])),
                        0,
                    ),
                },
            )
        except Exception as exc:
            raise TaskExecutionError("Failed to execute run task") from exc
