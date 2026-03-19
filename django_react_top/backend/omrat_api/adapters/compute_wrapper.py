"""Wrapper boundary around OMRAT ``compute`` package execution.

This module intentionally centralizes all imports from the OMRAT ``compute``
folder so adapters can call the plugin-equivalent calculations verbatim
without duplicating or rewriting any computation logic.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import sys


class _NullLineEdit:
    def setText(self, _value: str) -> None:  # pragma: no cover - UI compatibility stub
        return None


class _PluginParentStub:
    """Minimal parent object required by legacy ``Calculation`` mixins."""

    class _MainWidget:
        LEPPoweredGrounding = _NullLineEdit()
        LEPPoweredAllision = _NullLineEdit()
        LEPHeadOnCollision = _NullLineEdit()
        LEPOvertakingCollision = _NullLineEdit()
        LEPCrossingCollision = _NullLineEdit()
        LEPMergingCollision = _NullLineEdit()
        LEPAAllision = _NullLineEdit()
        LEPAGrounding = _NullLineEdit()

    main_widget = _MainWidget()


@dataclass(frozen=True)
class ComputeExecutionResult:
    drifting_allision: float
    drifting_grounding: float
    powered_grounding: float
    powered_allision: float
    collision: dict
    drifting_report: dict


class ComputeWrapper:
    """Stable wrapper that executes OMRAT compute calculations verbatim."""

    @staticmethod
    def _load_calculation_class():
        repo_root = Path(__file__).resolve().parents[4]
        if str(repo_root) not in sys.path:
            sys.path.insert(0, str(repo_root))
        from compute.run_calculations import Calculation

        return Calculation

    def execute_plugin_equivalent(self, legacy_payload: dict) -> ComputeExecutionResult:
        Calculation = self._load_calculation_class()
        calc = Calculation(_PluginParentStub())

        drifting_allision, drifting_grounding = calc.run_drifting_model(legacy_payload)
        collision = calc.run_ship_collision_model(legacy_payload)
        powered_grounding = calc.run_powered_grounding_model(legacy_payload)
        powered_allision = calc.run_powered_allision_model(legacy_payload)

        return ComputeExecutionResult(
            drifting_allision=float(drifting_allision or 0.0),
            drifting_grounding=float(drifting_grounding or 0.0),
            powered_grounding=float(powered_grounding or 0.0),
            powered_allision=float(powered_allision or 0.0),
            collision=collision or {},
            drifting_report=getattr(calc, "drifting_report", None) or {},
        )
