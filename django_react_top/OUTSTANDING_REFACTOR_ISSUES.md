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
| Drift/powered/collision run orchestration | `compute/run_calculations.py` | `RunOrchestrationService` + execution adapter | 🟡 | Orchestration/parity facade done; simulation adapter still placeholder for full numerics parity. |
| OSM land/fixed-object integration | N/A (plugin uses depth/object layers) | `OSMSceneService` | ✅ | Context merged into objects; land crossings reported in run summary. |
| Background task execution UX | QGIS task manager | `TaskManagerService` + queue worker + async dispatch | ✅ | Queue + retry + persistence available. |
| Readiness diagnostics before run | Implicit user checks in GUI workflow docs | `assess-project-readiness` action | ✅ | New run-readiness endpoint returns blockers/warnings and counts. |
| `.omrat` full import/export compatibility checks | plugin file I/O (`storage.py`) | web APIs/services | 🟡 | Seed golden tests added using `tests/test_res.omrat`; broader corpus and stricter fidelity checks still needed. |
| IWRAP XML import/export parity | `compute/iwrap_convertion.py` | web APIs/services | 🟡 | Web XML import/export endpoints added; full schema-fidelity and golden parity checks still pending. |
| Drift corridor visual diagnostics parity | QGIS layer rendering | React map preview | 🟡 | Geometry preview exists; full corridor rendering workflow still incomplete. |
| Frontend workflow tab parity | `omrat_base.ui`/widget tabs | `RiskWorkbench` reducer/components | 🟡 | Major flows are present; run tab now includes readiness gating; per-tab feature completeness still uneven. |
| User-facing error taxonomy/messages consistency | plugin dialogs + log | web dispatch envelopes | 🟡 | Core taxonomy exists; some endpoint-specific messages still generic. |
| Last run summary projection for dashboard/history | QGIS task manager + result widgets | `list-runs` action + task manager summaries | ✅ | Recent completed runs now exposed with report/status/powered/drifting/osm summaries. |
| Migration documentation and gap log | plugin docs | Django/React docs | 🟡 | This tracker added; deeper per-feature migration notes still needed. |

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

---

## Priority outstanding issues (ordered)

### P0 – Required for parity confidence

1. **Integrate real compute engine adapter for web runs** (replace simulation-first path with plugin-equivalent numerical pipeline where feasible).
2. **Expand `.omrat` golden compatibility corpus** beyond the seed fixture to include multiple real-world projects and stricter per-field parity checks.
3. **Expand IWRAP XML parity tests** using plugin-generated golden files and strict field-level comparisons.
4. **Drift corridor parity test suite** comparing plugin and web overlap/corridor artifacts for fixed scenarios.

### P1 – High-impact reliability and UX

5. Add endpoint-specific error codes and stable message IDs for frontend localization/supportability.
6. ✅ Implemented: run-history summary projection available through `list-runs`.
7. ✅ Implemented: frontend readiness panel driven by `assess-project-readiness` now blocks invalid runs and shows actionable issues.

### P2 – Migration hardening and maintainability

8. Document plugin-to-web field mapping tables for all payload entities (`segment_data`, traffic matrix, depths, objects, settings).
9. Add load-testing and queue throughput characterization for async run execution.
10. Expand audit trail schema with per-action latency and request fingerprint metadata.

---

## Definition of done for “full refactor complete”

The refactor will be considered complete when:

1. P0 issues are closed with automated tests.
2. At least one plugin-vs-web parity test pack runs in CI for representative scenarios.
3. Frontend enforces readiness checks before run dispatch.
4. Migration docs include known deltas and upgrade guidance for legacy projects.
