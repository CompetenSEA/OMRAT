"""Map layer lifecycle service mirroring plugin-style layer operations."""

from __future__ import annotations

from dataclasses import dataclass

from omrat_api.engine.layer_store import LayerStore


@dataclass
class MapLayerService:
    store: LayerStore

    def sync_route_layer(self, rows: list[dict]) -> dict:
        self.store.upsert_layer("routes", rows)
        return {"layer": "routes", "rows": len(rows)}

    def sync_depth_layer(self, rows: list[dict]) -> dict:
        self.store.upsert_layer("depths", rows)
        return {"layer": "depths", "rows": len(rows)}

    def sync_object_layer(self, rows: list[dict]) -> dict:
        self.store.upsert_layer("objects", rows)
        return {"layer": "objects", "rows": len(rows)}

    def clear_all_layers(self) -> dict:
        self.store.clear_all()
        return {"status": "cleared"}
