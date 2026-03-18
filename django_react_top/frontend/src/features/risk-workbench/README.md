# Risk workbench feature (React)

Target tabs/components (aligned to plugin workflow, but QGIS-free):

- `RouteEditor`: segment creation, direction labels, width editing.
- `TrafficMatrix`: category-by-segment matrix and AIS patch ingestion.
- `DepthsAndObjects`: synchronized depth/object feature tables.
- `MapPreview`: canvas/SVG corridor and object overlays from backend overlap API.
- `RunAnalysis`: run start/progress, report path, and summary panel.

## Implemented frontend behavior-mimic model

- `model/workbenchState.js`
  - reducer/state transitions mirroring plugin tab workflow and run-task lifecycle
  - canonical payload builder for backend API calls
- `model/mapPreview.js`
  - SVG path/polygon helpers
  - shared bounds computation for route/object preview rendering

## API contract usage

All tab submissions should use backend canonical payload keys:

- `segment_data`
- `traffic_data`
- `depths`
- `objects`
- `settings`

## Mimic endpoints (no QGIS dependency)

- `sync_layers(payload)` for layer-like state updates.
- `preview_corridor_overlaps(payload)` for geometry diagnostics.
- `enqueue_run(payload) -> execute_run(task_id) -> get_task(task_id)` for run lifecycle polling.
