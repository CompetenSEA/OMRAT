from omrat_api.api.workbench_state_api import (
    create_route_segment,
    enqueue_run,
    execute_run,
    get_task,
    preview_corridor_overlaps,
    sync_layers,
)


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


def test_state_api_route_segment_and_layer_helpers():
    segment = create_route_segment(
        {
            "start_point": (2, 2),
            "end_point": (14, 2),
            "segment_id": 2,
            "route_id": 5,
            "tangent_offset_m": 2,
            "width_m": 80,
        }
    )
    assert segment["label"] == "LEG_2_5"
    assert segment["leg_direction"] == "E"

    sync_status = sync_layers(_payload())
    assert sync_status["routes"]["rows"] == 1

    preview = preview_corridor_overlaps(_payload())
    assert preview["count"] == 1


def test_state_api_run_lifecycle_contract():
    queued = enqueue_run(_payload())
    assert queued["state"] == "queued"

    completed = execute_run(queued["task_id"])
    assert completed["state"] == "completed"
    assert completed["result"]["status"] == "completed"

    fetched = get_task(queued["task_id"])
    assert fetched["state"] == "completed"
