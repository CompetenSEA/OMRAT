"""Authorization policy and audit logging for workbench web actions."""

from __future__ import annotations

import json
import os
from hashlib import sha256
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class AuthDecision:
    allowed: bool
    role: str
    reason: str


_ACTION_ROLES = {
    "load-project": {"viewer", "analyst", "admin"},
    "import-project": {"analyst", "admin"},
    "ingest-ais": {"analyst", "admin"},
    "build-osm-scene": {"viewer", "analyst", "admin"},
    "evaluate-land-crossings": {"viewer", "analyst", "admin"},
    "create-route-segment": {"analyst", "admin"},
    "sync-layers": {"analyst", "admin"},
    "preview-corridor-overlaps": {"viewer", "analyst", "admin"},
    "enqueue-run": {"analyst", "admin"},
    "execute-run": {"analyst", "admin"},
    "execute-run-async": {"analyst", "admin"},
    "get-task": {"viewer", "analyst", "admin"},
    "list-runs": {"viewer", "analyst", "admin"},
    "queue-metrics": {"viewer", "analyst", "admin"},
    "start-analysis": {"analyst", "admin"},
    "process-queue": {"admin"},
}


def _extract_project_id(payload: dict[str, Any]) -> str | None:
    settings = payload.get("settings")
    if isinstance(settings, dict) and settings.get("project_id"):
        return str(settings["project_id"])
    nested = payload.get("payload")
    if isinstance(nested, dict):
        return _extract_project_id(nested)
    return None


def _token_registry() -> dict[str, dict[str, Any]]:
    raw = os.getenv("OMRAT_API_TOKENS_JSON", "").strip()
    if raw:
        try:
            parsed = json.loads(raw)
            if isinstance(parsed, dict):
                return parsed
        except json.JSONDecodeError:
            pass
    fallback_token = os.getenv("OMRAT_API_TOKEN", "").strip()
    if fallback_token:
        return {fallback_token: {"role": "admin", "projects": ["*"]}}
    return {}


def authorize(action: str, payload: dict[str, Any], auth_token: str | None) -> AuthDecision:
    registry = _token_registry()
    if not registry:
        # Explicitly allow when no token registry exists (dev mode).
        return AuthDecision(allowed=True, role="dev-open", reason="No token registry configured")

    token_info = registry.get(auth_token or "")
    if not token_info:
        return AuthDecision(allowed=False, role="anonymous", reason="Unknown token")

    role = str(token_info.get("role", "viewer"))
    allowed_roles = _ACTION_ROLES.get(action, {"admin"})
    if role not in allowed_roles:
        return AuthDecision(allowed=False, role=role, reason=f"Role {role} cannot call {action}")

    project_id = _extract_project_id(payload)
    allowed_projects = token_info.get("projects", ["*"])
    if isinstance(allowed_projects, list) and "*" not in allowed_projects and project_id:
        if project_id not in {str(item) for item in allowed_projects}:
            return AuthDecision(allowed=False, role=role, reason=f"Project {project_id} is not allowed")

    return AuthDecision(allowed=True, role=role, reason="Authorized")


def audit_log(
    *,
    action: str,
    payload: dict[str, Any],
    decision: AuthDecision,
    outcome: str,
    request_fingerprint: str | None = None,
    latency_ms: float | None = None,
) -> None:
    path = Path(os.getenv("OMRAT_AUDIT_LOG_PATH", "/tmp/omrat_audit.log"))
    path.parent.mkdir(parents=True, exist_ok=True)
    event = {
        "timestamp": datetime.now(tz=timezone.utc).isoformat(),
        "action": action,
        "project_id": _extract_project_id(payload),
        "role": decision.role,
        "allowed": decision.allowed,
        "reason": decision.reason,
        "outcome": outcome,
        "request_fingerprint": request_fingerprint or build_request_fingerprint(action, payload),
        "latency_ms": round(float(latency_ms), 3) if latency_ms is not None else None,
        "payload_bytes": len(json.dumps(payload or {}, default=str).encode("utf-8")),
    }
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(event) + "\n")


def build_request_fingerprint(action: str, payload: dict[str, Any]) -> str:
    """Build deterministic short fingerprint for request correlation and diagnostics."""
    canonical = json.dumps(payload or {}, sort_keys=True, separators=(",", ":"), default=str)
    raw = f"{action}|{canonical}".encode("utf-8")
    return sha256(raw).hexdigest()[:20]
