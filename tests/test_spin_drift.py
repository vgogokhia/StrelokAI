"""Litz empirical spin drift tests.

Reference (Litz, Applied Ballistics):
- .308 175 gr SMK, 11.25" twist, 2600 fps, std atmo: ~9-11" right drift at 1000 yd
  1000 yd = 914 m, 10 inches = 0.254 m -> ~0.28 MRAD
"""
import pytest

from ballistics.solver import calculate_solution


def test_308_175smk_spin_drift_1000yd(load_308_175smk):
    """Spin drift at ~1000 yd for a RH-twist .308 should be ~0.2-0.35 MRAD right."""
    solution = calculate_solution(
        target_range_m=914.0,
        **load_308_175smk,
    )
    # Solver stores absolute spin drift in meters at the target range
    sd_m = solution.spin_drift_m
    sd_mrad = (sd_m / 914.0) * 1000.0
    assert 0.15 < sd_mrad < 0.40, f"spin drift {sd_mrad:.3f} MRAD out of Litz range"


def test_spin_drift_zero_at_muzzle():
    solution = calculate_solution(
        muzzle_velocity_mps=800.0,
        bc_g7=0.243,
        mass_grains=175.0,
        diameter_inches=0.308,
        bullet_length_in=1.24,
        twist_rate_inches=11.25,
        zero_range_m=100.0,
        target_range_m=150.0,
    )
    # At very short range, spin drift is negligible
    pt = solution.at_range(50.0)
    assert pt is not None
    assert abs(pt.windage_mrad) < 0.1


def test_spin_drift_reverses_for_left_twist(load_308_175smk):
    params = dict(load_308_175smk)
    params["twist_direction"] = "right"
    right = calculate_solution(target_range_m=800.0, **params).spin_drift_m
    params["twist_direction"] = "left"
    left = calculate_solution(target_range_m=800.0, **params).spin_drift_m
    assert right * left < 0
    assert abs(abs(right) - abs(left)) < 1e-6
