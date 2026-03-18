"""Project import/load orchestration with clear-vs-merge semantics."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Mapping

from omrat_api.contracts import normalize_payload, serialize_payload
from omrat_api.errors import ImportMergeError


@dataclass
class ProjectState:
    segment_data: list
    traffic_data: list
    depths: list
    objects: list
    settings: object

    def as_dict(self) -> Dict[str, Any]:
        return {
            "segment_data": self.segment_data,
            "traffic_data": self.traffic_data,
            "depths": self.depths,
            "objects": self.objects,
            "settings": self.settings,
        }

    def as_json_dict(self) -> Dict[str, Any]:
        return serialize_payload(self.as_dict())


class ProjectIOService:
    @staticmethod
    def load(payload: Mapping[str, Any]) -> ProjectState:
        normalized = normalize_payload(payload)
        return ProjectState(**normalized)

    @staticmethod
    def import_into(
        current_state: Mapping[str, Any], incoming_payload: Mapping[str, Any], *, merge: bool
    ) -> ProjectState:
        try:
            incoming = normalize_payload(incoming_payload)
            if not merge:
                return ProjectState(**incoming)

            current = normalize_payload(current_state)
            return ProjectState(
                segment_data=[*current["segment_data"], *incoming["segment_data"]],
                traffic_data=[*current["traffic_data"], *incoming["traffic_data"]],
                depths=[*current["depths"], *incoming["depths"]],
                objects=[*current["objects"], *incoming["objects"]],
                settings=incoming["settings"],
            )
        except Exception as exc:
            raise ImportMergeError("Failed to import project payload") from exc
