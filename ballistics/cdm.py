"""
Custom Drag Model (CDM) support.

A CDM is a user- or vendor-supplied {mach: cd} table that replaces the
G1/G7 reference table entirely. Typical sources: Applied Ballistics
custom drag curves, Hornady 4DOF, Doppler-radar measurements from
bullet manufacturers.

When a CDM is attached to a projectile the solver uses it directly and
ignores the G1/G7 BC — the CDM is absolute and already calibrated to
the specific bullet. Precedence in the solver is:

    drag_curve  >  bc_segments  >  bc_g7 / bc_g1

This module provides:
  - `DragCurve` dataclass (an immutable sorted mach→cd mapping)
  - `load_curve_from_json(path)` loader for on-disk curves
  - `load_curve_from_dict(d)` loader for in-memory curves

The linear interpolation itself reuses
`ballistics.drag_models.get_drag_coefficient` so the integrator path
is identical regardless of curve source.
"""
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Tuple, Union


@dataclass(frozen=True)
class DragCurve:
    """
    Immutable Cd-vs-Mach curve.

    Attributes
    ----------
    name:
        Short display name ("Berger 175 Hybrid CDM").
    table:
        Sorted list of (mach, cd) pairs. Low mach first, high mach last.
        The solver's interpolator requires ascending mach.
    """
    name: str
    table: Tuple[Tuple[float, float], ...]

    def __post_init__(self):
        # Validate basic structure. Frozen dataclass: use object.__setattr__.
        if len(self.table) < 2:
            raise ValueError("DragCurve requires at least 2 data points")
        machs = [m for m, _ in self.table]
        if machs != sorted(machs):
            raise ValueError("DragCurve mach values must be ascending")

    @property
    def mach_range(self) -> Tuple[float, float]:
        return self.table[0][0], self.table[-1][0]


def _mach_cd_list(raw: Union[Dict[str, float], List[List[float]], List[Tuple[float, float]]]) -> List[Tuple[float, float]]:
    """Normalize various input forms into a list of (mach, cd) tuples."""
    if isinstance(raw, dict):
        items = [(float(k), float(v)) for k, v in raw.items()]
    else:
        items = [(float(pair[0]), float(pair[1])) for pair in raw]
    items.sort(key=lambda p: p[0])
    return items


def load_curve_from_dict(data: dict) -> DragCurve:
    """
    Build a DragCurve from a plain dict.

    Accepted schemas:
        {"name": "...", "table": [[mach, cd], ...]}
        {"name": "...", "table": {"0.0": 0.20, "0.5": 0.19, ...}}
    """
    name = data.get("name", "custom")
    if "table" not in data:
        raise ValueError("CDM dict missing 'table' key")
    items = _mach_cd_list(data["table"])
    return DragCurve(name=name, table=tuple(items))


def load_curve_from_json(path: Union[str, Path]) -> DragCurve:
    """Load a DragCurve from a JSON file."""
    path = Path(path)
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    return load_curve_from_dict(data)


def curve_to_drag_table(curve: DragCurve) -> list:
    """
    Convert a DragCurve to the (mach, cd) list format expected by
    `ballistics.drag_models.get_drag_coefficient`, so the existing
    interpolator works unchanged.
    """
    return [[m, cd] for m, cd in curve.table]
