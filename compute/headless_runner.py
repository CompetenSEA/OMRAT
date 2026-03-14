"""Headless OMRAT calculation runner.

This module lets the OMRAT compute layer run without a QGIS installation.
It performs three tasks in order:

1. Installs :mod:`qgis_shims` so every ``qgis.*`` and ``PyQt5.*`` import in
   the OMRAT source resolves to a :class:`unittest.mock.MagicMock`.
2. Monkey-patches :func:`compute.data_preparation.transform_to_utm` with a
   pure-Python implementation that uses :mod:`pyproj` and :mod:`shapely`
   instead of the QGIS coordinate-transform API.
3. Exposes :class:`HeadlessRunner` — a thin facade around
   :class:`compute.run_calculations.Calculation` that:
   - loads a ``.omrat`` project file (or accepts a raw dict),
   - normalises legacy formats,
   - runs the ship-ship, powered-grounding, and drifting models, and
   - returns a plain ``dict`` of results suitable for JSON serialisation.

Usage::

    from compute.headless_runner import HeadlessRunner

    runner = HeadlessRunner()
    results = runner.run_from_file("/path/to/project.omrat")
    # or
    results = runner.run_from_dict(omrat_data_dict)

The runner is thread-safe for concurrent calls as long as each call creates
its own ``HeadlessRunner`` instance (``Calculation`` is **not** thread-safe).
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock

# ---------------------------------------------------------------------------
# Step 1 — install QGIS/PyQt5 shims BEFORE any OMRAT import
# ---------------------------------------------------------------------------
# Resolve the OMRAT root so we can import qgis_shims regardless of cwd.
_OMRAT_ROOT = Path(__file__).resolve().parents[1]
if str(_OMRAT_ROOT) not in sys.path:
    sys.path.insert(0, str(_OMRAT_ROOT))

import qgis_shims  # noqa: E402  (must be after path setup)

qgis_shims.install()

# ---------------------------------------------------------------------------
# Step 2 — import OMRAT modules (now safe; shims are in sys.modules)
# ---------------------------------------------------------------------------
from compute.data_preparation import (  # noqa: E402
    clean_traffic,
    get_distribution,
    load_areas,
    safe_load_wkt,
    split_structures_and_depths,
    prepare_traffic_lists,
)
import compute.data_preparation as _dp  # noqa: E402  (for monkey-patching)


# ---------------------------------------------------------------------------
# Step 2a — replace transform_to_utm with pyproj implementation
# ---------------------------------------------------------------------------

def _transform_to_utm_pyproj(
    lines: list,
    objects: list,
) -> tuple[list, list, int]:
    """WGS84 → UTM transformation using pyproj (no QGIS required).

    Mirrors the interface of :func:`compute.data_preparation.transform_to_utm`:
    returns ``(transformed_lines, transformed_objects, utm_epsg)``.

    The UTM zone is determined from the centroid of all input geometries,
    matching the original QGIS-based logic exactly.
    """
    try:
        from pyproj import Transformer
        from shapely.ops import transform as shp_transform
    except ImportError as exc:
        raise ImportError(
            "pyproj is required for headless OMRAT coordinate transforms.  "
            "Install it with: pip install pyproj"
        ) from exc

    if not lines and not objects:
        return lines, objects, 32633  # fallback: UTM zone 33N

    all_geoms = list(lines) + list(objects)
    cx = sum(g.centroid.x for g in all_geoms) / len(all_geoms)
    cy = sum(g.centroid.y for g in all_geoms) / len(all_geoms)

    utm_zone = int((cx + 180) // 6) + 1
    utm_epsg = (32600 if cy >= 0 else 32700) + utm_zone

    transformer = Transformer.from_crs(
        "EPSG:4326", f"EPSG:{utm_epsg}", always_xy=True
    )

    def _transform(x, y, z=None):  # shapely passes z for 3-D geometries
        if z is not None:
            return transformer.transform(x, y, z)
        return transformer.transform(x, y)

    transformed_lines = [shp_transform(_transform, geom) for geom in lines]
    transformed_objects = [shp_transform(_transform, geom) for geom in objects]

    return transformed_lines, transformed_objects, utm_epsg


# Patch the function in the module so callers via `from compute.data_preparation
# import transform_to_utm` see the replacement.
_dp.transform_to_utm = _transform_to_utm_pyproj

# Also patch it in any already-imported sibling modules that imported the
# function by name (e.g. compute.drifting_model).
for _mod_name, _mod in list(sys.modules.items()):
    if (
        _mod_name.startswith("compute.")
        and _mod_name != "compute.data_preparation"
        and hasattr(_mod, "transform_to_utm")
    ):
        setattr(_mod, "transform_to_utm", _transform_to_utm_pyproj)

# ---------------------------------------------------------------------------
# Step 3 — import the Calculation facade (depends on shims being installed)
# ---------------------------------------------------------------------------
from compute.run_calculations import Calculation  # noqa: E402


# ---------------------------------------------------------------------------
# HeadlessOMRAT — minimal parent object expected by Calculation
# ---------------------------------------------------------------------------

class _HeadlessParent:
    """Minimal stand-in for the ``OMRAT`` plugin object.

    ``Calculation`` accesses ``self.p.<widget>`` to push results into the UI.
    All widget attributes here are MagicMock objects so those calls silently
    succeed without a Qt event loop.
    """

    def __init__(self, data: dict[str, Any]) -> None:
        self._data = data
        # UI widgets — every ``setText`` / ``text`` call is a no-op
        self.main_widget = MagicMock()
        self.iface = MagicMock()
        self.canvas = MagicMock()

    # Convenience accessor used by some Calculation helpers
    @property
    def ship_categories(self) -> dict[str, Any]:
        return self._data.get("ship_categories", {})

    @property
    def pc(self) -> dict[str, Any]:
        return self._data.get("pc", {})

    @property
    def drift(self) -> dict[str, Any]:
        return self._data.get("drift", {})


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

class HeadlessRunner:
    """Run OMRAT calculations without a QGIS installation.

    Each instance is independent; create a new one per calculation request.
    """

    # Default ship categories that match OMRAT's built-in UI defaults
    DEFAULT_SHIP_CATEGORIES: dict[str, Any] = {
        "types": [
            "Tanker",
            "Bulk carrier",
            "General cargo",
            "Container",
            "Ro-Ro / Ferry",
            "High-speed craft",
            "Fishing",
            "Other",
        ],
        "length_intervals": [
            {"min": 0, "max": 50, "label": "< 50 m"},
            {"min": 50, "max": 100, "label": "50–100 m"},
            {"min": 100, "max": 150, "label": "100–150 m"},
            {"min": 150, "max": 200, "label": "150–200 m"},
            {"min": 200, "max": 250, "label": "200–250 m"},
            {"min": 250, "max": 300, "label": "250–300 m"},
            {"min": 300, "max": 350, "label": "300–350 m"},
            {"min": 350, "max": 400, "label": "350–400 m"},
            {"min": 400, "max": 450, "label": "400–450 m"},
            {"min": 450, "max": 999, "label": "> 450 m"},
        ],
        "selection_mode": "size_x_type",
    }

    def __init__(self) -> None:
        self._data: dict[str, Any] | None = None
        self._calc: Calculation | None = None

    # ------------------------------------------------------------------
    # Data loading
    # ------------------------------------------------------------------

    def load_file(self, path: str | os.PathLike) -> "HeadlessRunner":
        """Load a ``.omrat`` project file.

        Applies the same legacy-normalisation logic as
        :meth:`omrat_utils.storage.Storage.load_from_path` without requiring
        PyQt.

        Returns ``self`` for chaining.
        """
        path = Path(path)
        with path.open("r", encoding="utf-8") as fh:
            raw = json.load(fh)
        self._data = self._normalize(raw)
        self._calc = self._make_calculation()
        return self

    def load_dict(self, data: dict[str, Any]) -> "HeadlessRunner":
        """Load project data from a plain dict (e.g. parsed from a POST body).

        Returns ``self`` for chaining.
        """
        self._data = self._normalize(dict(data))
        self._calc = self._make_calculation()
        return self

    # ------------------------------------------------------------------
    # High-level runners
    # ------------------------------------------------------------------

    def run_ship_collision(self) -> dict[str, Any]:
        """Run the ship-ship collision model.

        Returns a dict with ``collision_frequency`` (events/year) and a
        per-leg breakdown.
        """
        self._assert_loaded()
        result = self._calc.run_ship_collision_model(self._data)  # type: ignore[union-attr]
        freq = getattr(self._calc, "ship_collision_prob", 0.0)
        report = getattr(self._calc, "collision_report", {}) or {}
        return {
            "collision_frequency": float(freq),
            "collision_report": report,
            "raw_result": result,
        }

    def run_powered_grounding(self) -> dict[str, Any]:
        """Run the powered grounding / allision model."""
        self._assert_loaded()
        result = self._calc.run_powered_grounding_model(self._data)  # type: ignore[union-attr]
        return {"powered_grounding_frequency": float(result or 0.0)}

    def run_drifting(self) -> dict[str, Any]:
        """Run the drifting model (allision + grounding)."""
        self._assert_loaded()
        result = self._calc.run_drifting_model(self._data)  # type: ignore[union-attr]
        allision = getattr(self._calc, "drifting_allision_prob", 0.0)
        grounding = getattr(self._calc, "drifting_grounding_prob", 0.0)
        report = getattr(self._calc, "drifting_report", {}) or {}
        return {
            "drifting_allision_frequency": float(allision),
            "drifting_grounding_frequency": float(grounding),
            "drifting_report": report,
            "raw_result": result,
        }

    def run_all(self) -> dict[str, Any]:
        """Run all three models and aggregate results.

        Returns a single dict suitable for JSON serialisation.
        """
        collision = self.run_ship_collision()
        powered = self.run_powered_grounding()
        drifting = self.run_drifting()

        total = (
            collision["collision_frequency"]
            + powered["powered_grounding_frequency"]
            + drifting["drifting_allision_frequency"]
            + drifting["drifting_grounding_frequency"]
        )

        return {
            "total_annual_frequency": total,
            "ship_collision": collision,
            "powered_grounding": powered,
            "drifting": drifting,
        }

    # ------------------------------------------------------------------
    # Convenience class-methods (factory + run in one call)
    # ------------------------------------------------------------------

    @classmethod
    def run_from_file(cls, path: str | os.PathLike) -> dict[str, Any]:
        """Load *path* and run all models.  Returns the aggregated results."""
        runner = cls()
        runner.load_file(path)
        return runner.run_all()

    @classmethod
    def run_from_dict(cls, data: dict[str, Any]) -> dict[str, Any]:
        """Load *data* dict and run all models.  Returns the aggregated results."""
        runner = cls()
        runner.load_dict(data)
        return runner.run_all()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _assert_loaded(self) -> None:
        if self._data is None or self._calc is None:
            raise RuntimeError(
                "No project loaded.  Call load_file() or load_dict() first."
            )

    def _make_calculation(self) -> Calculation:
        assert self._data is not None
        parent = _HeadlessParent(self._data)
        return Calculation(parent)

    @staticmethod
    def _normalize(data: dict[str, Any]) -> dict[str, Any]:
        """Apply the same normalisation as Storage._normalize_legacy_to_schema."""
        out = dict(data)

        # depths: ensure list of [id, depth, wkt]
        depths = out.get("depths", [])
        new_depths = []
        for dep in depths:
            if isinstance(dep, dict):
                new_depths.append([str(dep.get("id", "")), str(dep.get("depth", "")), str(dep.get("polygon", ""))])
            else:
                try:
                    did, depth, poly = dep
                    new_depths.append([str(did), str(depth), str(poly)])
                except Exception:
                    pass
        out["depths"] = new_depths

        # objects: ensure list of [id, height, wkt]
        objects = out.get("objects", [])
        new_objects = []
        for obj in objects:
            if isinstance(obj, dict):
                new_objects.append([str(obj.get("id", "")), str(obj.get("height", obj.get("heights", ""))), str(obj.get("polygon", ""))])
            else:
                try:
                    oid, height, poly = obj
                    new_objects.append([str(oid), str(height), str(poly)])
                except Exception:
                    pass
        out["objects"] = new_objects

        # segment_data: key normalisation and defaults
        segs = out.get("segment_data", {}) or {}
        for sid, seg in segs.items():
            if "Start Point" in seg and "Start_Point" not in seg:
                seg["Start_Point"] = seg.pop("Start Point")
            if "End Point" in seg and "End_Point" not in seg:
                seg["End_Point"] = seg.pop("End Point")
            for key, default in [
                ("line_length", 0.0),
                ("Route_Id", 0),
                ("Leg_name", ""),
                ("Segment_Id", str(sid)),
                ("u_min1", 0.0), ("u_max1", 0.0), ("ai1", 0.0),
                ("u_min2", 0.0), ("u_max2", 0.0), ("ai2", 0.0),
                ("Width", seg.get("Width", 0)),
            ]:
                seg.setdefault(key, default)
            seg.setdefault("dist1", [])
            seg.setdefault("dist2", [])
        out["segment_data"] = segs

        # traffic_data: ensure Ship Beam (meters) exists
        td = out.get("traffic_data", {}) or {}
        for leg_id, dirs in td.items():
            for dir_name, dir_data in dirs.items():
                if "Ship Beam (meters)" not in dir_data:
                    sp = dir_data.get("Speed (knots)", [])
                    beam = []
                    for row in sp:
                        try:
                            beam.append([0 for _ in row])
                        except Exception:
                            beam.append([])
                    dir_data["Ship Beam (meters)"] = beam
        out["traffic_data"] = td

        # drift defaults
        drift = out.get("drift", {}) or {}
        repair = drift.get("repair", {}) or {}
        repair.setdefault("use_lognormal", False)
        drift["repair"] = repair
        if "anchor_d" not in drift:
            drift["anchor_d"] = drift.get("anchor_depth", 0)
        out["drift"] = drift

        # ship_categories default
        out.setdefault("ship_categories", HeadlessRunner.DEFAULT_SHIP_CATEGORIES)

        return out
