"""API-facing orchestration functions for Django/DRF views.

These functions are framework-agnostic to keep business logic testable.
"""

from __future__ import annotations

from dataclasses import asdict
from typing import Any, Dict, Mapping

from omrat_api.engine.geometry_engine import GeometryEngine
from omrat_api.engine.layer_store import LayerStore
from omrat_api.services.ais_ingestion import AISIngestionService
from omrat_api.services.map_layer_service import MapLayerService
from omrat_api.services.project_io import ProjectIOService
from omrat_api.services.run_orchestration import RunOrchestrationService

_LAYER_STORE = LayerStore()
_LAYER_SERVICE = MapLayerService(store=_LAYER_STORE)


def load_project(payload: Mapping[str, Any]) -> Dict[str, Any]:
    state = ProjectIOService.load(payload)
    return state.as_json_dict()


def import_project(
    current_state: Mapping[str, Any], incoming_payload: Mapping[str, Any], *, merge: bool
) -> Dict[str, Any]:
    state = ProjectIOService.import_into(current_state, incoming_payload, merge=merge)
    return state.as_json_dict()


def ingest_ais(rows: list[Mapping[str, Any]]) -> Dict[str, Any]:
    records = AISIngestionService.ingest(rows)
    return {"traffic_data": [asdict(r) for r in records], "rows_written": len(records)}


def start_analysis(payload: Dict[str, Any]) -> Dict[str, Any]:
    summary = RunOrchestrationService().start_run(payload)
    return asdict(summary)


def sync_layers(payload: Dict[str, Any]) -> Dict[str, Any]:
    route_status = _LAYER_SERVICE.sync_route_layer(payload.get("segment_data", []))
    depth_status = _LAYER_SERVICE.sync_depth_layer(payload.get("depths", []))
    object_status = _LAYER_SERVICE.sync_object_layer(payload.get("objects", []))
    return {
        "routes": route_status,
        "depths": depth_status,
        "objects": object_status,
    }


def preview_corridor_overlaps(payload: Dict[str, Any]) -> Dict[str, Any]:
    segments = GeometryEngine.parse_segments(payload.get("segment_data", []))
    objects = GeometryEngine.parse_objects(payload.get("objects", []))
    overlaps = GeometryEngine.compute_corridor_overlaps(segments, objects)
    return {
        "overlaps": [asdict(item) for item in overlaps],
        "count": len(overlaps),
    }
