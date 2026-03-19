"""Shared helpers for parity fixture/golden corpus discovery and status projection."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any


CORPUS_ENV_VAR = "OMRAT_EXTRA_CORPUS_DIR"


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[4]


def corpus_roots() -> list[Path]:
    repo_root = _repo_root()
    roots = [repo_root / "tests", repo_root / "django_react_top" / "backend" / "tests" / "corpus"]
    extra_root = os.getenv(CORPUS_ENV_VAR, "").strip()
    if extra_root:
        roots.append(Path(extra_root))
    return roots


def fixture_paths() -> list[str]:
    repo_root = _repo_root()
    discovered: list[str] = []
    for root in corpus_roots():
        if not root.exists():
            continue
        for fixture in root.rglob("*.omrat"):
            try:
                discovered.append(fixture.relative_to(repo_root).as_posix())
            except ValueError:
                discovered.append(str(fixture.resolve()))
    return sorted(set(discovered))


def read_fixture(path: str) -> dict[str, Any]:
    repo_root = _repo_root()
    fixture_path = Path(path)
    if not fixture_path.is_absolute():
        fixture_path = repo_root / path
    return json.loads(fixture_path.read_text(encoding="utf-8"))


def golden_iwrap_path_for_fixture(fixture_path: str) -> Path:
    repo_root = _repo_root()
    return repo_root / "django_react_top" / "backend" / "tests" / "golden" / "iwrap" / f"{Path(fixture_path).stem}.plugin.xml"


def parity_corpus_status() -> dict[str, Any]:
    missing_golden: list[dict[str, str]] = []
    schema_sections = {
        "segment_data": 0,
        "traffic_data": 0,
        "depths": 0,
        "objects": 0,
        "drift": 0,
        "routes_like": 0,
    }

    fixtures = fixture_paths()
    for fixture in fixtures:
        golden = golden_iwrap_path_for_fixture(fixture)
        if not golden.exists():
            missing_golden.append({"fixture": fixture, "missing_golden": str(golden)})

        try:
            payload = read_fixture(fixture)
        except Exception:
            continue

        if payload.get("segment_data"):
            schema_sections["segment_data"] += 1
        if payload.get("traffic_data"):
            schema_sections["traffic_data"] += 1
        if payload.get("depths"):
            schema_sections["depths"] += 1
        if payload.get("objects"):
            schema_sections["objects"] += 1
        if payload.get("drift"):
            schema_sections["drift"] += 1
        if payload.get("routes") or payload.get("legs"):
            schema_sections["routes_like"] += 1

    return {
        "fixture_count": len(fixtures),
        "missing_golden_count": len(missing_golden),
        "missing_golden": missing_golden,
        "schema_sections": schema_sections,
    }
