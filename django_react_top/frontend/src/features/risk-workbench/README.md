# Risk workbench feature (React)

Target tabs/components (aligned to plugin workflow, but QGIS-free):

- `RouteEditor`: segment creation, direction labels, width editing.
- `TrafficMatrix`: category-by-segment matrix and AIS patch ingestion.
- `DepthsAndObjects`: synchronized depth/object feature tables.
- `MapPreview`: canvas/SVG corridor, land and fixed-object overlays from backend APIs.
- `RunAnalysis`: run start/progress, report path, and summary panel.

## Implemented frontend behavior-mimic model

- `model/workbenchState.js`
  - reducer/state transitions mirroring plugin tab workflow and run-task lifecycle
  - canonical payload builder for backend API calls
- `model/mapPreview.js`
  - SVG path/polygon helpers
  - shared bounds computation for route/object preview rendering
- `model/osmSceneModel.js`
  - maps OSM scene response to land/fixed-object visual layers
  - merges manual objects with OSM fixed objects for display parity

## API contract usage

All tab submissions should use backend canonical payload keys:

- `segment_data`
- `traffic_data`
- `depths`
- `objects`
- `settings`
- `osm_context` (with `land_features` and `fixed_object_features`)

## Mimic endpoints (no QGIS dependency)

- `build_osm_scene(osm_context)` for map land/fixed-object assumptions.
- `evaluate_land_crossings(payload, osm_context)` for route-to-land checks.
- `sync_layers(payload)` for layer-like state updates.
- `preview_corridor_overlaps(payload)` for geometry diagnostics.
- `enqueue_run(payload) -> execute_run(task_id) -> get_task(task_id)` for run lifecycle polling.
