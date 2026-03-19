"""AIS ingestion normalizer service."""

from __future__ import annotations

from typing import Any, Iterable, Mapping

from omrat_api.contracts import TrafficRecord, normalize_traffic
from omrat_api.services.ais_repository import AISTrafficRepository


class AISIngestionService:
    """Maps AIS patch payloads to canonical traffic records."""

    _repository = AISTrafficRepository()

    @staticmethod
    def ingest(rows: Iterable[Mapping[str, Any]]) -> list[TrafficRecord]:
        records = normalize_traffic(rows)
        AISIngestionService._repository.write_rows(records)
        return records
