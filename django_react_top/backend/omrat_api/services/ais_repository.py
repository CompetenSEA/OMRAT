"""Persistence adapter for AIS traffic rows."""

from __future__ import annotations

import json
import os
import sqlite3
from dataclasses import asdict
from pathlib import Path

from omrat_api.contracts import TrafficRecord


class AISTrafficRepository:
    """Stores canonical AIS records in PostgreSQL/SQLite or in-memory fallback."""

    def __init__(self, *, db_url: str | None = None, sqlite_path: str | None = None):
        self._db_url = db_url or os.getenv("OMRAT_DATABASE_URL", "").strip() or None
        self._sqlite_path = sqlite_path or os.getenv("OMRAT_AIS_SQLITE_PATH", "").strip() or None
        self._backend = "memory"
        self._memory_rows: list[dict] = []

        if self._db_url:
            if self._db_url.startswith("postgresql://") or self._db_url.startswith("postgres://"):
                self._backend = "postgres"
                self._init_postgres()
            elif self._db_url.startswith("sqlite:///"):
                self._backend = "sqlite"
                self._sqlite_path = self._db_url.replace("sqlite:///", "", 1)
                self._init_sqlite()
        elif self._sqlite_path:
            self._backend = "sqlite"
            self._init_sqlite()

    def _init_sqlite(self) -> None:
        db_parent = Path(self._sqlite_path).expanduser().resolve().parent
        db_parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(self._sqlite_path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS omrat_ais_records (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    segment_id TEXT NOT NULL,
                    ship_category TEXT NOT NULL,
                    annual_transits REAL NOT NULL,
                    metadata_json TEXT NOT NULL
                )
                """
            )
            conn.commit()

    @staticmethod
    def _connect_psycopg_module():
        try:
            import psycopg  # type: ignore

            return psycopg
        except Exception:
            try:
                import psycopg2  # type: ignore

                return psycopg2
            except Exception as exc:
                raise RuntimeError(
                    "PostgreSQL AIS persistence requires psycopg/psycopg2 to be installed"
                ) from exc

    def _connect_postgres(self):
        module = self._connect_psycopg_module()
        return module.connect(self._db_url)

    def _init_postgres(self) -> None:
        conn = self._connect_postgres()
        with conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    CREATE TABLE IF NOT EXISTS omrat_ais_records (
                        id BIGSERIAL PRIMARY KEY,
                        segment_id TEXT NOT NULL,
                        ship_category TEXT NOT NULL,
                        annual_transits DOUBLE PRECISION NOT NULL,
                        metadata_json JSONB NOT NULL
                    )
                    """
                )
        conn.close()

    def write_rows(self, records: list[TrafficRecord]) -> int:
        if not records:
            return 0
        if self._backend == "sqlite":
            return self._write_sqlite(records)
        if self._backend == "postgres":
            return self._write_postgres(records)
        self._memory_rows.extend(asdict(record) for record in records)
        return len(records)

    def _write_sqlite(self, records: list[TrafficRecord]) -> int:
        with sqlite3.connect(self._sqlite_path) as conn:
            conn.executemany(
                """
                INSERT INTO omrat_ais_records(segment_id, ship_category, annual_transits, metadata_json)
                VALUES (?, ?, ?, ?)
                """,
                [
                    (
                        record.segment_id,
                        record.ship_category,
                        float(record.annual_transits),
                        json.dumps(asdict(record)),
                    )
                    for record in records
                ],
            )
            conn.commit()
        return len(records)

    def _write_postgres(self, records: list[TrafficRecord]) -> int:
        conn = self._connect_postgres()
        with conn:
            with conn.cursor() as cur:
                cur.executemany(
                    """
                    INSERT INTO omrat_ais_records(segment_id, ship_category, annual_transits, metadata_json)
                    VALUES (%s, %s, %s, %s::jsonb)
                    """,
                    [
                        (
                            record.segment_id,
                            record.ship_category,
                            float(record.annual_transits),
                            json.dumps(asdict(record)),
                        )
                        for record in records
                    ],
                )
        conn.close()
        return len(records)

