"""OSM-backed scene model used for map assumptions and visualization.

This module does not call external map APIs; it accepts pre-fetched or static OSM-like
GeoJSON fragments and normalizes them for analysis and preview.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Iterable

from shapely.geometry import Polygon, shape


@dataclass(frozen=True)
class LandArea:
    land_id: str
    polygon: Polygon


@dataclass(frozen=True)
class FixedObject:
    feature_id: str
    object_type: str
    polygon: Polygon
    source: str


class OSMScene:
    """Normalized OSM scene context with land and fixed objects."""

    def __init__(self, land_areas: list[LandArea], fixed_objects: list[FixedObject]):
        self.land_areas = land_areas
        self.fixed_objects = fixed_objects

    @staticmethod
    def from_geojson(
        *,
        land_features: Iterable[dict[str, Any]] | None,
        fixed_object_features: Iterable[dict[str, Any]] | None,
    ) -> "OSMScene":
        lands: list[LandArea] = []
        for idx, feature in enumerate(land_features or []):
            geom = shape(feature.get("geometry", {}))
            if geom.is_empty:
                continue
            if geom.geom_type == "MultiPolygon":
                for sub_idx, poly in enumerate(geom.geoms):
                    lands.append(LandArea(land_id=f"land-{idx}-{sub_idx}", polygon=poly))
            elif geom.geom_type == "Polygon":
                lands.append(LandArea(land_id=f"land-{idx}", polygon=geom))

        objects: list[FixedObject] = []
        for idx, feature in enumerate(fixed_object_features or []):
            geom = shape(feature.get("geometry", {}))
            if geom.is_empty:
                continue
            if geom.geom_type == "Polygon":
                polygons = [geom]
            elif geom.geom_type == "MultiPolygon":
                polygons = list(geom.geoms)
            else:
                continue

            tags = feature.get("properties", {})
            object_type = (
                tags.get("man_made")
                or tags.get("building")
                or tags.get("seamark:type")
                or tags.get("type")
                or "fixed_object"
            )
            for sub_idx, poly in enumerate(polygons):
                objects.append(
                    FixedObject(
                        feature_id=f"osm-fixed-{idx}-{sub_idx}",
                        object_type=str(object_type),
                        polygon=poly,
                        source="osm",
                    )
                )

        return OSMScene(land_areas=lands, fixed_objects=objects)

    def to_serializable(self) -> dict[str, Any]:
        return {
            "land_areas": [
                {"land_id": area.land_id, "coords": list(area.polygon.exterior.coords)}
                for area in self.land_areas
            ],
            "fixed_objects": [
                {
                    "feature_id": obj.feature_id,
                    "object_type": obj.object_type,
                    "coords": list(obj.polygon.exterior.coords),
                    "source": obj.source,
                }
                for obj in self.fixed_objects
            ],
        }

    def fixed_objects_as_payload(self) -> list[dict[str, Any]]:
        return [
            {
                "feature_id": obj.feature_id,
                "object_type": obj.object_type,
                "coords": list(obj.polygon.exterior.coords),
                "source": obj.source,
            }
            for obj in self.fixed_objects
        ]
