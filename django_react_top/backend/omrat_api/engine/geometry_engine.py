"""Geospatial behavior simulation using Shapely only (no QGIS runtime)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List, Mapping

from shapely.geometry import LineString, Polygon
from shapely.geometry.base import BaseGeometry


@dataclass(frozen=True)
class SegmentGeometry:
    segment_id: str
    line: LineString
    width_m: float


@dataclass(frozen=True)
class ObjectGeometry:
    feature_id: str
    polygon: Polygon
    object_type: str


@dataclass(frozen=True)
class CorridorOverlap:
    segment_id: str
    feature_id: str
    overlap_area_m2: float
    overlap_polygon: list[tuple[float, float]] | None = None




def _extract_polygon_coords(geometry: BaseGeometry) -> list[tuple[float, float]] | None:
    if geometry.is_empty:
        return None
    candidate = geometry
    if geometry.geom_type == "MultiPolygon":
        try:
            candidate = max(geometry.geoms, key=lambda g: g.area)
        except ValueError:
            return None
    if candidate.geom_type != "Polygon":
        return None
    coords = list(candidate.exterior.coords)
    if len(coords) < 4:
        return None
    return [(float(x), float(y)) for x, y in coords]

class GeometryEngine:
    """Mimics plugin map/geometry calculations in pure backend code."""

    @staticmethod
    def parse_segments(segment_rows: Iterable[Mapping]) -> List[SegmentGeometry]:
        parsed: List[SegmentGeometry] = []
        for row in segment_rows:
            coords = row.get("coords") or []
            if len(coords) < 2:
                continue
            parsed.append(
                SegmentGeometry(
                    segment_id=row["segment_id"],
                    line=LineString(coords),
                    width_m=float(row.get("width_m", 0.0)),
                )
            )
        return parsed

    @staticmethod
    def parse_objects(object_rows: Iterable[Mapping]) -> List[ObjectGeometry]:
        parsed: List[ObjectGeometry] = []
        for row in object_rows:
            coords = row.get("coords") or []
            if len(coords) < 3:
                continue
            polygon = Polygon(coords)
            if not polygon.is_valid or polygon.is_empty:
                continue
            parsed.append(
                ObjectGeometry(
                    feature_id=row["feature_id"],
                    polygon=polygon,
                    object_type=row.get("object_type", "Unknown"),
                )
            )
        return parsed

    @staticmethod
    def compute_corridor_overlaps(
        segments: Iterable[SegmentGeometry], objects: Iterable[ObjectGeometry]
    ) -> List[CorridorOverlap]:
        overlaps: List[CorridorOverlap] = []
        object_list = list(objects)
        for segment in segments:
            corridor = segment.line.buffer(max(segment.width_m / 2.0, 0.0), cap_style=2)
            if corridor.is_empty:
                continue
            for obj in object_list:
                overlap_geometry = corridor.intersection(obj.polygon)
                area = overlap_geometry.area
                if area > 0:
                    overlaps.append(
                        CorridorOverlap(
                            segment_id=segment.segment_id,
                            feature_id=obj.feature_id,
                            overlap_area_m2=float(area),
                            overlap_polygon=_extract_polygon_coords(overlap_geometry),
                        )
                    )
        return overlaps
