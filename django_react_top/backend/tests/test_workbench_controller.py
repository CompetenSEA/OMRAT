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

    recent = controller.list_recent_runs(limit=5)
    assert len(recent["runs"]) >= 1
    assert recent["runs"][0]["status"] == "completed"


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


def test_controller_create_route_segment_shape():
    controller = WorkbenchController()
    segment = controller.create_route_segment(
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
    assert segment["bearing_deg"] == 90.0
    assert segment["tangent_line"]["start"] == (8.0, 0.0)
    assert segment["tangent_line"]["end"] == (8.0, 4.0)


def test_controller_assess_project_readiness():
    controller = WorkbenchController()
    readiness = controller.assess_project_readiness(_sample_payload())
    assert readiness["ready_for_run"] is True
    assert readiness["counts"]["segments"] == 1


def test_controller_legacy_import_export():
    controller = WorkbenchController()
    legacy_payload = {
        "segment_data": {"S1": {"Segment_Id": "S1", "Start_Point": "0 0", "End_Point": "5 0", "Width": 50}},
        "traffic_data": {"S1": {"East going": {"Frequency (ships/year)": [[1, 1]]}}},
        "depths": [["D1", "-10", ""]],
        "objects": [["O1", "12", ""]],
        "model_name": "legacy",
    }
    imported = controller.import_legacy_project(legacy_payload)
    assert imported["segment_data"][0]["segment_id"] == "S1"

    exported = controller.export_legacy_project(imported)
    assert "legacy_payload" in exported


def test_controller_iwrap_import_export():
    controller = WorkbenchController()
    canonical_payload = {
        "segment_data": [{"segment_id": "S1", "from_waypoint": "A", "to_waypoint": "B", "width_m": 50, "coords": [(0, 0), (1, 1)]}],
        "traffic_data": [{"segment_id": "S1", "ship_category": "East going", "annual_transits": 4}],
        "depths": [],
        "objects": [],
        "settings": {"model_name": "demo", "report_path": "/tmp/demo.md", "causation_version": "v1"},
    }
    exported = controller.export_iwrap_xml(canonical_payload)
    assert "<riskmodel" in exported["iwrap_xml"]

    imported = controller.import_iwrap_xml(exported["iwrap_xml"])
    assert len(imported["segment_data"]) >= 1
