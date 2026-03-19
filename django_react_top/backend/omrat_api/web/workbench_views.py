"""Django-ready web handlers for the standalone OMRAT workbench API."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Callable

from omrat_api.api.workbench_api import (
    build_osm_scene,
    evaluate_land_crossings,
    import_project,
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


def _import_project_handler(payload: dict[str, Any]) -> dict[str, Any]:
    _require_keys(payload, ("current_state", "incoming_payload"))
    merge = bool(payload.get("merge", True))
    return import_project(payload["current_state"], payload["incoming_payload"], merge=merge)


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


def _endpoint_specs() -> dict[str, EndpointSpec]:
    return {
        "load-project": EndpointSpec(
            handler=_with_required_keys(load_project, keys=("segment_data", "traffic_data", "depths", "objects", "settings"))
        ),
        "import-project": EndpointSpec(handler=_import_project_handler),
        "ingest-ais": EndpointSpec(handler=_ingest_ais_handler),
        "build-osm-scene": EndpointSpec(handler=_build_osm_scene_handler),
        "evaluate-land-crossings": EndpointSpec(handler=_evaluate_land_crossings_handler),
        "create-route-segment": EndpointSpec(
            handler=_with_required_keys(
                _CONTROLLER.create_route_segment,
                keys=("start_point", "end_point"),
            )
        ),
        "sync-layers": EndpointSpec(handler=_CONTROLLER.sync_layers),
        "preview-corridor-overlaps": EndpointSpec(handler=_CONTROLLER.preview_corridor_overlaps),
        "enqueue-run": EndpointSpec(handler=_CONTROLLER.enqueue_run),
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
    spec = _endpoint_specs().get(action)
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
