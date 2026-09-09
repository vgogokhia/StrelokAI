"""
Truing back-solver tests.

Strategy: run the forward solver at a known MV to produce an
"observed" drop, then feed that drop into the back-solver with a
wrong initial MV guess and check it recovers the original.
"""
import pytest

from ballistics.solver import calculate_solution
from ballistics.truing import true_muzzle_velocity


BASE = dict(
    bc_g7=0.243,
    mass_grains=175,
    diameter_inches=0.308,
    zero_range_m=100,
    temperature_c=15.0,
    pressure_mbar=1013.25,
    humidity_pct=0.0,
    wind_speed_mps=0.0,
    wind_direction_deg=90.0,
    bullet_length_in=1.24,
    twist_rate_inches=11.25,
    sight_height_mm=40.0,
)


@pytest.mark.parametrize("true_mv,guess_mv,range_m", [
    (792.0, 780.0, 800),   # User thinks MV is 780, real is 792 (~12 m/s off)
    (792.0, 805.0, 800),   # User thinks too high
    (820.0, 800.0, 600),   # Shorter range, bigger MV
    (780.0, 792.0, 1000),  # Long range amplifies sensitivity
])
def test_truing_recovers_mv(true_mv, guess_mv, range_m):
    # Forward solve to get "observed" drop
    sol = calculate_solution(
        muzzle_velocity_mps=true_mv,
        target_range_m=range_m,
        **BASE,
    )
    pt = sol.at_range(range_m)
    assert pt is not None
    observed_drop = pt.drop_mrad

    # Back-solve with wrong initial guess
    result = true_muzzle_velocity(
        observed_drop_mrad=observed_drop,
        observed_range_m=range_m,
        initial_mv_guess_mps=guess_mv,
        **BASE,
    )

    assert result["converged"], f"did not converge: {result}"
    assert abs(result["trued_mv_mps"] - true_mv) < 1.0, (
        f"recovered {result['trued_mv_mps']:.1f} vs true {true_mv} "
        f"(off by {result['trued_mv_mps'] - true_mv:+.2f} m/s)"
    )
    assert abs(result["residual_mrad"]) < 0.01
    assert result["iterations"] < 12


def test_true_bc_recovers_known_bc(load_308_175smk):
    """Generate a drop with BC 0.230, start from 0.243, expect ~0.230 back."""
    from ballistics.truing import true_ballistic_coefficient
    from ballistics.solver import calculate_solution
    P = dict(load_308_175smk)
    truth = calculate_solution(target_range_m=900.0, **{**P, "bc_g7": 0.230}).at_range(900.0).drop_mrad
    res = true_ballistic_coefficient(
        observed_drop_mrad=truth, observed_range_m=900.0,
        muzzle_velocity_mps=P["muzzle_velocity_mps"], initial_bc=0.243, drag_model="G7",
        mass_grains=P["mass_grains"], diameter_inches=P["diameter_inches"], zero_range_m=P["zero_range_m"],
        temperature_c=15.0, pressure_mbar=1013.25, humidity_pct=0.0,
        bullet_length_in=P["bullet_length_in"], twist_rate_inches=P["twist_rate_inches"],
        sight_height_mm=P["sight_height_mm"],
    )
    assert res["converged"]
    assert abs(res["trued_bc"] - 0.230) < 0.002
