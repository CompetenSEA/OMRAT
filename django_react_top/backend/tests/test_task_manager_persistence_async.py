import time
from pathlib import Path

from omrat_api.api.workbench_controller import WorkbenchController
from omrat_api.services.task_manager import TaskManagerService


def _payload():
    return {
        "segment_data": [
            {
                "segment_id": "S1",
                "from_waypoint": "A",
                "to_waypoint": "B",
                "width_m": 20,
                "coords": [(0, 0), (20, 0)],
            }
        ],
        "traffic_data": [{"segment_id": "S1", "ship_category": "Cargo", "annual_transits": 8}],
        "depths": [{"feature_id": "D1", "depth_m": -14}],
        "objects": [
            {
                "feature_id": "O1",
                "object_type": "Turbine",
                "coords": [(3, -2), (5, -2), (5, 2), (3, 2)],
            }
        ],
        "settings": {"model_name": "demo", "report_path": "/tmp/demo.md", "causation_version": "v1"},
    }


def test_task_manager_persists_records_in_sqlite(tmp_path):
    db_path = Path(tmp_path) / "tasks.sqlite3"
    manager_a = TaskManagerService(db_path=str(db_path))
    created = manager_a.create_task(_payload(), message="queued")
    manager_a.start_task(created.task_id, message="running")
    manager_a.complete_task(created.task_id, {"status": "completed"})

    manager_b = TaskManagerService(db_path=str(db_path))
    loaded = manager_b.get_task(created.task_id)
    assert loaded.state == "completed"
    assert loaded.result["status"] == "completed"


def test_task_manager_accepts_sqlite_database_url(tmp_path):
    db_path = Path(tmp_path) / "tasks_via_url.sqlite3"
    manager = TaskManagerService(db_url=f"sqlite:///{db_path}")
    record = manager.create_task(_payload())
    fetched = manager.get_task(record.task_id)
    assert fetched.task_id == record.task_id


def test_execute_run_async_completes_eventually():
    controller = WorkbenchController()
    task = controller.enqueue_run(_payload())
    controller.execute_run_async(task["task_id"])

    deadline = time.time() + 5
    current = None
    while time.time() < deadline:
        current = controller.get_task(task["task_id"])
        if current["state"] in {"completed", "failed"}:
            break
        time.sleep(0.05)

    assert current is not None
    assert current["state"] == "completed"


def test_task_retry_and_claim_cycle():
    manager = TaskManagerService()
    record = manager.create_task(_payload(), max_attempts=2)
    claimed = manager.claim_next_queued_task()
    assert claimed is not None
    assert claimed.task_id == record.task_id
    assert claimed.state == "running"

    retried = manager.schedule_retry(record.task_id, error="boom", retry_in_seconds=0)
    assert retried.state == "queued"
    assert retried.attempts == 1

    manager.claim_next_queued_task()
    failed = manager.schedule_retry(record.task_id, error="again", retry_in_seconds=0)
    assert failed.state == "failed"
