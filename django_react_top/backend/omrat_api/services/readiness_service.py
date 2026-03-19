"""Project readiness checks for plugin-parity web workflows."""

from __future__ import annotations

from typing import Any, Mapping

from omrat_api.contracts import normalize_payload


class ProjectReadinessService:
    """Evaluates whether a payload is ready for run execution.

    The checks mirror the core prerequisites from the legacy QGIS plugin:
    routes, traffic, hazards/depths, and run metadata.
    """

    @staticmethod
    def assess(payload: Mapping[str, Any]) -> dict[str, Any]:
        normalized = normalize_payload(payload)
        segment_data = normalized["segment_data"]
        traffic_data = normalized["traffic_data"]
        depths = normalized["depths"]
        objects = normalized["objects"]
        settings = normalized["settings"]

        issues: list[dict[str, Any]] = []

        if not segment_data:
            issues.append(
                {
                    "id": "routes_missing",
                    "area": "routes",
                    "severity": "blocking",
                    "message": "No route segments are defined.",
                    "recommendation": "Create at least one route segment before running analysis.",
                }
            )

        segments_without_coords = [item.segment_id for item in segment_data if not item.coords]
        if segments_without_coords:
            issues.append(
                {
                    "id": "route_coords_missing",
                    "area": "routes",
                    "severity": "blocking",
                    "message": "One or more route segments are missing coordinates.",
                    "recommendation": "Ensure each segment has valid coordinate geometry.",
                    "segments": segments_without_coords,
                }
            )

        traffic_segments = {item.segment_id for item in traffic_data}
        segments_without_traffic = [
            item.segment_id for item in segment_data if item.segment_id not in traffic_segments
        ]
        if segments_without_traffic:
            issues.append(
                {
                    "id": "traffic_missing_for_segments",
                    "area": "traffic",
                    "severity": "blocking",
                    "message": "One or more segments have no traffic rows.",
                    "recommendation": "Populate traffic rows for all route segments.",
                    "segments": segments_without_traffic,
                }
            )

        if not depths:
            issues.append(
                {
                    "id": "depths_missing",
                    "area": "depths",
                    "severity": "warning",
                    "message": "No depth polygons are present.",
                    "recommendation": "Load depth data to improve grounding realism.",
                }
            )

        if not objects:
            issues.append(
                {
                    "id": "objects_missing",
                    "area": "objects",
                    "severity": "warning",
                    "message": "No fixed objects are present.",
                    "recommendation": "Load structures/objects if allision risk is in scope.",
                }
            )

        if not settings.model_name.strip():
            issues.append(
                {
                    "id": "model_name_missing",
                    "area": "run-settings",
                    "severity": "blocking",
                    "message": "Model name is empty.",
                    "recommendation": "Set a model name before starting a run.",
                }
            )

        if not settings.report_path.strip():
            issues.append(
                {
                    "id": "report_path_missing",
                    "area": "run-settings",
                    "severity": "warning",
                    "message": "Report path is empty.",
                    "recommendation": "Set a report path to persist run reporting outputs.",
                }
            )

        blocking_count = sum(1 for issue in issues if issue["severity"] == "blocking")
        warning_count = sum(1 for issue in issues if issue["severity"] == "warning")

        return {
            "ready_for_run": blocking_count == 0,
            "counts": {
                "segments": len(segment_data),
                "traffic_rows": len(traffic_data),
                "depth_rows": len(depths),
                "object_rows": len(objects),
                "blocking_issues": blocking_count,
                "warnings": warning_count,
            },
            "issues": issues,
        }
