import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

from omrat_api.api.workbench_api import export_iwrap_xml, import_legacy_project
from omrat_api.services.iwrap_service import _load_iwrap_functions
from omrat_api.services.parity_corpus import fixture_paths, golden_iwrap_path_for_fixture, read_fixture


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


@pytest.mark.parametrize("fixture_path", fixture_paths())
def test_web_iwrap_export_matches_plugin_golden_field_projection(fixture_path: str):
    parse_iwrap_xml, _write_iwrap_xml = _load_iwrap_functions()
    canonical = import_legacy_project(read_fixture(fixture_path))

    web_xml = export_iwrap_xml(canonical)["iwrap_xml"]
    golden_path = golden_iwrap_path_for_fixture(fixture_path)
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


def test_iwrap_corpus_and_golden_pairing_is_complete():
    missing = []
    for fixture_path in fixture_paths():
        golden = golden_iwrap_path_for_fixture(fixture_path)
        if not golden.exists():
            missing.append((fixture_path, str(golden)))
    assert not missing, f"Missing golden plugin XML for fixtures: {missing}"


@pytest.mark.parametrize("fixture_path", fixture_paths())
def test_web_iwrap_export_contains_extended_schema_nodes(fixture_path: str):
    canonical = import_legacy_project(read_fixture(fixture_path))
    web_xml = export_iwrap_xml(canonical)["iwrap_xml"]
    root = ET.fromstring(web_xml)

    required_nodes = ["traffic_distributions", "waypoints", "legs", "routes", "global_settings"]
    for node in required_nodes:
        assert root.find(node) is not None, f"Missing node '{node}' for fixture {fixture_path}"
