# OMRAT Plugin ↔ Web Field Mapping (Canonical Contract)

Last updated: 2026-03-19

This document defines the current mapping between:

- Legacy QGIS/plugin `.omrat` payload shape, and
- Django/React canonical API payload (`segment_data`, `traffic_data`, `depths`, `objects`, `settings`).

The mapping is implemented in `backend/omrat_api/services/legacy_project_compat.py`.

---

## 1) `segment_data`

| Legacy field | Canonical field | Direction | Notes |
|---|---|---|---|
| `segment_data.<id>.Segment_Id` | `segment_data[].segment_id` | legacy → web | Falls back to dict key when missing. |
| `segment_data.<id>.Leg_name` / `Start_Point` | `segment_data[].from_waypoint` | legacy → web | Current adapter keeps lightweight waypoint text for web UI. |
| `segment_data.<id>.End_Point` | `segment_data[].to_waypoint` | legacy → web | |
| `segment_data.<id>.Width` | `segment_data[].width_m` | both | Stored as float meters in canonical model. |
| `segment_data.<id>.Start_Point`, `End_Point` | `segment_data[].coords` | legacy → web | Parsed from `"x y"` text into two coordinate tuples when possible. |
| `segment_data[].segment_id` | `segment_data.<id>.Segment_Id` | web → legacy | Export builds map keyed by `segment_id` (or row index). |
| `segment_data[].coords[0]` | `segment_data.<id>.Start_Point` | web → legacy | Serialized as `"x y"` text. |
| `segment_data[].coords[1]` | `segment_data.<id>.End_Point` | web → legacy | Serialized as `"x y"` text. |
| `segment_data[].width_m` | `segment_data.<id>.Width` | web → legacy | |
| _(derived)_ | `segment_data.<id>.dist1`, `dist2` | web → legacy | Currently exported as empty lists to satisfy legacy schema expectations. |

---

## 2) `traffic_data`

| Legacy field | Canonical field | Direction | Notes |
|---|---|---|---|
| `traffic_data.<segment>.<dir>.Frequency (ships/year)` matrix sum | `traffic_data[].annual_transits` | legacy → web | Matrix rows are summed into one scalar total per row in canonical adapter. |
| `traffic_data` segment key | `traffic_data[].segment_id` | legacy → web | |
| Direction key (`East going`, etc.) | `traffic_data[].ship_category` | legacy → web | Preserved as string label in canonical rows. |
| `traffic_data[].segment_id` + `traffic_data[].ship_category` | `traffic_data.<segment>.<dir>` | web → legacy | |
| `traffic_data[].annual_transits` | `Frequency (ships/year)=[[value]]` | web → legacy | Scalar expanded to 1×1 matrix for compatibility. |
| _(not currently modeled)_ | `Speed (knots)`, `Draught (meters)`, `Ship heights (meters)`, `Ship Beam (meters)` | web → legacy | Export currently uses `[[0]]` placeholders. |

---

## 3) `depths`

| Legacy field | Canonical field | Direction | Notes |
|---|---|---|---|
| `depths[] = [id, depth, polygon_wkt]` | `depths[].feature_id` / `depths[].depth_m` | legacy → web | Polygon WKT is not yet projected into canonical depth geometry fields. |
| `depths[].feature_id`, `depths[].depth_m` | `depths[] = [id, depth, ""]` | web → legacy | Export keeps empty geometry slot pending full geometry mapping. |

---

## 4) `objects`

| Legacy field | Canonical field | Direction | Notes |
|---|---|---|---|
| `objects[] = [id, height, polygon_wkt]` | `objects[].feature_id` | legacy → web | Current adapter preserves identifier, sets simplified `object_type`. |
| _(derived)_ | `objects[].object_type = "Structure"` | legacy → web | Placeholder classification for canonical rows. |
| `objects[].feature_id` | `objects[] = [id, "0", ""]` | web → legacy | Height/geometry are currently placeholder values on export. |

---

## 5) `settings`

| Legacy field | Canonical field | Direction | Notes |
|---|---|---|---|
| `model_name` / `name` | `settings.model_name` | legacy → web | Falls back to `"omrat-model"`. |
| `report_path` | `settings.report_path` | both | |
| _(derived)_ | `settings.causation_version="v1"` | legacy → web | Explicit canonical default. |
| `settings.model_name` | `model_name` | web → legacy | |
| `settings.report_path` | `report_path` | web → legacy | |
| _(derived)_ | `pc`, `drift`, `ship_categories` blocks | web → legacy | Export fills defaults to keep plugin-compatible structure. |

---

## Known gaps (tracked for parity hardening)

1. Canonical model currently flattens legacy traffic matrices to aggregate totals.
2. Depth/object polygon WKT is not fully preserved in canonical export/import mappings.
3. Some legacy numeric fields are represented with compatibility defaults on web→legacy export.
4. Full per-field parity must be expanded with golden tests for additional real projects and plugin-generated XML fixtures.

