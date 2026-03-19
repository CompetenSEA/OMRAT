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
from omrat_api.services.legacy_project_compat import LegacyProjectCompatService
from omrat_api.services.iwrap_service import IWrapService
from omrat_api.services.osm_scene_service import OSMSceneService
from omrat_api.services.project_io import ProjectIOService
from omrat_api.services.readiness_service import ProjectReadinessService
from omrat_api.services.route_editing_service import RouteEditingService
from omrat_api.services.run_orchestration import RunOrchestrationService
from omrat_api.services.parity_corpus import parity_corpus_status as _parity_corpus_status

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


def build_osm_scene(osm_context: Dict[str, Any]) -> Dict[str, Any]:
    return OSMSceneService.build_scene(osm_context)


def evaluate_land_crossings(payload: Dict[str, Any], osm_context: Dict[str, Any]) -> Dict[str, Any]:
    return OSMSceneService.compute_land_crossings(payload, osm_context)




def create_route_segment(payload: Dict[str, Any]) -> Dict[str, Any]:
    draft = RouteEditingService.build_segment_draft(
        payload["start_point"],
        payload["end_point"],
        segment_id=payload.get("segment_id", 1),
        route_id=payload.get("route_id", 1),
        width_m=payload.get("width_m", 2500),
        tangent_offset_m=payload.get("tangent_offset_m", 2500),
    )
    return asdict(draft)

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
        "lifecycle": {
            "latest_revision": max(route_status["revision"], depth_status["revision"], object_status["revision"]),
            "layer_revisions": {
                "routes": route_status["revision"],
                "depths": depth_status["revision"],
                "objects": object_status["revision"],
            },
        },
        "render_surface": _render_surface_projection(payload),
    }


def _render_surface_projection(payload: Dict[str, Any]) -> Dict[str, Any]:
    segments = payload.get("segment_data", [])
    depths = payload.get("depths", [])
    objects = payload.get("objects", [])
    return {
        "routes": [
            {
                "segment_id": row.get("segment_id"),
                "coords": row.get("coords", []),
                "style": {"stroke": "#0f172a", "strokeWidth": 0.5},
            }
            for row in segments
            if isinstance(row, dict) and row.get("coords")
        ],
        "depths": [
            {
                "feature_id": row.get("feature_id"),
                "coords": row.get("coords", []),
                "style": {"fill": "#bfdbfe", "stroke": "#60a5fa", "opacity": 0.35},
            }
            for row in depths
            if isinstance(row, dict) and row.get("coords")
        ],
        "objects": [
            {
                "feature_id": row.get("feature_id"),
                "coords": row.get("coords", []),
                "style": {"fill": "#fb7185", "stroke": "#be123c", "opacity": 0.35},
            }
            for row in objects
            if isinstance(row, dict) and row.get("coords")
        ],
    }


def preview_corridor_overlaps(payload: Dict[str, Any]) -> Dict[str, Any]:
    segments = GeometryEngine.parse_segments(payload.get("segment_data", []))
    objects = GeometryEngine.parse_objects(payload.get("objects", []))
    overlaps = GeometryEngine.compute_corridor_overlaps(segments, objects)
    return {
        "overlaps": [asdict(item) for item in overlaps],
        "count": len(overlaps),
    }


def assess_project_readiness(payload: Mapping[str, Any]) -> Dict[str, Any]:
    return ProjectReadinessService.assess(payload)


def import_legacy_project(payload: Mapping[str, Any]) -> Dict[str, Any]:
    state = ProjectIOService.load(LegacyProjectCompatService.from_legacy(payload))
    return state.as_json_dict()


def export_legacy_project(payload: Mapping[str, Any]) -> Dict[str, Any]:
    state = ProjectIOService.load(payload)
    return {"legacy_payload": LegacyProjectCompatService.to_legacy(state.as_json_dict())}


def export_iwrap_xml(payload: Mapping[str, Any]) -> Dict[str, Any]:
    state = ProjectIOService.load(payload)
    return {"iwrap_xml": IWrapService.export_xml(state.as_json_dict())}


def import_iwrap_xml(xml_payload: str) -> Dict[str, Any]:
    state = ProjectIOService.load(IWrapService.import_xml(xml_payload))
    return state.as_json_dict()


def parity_corpus_status() -> Dict[str, Any]:
    return _parity_corpus_status()
