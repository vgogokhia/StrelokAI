"""
Tests for Phase 3 additions:
  - Custom Drag Model (CDM) path in the solver
  - Non-linear muzzle-velocity temperature curve
"""
import math

from ballistics.cdm import DragCurve, load_curve_from_dict
from ballistics.drag_models import G7_DRAG
from ballistics.mv_curve import apply_mv_curve
from ballistics.solver import calculate_solution


def _g7_as_curve() -> DragCurve:
    """Build a CDM from the G7 table, scaled by the G7 BC form factor,
    so the resulting trajectory should match the G7 BC path closely."""
    # For a projectile with G7 BC b (lb/in^2), the BC-based drag formula is
    #   a = (pi/8) * Cd_g7 * rho * v^2 / (b * 703.0696)
    # while the CDM-based formula for the same projectile is
    #   a = (pi/8) * Cd_eff * rho * v^2 * d^2 / m
    # Setting them equal:
    #   Cd_eff = Cd_g7 * m / (d^2 * b * 703.0696)
    # For .308 175 SMK (bc 0.243, m=175 gr, d=0.308 in):
    mass_kg = 175.0 * 0.0000647989
    d_m = 0.308 * 0.0254
    bc_si = 0.243 * 703.0696
    scale = mass_kg / (d_m * d_m * bc_si)
    table = [(m, cd * scale) for m, cd in G7_DRAG]
    return DragCurve(name="scaled-G7-for-308-175", table=tuple(table))


def test_cdm_matches_scaled_g7_at_800m():
    """A CDM built from the G7 table scaled by the bullet's form factor
    should reproduce the G7 BC trajectory within a few cm at 800 m."""
    curve = _g7_as_curve()

    sol_bc = calculate_solution(
        muzzle_velocity_mps=792.0,
        bc_g7=0.243,
        mass_grains=175,
        diameter_inches=0.308,
        bullet_length_in=1.24,
        twist_rate_inches=11.25,
        zero_range_m=100,
        target_range_m=800,
        temperature_c=15.0,
        pressure_mbar=1013.25,
        humidity_pct=0.0,
    )

    sol_cdm = calculate_solution(
        muzzle_velocity_mps=792.0,
        bc_g7=None,
        mass_grains=175,
        diameter_inches=0.308,
        bullet_length_in=1.24,
        twist_rate_inches=11.25,
        zero_range_m=100,
        target_range_m=800,
        temperature_c=15.0,
        pressure_mbar=1013.25,
        humidity_pct=0.0,
        drag_curve=curve,
    )

    pt_bc = sol_bc.at_range(800.0)
    pt_cdm = sol_cdm.at_range(800.0)
    assert pt_bc is not None and pt_cdm is not None

    # Drop within 5 cm
    assert abs(pt_bc.drop_m - pt_cdm.drop_m) < 0.05, (
        f"drop diff {pt_bc.drop_m - pt_cdm.drop_m:.4f} m too large"
    )
    # Velocity within 5 m/s
    assert abs(pt_bc.velocity_mps - pt_cdm.velocity_mps) < 5.0


def test_cdm_dict_loader():
    curve = load_curve_from_dict({
        "name": "test",
        "table": {"0.0": 0.20, "1.0": 0.30, "2.0": 0.28},
    })
    assert curve.name == "test"
    assert curve.table[0] == (0.0, 0.20)
    assert curve.table[-1] == (2.0, 0.28)
    assert curve.mach_range == (0.0, 2.0)


def test_mv_curve_linear_fallback():
    # No curve -> linear formula
    mv = apply_mv_curve(
        base_mv=800.0,
        base_temp_c=15.0,
        current_temp_c=-15.0,
        temp_sensitivity_pct_per_c=0.1,
        mv_curve=None,
    )
    # 30°C colder * 0.1%/°C = -3% -> 776 m/s
    assert abs(mv - 776.0) < 0.5


def test_mv_curve_interpolation():
    curve = {-20.0: 780.0, 0.0: 795.0, 20.0: 805.0, 40.0: 810.0}
    # Exact knots
    assert apply_mv_curve(0.0, 15.0, 0.0, 0.1, curve) == 795.0
    assert apply_mv_curve(0.0, 15.0, 20.0, 0.1, curve) == 805.0
    # Interpolated
    mv = apply_mv_curve(0.0, 15.0, 10.0, 0.1, curve)
    assert 799.0 < mv < 801.0  # midpoint of 795 and 805
    # Clamp below and above the curve range
    assert apply_mv_curve(0.0, 15.0, -50.0, 0.1, curve) == 780.0
    assert apply_mv_curve(0.0, 15.0, 100.0, 0.1, curve) == 810.0
