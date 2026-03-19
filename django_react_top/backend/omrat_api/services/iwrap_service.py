"""IWRAP XML conversion service for web APIs."""

from __future__ import annotations

import json
import importlib.util
import tempfile
from pathlib import Path
from typing import Any, Mapping

from omrat_api.services.legacy_project_compat import LegacyProjectCompatService


def _load_iwrap_functions():
    repo_root = Path(__file__).resolve().parents[4]
    module_path = repo_root / "compute" / "iwrap_convertion.py"
    spec = importlib.util.spec_from_file_location("omrat_compute_iwrap_convertion", module_path)
    if spec is None or spec.loader is None:
        raise RuntimeError("Failed to load compute/iwrap_convertion.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.parse_iwrap_xml, module.write_iwrap_xml


class IWrapService:
    @staticmethod
    def export_xml(payload: Mapping[str, Any]) -> str:
        _parse_iwrap_xml, write_iwrap_xml = _load_iwrap_functions()
        legacy_payload = LegacyProjectCompatService.to_legacy(payload)
        with tempfile.TemporaryDirectory(prefix="omrat-iwrap-export-") as tmp_dir:
            source_path = Path(tmp_dir) / "source.omrat"
            xml_path = Path(tmp_dir) / "output.xml"
            source_path.write_text(json.dumps(legacy_payload), encoding="utf-8")
            write_iwrap_xml(str(source_path), str(xml_path))
            return xml_path.read_text(encoding="utf-8")

    @staticmethod
    def import_xml(xml_payload: str) -> dict[str, Any]:
        parse_iwrap_xml, _write_iwrap_xml = _load_iwrap_functions()
        with tempfile.TemporaryDirectory(prefix="omrat-iwrap-import-") as tmp_dir:
            xml_path = Path(tmp_dir) / "input.xml"
            xml_path.write_text(xml_payload, encoding="utf-8")
            legacy_payload = parse_iwrap_xml(str(xml_path))
            return LegacyProjectCompatService.from_legacy(legacy_payload)
