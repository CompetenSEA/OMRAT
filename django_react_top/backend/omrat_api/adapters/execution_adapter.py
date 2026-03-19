"""Execution adapter boundary for pure-python engine execution (no QGIS dependency)."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import sys
from typing import Protocol

from shapely.geometry import LineString, Polygon

from omrat_api.engine.geometry_engine import GeometryEngine
from omrat_api.services.legacy_project_compat import LegacyProjectCompatService


def _load_shadow_adjusted_holes():
    """Load drift probability integration from repo root in backend-only runtime."""
    repo_root = Path(__file__).resolve().parents[4]
    if str(repo_root) not in sys.path:
        sys.path.insert(0, str(repo_root))
    from geometries.drift.probability_integration import compute_shadow_adjusted_holes
    return compute_shadow_adjusted_holes


def _load_legacy_calculation():
    """Load plugin-equivalent Calculation class from legacy compute package."""
    repo_root = Path(__file__).resolve().parents[4]
    if str(repo_root) not in sys.path:
        sys.path.insert(0, str(repo_root))
    from compute.run_calculations import Calculation
    return Calculation


class _NullLineEdit:
    def setText(self, _value: str) -> None:  # pragma: no cover - simple UI stub
        return None


class _PluginParentStub:
    """Minimal parent object required by legacy `Calculation` mixins."""

    class _MainWidget:
        LEPPoweredGrounding = _NullLineEdit()
        LEPPoweredAllision = _NullLineEdit()
        LEPHeadOnCollision = _NullLineEdit()
        LEPOvertakingCollision = _NullLineEdit()
        LEPCrossingCollision = _NullLineEdit()
        LEPMergingCollision = _NullLineEdit()
        LEPAAllision = _NullLineEdit()
        LEPAGrounding = _NullLineEdit()

    main_widget = _MainWidget()


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
                "engine": "simulation",
                "segments": len(segments),
                "traffic_rows": len(payload.get("traffic_data", [])),
            },
            drifting_summary={
                "engine": "simulation",
                "objects": len(objects),
                "overlap_hits": len(overlaps),
                "overlap_area_m2": round(total_overlap, 3),
            },
        )


def _line_from_segment_row(row: dict) -> LineString | None:
    coords = row.get("coords") or []
    if len(coords) < 2:
        return None
    try:
        p1 = tuple(coords[0])
        p2 = tuple(coords[-1])
        return LineString([p1, p2])
    except Exception:
        return None


def _polygon_from_object_row(row: dict) -> Polygon | None:
    coords = row.get("coords") or []
    if len(coords) < 3:
        return None
    try:
        poly = Polygon(coords)
        if poly.is_valid and not poly.is_empty and poly.area > 0:
            return poly
    except Exception:
        return None
    return None


class ShadowCascadeExecutionAdapter:
    """Numerical execution adapter using the drift shadow-cascade integration model."""

    def run_model(self, *, run_id: str, payload: dict) -> RunArtifacts:
        segments_raw = payload.get("segment_data", [])
        objects_raw = payload.get("objects", [])
        depths_raw = payload.get("depths", [])

        legs = [line for row in segments_raw if isinstance(row, dict) for line in [_line_from_segment_row(row)] if line is not None]
        structures = [poly for row in objects_raw if isinstance(row, dict) for poly in [_polygon_from_object_row(row)] if poly is not None]
        depth_polygons = [poly for row in depths_raw if isinstance(row, dict) for poly in [_polygon_from_object_row(row)] if poly is not None]
        obstacles = [(poly, 0.0, "structure", idx) for idx, poly in enumerate(structures)] + [
            (poly, 0.0, "depth", idx) for idx, poly in enumerate(depth_polygons)
        ]

        report_path = payload.get("settings", {}).get("report_path") or f"/tmp/{run_id}.md"
        if not legs or not obstacles:
            return SimulationExecutionAdapter().run_model(run_id=run_id, payload=payload)

        overlaps = GeometryEngine.compute_corridor_overlaps(
            GeometryEngine.parse_segments(segments_raw),
            GeometryEngine.parse_objects(objects_raw),
        )

        # Project with a conservative width/projection baseline.
        # These values align with default workbench geometry preview assumptions.
        integration = _load_shadow_adjusted_holes()(
            legs_utm=legs,
            obstacles_utm=obstacles,
            half_width=1250.0,
            projection_dist=5000.0,
        )

        effective_holes = integration.get("effective_holes", [])
        shadow_factors = integration.get("shadow_factors", [])
        flattened_holes = [v for leg_vals in effective_holes for dir_vals in leg_vals for v in dir_vals]
        flattened_shadow = [v for leg_vals in shadow_factors for dir_vals in leg_vals for v in dir_vals]

        return RunArtifacts(
            run_id=run_id,
            report_path=report_path,
            powered_summary={
                "engine": "shadow-cascade",
                "segments": len(legs),
                "traffic_rows": len(payload.get("traffic_data", [])),
            },
            drifting_summary={
                "engine": "shadow-cascade",
                "objects": len(structures),
                "depth_areas": len(depth_polygons),
                "overlap_hits": len(overlaps),
                "overlap_area_m2": round(sum(item.overlap_area_m2 for item in overlaps), 3),
                "effective_hole_sum": round(sum(flattened_holes), 6),
                "effective_hole_max": round(max(flattened_holes) if flattened_holes else 0.0, 6),
                "shadow_factor_min": round(min(flattened_shadow) if flattened_shadow else 0.0, 6),
            },
        )


class PluginEquivalentExecutionAdapter:
    """Adapter that executes legacy plugin compute pipeline when runtime is available."""

    def run_model(self, *, run_id: str, payload: dict) -> RunArtifacts:
        report_path = payload.get("settings", {}).get("report_path") or f"/tmp/{run_id}.md"
        legacy_payload = LegacyProjectCompatService.to_legacy(payload)

        Calculation = _load_legacy_calculation()
        calc = Calculation(_PluginParentStub())

        drifting_allision, drifting_grounding = calc.run_drifting_model(legacy_payload)
        collision = calc.run_ship_collision_model(legacy_payload)
        powered_grounding = calc.run_powered_grounding_model(legacy_payload)
        powered_allision = calc.run_powered_allision_model(legacy_payload)

        return RunArtifacts(
            run_id=run_id,
            report_path=report_path,
            powered_summary={
                "engine": "plugin-equivalent",
                "powered_grounding_prob": float(powered_grounding or 0.0),
                "powered_allision_prob": float(powered_allision or 0.0),
                "collision_total": float((collision or {}).get("total", 0.0)),
                "collision_breakdown": collision or {},
            },
            drifting_summary={
                "engine": "plugin-equivalent",
                "drifting_allision_prob": float(drifting_allision or 0.0),
                "drifting_grounding_prob": float(drifting_grounding or 0.0),
                "drifting_report": getattr(calc, "drifting_report", None) or {},
            },
        )
