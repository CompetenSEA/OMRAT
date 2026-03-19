import json
from pathlib import Path

import pytest

from omrat_api.api.workbench_api import export_iwrap_xml, import_legacy_project
from omrat_api.services.iwrap_service import _load_iwrap_functions


def _legacy_fixture(path: str) -> dict:
    repo_root = Path(__file__).resolve().parents[3]
    return json.loads((repo_root / path).read_text(encoding="utf-8"))


def _legacy_fixture_paths() -> list[str]:
    repo_root = Path(__file__).resolve().parents[3]
    roots = [repo_root / "tests", repo_root / "django_react_top" / "backend" / "tests" / "corpus"]
    return sorted(
        p.relative_to(repo_root).as_posix()
        for root in roots
        for p in root.rglob("*.omrat")
    )


def _golden_plugin_xml_path_for_fixture(fixture_path: str) -> Path:
    repo_root = Path(__file__).resolve().parents[3]
    return repo_root / "django_react_top" / "backend" / "tests" / "golden" / "iwrap" / f"{Path(fixture_path).stem}.plugin.xml"


def _legacy_projection(payload: dict) -> dict:
    segment_data = payload.get("segment_data", {}) or {}
    width_by_segment = {
        str(seg.get("Segment_Id") or seg_id): float(seg.get("Width") or 0.0)
        for seg_id, seg in segment_data.items()
    }
    return {
        "segment_ids": sorted(str(seg.get("Segment_Id") or seg_id) for seg_id, seg in segment_data.items()),
        "depth_ids": sorted(str(row[0]) for row in payload.get("depths", []) if isinstance(row, list) and row),
        "object_ids": sorted(str(row[0]) for row in payload.get("objects", []) if isinstance(row, list) and row),
        "traffic_segments": sorted(str(seg_id) for seg_id in payload.get("traffic_data", {}).keys()),
        "segment_widths": width_by_segment,
    }


@pytest.mark.parametrize("fixture_path", _legacy_fixture_paths())
def test_web_iwrap_export_matches_plugin_golden_field_projection(fixture_path: str):
    parse_iwrap_xml, _write_iwrap_xml = _load_iwrap_functions()
    canonical = import_legacy_project(_legacy_fixture(fixture_path))

    web_xml = export_iwrap_xml(canonical)["iwrap_xml"]
    golden_path = _golden_plugin_xml_path_for_fixture(fixture_path)
    assert golden_path.exists(), f"Missing golden XML: {golden_path}"
    plugin_xml = golden_path.read_text(encoding="utf-8")

    from tempfile import TemporaryDirectory

    with TemporaryDirectory(prefix="omrat-iwrap-compare-") as tmp_dir:
        web_path = Path(tmp_dir) / "web.xml"
        plugin_path = Path(tmp_dir) / "plugin.xml"
        web_path.write_text(web_xml, encoding="utf-8")
        plugin_path.write_text(plugin_xml, encoding="utf-8")

        web_legacy = parse_iwrap_xml(str(web_path))
        plugin_legacy = parse_iwrap_xml(str(plugin_path))

    assert _legacy_projection(web_legacy) == _legacy_projection(plugin_legacy)
