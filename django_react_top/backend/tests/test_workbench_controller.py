from omrat_api.api.workbench_controller import WorkbenchController


def _osm_context():
    return {
        "land_features": [
            {
                "type": "Feature",
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [[(8, -3), (12, -3), (12, 3), (8, 3), (8, -3)]],
                },
                "properties": {"natural": "coastline"},
            }
        ],
        "fixed_object_features": [
            {
                "type": "Feature",
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [[(14, -1), (16, -1), (16, 1), (14, 1), (14, -1)]],
                },
                "properties": {"man_made": "offshore_platform"},
            }
        ],
    }


def _sample_payload():
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
        "osm_context": _osm_context(),
        "settings": {"model_name": "demo", "report_path": "/tmp/demo.md", "causation_version": "v1"},
    }


def test_controller_run_queue_and_execute_flow():
    controller = WorkbenchController()

    queued = controller.enqueue_run(_sample_payload())
    assert queued["state"] == "queued"
    assert queued["progress"] == 0

    completed = controller.execute_run(queued["task_id"])
    assert completed["state"] == "completed"
    assert completed["progress"] == 100
    assert completed["result"]["status"] == "completed"
    assert completed["result"]["osm_summary"]["land_crossing_count"] == 1

    fetched = controller.get_task(queued["task_id"])
    assert fetched["state"] == "completed"


def test_controller_exposes_sync_preview_and_osm_helpers():
    controller = WorkbenchController()
    payload = _sample_payload()

    sync_status = controller.sync_layers(payload)
    preview = controller.preview_corridor_overlaps(payload)
    scene = controller.build_osm_scene(payload["osm_context"])
    crossings = controller.evaluate_land_crossings(payload, payload["osm_context"])

    assert sync_status["routes"]["rows"] == 1
    assert preview["count"] == 1
    assert len(scene["fixed_objects"]) == 1
    assert crossings["count"] == 1
