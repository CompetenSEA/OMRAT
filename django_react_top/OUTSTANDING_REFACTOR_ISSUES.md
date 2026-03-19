# OMRAT React/Django Refactor – Outstanding (Release Readiness)

Last updated: 2026-03-19

This list is intentionally concise and prioritized for clean repo split readiness.

## P0 (must close before split)

1. Expand corpus with at least 3 additional real-world `.omrat` projects (mixed route/depth/object complexity) and matching plugin-generated IWRAP goldens.
2. Add CI artifact retention for parity diff outputs (XML projection mismatches and fixture name) to speed triage.
3. Gate release on parity matrix pass (legacy golden + IWRAP parity + drift corridor parity) with no known flaky tests.

## P1 (high-value near-term)

1. Replace string-based IWRAP checks (where still present outside parity suite) with parsed XML assertions.
2. Add deterministic seeds and tolerance docs for geometry/compute tests that can vary by environment.
3. Add a compact developer script (`make parity-pack`) that runs the full parity matrix locally.

## P2 (maintainability)

1. Continue removing duplicate fixture-discovery helpers in remaining test modules and API endpoints.
2. Split diagnostics UI actions into reusable hooks to keep `RiskWorkbench` component size stable.
3. Extend parity-corpus diagnostics with per-fixture schema-gap hints (missing sections by fixture stem).

## Notes

- Canonical fixture/golden guidance is now tracked in `django_react_top/PARITY_CORPUS.md`.
- Historical done-items were removed from this file to keep release-readiness triage focused.
