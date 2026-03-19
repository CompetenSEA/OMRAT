# OMRAT Plugin → Web Migration Deltas and Upgrade Guide

Last updated: 2026-03-19

## Known behavior deltas

1. **Rendering surface**
   - Plugin: direct QGIS layer rendering and task UI.
   - Web: backend parity provides data/layer sync contracts, while visualization is via React map preview.

2. **Execution adapter fallback chain**
   - Web runtime uses `plugin-equivalent` first, then falls back to `shadow-cascade`, then `simulation` when dependencies/geometry are insufficient.
   - This differs from plugin's single runtime path, but preserves run continuity in server environments.

3. **Readiness gate before run**
   - Web run flow supports explicit readiness checks (`assess-project-readiness`) and can block invalid starts.
   - Plugin relied more on user workflow discipline and UI guidance.

## Upgrade guidance for legacy projects

1. Import `.omrat` payloads through legacy compatibility actions first (`import-legacy-project`) before manual edits.
2. Run readiness diagnostics immediately after import and resolve blockers before analysis.
3. If plugin-equivalent runtime dependencies are unavailable, expect fallback execution engine metadata in run summaries.
4. Verify exports with golden parity tests for representative fixtures before promoting upgraded project templates.

## Operational checklist

- Keep all OMRAT `compute/*` calculation logic unchanged; adapt integration via backend wrapper boundaries.
- Add new parity fixtures for any domain expansion (new segment attributes, traffic schemas, or object categories).
- Re-run parity suites after any compute-layer update.
