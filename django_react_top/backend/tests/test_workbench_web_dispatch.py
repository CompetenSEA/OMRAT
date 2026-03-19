from omrat_api.web.workbench_views import dispatch_workbench_action


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


def test_dispatch_unknown_action_returns_not_found():
    response = dispatch_workbench_action("nope", {})
    assert response["ok"] is False
    assert response["error"]["type"] == "not_found"


def test_dispatch_validates_required_keys():
    response = dispatch_workbench_action("create-route-segment", {})
    assert response["ok"] is False
    assert response["error"]["type"] == "validation_error"


def test_dispatch_route_build_and_run_lifecycle():
    route = dispatch_workbench_action(
        "create-route-segment",
        {
            "start_point": (2, 2),
            "end_point": (14, 2),
            "segment_id": 2,
            "route_id": 5,
            "tangent_offset_m": 2,
            "width_m": 80,
        },
    )
    assert route["ok"] is True
    assert route["data"]["label"] == "LEG_2_5"

    queued = dispatch_workbench_action("enqueue-run", _payload())
    assert queued["ok"] is True
    task_id = queued["data"]["task_id"]

    executed = dispatch_workbench_action("execute-run", {"task_id": task_id})
    assert executed["ok"] is True
    assert executed["data"]["state"] == "completed"

    fetched = dispatch_workbench_action("get-task", {"task_id": task_id})
    assert fetched["ok"] is True
    assert fetched["data"]["state"] == "completed"


def test_dispatch_execute_run_async_action():
    queued = dispatch_workbench_action("enqueue-run", _payload())
    assert queued["ok"] is True
    task_id = queued["data"]["task_id"]

    started = dispatch_workbench_action("execute-run-async", {"task_id": task_id})
    assert started["ok"] is True
    assert started["data"]["task_id"] == task_id

    listed = dispatch_workbench_action("list-runs", {"limit": 5})
    assert listed["ok"] is True
    assert isinstance(listed["data"]["runs"], list)

    invalid_limit = dispatch_workbench_action("list-runs", {"limit": 0})
    assert invalid_limit["ok"] is False
    assert invalid_limit["error"]["type"] == "validation_error"


def test_dispatch_enqueue_run_coerces_max_attempts():
    queued = dispatch_workbench_action("enqueue-run", {**_payload(), "max_attempts": "5"})
    assert queued["ok"] is True
    assert queued["data"]["max_attempts"] == 5


def test_dispatch_enqueue_run_rejects_invalid_max_attempts():
    invalid_type = dispatch_workbench_action("enqueue-run", {**_payload(), "max_attempts": "abc"})
    assert invalid_type["ok"] is False
    assert invalid_type["error"]["type"] == "validation_error"

    too_small = dispatch_workbench_action("enqueue-run", {**_payload(), "max_attempts": 0})
    assert too_small["ok"] is False
    assert too_small["error"]["type"] == "validation_error"


def test_dispatch_supports_osm_and_import_actions():
    osm_context = {
        "land_features": [
            {
                "type": "Feature",
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [[(4, -3), (7, -3), (7, 3), (4, 3), (4, -3)]],
                },
                "properties": {"natural": "coastline"},
            }
        ],
        "fixed_object_features": [
            {
                "type": "Feature",
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [[(9, -1), (11, -1), (11, 1), (9, 1), (9, -1)]],
                },
                "properties": {"man_made": "offshore_platform"},
            }
        ],
    }

    loaded = dispatch_workbench_action("load-project", _payload())
    assert loaded["ok"] is True

    imported = dispatch_workbench_action(
        "import-project",
        {
            "current_state": loaded["data"],
            "incoming_payload": _payload(),
            "merge": "false",
        },
    )
    assert imported["ok"] is True
    assert len(imported["data"]["segment_data"]) == 1

    ais = dispatch_workbench_action(
        "ingest-ais",
        {
            "rows": [
                {"segment_id": "S1", "category": "Cargo", "transits": 12},
                {"segment_id": "", "category": "Skip", "transits": 1},
            ]
        },
    )
    assert ais["ok"] is True
    assert ais["data"]["rows_written"] == 1

    scene = dispatch_workbench_action("build-osm-scene", {"osm_context": osm_context})
    assert scene["ok"] is True
    assert len(scene["data"]["land_areas"]) == 1

    crossings = dispatch_workbench_action(
        "evaluate-land-crossings",
        {"payload": _payload(), "osm_context": osm_context},
    )
    assert crossings["ok"] is True
    assert crossings["data"]["count"] == 1


def test_dispatch_import_rejects_invalid_merge_field():
    loaded = dispatch_workbench_action("load-project", _payload())
    assert loaded["ok"] is True

    imported = dispatch_workbench_action(
        "import-project",
        {
            "current_state": loaded["data"],
            "incoming_payload": _payload(),
            "merge": "maybe",
        },
    )
    assert imported["ok"] is False
    assert imported["error"]["type"] == "validation_error"


def test_dispatch_assess_project_readiness():
    readiness = dispatch_workbench_action("assess-project-readiness", _payload())
    assert readiness["ok"] is True
    assert readiness["data"]["ready_for_run"] is True
    assert readiness["data"]["counts"]["segments"] == 1

    missing_routes = dispatch_workbench_action(
        "assess-project-readiness",
        {
            "segment_data": [],
            "traffic_data": [],
            "depths": [],
            "objects": [],
            "settings": {"model_name": "demo", "report_path": "", "causation_version": "v1"},
        },
    )
    assert missing_routes["ok"] is True
    assert missing_routes["data"]["ready_for_run"] is False
    assert missing_routes["data"]["counts"]["blocking_issues"] >= 1


def test_dispatch_legacy_import_export_actions():
    legacy_payload = {
        "segment_data": {"S1": {"Segment_Id": "S1", "Start_Point": "0 0", "End_Point": "5 0", "Width": 50}},
        "traffic_data": {"S1": {"East going": {"Frequency (ships/year)": [[2, 3]]}}},
        "depths": [["D1", "-10", ""]],
        "objects": [["O1", "12", ""]],
        "model_name": "legacy",
        "report_path": "/tmp/r.md",
    }
    imported = dispatch_workbench_action("import-legacy-project", legacy_payload)
    assert imported["ok"] is True
    assert imported["data"]["segment_data"][0]["segment_id"] == "S1"

    exported = dispatch_workbench_action("export-legacy-project", _payload())
    assert exported["ok"] is True
    assert "legacy_payload" in exported["data"]

    exported_iwrap = dispatch_workbench_action("export-iwrap-xml", _payload())
    assert exported_iwrap["ok"] is True
    assert "<riskmodel" in exported_iwrap["data"]["iwrap_xml"]

    imported_iwrap = dispatch_workbench_action(
        "import-iwrap-xml",
        {"iwrap_xml": exported_iwrap["data"]["iwrap_xml"]},
    )
    assert imported_iwrap["ok"] is True
    assert len(imported_iwrap["data"]["segment_data"]) >= 1


def test_dispatch_enforces_auth_and_project_scope(monkeypatch):
    monkeypatch.setenv(
        "OMRAT_API_TOKENS_JSON",
        '{"expected-token":{"role":"analyst","projects":["alpha","beta"]}}',
    )

    unauthorized = dispatch_workbench_action(
        "sync-layers",
        {"segment_data": [], "settings": {"project_id": "alpha"}},
        auth_token="wrong-token",
    )
    assert unauthorized["ok"] is False
    assert unauthorized["error"]["type"] == "unauthorized"

    forbidden_project = dispatch_workbench_action(
        "sync-layers",
        {"segment_data": [], "settings": {"project_id": "gamma"}},
        auth_token="expected-token",
    )
    assert forbidden_project["ok"] is False
    assert forbidden_project["error"]["type"] == "unauthorized"

    allowed = dispatch_workbench_action(
        "sync-layers",
        {"segment_data": [], "settings": {"project_id": "alpha"}},
        auth_token="expected-token",
    )
    assert allowed["ok"] is True


def test_dispatch_writes_audit_log(monkeypatch, tmp_path):
    monkeypatch.setenv("OMRAT_API_TOKENS_JSON", '{"admin-token":{"role":"admin","projects":["*"]}}')
    monkeypatch.setenv("OMRAT_AUDIT_LOG_PATH", str(tmp_path / "audit.log"))
    response = dispatch_workbench_action(
        "sync-layers",
        {"segment_data": [], "settings": {"project_id": "alpha"}},
        auth_token="admin-token",
    )
    assert response["ok"] is True
    assert (tmp_path / "audit.log").exists()


def test_process_queue_requires_admin_role(monkeypatch):
    monkeypatch.setenv(
        "OMRAT_API_TOKENS_JSON",
        '{"analyst-token":{"role":"analyst","projects":["*"]},"admin-token":{"role":"admin","projects":["*"]}}',
    )
    denied = dispatch_workbench_action("process-queue", {}, auth_token="analyst-token")
    assert denied["ok"] is False
    assert denied["error"]["type"] == "unauthorized"

    allowed = dispatch_workbench_action("process-queue", {}, auth_token="admin-token")
    assert allowed["ok"] is True
