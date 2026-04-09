"""
Dope card builder.

Iterates the ballistic solver over a range band and collects a per-range
summary suitable for dope-card tables and CSV export.
"""
from dataclasses import dataclass
from typing import List, Optional

from ballistics.solver import calculate_solution


@dataclass
class DopeRow:
    range_m: int
    drop_mrad: float
    drop_moa: float
    wind_mrad: float          # full value at reference wind
    wind_half_mrad: float     # half value
    velocity_mps: float
    mach: float
    energy_j: float
    tof_s: float


def build_dope_table(
    *,
    muzzle_velocity_mps: float,
    drag_model: str,
    bc_val: float,
    mass_grains: float,
    diameter_in: float,
    zero_range_m: float,
    temp_c: float = 15.0,
    pressure_mbar: float = 1013.25,
    humidity_pct: float = 50.0,
    altitude_m: float = 0.0,
    wind_reference_mps: float = 4.47,  # 10 mph
    wind_direction_deg: float = 270.0,  # full value from 9 o'clock
    bullet_length_in: float = 1.0,
    twist_rate_inches: float = 10.0,
    twist_direction: str = "right",
    sight_height_mm: float = 40.0,
    range_start_m: int = 100,
    range_end_m: int = 1500,
    range_step_m: int = 50,
) -> List[DopeRow]:
    """Build a dope table in a single solver call.

    Uses one long solve out to range_end_m and picks trajectory points at the
    requested range multiples. Wind is given at the reference value; the
    half-value column is produced by simple scaling (linear in crosswind
    component, accurate to a few percent for sub-transonic flight).
    """
    solution = calculate_solution(
        muzzle_velocity_mps=muzzle_velocity_mps,
        bc_g7=bc_val if drag_model == "G7" else None,
        bc_g1=bc_val if drag_model == "G1" else None,
        mass_grains=mass_grains,
        diameter_inches=diameter_in,
        zero_range_m=zero_range_m,
        target_range_m=float(range_end_m),
        temperature_c=temp_c,
        pressure_mbar=pressure_mbar,
        humidity_pct=humidity_pct,
        altitude_m=altitude_m,
        wind_speed_mps=wind_reference_mps,
        wind_direction_deg=wind_direction_deg,
        bullet_length_in=bullet_length_in,
        twist_rate_inches=twist_rate_inches,
        twist_direction=twist_direction,
        sight_height_mm=sight_height_mm,
    )

    rows: List[DopeRow] = []
    targets = list(range(range_start_m, range_end_m + 1, range_step_m))
    for r in targets:
        pt = solution.at_range(float(r))
        if pt is None:
            continue
        rows.append(
            DopeRow(
                range_m=r,
                drop_mrad=pt.drop_mrad,
                drop_moa=pt.drop_mrad * 3.4377,  # 1 mrad = 3.4377 MOA
                wind_mrad=pt.windage_mrad,
                wind_half_mrad=pt.windage_mrad * 0.5,
                velocity_mps=pt.velocity_mps,
                mach=pt.mach,
                energy_j=pt.energy_j,
                tof_s=pt.time_s,
            )
        )
    return rows


def rows_to_csv(rows: List[DopeRow]) -> str:
    """Serialize to CSV text."""
    header = "Range_m,Drop_MRAD,Drop_MOA,Wind10mph_MRAD,WindHalf_MRAD,Velocity_mps,Mach,Energy_J,TOF_s\n"
    lines = [header]
    for r in rows:
        lines.append(
            f"{r.range_m},{r.drop_mrad:.3f},{r.drop_moa:.2f},"
            f"{r.wind_mrad:.3f},{r.wind_half_mrad:.3f},"
            f"{r.velocity_mps:.1f},{r.mach:.3f},{r.energy_j:.0f},{r.tof_s:.3f}\n"
        )
    return "".join(lines)
