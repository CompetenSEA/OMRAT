import pytest
from shapely.geometry import LineString
import sys
from pathlib import Path

repo_root = Path(__file__).resolve().parents[3]
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

from geometries.drift.corridor import create_projected_corridor as create_projected_corridor_refactored
from geometries.drift.corridor import create_base_surface as create_base_surface_refactored
from geometries.drift_corridor import create_projected_corridor as create_projected_corridor_legacy
from geometries.drift_corridor import create_base_surface as create_base_surface_legacy


@pytest.mark.parametrize(
    "leg_coords,half_width,spec_angle,projection",
    [
        ([(0, 0), (1000, 0)], 80.0, 0.0, 500.0),    # North
        ([(0, 0), (1000, 0)], 120.0, 90.0, 750.0),  # West
        ([(0, 0), (800, 200)], 60.0, 180.0, 300.0),  # South
        ([(0, 0), (800, 200)], 40.0, 270.0, 900.0),  # East
        ([(10, 20), (500, 700)], 100.0, 315.0, 1200.0),  # NorthEast
    ],
)
def test_refactored_corridor_matches_legacy_geometry(leg_coords, half_width, spec_angle, projection):
    leg = LineString(leg_coords)

    # Refactored module uses compass convention:
    # 0=N, 90=W, 180=S, 270=E
    new_corridor = create_projected_corridor_refactored(leg, half_width, spec_angle, projection)

    # Legacy module uses math angle convention:
    # 0=E, 90=N, 180=W, 270=S
    legacy_math_angle = 90.0 + spec_angle
    old_corridor = create_projected_corridor_legacy(leg, half_width, legacy_math_angle, projection)

    assert new_corridor.is_valid
    assert old_corridor.is_valid
    assert new_corridor.area == pytest.approx(old_corridor.area, rel=1e-9, abs=1e-6)
    assert new_corridor.symmetric_difference(old_corridor).area == pytest.approx(0.0, abs=1e-6)


@pytest.mark.parametrize(
    "leg_coords,half_width",
    [
        ([(0, 0), (1000, 0)], 80.0),
        ([(0, 0), (800, 200)], 120.0),
        ([(10, 20), (500, 700)], 60.0),
    ],
)
def test_refactored_base_surface_matches_legacy_geometry(leg_coords, half_width):
    leg = LineString(leg_coords)
    new_surface = create_base_surface_refactored(leg, half_width)
    old_surface = create_base_surface_legacy(leg, half_width)

    assert new_surface.is_valid
    assert old_surface.is_valid
    assert new_surface.area == pytest.approx(old_surface.area, rel=1e-9, abs=1e-6)
    assert new_surface.symmetric_difference(old_surface).area == pytest.approx(0.0, abs=1e-6)
