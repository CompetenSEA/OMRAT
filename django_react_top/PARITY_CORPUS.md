# Parity Corpus & Golden Fixtures (Source of Truth)

Last updated: 2026-03-19

This document is the single source of truth for `.omrat` parity fixtures and plugin-generated IWRAP golden XML coverage.

## Canonical locations

- Fixture corpus: `django_react_top/backend/tests/corpus/*.omrat`
- Golden XML: `django_react_top/backend/tests/golden/iwrap/*.plugin.xml`
- Legacy seed fixtures retained for compatibility: `tests/*.omrat`
- Optional external fixture expansion: `OMRAT_EXTRA_CORPUS_DIR`

## Coverage contract

For every discovered fixture `X.omrat`, a golden file must exist at:

- `django_react_top/backend/tests/golden/iwrap/X.plugin.xml`

Enforced by:

- `django_react_top/backend/tests/test_iwrap_xml_parity.py::test_iwrap_corpus_and_golden_pairing_is_complete`
- `django_react_top/backend/omrat_api/api/workbench_api.py::parity_corpus_status`

## High-value parity suites

- `test_legacy_golden_parity.py`
  - legacy import canonical shape
  - roundtrip ID/count parity (`segment_data`, `depths`, `objects`)
  - IWRAP roundtrip cardinality parity
- `test_iwrap_xml_parity.py`
  - plugin-vs-web projected field parity from parsed XML
  - corpus↔golden completeness gate
  - required schema-node presence
- `test_drift_corridor_parity.py`
  - legacy vs refactored geometry equivalence for corridor/base surface

## Naming conventions

- Fixture name: `<scenario>.omrat`
- Matching golden: `<scenario>.plugin.xml`
- New tests must use shared discovery helpers in `omrat_api.services.parity_corpus`.

## Corpus maintenance checklist

1. Add new fixture under `backend/tests/corpus`.
2. Generate plugin XML and commit to `backend/tests/golden/iwrap` using the same stem.
3. Run parity suites before merge.
4. Confirm no missing-golden entries via diagnostics endpoint.
