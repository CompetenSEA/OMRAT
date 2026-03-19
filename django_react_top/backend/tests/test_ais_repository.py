import sqlite3
from pathlib import Path

from omrat_api.contracts import TrafficRecord
from omrat_api.services.ais_repository import AISTrafficRepository


def test_ais_repository_writes_sqlite_rows(tmp_path):
    db_file = Path(tmp_path) / "ais.sqlite3"
    repo = AISTrafficRepository(sqlite_path=str(db_file))
    written = repo.write_rows(
        [
            TrafficRecord(segment_id="S1", ship_category="Cargo", annual_transits=12.0),
            TrafficRecord(segment_id="S2", ship_category="Tanker", annual_transits=5.0),
        ]
    )
    assert written == 2

    with sqlite3.connect(db_file) as conn:
        count = conn.execute("SELECT COUNT(*) FROM omrat_ais_records").fetchone()[0]
    assert count == 2

