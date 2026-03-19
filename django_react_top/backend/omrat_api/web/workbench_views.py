"""Django-ready web handlers for the standalone OMRAT workbench API."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Callable

from omrat_api.api.workbench_api import (
    assess_project_readiness,
    build_osm_scene,
    evaluate_land_crossings,
    export_legacy_project,
    export_iwrap_xml,
    import_project,
    import_iwrap_xml,
    import_legacy_project,
    ingest_ais,
    load_project,
    start_analysis,
)
from omrat_api.api.workbench_controller import WorkbenchController
from omrat_api.errors import ImportMergeError, OmratAPIError, TaskExecutionError, ValidationError
from omrat_api.security import AuthDecision, audit_log, authorize

try:  # pragma: no cover - optional runtime dependency
    from django.http import HttpRequest, JsonResponse
    from django.views.decorators.csrf import csrf_exempt
except Exception:  # pragma: no cover - tests run without Django installed
    HttpRequest = Any
    JsonResponse = None

    def csrf_exempt(fn: Callable[..., Any]) -> Callable[..., Any]:
        return fn


_CONTROLLER = WorkbenchController()


@dataclass(frozen=True)
class EndpointSpec:
    """Endpoint contract used by the framework-agnostic dispatcher."""

    handler: Callable[[dict[str, Any]], dict[str, Any]]
    required_keys: tuple[str, ...] = ()


def _require_keys(payload: dict[str, Any], keys: tuple[str, ...]) -> None:
    missing = [key for key in keys if key not in payload]
    if missing:
        raise ValidationError(f"Missing required payload keys: {', '.join(missing)}")


def _with_required_keys(
    fn: Callable[[dict[str, Any]], dict[str, Any]],
    *,
    keys: tuple[str, ...],
) -> Callable[[dict[str, Any]], dict[str, Any]]:
    def wrapped(payload: dict[str, Any]) -> dict[str, Any]:
        _require_keys(payload, keys)
        return fn(payload)

    return wrapped


def _parse_bool_field(payload: dict[str, Any], key: str, *, default: bool) -> bool:
    """Parse boolean fields from JSON payloads with strict validation."""
    value = payload.get(key, default)
    if isinstance(value, bool):
        return value
    if isinstance(value, int) and value in (0, 1):
        return bool(value)
    if isinstance(value, str):
        lowered = value.strip().lower()
        if lowered in {"true", "1", "yes"}:
            return True
        if lowered in {"false", "0", "no"}:
            return False
    raise ValidationError(f"Field '{key}' must be a boolean")


def _parse_int_field(
    payload: dict[str, Any],
    key: str,
    *,
    default: int,
    minimum: int | None = None,
    maximum: int | None = None,
) -> int:
    """Parse integer fields from JSON payloads with strict validation."""
    value = payload.get(key, default)
    if isinstance(value, bool):
        raise ValidationError(f"Field '{key}' must be an integer")
    try:
        parsed = int(value)
    except (TypeError, ValueError) as exc:
        raise ValidationError(f"Field '{key}' must be an integer") from exc

    if minimum is not None and parsed < minimum:
        raise ValidationError(f"Field '{key}' must be >= {minimum}")
    if maximum is not None and parsed > maximum:
        raise ValidationError(f"Field '{key}' must be <= {maximum}")
    return parsed


def _import_project_handler(payload: dict[str, Any]) -> dict[str, Any]:
    _require_keys(payload, ("current_state", "incoming_payload"))
    merge = _parse_bool_field(payload, "merge", default=True)
    return import_project(payload["current_state"], payload["incoming_payload"], merge=merge)


def _enqueue_run_handler(payload: dict[str, Any]) -> dict[str, Any]:
    max_attempts = _parse_int_field(payload, "max_attempts", default=3, minimum=1, maximum=10)
    normalized_payload = dict(payload)
    normalized_payload["max_attempts"] = max_attempts
    return _CONTROLLER.enqueue_run(normalized_payload)


def _execute_run_handler(payload: dict[str, Any]) -> dict[str, Any]:
    _require_keys(payload, ("task_id",))
    return _CONTROLLER.execute_run(payload["task_id"])


def _get_task_handler(payload: dict[str, Any]) -> dict[str, Any]:
    _require_keys(payload, ("task_id",))
    return _CONTROLLER.get_task(payload["task_id"])


def _ingest_ais_handler(payload: dict[str, Any]) -> dict[str, Any]:
    _require_keys(payload, ("rows",))
    return ingest_ais(payload["rows"])


def _build_osm_scene_handler(payload: dict[str, Any]) -> dict[str, Any]:
    _require_keys(payload, ("osm_context",))
    return build_osm_scene(payload["osm_context"])


def _evaluate_land_crossings_handler(payload: dict[str, Any]) -> dict[str, Any]:
    _require_keys(payload, ("payload", "osm_context"))
    return evaluate_land_crossings(payload["payload"], payload["osm_context"])


def _assess_project_readiness_handler(payload: dict[str, Any]) -> dict[str, Any]:
    _require_keys(payload, ("segment_data", "traffic_data", "depths", "objects", "settings"))
    return assess_project_readiness(payload)


def _import_legacy_project_handler(payload: dict[str, Any]) -> dict[str, Any]:
    return import_legacy_project(payload)


def _export_legacy_project_handler(payload: dict[str, Any]) -> dict[str, Any]:
    _require_keys(payload, ("segment_data", "traffic_data", "depths", "objects", "settings"))
    return export_legacy_project(payload)


def _export_iwrap_xml_handler(payload: dict[str, Any]) -> dict[str, Any]:
    _require_keys(payload, ("segment_data", "traffic_data", "depths", "objects", "settings"))
    return export_iwrap_xml(payload)


def _import_iwrap_xml_handler(payload: dict[str, Any]) -> dict[str, Any]:
    _require_keys(payload, ("iwrap_xml",))
    return import_iwrap_xml(payload["iwrap_xml"])


def _list_runs_handler(payload: dict[str, Any]) -> dict[str, Any]:
    limit = _parse_int_field(payload, "limit", default=20, minimum=1, maximum=200)
    return _CONTROLLER.list_recent_runs(limit=limit)


_ENDPOINT_SPECS: dict[str, EndpointSpec] = {
    "load-project": EndpointSpec(
        handler=_with_required_keys(load_project, keys=("segment_data", "traffic_data", "depths", "objects", "settings"))
    ),
    "import-project": EndpointSpec(handler=_import_project_handler),
    "ingest-ais": EndpointSpec(handler=_ingest_ais_handler),
    "build-osm-scene": EndpointSpec(handler=_build_osm_scene_handler),
    "evaluate-land-crossings": EndpointSpec(handler=_evaluate_land_crossings_handler),
    "assess-project-readiness": EndpointSpec(handler=_assess_project_readiness_handler),
    "import-legacy-project": EndpointSpec(handler=_import_legacy_project_handler),
    "export-legacy-project": EndpointSpec(handler=_export_legacy_project_handler),
    "export-iwrap-xml": EndpointSpec(handler=_export_iwrap_xml_handler),
    "import-iwrap-xml": EndpointSpec(handler=_import_iwrap_xml_handler),
    "list-runs": EndpointSpec(handler=_list_runs_handler),
    "create-route-segment": EndpointSpec(
        handler=_with_required_keys(
            _CONTROLLER.create_route_segment,
            keys=("start_point", "end_point"),
        )
    ),
    "sync-layers": EndpointSpec(handler=_CONTROLLER.sync_layers),
    "preview-corridor-overlaps": EndpointSpec(handler=_CONTROLLER.preview_corridor_overlaps),
    "enqueue-run": EndpointSpec(handler=_enqueue_run_handler),
    "execute-run": EndpointSpec(handler=_execute_run_handler),
    "execute-run-async": EndpointSpec(handler=_execute_run_handler),
    "get-task": EndpointSpec(handler=_get_task_handler),
    "start-analysis": EndpointSpec(handler=start_analysis),
    "process-queue": EndpointSpec(handler=lambda _payload: _CONTROLLER.process_queue_once()),
}


def dispatch_workbench_action(
    action: str,
    payload: dict[str, Any] | None,
    *,
    auth_token: str | None = None,
) -> dict[str, Any]:
    """Execute a workbench action and return a normalized response envelope."""
    request_payload = payload or {}
    spec = _ENDPOINT_SPECS.get(action)
    if spec is None:
        decision = AuthDecision(allowed=False, role="unknown", reason="Action not found")
        audit_log(action=action, payload=request_payload, decision=decision, outcome="not_found")
        return {"ok": False, "error": {"type": "not_found", "message": f"Unknown workbench action: {action}"}}
    decision = authorize(action, request_payload, auth_token)
    if not decision.allowed:
        audit_log(action=action, payload=request_payload, decision=decision, outcome="unauthorized")
        return {"ok": False, "error": {"type": "unauthorized", "message": "Invalid auth token or project scope"}}

    try:
        if action == "execute-run-async":
            _require_keys(request_payload, ("task_id",))
            result = _CONTROLLER.execute_run_async(request_payload["task_id"])
            audit_log(action=action, payload=request_payload, decision=decision, outcome="ok")
            return {"ok": True, "data": result}
        result = spec.handler(request_payload)
        audit_log(action=action, payload=request_payload, decision=decision, outcome="ok")
        return {"ok": True, "data": result}
    except ValidationError as exc:
        audit_log(action=action, payload=request_payload, decision=decision, outcome="validation_error")
        return {"ok": False, "error": {"type": "validation_error", "message": str(exc)}}
    except ImportMergeError as exc:
        audit_log(action=action, payload=request_payload, decision=decision, outcome="import_error")
        return {"ok": False, "error": {"type": "import_error", "message": str(exc)}}
    except TaskExecutionError as exc:
        audit_log(action=action, payload=request_payload, decision=decision, outcome="task_error")
        return {"ok": False, "error": {"type": "task_error", "message": str(exc)}}
    except OmratAPIError as exc:
        audit_log(action=action, payload=request_payload, decision=decision, outcome="api_error")
        return {"ok": False, "error": {"type": "api_error", "message": str(exc)}}
    except Exception as exc:  # pragma: no cover - defensive catch for HTTP adapter boundary
        audit_log(action=action, payload=request_payload, decision=decision, outcome="unexpected_error")
        return {"ok": False, "error": {"type": "unexpected_error", "message": str(exc)}}


@csrf_exempt
def workbench_action_view(request: HttpRequest, action: str):  # pragma: no cover - requires Django runtime
    """Django-compatible POST handler for `/api/workbench/<action>` endpoints."""
    if JsonResponse is None:
        raise RuntimeError("Django is not installed in this environment")

    if request.method != "POST":
        return JsonResponse(
            {"ok": False, "error": {"type": "method_not_allowed", "message": "Only POST is supported"}},
            status=405,
        )

    try:
        payload = json.loads(request.body.decode("utf-8")) if request.body else {}
    except json.JSONDecodeError as exc:
        return JsonResponse(
            {"ok": False, "error": {"type": "invalid_json", "message": str(exc)}},
            status=400,
        )

    auth_header = request.headers.get("Authorization", "")
    auth_token = auth_header.replace("Bearer ", "", 1).strip() if auth_header.startswith("Bearer ") else None
    response = dispatch_workbench_action(action, payload, auth_token=auth_token)
    status_code = 200 if response.get("ok") else 400
    error_type = response.get("error", {}).get("type")
    if error_type == "not_found":
        status_code = 404
    elif error_type == "unauthorized":
        status_code = 401
    elif error_type == "method_not_allowed":
        status_code = 405
    return JsonResponse(response, status=status_code)
