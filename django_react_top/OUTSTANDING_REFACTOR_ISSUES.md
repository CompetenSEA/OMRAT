# OMRAT React/Django Refactor – Outstanding Issues (Live Tracker)

Last updated: 2026-03-19

This tracker is the canonical backlog for achieving parity between:

- the legacy **QGIS plugin workflow** (`omrat.py` + `omrat_utils/*` + `geometries/*`), and
- the new **Django/React subsystem** (`django_react_top/backend` + `django_react_top/frontend`).

---

## 360° parity status by capability

Legend: ✅ done · 🟡 partial · ❌ not started

| Capability area | Plugin source of truth | Web target | Status | Notes |
|---|---|---|---|---|
| Canonical payload normalization/validation | `omrat_utils/validate_data.py`, `gather_data.py` | `backend/omrat_api/contracts.py` | ✅ | Unified normalization path exists for load/import/AIS/analysis entry points. |
| Clear vs merge import semantics | `omrat.py` load/import behavior | `ProjectIOService.import_into` + `import-project` action | ✅ | Strict merge parsing now enforced at web boundary. |
| Route geometry drafting (bearing, leg labels, tangent) | `geometries/route.py`, `handle_qgis_iface.py` | `RouteEditingService` + `create-route-segment` | ✅ | Core leg generation parity exists. |
| Layer synchronization lifecycle | plugin layer tables + QGIS layer operations | `MapLayerService` + `LayerStore` | 🟡 | Data-side sync present; no direct QGIS rendering surface in web target by design. |
| Drift/powered/collision run orchestration | `compute/run_calculations.py` | `RunOrchestrationService` + execution adapter | ✅ | Plugin-equivalent adapter path added with auto fallback chain (`plugin-equivalent` → `shadow-cascade` → `simulation`) for production runtime resilience. |
| OSM land/fixed-object integration | N/A (plugin uses depth/object layers) | `OSMSceneService` | ✅ | Context merged into objects; land crossings reported in run summary. |
| Background task execution UX | QGIS task manager | `TaskManagerService` + queue worker + async dispatch | ✅ | Queue + retry + persistence available. |
| Readiness diagnostics before run | Implicit user checks in GUI workflow docs | `assess-project-readiness` action | ✅ | New run-readiness endpoint returns blockers/warnings and counts. |
| `.omrat` full import/export compatibility checks | plugin file I/O (`storage.py`) | web APIs/services | 🟡 | Golden suite now discovers all test `.omrat` fixtures and validates stricter per-field roundtrip parity; larger real-world corpus still needed. |
| IWRAP XML import/export parity | `compute/iwrap_convertion.py` | web APIs/services | 🟡 | Added plugin-vs-web XML projection parity tests over all available `.omrat` fixtures; full schema golden corpus still pending. |
| Drift corridor visual diagnostics parity | QGIS layer rendering | React map preview | 🟡 | Corridor/base-surface parity suite now validates refactored vs legacy geometry for fixed scenarios; UI rendering parity still pending. |
| Frontend workflow tab parity | `omrat_base.ui`/widget tabs | `RiskWorkbench` reducer/components | 🟡 | Major flows are present; run tab now includes readiness gating; per-tab feature completeness still uneven. |
| User-facing error taxonomy/messages consistency | plugin dialogs + log | web dispatch envelopes | 🟡 | Core taxonomy exists; some endpoint-specific messages still generic. |
| Last run summary projection for dashboard/history | QGIS task manager + result widgets | `list-runs` action + task manager summaries | ✅ | Recent completed runs now exposed with report/status/powered/drifting/osm summaries. |
| Migration documentation and gap log | plugin docs | Django/React docs | 🟡 | Tracker + explicit field mapping table now added; deeper per-feature migration notes still needed. |

---

## Completed in this update (2026-03-19)

1. Added backend **project readiness assessment service** that mirrors plugin workflow prerequisites:
   - routes present and geometrically valid,
   - traffic rows mapped to segments,
   - depth/object presence checks,
   - run metadata checks (model/report path).
2. Added new web action: `assess-project-readiness`.
3. Added tests for API, controller, and dispatch coverage for readiness checks.
4. Added frontend readiness integration (`Check readiness` + run gating) with client fallback support and tests.
5. Carried forward strict payload parsing hardening for merge/int fields as an enforced boundary pattern.
6. Added legacy `.omrat` compatibility adapters and dispatch actions (`import-legacy-project`, `export-legacy-project`) with API/controller/dispatch tests.
7. Added IWRAP XML service boundary with web actions (`export-iwrap-xml`, `import-iwrap-xml`) and end-to-end tests.
8. Added first golden compatibility suite (`backend/tests/test_legacy_golden_parity.py`) covering legacy `.omrat` import/export/IWRAP roundtrips.
9. Added run-history summary projection via `list-runs` endpoint and task-manager list APIs.
10. Added frontend results-tab integration to load and display recent completed runs from `list-runs`.
11. Expanded golden compatibility coverage to include both `tests/test_res.omrat` and `tests/example_data/proj.omrat`, with stricter legacy roundtrip parity checks for segment/depth/object IDs and IWRAP geometry counts.
12. Added plugin↔web field mapping reference (`PLUGIN_WEB_FIELD_MAPPING.md`) for segment, traffic, depths, objects, and settings contracts.
13. Added plugin-vs-web IWRAP parity tests (`backend/tests/test_iwrap_xml_parity.py`) with stricter segment/depth/object/traffic projection checks across all available `.omrat` fixtures.
14. Added drift corridor parity suite (`backend/tests/test_drift_corridor_parity.py`) validating refactored vs legacy geometry equivalence for projected corridors and base surfaces.
15. Switched default web run execution adapter from simulation-first to numerical shadow-cascade integration (`ShadowCascadeExecutionAdapter`) with simulation fallback when insufficient geometry exists.
16. Added queue throughput characterization metrics (`queue-metrics` action + task-manager percentile/throughput summaries) for operational load baselining.
17. Expanded audit event schema with request fingerprint, payload byte size, and request latency metrics for support/forensics.
18. Added persistent plugin-generated IWRAP golden corpus files under `backend/tests/golden/iwrap` and wired parity tests to compare web exports against committed golden XML fixtures.
19. Completed endpoint-specific error code/message-id rollout for dispatcher error envelopes.
20. Added plugin-equivalent compute adapter path in backend run orchestration with auto fallback chain for environments lacking full legacy runtime dependencies.
21. Expanded `.omrat` fixture corpus with additional tracked scenario (`backend/tests/corpus/proj_expanded.omrat`) and corresponding persistent plugin-generated IWRAP golden.

---

## Priority outstanding issues (ordered)

### P0 – Required for parity confidence

1. ✅ Implemented: integrated plugin-equivalent compute adapter path for web runs with production fallback behavior.
2. ✅ Implemented: expanded `.omrat` compatibility corpus beyond original fixtures and wired it into persistent golden parity validation.
3. ✅ Implemented: expanded IWRAP XML parity tests with persistent plugin-generated golden corpus and strict projection assertions.
4. ✅ Implemented: drift corridor parity test suite comparing legacy and refactored geometry for fixed scenarios.

### P1 – High-impact reliability and UX

5. ✅ Implemented: endpoint-specific error codes and stable message IDs for frontend localization/supportability.
6. ✅ Implemented: run-history summary projection available through `list-runs`.
7. ✅ Implemented: frontend readiness panel driven by `assess-project-readiness` now blocks invalid runs and shows actionable issues.

### P2 – Migration hardening and maintainability

8. ✅ Implemented: documented plugin-to-web field mapping tables for `segment_data`, traffic matrix, depths, objects, and settings.
9. ✅ Implemented: queue throughput characterization for async run execution via task-manager metrics and `queue-metrics` action.
10. ✅ Implemented: audit trail schema expansion with per-action latency and request fingerprint metadata.

---

## Definition of done for “full refactor complete”

The refactor will be considered complete when:

1. P0 issues are closed with automated tests.
2. At least one plugin-vs-web parity test pack runs in CI for representative scenarios.
3. Frontend enforces readiness checks before run dispatch.
4. Migration docs include known deltas and upgrade guidance for legacy projects.
