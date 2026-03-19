"""Pure-python route editing helpers for web-native map interactions."""

from __future__ import annotations

from dataclasses import dataclass
from math import atan2, degrees, hypot
from typing import Iterable


@dataclass(frozen=True)
class XYPoint:
    """Simple coordinate container shared across API boundaries."""

    x: float
    y: float

    def as_tuple(self) -> tuple[float, float]:
        return (self.x, self.y)


@dataclass(frozen=True)
class RouteSegmentDraft:
    """Canonical route segment structure generated from two clicked points."""

    segment_id: str
    route_id: str
    label: str
    leg_direction: str
    bearing_deg: float
    coords: list[tuple[float, float]]
    width_m: float
    start_point: tuple[float, float]
    end_point: tuple[float, float]
    tangent_line: dict[str, tuple[float, float]]
    corridor_polygon: list[tuple[float, float]]


class RouteEditingService:
    """Standalone implementation of route editing geometry helpers."""

    @staticmethod
    def parse_point(value: XYPoint | Iterable[float]) -> XYPoint:
        if isinstance(value, XYPoint):
            return value
        x, y = value
        return XYPoint(float(x), float(y))

    @staticmethod
    def is_valid_point_pair(start: XYPoint | Iterable[float], end: XYPoint | Iterable[float]) -> bool:
        start_point = RouteEditingService.parse_point(start)
        end_point = RouteEditingService.parse_point(end)

        def _is_near_origin(point: XYPoint) -> bool:
            return -1 <= point.x <= 1 and -1 <= point.y <= 1

        if _is_near_origin(start_point) or _is_near_origin(end_point):
            return False

        return hypot(end_point.x - start_point.x, end_point.y - start_point.y) > 0

    @staticmethod
    def calculate_tangent_line(
        mid: XYPoint | Iterable[float],
        start: XYPoint | Iterable[float],
        end: XYPoint | Iterable[float],
        offset: float,
    ) -> tuple[XYPoint, XYPoint]:
        mid_point = RouteEditingService.parse_point(mid)
        start_point = RouteEditingService.parse_point(start)
        end_point = RouteEditingService.parse_point(end)

        dx = end_point.x - start_point.x
        dy = end_point.y - start_point.y
        length = hypot(dx, dy)
        if length == 0:
            raise ValueError("Start and end points cannot be identical")

        unit_dx = dx / length
        unit_dy = dy / length
        perp_dx = -unit_dy
        perp_dy = unit_dx

        start_tangent = XYPoint(mid_point.x - perp_dx * offset, mid_point.y - perp_dy * offset)
        end_tangent = XYPoint(mid_point.x + perp_dx * offset, mid_point.y + perp_dy * offset)
        return start_tangent, end_tangent

    @staticmethod
    def calculate_bearing(start: XYPoint | Iterable[float], end: XYPoint | Iterable[float]) -> float:
        start_point = RouteEditingService.parse_point(start)
        end_point = RouteEditingService.parse_point(end)
        dx = end_point.x - start_point.x
        dy = end_point.y - start_point.y
        if dx == 0 and dy == 0:
            raise ValueError("Cannot compute bearing for identical points")
        return (degrees(atan2(dx, dy)) + 360) % 360

    @staticmethod
    def direction_label_from_bearing(bearing_deg: float) -> str:
        directions = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"]
        idx = int((bearing_deg + 22.5) // 45) % 8
        return directions[idx]

    @staticmethod
    def build_corridor_polygon(
        start: XYPoint | Iterable[float],
        end: XYPoint | Iterable[float],
        width_m: float,
    ) -> list[tuple[float, float]]:
        start_point = RouteEditingService.parse_point(start)
        end_point = RouteEditingService.parse_point(end)
        dx = end_point.x - start_point.x
        dy = end_point.y - start_point.y
        length = hypot(dx, dy)
        if length == 0:
            raise ValueError("Cannot build corridor for identical points")

        half_width = width_m / 2
        unit_dx = dx / length
        unit_dy = dy / length
        perp_dx = -unit_dy
        perp_dy = unit_dx

        s_left = (start_point.x + perp_dx * half_width, start_point.y + perp_dy * half_width)
        s_right = (start_point.x - perp_dx * half_width, start_point.y - perp_dy * half_width)
        e_right = (end_point.x - perp_dx * half_width, end_point.y - perp_dy * half_width)
        e_left = (end_point.x + perp_dx * half_width, end_point.y + perp_dy * half_width)

        return [s_left, s_right, e_right, e_left, s_left]

    @staticmethod
    def build_segment_draft(
        start: XYPoint | Iterable[float],
        end: XYPoint | Iterable[float],
        *,
        segment_id: int | str,
        route_id: int | str,
        width_m: float,
        tangent_offset_m: float,
    ) -> RouteSegmentDraft:
        start_point = RouteEditingService.parse_point(start)
        end_point = RouteEditingService.parse_point(end)
        if not RouteEditingService.is_valid_point_pair(start_point, end_point):
            raise ValueError("Invalid route points. Both points must be non-origin and distinct")

        bearing = RouteEditingService.calculate_bearing(start_point, end_point)
        mid = XYPoint((start_point.x + end_point.x) / 2, (start_point.y + end_point.y) / 2)
        tangent_start, tangent_end = RouteEditingService.calculate_tangent_line(
            mid, start_point, end_point, tangent_offset_m
        )

        corridor_polygon = RouteEditingService.build_corridor_polygon(
            start_point, end_point, width_m=float(width_m)
        )

        return RouteSegmentDraft(
            segment_id=str(segment_id),
            route_id=str(route_id),
            label=f"LEG_{segment_id}_{route_id}",
            leg_direction=RouteEditingService.direction_label_from_bearing(bearing),
            bearing_deg=round(bearing, 2),
            coords=[start_point.as_tuple(), end_point.as_tuple()],
            width_m=float(width_m),
            start_point=start_point.as_tuple(),
            end_point=end_point.as_tuple(),
            tangent_line={
                "start": tangent_start.as_tuple(),
                "end": tangent_end.as_tuple(),
            },
            corridor_polygon=corridor_polygon,
        )
