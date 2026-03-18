"""Execution adapter boundary for pure-python engine execution (no QGIS dependency)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from omrat_api.engine.geometry_engine import GeometryEngine


@dataclass(frozen=True)
class RunArtifacts:
    run_id: str
    report_path: str
    powered_summary: dict
    drifting_summary: dict


class ExecutionAdapter(Protocol):
    """Abstraction for model execution side effects in worker/runtime backends."""

    def run_model(self, *, run_id: str, payload: dict) -> RunArtifacts:
        """Execute a full run and return report metadata + summaries."""


class SimulationExecutionAdapter:
    """Pure-python adapter that mimics route/object overlap behavior."""

    def run_model(self, *, run_id: str, payload: dict) -> RunArtifacts:
        segments = GeometryEngine.parse_segments(payload.get("segment_data", []))
        objects = GeometryEngine.parse_objects(payload.get("objects", []))
        overlaps = GeometryEngine.compute_corridor_overlaps(segments, objects)

        report_path = payload.get("settings", {}).get("report_path") or f"/tmp/{run_id}.md"
        total_overlap = sum(item.overlap_area_m2 for item in overlaps)

        return RunArtifacts(
            run_id=run_id,
            report_path=report_path,
            powered_summary={
                "segments": len(segments),
                "traffic_rows": len(payload.get("traffic_data", [])),
            },
            drifting_summary={
                "objects": len(objects),
                "overlap_hits": len(overlaps),
                "overlap_area_m2": round(total_overlap, 3),
            },
        )
