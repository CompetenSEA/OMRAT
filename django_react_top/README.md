# OMRAT Django + React top folder

This folder is the active migration target for moving the QGIS plugin workflow to a web architecture while preserving behavior and data compatibility.

## Hard constraint implemented

The Django/React refactor **does not depend on QGIS runtime**. It mimics QGIS behavior through a pure-python backend engine and frontend state/geometry models.

## OSM assumption wired in

The map model now assumes **OpenStreetMap-style context** as the base map semantics:

- `osm_context.land_features` represent land polygons.
- `osm_context.fixed_object_features` represent fixed hazards/structures.
- Backend run orchestration merges OSM fixed objects into analysis objects.
- Land crossings are evaluated and surfaced in run summaries.
- Frontend model maps OSM scene responses into land/fixed-object visual layers.

## Refactor status (large-chunk update)

Implemented backend boundaries that map directly to plugin behavior:

- **Data contracts/normalization boundary** (`contracts.py`) for all data entry points.
- **Project I/O service** (`project_io.py`) with explicit clear-vs-merge semantics.
- **AIS ingestion service** (`ais_ingestion.py`) for traffic data writes.
- **Map layer lifecycle service** (`map_layer_service.py`) + in-memory layer store.
- **Execution adapter boundary** (`execution_adapter.py`) with pure simulation adapter.
- **Geometry engine** (`geometry_engine.py`) for corridor/object overlap diagnostics.
- **OSM scene service** (`osm_scene_service.py`) for land/fixed-object assumptions and crossings.
- **Stateless API façade** (`api/workbench_api.py`) for load/import/sync/preview/run/OSM.
- **Stateful controller** (`api/workbench_controller.py`) with task queue semantics to mimic background task UX.

Implemented frontend mimic behavior modules:

- **Workflow reducer** (`frontend/.../model/workbenchState.js`) for tab progression and run lifecycle state.
- **Map preview helpers** (`frontend/.../model/mapPreview.js`) for SVG-friendly route/object rendering.
- **OSM scene model** (`frontend/.../model/osmSceneModel.js`) for land/fixed-object visualization layers.

## QGIS-behavior mimic mapping

- Route/depth/object layer sync -> `sync_layers(payload)` and `MapLayerService`
- Geometry diagnostics panel -> `preview_corridor_overlaps(payload)` + `GeometryEngine`
- Land/fixed object assumptions -> `build_osm_scene(...)` + `evaluate_land_crossings(...)`
- Background run task manager -> `enqueue_run` / `execute_run` / `get_task`
- Frontend tab-state progression -> `workbenchReducer`

## Recommended next implementation chunk

1. Add Django project + DRF viewsets wrapping `WorkbenchController` methods.
2. Persist task state and run history in database instead of in-memory service.
3. Build React tab components using reducer/map preview/OSM scene models and connect to polling endpoints.
