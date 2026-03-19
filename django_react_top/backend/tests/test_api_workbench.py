from omrat_api.api.workbench_api import (
    assess_project_readiness,
    build_osm_scene,
    create_route_segment,
    evaluate_land_crossings,
    export_legacy_project,
    export_iwrap_xml,
    ingest_ais,
    import_iwrap_xml,
    import_legacy_project,
    import_project,
    load_project,
    preview_corridor_overlaps,
    start_analysis,
    sync_layers,
)


def _osm_context():
    return {
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


def test_load_and_import_project_api_shapes():
    payload = {
        "segment_data": [{"segment_id": "S1", "from_waypoint": "A", "to_waypoint": "B", "width_m": 50}],
        "traffic_data": [],
        "depths": [],
        "objects": [],
        "settings": {"model_name": "demo", "report_path": "report.md", "causation_version": "v1"},
    }

    loaded = load_project(payload)
    assert loaded["segment_data"][0]["segment_id"] == "S1"

    merged = import_project(loaded, payload, merge=True)
    assert len(merged["segment_data"]) == 2


def test_ingest_ais_returns_rows_written():
    result = ingest_ais(
        [
            {"segment_id": "S1", "category": "Cargo", "transits": 12},
            {"segment_id": "", "category": "Skip", "transits": 1},
        ]
    )

    assert result["rows_written"] == 1
    assert result["traffic_data"][0]["ship_category"] == "Cargo"


def test_sync_layers_returns_counts():
    result = sync_layers(
        {
            "segment_data": [{"segment_id": "S1"}],
            "depths": [{"feature_id": "D1"}, {"feature_id": "D2"}],
            "objects": [{"feature_id": "O1"}],
        }
    )

    assert result["routes"]["rows"] == 1
    assert result["depths"]["rows"] == 2
    assert result["objects"]["rows"] == 1


def test_preview_corridor_overlaps_returns_hits():
    payload = {
        "segment_data": [
            {
                "segment_id": "S1",
                "coords": [(0, 0), (10, 0)],
                "width_m": 4,
            }
        ],
        "objects": [
            {
                "feature_id": "O1",
                "object_type": "Turbine",
                "coords": [(4, -1), (6, -1), (6, 1), (4, 1)],
            }
        ],
    }

    preview = preview_corridor_overlaps(payload)

    assert preview["count"] == 1
    assert preview["overlaps"][0]["segment_id"] == "S1"


def test_osm_scene_and_land_crossings():
    payload = {
        "segment_data": [
            {
                "segment_id": "S1",
                "coords": [(0, 0), (12, 0)],
                "width_m": 2,
            }
        ],
        "objects": [],
        "traffic_data": [],
        "depths": [],
        "settings": {"model_name": "demo", "report_path": "/tmp/demo.md", "causation_version": "v1"},
    }

    scene = build_osm_scene(_osm_context())
    crossings = evaluate_land_crossings(payload, _osm_context())

    assert len(scene["land_areas"]) == 1
    assert len(scene["fixed_objects"]) == 1
    assert crossings["count"] == 1


def test_start_analysis_uses_simulation_adapter_with_osm_context():
    summary = start_analysis(
        {
            "segment_data": [
                {
                    "segment_id": "S1",
                    "from_waypoint": "A",
                    "to_waypoint": "B",
                    "width_m": 50,
                    "coords": [(0, 0), (12, 0)],
                }
            ],
            "traffic_data": [{"segment_id": "S1", "ship_category": "Cargo", "annual_transits": 12}],
            "depths": [],
            "objects": [
                {
                    "feature_id": "O1",
                    "object_type": "Turbine",
                    "coords": [(1, -2), (2, -2), (2, 2), (1, 2)],
                }
            ],
            "osm_context": _osm_context(),
            "settings": {"model_name": "demo", "report_path": "/tmp/demo.md", "causation_version": "v1"},
        }
    )

    assert summary["status"] == "completed"
    assert summary["powered_summary"]["segments"] == 1
    assert summary["drifting_summary"]["objects"] >= 1
    assert summary["osm_summary"]["land_crossing_count"] == 1
    assert summary["osm_summary"]["osm_fixed_objects_added"] == 1


def test_create_route_segment_replaces_qgis_leg_generation():
    segment = create_route_segment(
        {
            "start_point": (2, 2),
            "end_point": (12, 2),
            "segment_id": 7,
            "route_id": 3,
            "width_m": 100,
            "tangent_offset_m": 4,
        }
    )

    assert segment["label"] == "LEG_7_3"
    assert segment["coords"] == [(2.0, 2.0), (12.0, 2.0)]
    assert segment["leg_direction"] == "E"
    assert segment["bearing_deg"] == 90.0
    assert segment["tangent_line"]["start"] == (7.0, -2.0)
    assert segment["tangent_line"]["end"] == (7.0, 6.0)
    assert len(segment["corridor_polygon"]) == 5


def test_assess_project_readiness_reports_blockers_and_warnings():
    readiness = assess_project_readiness(
        {
            "segment_data": [{"segment_id": "S1", "from_waypoint": "A", "to_waypoint": "B", "width_m": 50}],
            "traffic_data": [],
            "depths": [],
            "objects": [],
            "settings": {"model_name": "demo", "report_path": "", "causation_version": "v1"},
        }
    )

    assert readiness["ready_for_run"] is False
    assert readiness["counts"]["blocking_issues"] >= 1
    assert readiness["counts"]["warnings"] >= 1


def test_legacy_project_import_export_contracts():
    legacy_payload = {
        "segment_data": {
            "S1": {
                "Segment_Id": "S1",
                "Route_Id": "1",
                "Leg_name": "LEG_1",
                "Start_Point": "0 0",
                "End_Point": "10 0",
                "Width": 100,
            }
        },
        "traffic_data": {"S1": {"East going": {"Frequency (ships/year)": [[12, 3]]}}},
        "depths": [["D1", "-12", "POLYGON(...)"]],
        "objects": [["O1", "15", "POLYGON(...)"]],
        "model_name": "legacy-model",
        "report_path": "/tmp/legacy.md",
    }

    imported = import_legacy_project(legacy_payload)
    assert imported["segment_data"][0]["segment_id"] == "S1"
    assert imported["traffic_data"][0]["annual_transits"] == 15

    exported = export_legacy_project(imported)
    assert "legacy_payload" in exported
    assert exported["legacy_payload"]["segment_data"]["S1"]["Width"] == 100.0


def test_iwrap_export_import_roundtrip_contracts():
    canonical_payload = {
        "segment_data": [
            {"segment_id": "S1", "from_waypoint": "A", "to_waypoint": "B", "width_m": 50, "coords": [(0, 0), (1, 1)]}
        ],
        "traffic_data": [{"segment_id": "S1", "ship_category": "East going", "annual_transits": 10}],
        "depths": [{"feature_id": "D1", "depth_m": -8}],
        "objects": [{"feature_id": "O1", "object_type": "Platform"}],
        "settings": {"model_name": "demo", "report_path": "/tmp/demo.md", "causation_version": "v1"},
    }
    exported = export_iwrap_xml(canonical_payload)
    assert "<riskmodel" in exported["iwrap_xml"]

    imported = import_iwrap_xml(exported["iwrap_xml"])
    assert len(imported["segment_data"]) >= 1
