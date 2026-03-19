from omrat_api.adapters.execution_adapter import PluginEquivalentExecutionAdapter
from omrat_api.adapters.compute_wrapper import ComputeExecutionResult


def test_plugin_equivalent_adapter_uses_legacy_wrapper(monkeypatch):
    captured = {}

    def _fake_execute(self, legacy_payload):
        captured["legacy_payload"] = legacy_payload
        return ComputeExecutionResult(
            drifting_allision=0.11,
            drifting_grounding=0.22,
            powered_grounding=0.33,
            powered_allision=0.44,
            collision={"total": 0.55, "Head-on": 0.12},
            drifting_report={"summary": "ok"},
        )

    monkeypatch.setattr("omrat_api.adapters.execution_adapter.ComputeWrapper.execute_plugin_equivalent", _fake_execute)

    payload = {
        "segment_data": [
            {
                "segment_id": "S1",
                "from_waypoint": "A",
                "to_waypoint": "B",
                "width_m": 50,
                "coords": [(0, 0), (1, 0)],
            }
        ],
        "traffic_data": [{"segment_id": "S1", "ship_category": "Cargo", "annual_transits": 3}],
        "depths": [],
        "objects": [],
        "settings": {"model_name": "demo", "report_path": "/tmp/demo.md", "causation_version": "v1"},
    }

    artifacts = PluginEquivalentExecutionAdapter().run_model(run_id="run-1", payload=payload)

    assert "segment_data" in captured["legacy_payload"]
    assert artifacts.powered_summary["engine"] == "plugin-equivalent"
    assert artifacts.powered_summary["powered_grounding_prob"] == 0.33
    assert artifacts.powered_summary["collision_total"] == 0.55
    assert artifacts.drifting_summary["drifting_report"] == {"summary": "ok"}
