"""Map layer lifecycle service mirroring plugin-style layer operations."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json

from omrat_api.engine.layer_store import LayerStore


def _rows_fingerprint(rows: list[dict]) -> str:
    encoded = json.dumps(rows, sort_keys=True, default=str, separators=(",", ":"))
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()[:16]


@dataclass
class MapLayerService:
    store: LayerStore

    def _sync_layer(self, layer: str, rows: list[dict]) -> dict:
        revision = self.store.upsert_layer(layer, rows)
        return {
            "layer": layer,
            "rows": len(rows),
            "revision": revision,
            "row_fingerprint": _rows_fingerprint(rows),
        }

    def sync_route_layer(self, rows: list[dict]) -> dict:
        return self._sync_layer("routes", rows)

    def sync_depth_layer(self, rows: list[dict]) -> dict:
        return self._sync_layer("depths", rows)

    def sync_object_layer(self, rows: list[dict]) -> dict:
        return self._sync_layer("objects", rows)

    def clear_all_layers(self) -> dict:
        self.store.clear_all()
        return {"status": "cleared", "revision": 0}
