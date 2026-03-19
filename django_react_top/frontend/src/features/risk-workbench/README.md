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
- `model/routeGeometry.js`
  - QGIS-free route-click helpers (`isValidPointPair`, tangent construction, segment draft builder)
  - emits canonical segment rows for backend API payloads
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
- `create_route_segment(payload)` to replace QGIS route/leg generation behavior.
- `preview_corridor_overlaps(payload)` for geometry diagnostics.
- `enqueue_run(payload) -> execute_run(task_id) -> get_task(task_id)` for run lifecycle polling.


## UI/UX implementation (shadcn/ui pattern)

- `components/RiskWorkbench.jsx` adds a full tabbed workbench shell for routes, traffic, map preview, run task progress, and results.
- New local shadcn-inspired primitives are available in `frontend/src/components/ui/` (`button`, `card`, `tabs`, `badge`, `progress`, `input`, `textarea`, `label`, `separator`, `alert`, `switch`, `table`).
- Route editing tab now uses `buildSegmentDraft` from `model/routeGeometry.js` so leg creation is fully QGIS-free on the client side, including bearing/direction labels and corridor polygon generation.

- UX improvements include local draft persistence, safer JSON parsing/validation alerts, richer settings/data editors, staged run progress states, and click-to-add route canvas interactions, chained leg drawing, undo/clear controls, grid snapping, and inline segment re-editing (start/end/width) that mimic QGIS map-tool behavior.

- `api/workbenchClient.js` adds backend-first route segment creation (`/api/workbench/create-route-segment`) with local fallback for offline/dev UX parity.

- Route editor internals are split into `components/RouteCanvas.jsx` and `components/SegmentTable.jsx` for maintainable UI logic and reusable QGIS-mimic interactions.
- Frontend Node tests now cover route geometry semantics and `workbenchClient` fallback behavior under `frontend/tests/*.test.mjs`.
- `hooks/useRunLifecycle.js` now drives enqueue/execute/poll run state transitions using backend-first client methods with fallback behavior for local/dev UX parity.
