"""Canonical normalized data contracts for OMRAT web APIs.

These contracts mirror plugin entities and provide one normalization path
for manual UI entries, AIS ingestion, and project import payloads.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Dict, Iterable, List, Mapping

from omrat_api.errors import ValidationError


@dataclass(frozen=True)
class SegmentRecord:
    segment_id: str
    from_waypoint: str
    to_waypoint: str
    width_m: float
    coords: list | None = None


@dataclass(frozen=True)
class TrafficRecord:
    segment_id: str
    ship_category: str
    annual_transits: float


@dataclass(frozen=True)
class DepthRecord:
    feature_id: str
    depth_m: float


@dataclass(frozen=True)
class ObjectRecord:
    feature_id: str
    object_type: str
    coords: list | None = None


@dataclass(frozen=True)
class SettingsRecord:
    model_name: str
    report_path: str
    causation_version: str


def _as_text(value: Any, *, default: str = "") -> str:
    if value is None:
        return default
    return str(value).strip()


def _as_float(value: Any, *, default: float = 0.0) -> float:
    try:
        if value is None or value == "":
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def _as_coords(value: Any) -> list | None:
    if not value or not isinstance(value, list):
        return None
    return value


def normalize_segments(records: Iterable[Mapping[str, Any]]) -> List[SegmentRecord]:
    normalized: List[SegmentRecord] = []
    for raw in records:
        segment_id = _as_text(raw.get("segment_id") or raw.get("id"))
        if not segment_id:
            continue

        width_m = _as_float(raw.get("width_m") or raw.get("width"))
        if width_m < 0:
            raise ValidationError(f"Segment '{segment_id}' has negative width: {width_m}")

        normalized.append(
            SegmentRecord(
                segment_id=segment_id,
                from_waypoint=_as_text(raw.get("from_waypoint") or raw.get("from")),
                to_waypoint=_as_text(raw.get("to_waypoint") or raw.get("to")),
                width_m=width_m,
                coords=_as_coords(raw.get("coords")),
            )
        )
    return normalized


def normalize_traffic(records: Iterable[Mapping[str, Any]]) -> List[TrafficRecord]:
    normalized: List[TrafficRecord] = []
    for raw in records:
        segment_id = _as_text(raw.get("segment_id"))
        ship_category = _as_text(raw.get("ship_category") or raw.get("category"))
        if not segment_id or not ship_category:
            continue

        annual_transits = _as_float(raw.get("annual_transits") or raw.get("transits"))
        if annual_transits < 0:
            raise ValidationError(
                f"Traffic row for segment '{segment_id}' has negative transits"
            )

        normalized.append(
            TrafficRecord(
                segment_id=segment_id,
                ship_category=ship_category,
                annual_transits=annual_transits,
            )
        )
    return normalized


def normalize_depths(records: Iterable[Mapping[str, Any]]) -> List[DepthRecord]:
    normalized: List[DepthRecord] = []
    for raw in records:
        feature_id = _as_text(raw.get("feature_id") or raw.get("id"))
        if not feature_id:
            continue
        normalized.append(
            DepthRecord(feature_id=feature_id, depth_m=_as_float(raw.get("depth_m")))
        )
    return normalized


def normalize_objects(records: Iterable[Mapping[str, Any]]) -> List[ObjectRecord]:
    normalized: List[ObjectRecord] = []
    for raw in records:
        feature_id = _as_text(raw.get("feature_id") or raw.get("id"))
        object_type = _as_text(raw.get("object_type") or raw.get("type"))
        if not feature_id or not object_type:
            continue
        normalized.append(
            ObjectRecord(
                feature_id=feature_id,
                object_type=object_type,
                coords=_as_coords(raw.get("coords")),
            )
        )
    return normalized


def normalize_settings(raw: Mapping[str, Any]) -> SettingsRecord:
    model_name = _as_text(raw.get("model_name"), default="omrat-model")
    if not model_name:
        raise ValidationError("Settings model_name cannot be empty")

    return SettingsRecord(
        model_name=model_name,
        report_path=_as_text(raw.get("report_path"), default=""),
        causation_version=_as_text(raw.get("causation_version"), default="v1"),
    )


def normalize_payload(payload: Mapping[str, Any]) -> Dict[str, Any]:
    return {
        "segment_data": normalize_segments(payload.get("segment_data", [])),
        "traffic_data": normalize_traffic(payload.get("traffic_data", [])),
        "depths": normalize_depths(payload.get("depths", [])),
        "objects": normalize_objects(payload.get("objects", [])),
        "settings": normalize_settings(payload.get("settings", {})),
    }


def serialize_payload(normalized: Mapping[str, Any]) -> Dict[str, Any]:
    """Convert normalized dataclass records to JSON-safe dicts."""
    return {
        "segment_data": [asdict(r) for r in normalized["segment_data"]],
        "traffic_data": [asdict(r) for r in normalized["traffic_data"]],
        "depths": [asdict(r) for r in normalized["depths"]],
        "objects": [asdict(r) for r in normalized["objects"]],
        "settings": asdict(normalized["settings"]),
    }
