import json
from pathlib import Path

from omrat_api.api.workbench_api import (
    export_iwrap_xml,
    export_legacy_project,
    import_iwrap_xml,
    import_legacy_project,
)


def _legacy_fixture() -> dict:
    repo_root = Path(__file__).resolve().parents[3]
    fixture_path = repo_root / "tests" / "test_res.omrat"
    return json.loads(fixture_path.read_text(encoding="utf-8"))


def test_golden_legacy_fixture_imports_to_canonical_shape():
    fixture = _legacy_fixture()
    canonical = import_legacy_project(fixture)

    assert len(canonical["segment_data"]) >= 1
    assert len(canonical["traffic_data"]) >= 1
    assert "settings" in canonical
    assert canonical["settings"]["model_name"] != ""


def test_golden_legacy_fixture_roundtrip_preserves_segment_ids():
    fixture = _legacy_fixture()
    canonical = import_legacy_project(fixture)
    exported = export_legacy_project(canonical)["legacy_payload"]

    original_ids = sorted(str(seg.get("Segment_Id") or seg_id) for seg_id, seg in fixture["segment_data"].items())
    roundtrip_ids = sorted(exported["segment_data"].keys())

    assert len(roundtrip_ids) == len(original_ids)
    assert roundtrip_ids[:5] == original_ids[:5]


def test_golden_legacy_fixture_iwrap_roundtrip_produces_canonical_payload():
    fixture = _legacy_fixture()
    canonical = import_legacy_project(fixture)

    iwrap_xml = export_iwrap_xml(canonical)["iwrap_xml"]
    assert "<riskmodel" in iwrap_xml

    restored = import_iwrap_xml(iwrap_xml)
    assert len(restored["segment_data"]) >= 1
    assert "settings" in restored
