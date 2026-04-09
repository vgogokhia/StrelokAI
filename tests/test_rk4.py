"""RK4 integrator correctness tests.

Cross-checks the integrator against analytically-known physics in regimes
where drag is negligible (very heavy bullet, very high BC). A ballistic
solver with a correct RK4 kernel must produce free-fall drop that tracks
(1/2) g t^2 to within a small tolerance.
"""
import math

import pytest

from ballistics.solver import calculate_solution

G = 9.80665


def test_near_vacuum_preserves_velocity():
    """
    With negligible drag (huge BC and vanishing air density), the projectile
    must lose essentially no speed over 1000 m. This verifies the RK4 kernel
    doesn't introduce phantom drag from numerical error.
    """
    solution = calculate_solution(
        muzzle_velocity_mps=800.0,
        bc_g7=9999.0,
        mass_grains=175.0,
        diameter_inches=0.308,
        zero_range_m=100.0,
        target_range_m=1000.0,
        temperature_c=15.0,
        pressure_mbar=1.0,   # nearly empty air
        humidity_pct=0.0,
    )
    pt = solution.at_range(1000.0)
    assert pt is not None
    assert pt.velocity_mps == pytest.approx(800.0, abs=2.0)


def test_near_vacuum_trajectory_is_parabolic():
    """
    In vacuum, the trajectory is a pure parabola. Sampled at three equally-
    spaced ranges past the zero, the second difference of drop must match
    the analytical -g/v^2 * dx^2 to high precision.
    """
    v0 = 800.0
    solution = calculate_solution(
        muzzle_velocity_mps=v0,
        bc_g7=9999.0,
        mass_grains=175.0,
        diameter_inches=0.308,
        zero_range_m=100.0,
        target_range_m=1000.0,
        temperature_c=15.0,
        pressure_mbar=1.0,
        humidity_pct=0.0,
    )
    # Three well-separated post-zero points
    p1 = solution.at_range(300.0)
    p2 = solution.at_range(500.0)
    p3 = solution.at_range(700.0)
    assert p1 and p2 and p3
    dx = 200.0
    second_diff = (p3.drop_m - 2.0 * p2.drop_m + p1.drop_m)
    expected = -G * dx * dx / (v0 * v0)
    assert second_diff == pytest.approx(expected, rel=0.01)


def test_zero_drop_at_zero_range():
    """At the configured zero range, drop should be essentially zero."""
    solution = calculate_solution(
        muzzle_velocity_mps=800.0,
        bc_g7=0.243,
        mass_grains=175.0,
        diameter_inches=0.308,
        zero_range_m=100.0,
        target_range_m=150.0,
    )
    pt = solution.at_range(100.0)
    assert pt is not None
    assert abs(pt.drop_m) < 0.01  # within 1 cm


def test_monotonic_drop_and_velocity():
    """Drop must be monotonically more negative and velocity monotonically
    decreasing over a typical long-range trajectory."""
    solution = calculate_solution(
        muzzle_velocity_mps=850.0,
        bc_g7=0.243,
        mass_grains=175.0,
        diameter_inches=0.308,
        zero_range_m=100.0,
        target_range_m=1000.0,
    )
    traj = [p for p in solution.trajectory if p.range_m >= 200]
    for a, b in zip(traj, traj[1:]):
        assert b.drop_m <= a.drop_m + 1e-9, f"drop not monotonic near {a.range_m}->{b.range_m}"
        assert b.velocity_mps <= a.velocity_mps + 1e-9, f"velocity not monotonic near {a.range_m}->{b.range_m}"
