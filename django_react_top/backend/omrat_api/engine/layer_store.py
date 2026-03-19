"""In-memory layer store to mimic plugin layer lifecycle semantics."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class LayerStore:
    """A minimal layer registry for frontend/backend parity tests."""

    layers: dict[str, list[dict]] = field(default_factory=dict)
    revisions: dict[str, int] = field(default_factory=dict)
    _revision_counter: int = 0

    def _touch(self, name: str) -> int:
        self._revision_counter += 1
        self.revisions[name] = self._revision_counter
        return self._revision_counter

    def upsert_layer(self, name: str, rows: list[dict]) -> int:
        self.layers[name] = rows
        return self._touch(name)

    def clear_layer(self, name: str) -> int:
        self.layers[name] = []
        return self._touch(name)

    def clear_all(self) -> None:
        self.layers.clear()
        self.revisions.clear()
        self._revision_counter = 0

    def get_layer(self, name: str) -> list[dict]:
        return self.layers.get(name, [])

    def get_revision(self, name: str) -> int:
        return self.revisions.get(name, 0)
