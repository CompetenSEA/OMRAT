import json
import os
from pathlib import Path

import pytest

from omrat_api.api.workbench_api import (
    export_iwrap_xml,
    export_legacy_project,
    import_iwrap_xml,
    import_legacy_project,
)


def _legacy_fixture(path: str) -> dict:
    repo_root = Path(__file__).resolve().parents[3]
    fixture_path = Path(path)
    if not fixture_path.is_absolute():
        fixture_path = repo_root / path
    return json.loads(fixture_path.read_text(encoding="utf-8"))


def _legacy_fixture_paths() -> list[str]:
    repo_root = Path(__file__).resolve().parents[3]
    roots = [repo_root / "tests", repo_root / "django_react_top" / "backend" / "tests" / "corpus"]
    extra_root = os.getenv("OMRAT_EXTRA_CORPUS_DIR", "").strip()
    if extra_root:
        roots.append(Path(extra_root))
    paths = []
    for root in roots:
        for fixture in root.rglob("*.omrat"):
            try:
                paths.append(fixture.relative_to(repo_root).as_posix())
            except ValueError:
                paths.append(str(fixture.resolve()))
    return sorted(paths)


@pytest.mark.parametrize("fixture_path", _legacy_fixture_paths())
def test_golden_legacy_fixture_imports_to_canonical_shape(fixture_path: str):
    fixture = _legacy_fixture(fixture_path)
    canonical = import_legacy_project(fixture)

    assert len(canonical["segment_data"]) >= 1
    assert len(canonical["traffic_data"]) >= 0
    assert len(canonical["depths"]) >= 1
    assert len(canonical["objects"]) >= 1
    assert "settings" in canonical
    assert canonical["settings"]["model_name"] != ""


@pytest.mark.parametrize("fixture_path", _legacy_fixture_paths())
def test_golden_legacy_fixture_roundtrip_preserves_segment_ids_and_counts(fixture_path: str):
    fixture = _legacy_fixture(fixture_path)
    canonical = import_legacy_project(fixture)
    exported = export_legacy_project(canonical)["legacy_payload"]

    original_ids = sorted(str(seg.get("Segment_Id") or seg_id) for seg_id, seg in fixture["segment_data"].items())
    roundtrip_ids = sorted(exported["segment_data"].keys())
    original_depth_ids = sorted(str(row[0]) for row in fixture.get("depths", []))
    original_object_ids = sorted(str(row[0]) for row in fixture.get("objects", []))
    roundtrip_depth_ids = sorted(str(row[0]) for row in exported.get("depths", []))
    roundtrip_object_ids = sorted(str(row[0]) for row in exported.get("objects", []))

    assert len(roundtrip_ids) == len(original_ids)
    assert roundtrip_ids == original_ids
    assert roundtrip_depth_ids == original_depth_ids
    assert roundtrip_object_ids == original_object_ids
    assert str(exported.get("model_name") or "") != ""
    assert str(exported.get("report_path") or "") == str(canonical.get("settings", {}).get("report_path") or "")

    # Stricter segment-level checks for key fields
    for seg_id in original_ids:
        original = fixture["segment_data"][seg_id]
        rt = exported["segment_data"][seg_id]
        assert str(rt.get("Segment_Id") or "") == str(original.get("Segment_Id") or seg_id)
        assert float(rt.get("Width") or 0) == pytest.approx(float(original.get("Width") or 0))


@pytest.mark.parametrize("fixture_path", _legacy_fixture_paths())
def test_golden_legacy_fixture_iwrap_roundtrip_produces_canonical_payload(fixture_path: str):
    fixture = _legacy_fixture(fixture_path)
    canonical = import_legacy_project(fixture)

    iwrap_xml = export_iwrap_xml(canonical)["iwrap_xml"]
    assert "<riskmodel" in iwrap_xml

    restored = import_iwrap_xml(iwrap_xml)
    assert len(restored["segment_data"]) == len(canonical["segment_data"])
    assert len(restored["depths"]) == len(canonical["depths"])
    assert len(restored["objects"]) == len(canonical["objects"])
    assert "settings" in restored
