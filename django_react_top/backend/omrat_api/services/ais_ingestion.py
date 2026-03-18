"""AIS ingestion normalizer service."""

from __future__ import annotations

from typing import Any, Iterable, Mapping

from omrat_api.contracts import TrafficRecord, normalize_traffic


class AISIngestionService:
    """Maps AIS patch payloads to canonical traffic records."""

    @staticmethod
    def ingest(rows: Iterable[Mapping[str, Any]]) -> list[TrafficRecord]:
        return normalize_traffic(rows)
