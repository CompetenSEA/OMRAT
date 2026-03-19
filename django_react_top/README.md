# OMRAT Django + React top folder

This folder is the active standalone web application target for OMRAT, preserving workflow behavior and data compatibility from the legacy desktop implementation.

## Hard constraint implemented

The Django/React refactor is **fully independent from QGIS runtime** and uses pure-python backend services plus frontend state/geometry models.

## OSM assumption wired in

The map model now assumes **OpenStreetMap-style context** as the base map semantics:

- `osm_context.land_features` represent land polygons.
- `osm_context.fixed_object_features` represent fixed hazards/structures.
- Backend run orchestration merges OSM fixed objects into analysis objects.
- Land crossings are evaluated and surfaced in run summaries.
- Frontend model maps OSM scene responses into land/fixed-object visual layers.

## Refactor status (large-chunk update)

Implemented backend boundaries that map directly to the standalone web workflow:

- **Data contracts/normalization boundary** (`contracts.py`) for all data entry points.
- **Project I/O service** (`project_io.py`) with explicit clear-vs-merge semantics.
- **AIS ingestion service** (`ais_ingestion.py`) for traffic data writes.
- **Map layer lifecycle service** (`map_layer_service.py`) + in-memory layer store.
- **Route editing service** (`route_editing_service.py`) for leg/tangent helpers.
- **Execution adapter boundary** (`execution_adapter.py`) with pure simulation adapter.
- **Geometry engine** (`geometry_engine.py`) for corridor/object overlap diagnostics.
- **OSM scene service** (`osm_scene_service.py`) for land/fixed-object assumptions and crossings.
- **Stateless API façade** (`api/workbench_api.py`) for load/import/sync/preview/run/OSM.
- **Stateful task API façade** (`api/workbench_state_api.py`) for enqueue/execute/get-task route + run flows.
- **Stateful controller** (`api/workbench_controller.py`) with task queue semantics for background task UX.
- **Web endpoint dispatcher** (`web/workbench_views.py`) for Django-ready action routing with normalized response envelopes.
- **Readiness diagnostics service** (`services/readiness_service.py`) and `assess-project-readiness` endpoint for plugin-style pre-run checks.
- **Legacy `.omrat` compatibility adapters** via `import-legacy-project` and `export-legacy-project` web actions.
- **IWRAP XML compatibility adapters** via `import-iwrap-xml` and `export-iwrap-xml` web actions.

Implemented frontend workflow modules:

- **Workflow reducer** (`frontend/.../model/workbenchState.js`) for tab progression and run lifecycle state.
- **Workbench UI shell** (`frontend/.../components/RiskWorkbench.jsx`) using shadcn/ui-style components for route-to-results UX, validation feedback, draft persistence, and map-tool-like route drawing.
- **Run-readiness UX** integrated into Run tab (backend-driven checks + client fallback) to block invalid run execution paths.
- **Results run-history UX** integrated into Results tab via `list-runs` loading of recent completed runs.
- **Map preview helpers** (`frontend/.../model/mapPreview.js`) for SVG-friendly route/object rendering.
- **OSM scene model** (`frontend/.../model/osmSceneModel.js`) for land/fixed-object visualization layers.

## Workflow capability mapping

- Route point-pair/tangent/leg generation (including direction and corridor polygon) -> `create_route_segment(payload)` + `RouteEditingService`
- Route/depth/object layer sync -> `sync_layers(payload)` and `MapLayerService`
- Geometry diagnostics panel -> `preview_corridor_overlaps(payload)` + `GeometryEngine`
- Land/fixed object assumptions -> `build_osm_scene(...)` + `evaluate_land_crossings(...)`
- Background run task manager -> `enqueue_run` / `execute_run` / `get_task`
- Frontend tab-state progression -> `workbenchReducer`

## Current implementation highlights

1. Minimal Django project bootstrap is now included under `backend/django_project` with URL routing to workbench action views.
2. Task state persistence now supports `OMRAT_DATABASE_URL` (PostgreSQL preferred) and SQLite fallback via `OMRAT_TASK_DB_PATH`.
3. Action endpoints now enforce optional bearer token auth + project scope checks via `OMRAT_API_TOKEN` and `OMRAT_ALLOWED_PROJECT_IDS`.
4. Background execution now supports threaded async dispatch through `execute_run_async`.
5. Frontend client now supports strict-server mode (`strictServer`) to disable local fallback paths.

## AIS + persistence notes

- AIS ingestion now writes canonical traffic rows through `AISTrafficRepository` into PostgreSQL (`OMRAT_DATABASE_URL`) when available, with SQLite/in-memory fallback for local dev.
- Django ORM models (`TaskRun`, `AISRecord`) are added in `backend/django_project/omrat_web/models.py` for migration-driven persistence hardening.

## Production readiness status

- Queue processing now supports claim/retry semantics (`claim_next_queued_task`, `schedule_retry`) and worker polling via `process-queue` action.
- Recent completed run summaries are queryable via `list-runs` for dashboard/history UX.
- ORM domain models now cover project, run, report artifact, API token, and audit event entities in addition to tasks/AIS.
- Authorization now supports role/action policies via token registry and writes structured audit logs for every dispatch outcome.
- Golden compatibility tests now include a seed plugin fixture (`tests/test_res.omrat`) for `.omrat` and IWRAP roundtrip sanity checks.

## Refactor backlog tracker

- Live outstanding issues list and plugin/web parity tracker:
  - `django_react_top/OUTSTANDING_REFACTOR_ISSUES.md`
