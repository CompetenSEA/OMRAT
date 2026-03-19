"""Compatibility adapters between legacy .omrat plugin schema and web canonical payload."""

from __future__ import annotations

from typing import Any, Mapping


def _parse_point_string(raw: str) -> tuple[float, float] | None:
    value = str(raw or "").strip()
    if not value:
        return None
    if "(" in value and ")" in value:
        value = value.split("(", 1)[1].split(")", 1)[0]
    parts = [part for part in value.replace(",", " ").split() if part]
    if len(parts) < 2:
        return None
    try:
        return float(parts[0]), float(parts[1])
    except ValueError:
        return None


class LegacyProjectCompatService:
    @staticmethod
    def from_legacy(payload: Mapping[str, Any]) -> dict[str, Any]:
        segment_rows: list[dict[str, Any]] = []
        legacy_segments = payload.get("segment_data", {}) or {}
        for segment_id, segment in legacy_segments.items():
            start_point = _parse_point_string(segment.get("Start_Point") or segment.get("Start Point"))
            end_point = _parse_point_string(segment.get("End_Point") or segment.get("End Point"))
            coords = [start_point, end_point] if start_point and end_point else None
            segment_rows.append(
                {
                    "segment_id": str(segment.get("Segment_Id") or segment_id),
                    "from_waypoint": str(segment.get("Leg_name") or segment.get("Start_Point") or ""),
                    "to_waypoint": str(segment.get("End_Point") or ""),
                    "width_m": float(segment.get("Width") or 0),
                    "coords": coords,
                }
            )

        traffic_rows: list[dict[str, Any]] = []
        legacy_traffic = payload.get("traffic_data", {}) or {}
        for segment_id, directions in legacy_traffic.items():
            for direction, direction_data in (directions or {}).items():
                matrix = (direction_data or {}).get("Frequency (ships/year)", [])
                total_transits = 0.0
                for row in matrix:
                    if isinstance(row, list):
                        total_transits += sum(float(value or 0) for value in row)
                traffic_rows.append(
                    {
                        "segment_id": str(segment_id),
                        "ship_category": str(direction),
                        "annual_transits": total_transits,
                    }
                )

        depth_rows = []
        for item in payload.get("depths", []) or []:
            if isinstance(item, (list, tuple)) and len(item) >= 2:
                depth_rows.append({"feature_id": str(item[0]), "depth_m": float(item[1] or 0)})

        object_rows = []
        for item in payload.get("objects", []) or []:
            if isinstance(item, (list, tuple)) and len(item) >= 2:
                object_rows.append({"feature_id": str(item[0]), "object_type": "Structure", "coords": None})

        return {
            "segment_data": segment_rows,
            "traffic_data": traffic_rows,
            "depths": depth_rows,
            "objects": object_rows,
            "settings": {
                "model_name": str(payload.get("model_name") or payload.get("name") or "omrat-model"),
                "report_path": str(payload.get("report_path") or ""),
                "causation_version": "v1",
            },
        }

    @staticmethod
    def to_legacy(payload: Mapping[str, Any]) -> dict[str, Any]:
        segment_data = {}
        for index, segment in enumerate(payload.get("segment_data", []) or [], start=1):
            segment_id = str(segment.get("segment_id") or index)
            coords = segment.get("coords") or []
            start = coords[0] if len(coords) > 0 else (0.0, 0.0)
            end = coords[1] if len(coords) > 1 else (0.0, 0.0)
            segment_data[segment_id] = {
                "Segment_Id": segment_id,
                "Route_Id": 1,
                "Leg_name": f"LEG_{segment_id}",
                "Start_Point": f"{start[0]} {start[1]}",
                "End_Point": f"{end[0]} {end[1]}",
                "Width": float(segment.get("width_m") or 0),
                "dist1": [],
                "dist2": [],
            }

        traffic_data = {}
        for row in payload.get("traffic_data", []) or []:
            segment_id = str(row.get("segment_id") or "")
            if not segment_id:
                continue
            traffic_data.setdefault(segment_id, {})
            direction = str(row.get("ship_category") or "Direction")
            traffic_data[segment_id][direction] = {
                "Frequency (ships/year)": [[float(row.get("annual_transits") or 0)]],
                "Speed (knots)": [[0]],
                "Draught (meters)": [[0]],
                "Ship heights (meters)": [[0]],
                "Ship Beam (meters)": [[0]],
            }

        settings = payload.get("settings", {}) or {}
        return {
            "pc": {"p_pc": 1.6e-4, "d_pc": 1.0, "ai": 180.0},
            "drift": {
                "drift_p": 1.0,
                "anchor_p": 0.95,
                "anchor_d": 7.0,
                "speed": 1.0,
                "rose": {"0": 0.125, "45": 0.125, "90": 0.125, "135": 0.125, "180": 0.125, "225": 0.125, "270": 0.125, "315": 0.125},
                "repair": {"func": "", "std": 0.95, "loc": 0.2, "scale": 0.85, "use_lognormal": True},
            },
            "segment_data": segment_data,
            "traffic_data": traffic_data,
            "depths": [[str(item.get("feature_id")), str(item.get("depth_m", 0)), ""] for item in payload.get("depths", []) or []],
            "objects": [[str(item.get("feature_id")), "0", ""] for item in payload.get("objects", []) or []],
            "ship_categories": {"types": [], "length_intervals": []},
            "model_name": str(settings.get("model_name") or "omrat-model"),
            "report_path": str(settings.get("report_path") or ""),
        }
