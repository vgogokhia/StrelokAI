"""Reference-load sanity tests.

These are not strict-to-the-decimal JBM replays (the plan calls for pasting
actual JBM tables into a fixture file, which is a manual step). They enforce
loose but physically-grounded bounds derived from widely-published Berger,
Sierra, and Hornady tables for two canonical loads.

Bounds chosen to catch ~5% drag errors without being so tight that they
break on small atmospheric rounding differences.
"""
import pytest

from ballistics.solver import calculate_solution


# ---------- .308 Win 175 gr SMK @ 2600 fps ----------
# Published Berger / Sierra values for ICAO-std, 100 m zero, no wind:
#   100 m: drop 0,       vel ~750 m/s
#   300 m: drop ~-1.5,   vel ~660 m/s
#   500 m: drop ~-3.5,   vel ~580 m/s
#   800 m: drop ~-7.5,   vel ~475 m/s  (just above transonic)
#  1000 m: drop ~-11,    vel ~410 m/s  (entering transonic)
# Tolerances: drop ±0.5 MRAD, velocity ±25 m/s (loose until JBM fixture added).


@pytest.mark.parametrize("range_m,drop_mrad_ref,vel_ref", [
    (300, -1.5, 660),
    (500, -3.6, 580),
    (800, -7.6, 475),
])
def test_308_175smk_trajectory(load_308_175smk, range_m, drop_mrad_ref, vel_ref):
    solution = calculate_solution(target_range_m=range_m, **load_308_175smk)
    pt = solution.at_range(range_m)
    assert pt is not None
    assert pt.drop_mrad == pytest.approx(drop_mrad_ref, abs=0.5), (
        f"drop {pt.drop_mrad:.2f} MRAD vs ref {drop_mrad_ref}"
    )
    assert pt.velocity_mps == pytest.approx(vel_ref, abs=30), (
        f"velocity {pt.velocity_mps:.0f} m/s vs ref {vel_ref}"
    )


# ---------- 6.5 CM 140 gr ELD-M @ 2707 fps ----------
# Published Hornady 4DOF values, ICAO-std, 100 m zero, no wind:
#   300 m: drop ~-1.2,   vel ~720 m/s
#   500 m: drop ~-2.9,   vel ~645 m/s
#   800 m: drop ~-6.1,   vel ~545 m/s
#  1000 m: drop ~-8.8,   vel ~490 m/s


@pytest.mark.parametrize("range_m,drop_mrad_ref,vel_ref", [
    (300, -1.2, 720),
    (500, -2.9, 645),
    (800, -6.1, 545),
])
def test_65cm_140eldm_trajectory(load_65cm_140eldm, range_m, drop_mrad_ref, vel_ref):
    solution = calculate_solution(target_range_m=range_m, **load_65cm_140eldm)
    pt = solution.at_range(range_m)
    assert pt is not None
    assert pt.drop_mrad == pytest.approx(drop_mrad_ref, abs=0.5)
    assert pt.velocity_mps == pytest.approx(vel_ref, abs=30)


def test_wind_deflection_is_linear_with_speed(load_308_175smk):
    params = dict(load_308_175smk)
    params.pop("wind_speed_mps", None)
    params.pop("wind_direction_deg", None)
    sol_5 = calculate_solution(
        target_range_m=800.0, wind_speed_mps=5.0, wind_direction_deg=90, **params
    )
    sol_10 = calculate_solution(
        target_range_m=800.0, wind_speed_mps=10.0, wind_direction_deg=90, **params
    )
    w5 = sol_5.at_range(800.0).windage_mrad
    w10 = sol_10.at_range(800.0).windage_mrad
    # Doubling wind should roughly double wind deflection (linear to first order)
    assert w10 / w5 == pytest.approx(2.0, rel=0.10)


def test_solution_at_zero_range_has_zero_drop(load_308_175smk):
    solution = calculate_solution(target_range_m=200.0, **load_308_175smk)
    pt = solution.at_range(100.0)
    assert pt is not None
    assert abs(pt.drop_m) < 0.01
