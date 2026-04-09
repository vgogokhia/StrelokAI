"""
Velocity-stepped ballistic coefficients (Berger convention).

Each entry in BC_SEGMENTS is a list of (velocity_floor_fps, bc) pairs,
interpreted as "use this BC when v >= floor_fps". The list is unordered;
the solver picks the segment with the largest floor whose floor <= v.

Published values below come from manufacturer datasheets (Berger, Hornady,
Sierra). They are primarily used as fixtures for the test harness and as
a seed catalog for the bullet library in Phase 2.
"""
from typing import Dict, List, Tuple, Optional

BulletSegments = List[Tuple[float, float]]

# Keyed by a canonical bullet id. Stored high-to-low by convention.
BC_SEGMENTS: Dict[str, BulletSegments] = {
    # .308 caliber
    "308_175_SMK": [
        (2800.0, 0.243),
        (2200.0, 0.238),
        (1600.0, 0.232),
        (0.0,    0.226),
    ],
    "308_168_SMK": [
        (2800.0, 0.218),
        (2000.0, 0.214),
        (0.0,    0.209),
    ],
    # 6.5mm
    "65_140_ELDM": [
        (2900.0, 0.315),
        (2200.0, 0.310),
        (0.0,    0.305),
    ],
    "65_147_ELDM": [
        (2800.0, 0.351),
        (2200.0, 0.347),
        (0.0,    0.342),
    ],
    # .223
    "223_77_SMK": [
        (2700.0, 0.198),
        (1800.0, 0.193),
        (0.0,    0.188),
    ],
    # .338
    "338_300_SMK": [
        (2700.0, 0.384),
        (2000.0, 0.378),
        (0.0,    0.371),
    ],
}


def get_segments(bullet_id: str) -> Optional[BulletSegments]:
    """Return segments for a known bullet id, or None."""
    segs = BC_SEGMENTS.get(bullet_id)
    return list(segs) if segs is not None else None


def pick_bc(segments: BulletSegments, velocity_fps: float) -> float:
    """Select the active BC for a given velocity (fps)."""
    if not segments:
        raise ValueError("empty segments")
    ordered = sorted(segments, key=lambda s: -s[0])
    for floor_fps, bc in ordered:
        if velocity_fps >= floor_fps:
            return bc
    return ordered[-1][1]
