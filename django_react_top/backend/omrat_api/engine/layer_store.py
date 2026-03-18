"""In-memory layer store to mimic plugin layer lifecycle semantics."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class LayerStore:
    """A minimal layer registry for frontend/backend parity tests."""

    layers: dict[str, list[dict]] = field(default_factory=dict)

    def upsert_layer(self, name: str, rows: list[dict]) -> None:
        self.layers[name] = rows

    def clear_layer(self, name: str) -> None:
        self.layers[name] = []

    def clear_all(self) -> None:
        self.layers.clear()

    def get_layer(self, name: str) -> list[dict]:
        return self.layers.get(name, [])
