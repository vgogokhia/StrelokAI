"""
Non-linear muzzle-velocity temperature curve.

Some powders behave approximately linearly (modern double-base) while
others (older stick, some extreme-temperature powders) are strongly
non-linear, especially at cold temperatures. This module supports a
user-supplied {temp_c: mv_mps} table and falls back to the existing
linear `temp_sensitivity` model when no curve is provided.
"""
from typing import Dict, List, Optional, Tuple


def apply_mv_curve(
    base_mv: float,
    base_temp_c: float,
    current_temp_c: float,
    temp_sensitivity_pct_per_c: float,
    mv_curve: Optional[Dict[float, float]] = None,
) -> float:
    """
    Compute the temperature-corrected muzzle velocity.

    Parameters
    ----------
    base_mv:
        Reference muzzle velocity at `base_temp_c` (m/s).
    base_temp_c:
        Temperature (°C) at which `base_mv` was measured.
    current_temp_c:
        Current ambient temperature (°C).
    temp_sensitivity_pct_per_c:
        Fallback linear sensitivity (% of MV per °C). Used only when
        `mv_curve` is None or empty.
    mv_curve:
        Optional {temp_c: mv_mps} table. When present, the returned MV
        is the linearly-interpolated value for `current_temp_c`; the
        base values and linear sensitivity are ignored because the
        curve is absolute.

    Returns
    -------
    float
        The corrected muzzle velocity in m/s.
    """
    if mv_curve:
        return _interpolate_curve(current_temp_c, mv_curve)

    # Linear fallback.
    dt = current_temp_c - base_temp_c
    return base_mv + base_mv * (temp_sensitivity_pct_per_c / 100.0) * dt


def _interpolate_curve(temp_c: float, curve: Dict[float, float]) -> float:
    """Linear interpolation across an absolute {temp: mv} curve."""
    pts: List[Tuple[float, float]] = sorted(
        ((float(k), float(v)) for k, v in curve.items()),
        key=lambda p: p[0],
    )
    if not pts:
        raise ValueError("Empty MV curve")
    if temp_c <= pts[0][0]:
        return pts[0][1]
    if temp_c >= pts[-1][0]:
        return pts[-1][1]
    for (t1, v1), (t2, v2) in zip(pts, pts[1:]):
        if t1 <= temp_c <= t2:
            span = t2 - t1
            if span == 0:
                return v1
            u = (temp_c - t1) / span
            return v1 + u * (v2 - v1)
    return pts[-1][1]
