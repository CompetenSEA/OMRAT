"""Service for applying OSM land/fixed-object assumptions to run payloads."""

from __future__ import annotations

from typing import Any

from shapely.geometry import LineString, Polygon

from omrat_api.engine.osm_scene import OSMScene


class OSMSceneService:
    """Composes user payload objects with fixed OSM scene objects."""

    @staticmethod
    def build_scene(osm_context: dict[str, Any]) -> dict[str, Any]:
        scene = OSMScene.from_geojson(
            land_features=osm_context.get("land_features"),
            fixed_object_features=osm_context.get("fixed_object_features"),
        )
        return scene.to_serializable()

    @staticmethod
    def merge_objects_with_scene(payload: dict[str, Any], osm_context: dict[str, Any]) -> dict[str, Any]:
        scene = OSMScene.from_geojson(
            land_features=osm_context.get("land_features"),
            fixed_object_features=osm_context.get("fixed_object_features"),
        )
        existing_objects = payload.get("objects", [])
        merged = {
            **payload,
            "objects": [*existing_objects, *scene.fixed_objects_as_payload()],
        }
        return merged

    @staticmethod
    def compute_land_crossings(payload: dict[str, Any], osm_context: dict[str, Any]) -> dict[str, Any]:
        scene = OSMScene.from_geojson(
            land_features=osm_context.get("land_features"),
            fixed_object_features=osm_context.get("fixed_object_features"),
        )

        crossings = []
        for segment in payload.get("segment_data", []):
            coords = segment.get("coords") or []
            if len(coords) < 2:
                continue
            line = LineString(coords)
            for land in scene.land_areas:
                hit_length = line.intersection(land.polygon).length
                if hit_length > 0:
                    crossings.append(
                        {
                            "segment_id": segment.get("segment_id", ""),
                            "land_id": land.land_id,
                            "crossing_length": float(hit_length),
                        }
                    )

        return {"land_crossings": crossings, "count": len(crossings)}
