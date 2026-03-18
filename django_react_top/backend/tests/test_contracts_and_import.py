import pytest

from omrat_api.contracts import normalize_payload
from omrat_api.errors import ValidationError
from omrat_api.services.project_io import ProjectIOService


def test_normalize_payload_maps_aliases_and_types():
    payload = {
        "segment_data": [{"id": "S1", "from": "A", "to": "B", "width": "120.5"}],
        "traffic_data": [
            {"segment_id": "S1", "category": "Cargo", "transits": "14"},
            {"segment_id": "", "category": "Skip", "transits": 1},
        ],
        "depths": [{"id": "D1", "depth_m": "-28.2"}],
        "objects": [{"id": "O1", "type": "Turbine"}],
        "settings": {"model_name": "demo", "report_path": "/tmp/report.md"},
    }

    normalized = normalize_payload(payload)

    assert len(normalized["segment_data"]) == 1
    assert normalized["segment_data"][0].width_m == 120.5
    assert len(normalized["traffic_data"]) == 1
    assert normalized["traffic_data"][0].annual_transits == 14.0
    assert normalized["depths"][0].depth_m == -28.2
    assert normalized["objects"][0].object_type == "Turbine"
    assert normalized["settings"].model_name == "demo"
    assert normalized["segment_data"][0].coords is None


def test_contract_validation_rejects_negative_values():
    with pytest.raises(ValidationError):
        normalize_payload(
            {
                "segment_data": [{"segment_id": "S1", "width_m": -1}],
                "traffic_data": [],
                "depths": [],
                "objects": [],
                "settings": {"model_name": "demo"},
            }
        )

    with pytest.raises(ValidationError):
        normalize_payload(
            {
                "segment_data": [],
                "traffic_data": [{"segment_id": "S1", "ship_category": "Cargo", "annual_transits": -2}],
                "depths": [],
                "objects": [],
                "settings": {"model_name": "demo"},
            }
        )


def test_import_clear_vs_merge_behavior():
    current = {
        "segment_data": [{"segment_id": "S1", "from_waypoint": "A", "to_waypoint": "B", "width_m": 50}],
        "traffic_data": [{"segment_id": "S1", "ship_category": "Cargo", "annual_transits": 7}],
        "depths": [],
        "objects": [],
        "settings": {"model_name": "current", "report_path": "a.md", "causation_version": "v1"},
    }
    incoming = {
        "segment_data": [{"segment_id": "S2", "from_waypoint": "B", "to_waypoint": "C", "width_m": 80}],
        "traffic_data": [{"segment_id": "S2", "ship_category": "Tanker", "annual_transits": 4}],
        "depths": [{"feature_id": "D1", "depth_m": -15}],
        "objects": [{"feature_id": "O1", "object_type": "Bridge"}],
        "settings": {"model_name": "incoming", "report_path": "b.md", "causation_version": "v2"},
    }

    clear_state = ProjectIOService.import_into(current, incoming, merge=False)
    merge_state = ProjectIOService.import_into(current, incoming, merge=True)

    assert [s.segment_id for s in clear_state.segment_data] == ["S2"]
    assert [s.segment_id for s in merge_state.segment_data] == ["S1", "S2"]
    assert merge_state.settings.model_name == "incoming"
