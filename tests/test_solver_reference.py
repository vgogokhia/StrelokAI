"""Reference-load sanity tests.

Expected values come from an independent implementation (py_ballisticcalc
2.3.1, RK4 engine on the same JBM/BRL drag tables) for the ICAO standard
atmosphere, 100 m zero, 40 mm sight height, no wind. The full per-100 m
tables live in ``tests/fixtures/published_tables`` and are exercised by
``test_published_tables.py``; the spot checks here guard the two most common
loads with an explicit, readable tolerance.

Tolerances: drop ±3 % (min ±0.05 MRAD), velocity ±2 %.
"""
import pytest

from ballistics.solver import calculate_solution


def _check(pt, drop_ref, vel_ref):
    assert pt is not None
    tol = max(0.05, abs(drop_ref) * 0.03)
    assert pt.drop_mrad == pytest.approx(drop_ref, abs=tol), (
        f"drop {pt.drop_mrad:.3f} MRAD vs ref {drop_ref}"
    )
    assert pt.velocity_mps == pytest.approx(vel_ref, rel=0.02), (
        f"velocity {pt.velocity_mps:.0f} m/s vs ref {vel_ref}"
    )


# ---------- .308 Win 175 gr SMK, G7 0.243 @ 792.48 m/s (2600 fps) ----------
@pytest.mark.parametrize("range_m,drop_mrad_ref,vel_ref", [
    (300, -1.681, 618.0),
    (500, -4.098, 514.6),
    (800, -9.264, 375.6),
    (1000, -14.296, 315.3),
])
def test_308_175smk_trajectory(load_308_175smk, range_m, drop_mrad_ref, vel_ref):
    solution = calculate_solution(target_range_m=range_m, **load_308_175smk)
    _check(solution.at_range(range_m), drop_mrad_ref, vel_ref)


# ---------- 6.5 CM 140 gr ELD-M, G7 0.315 @ 825 m/s ----------
@pytest.mark.parametrize("range_m,drop_mrad_ref,vel_ref", [
    (300, -1.433, 684.9),
    (500, -3.404, 599.8),
    (800, -7.223, 482.5),
    (1000, -10.530, 410.6),
])
def test_65cm_140eldm_trajectory(load_65cm_140eldm, range_m, drop_mrad_ref, vel_ref):
    solution = calculate_solution(target_range_m=range_m, **load_65cm_140eldm)
    _check(solution.at_range(range_m), drop_mrad_ref, vel_ref)


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
    assert w10 / w5 == pytest.approx(2.0, rel=0.10)


def test_solution_at_zero_range_has_zero_drop(load_308_175smk):
    solution = calculate_solution(target_range_m=200.0, **load_308_175smk)
    pt = solution.at_range(100.0)
    assert pt is not None
    assert abs(pt.drop_m) < 0.01


def test_wind_from_right_pushes_bullet_left(load_308_175smk):
    """Solver convention: wind FROM the right (90°) drifts the bullet left (negative)."""
    params = dict(load_308_175smk)
    sol = calculate_solution(
        target_range_m=500.0, wind_speed_mps=5.0, wind_direction_deg=90, **params
    )
    assert sol.at_range(500.0).windage_mrad < -0.5


# ---------- Cross-check against py_ballisticcalc when it is installed ----------
pbc = pytest.importorskip("py_ballisticcalc", reason="py_ballisticcalc not installed")


def test_matches_py_ballisticcalc_308(load_308_175smk):
    from py_ballisticcalc import (
        DragModel, TableG7, Weight, Distance, Ammo, Velocity, Weapon, Atmo,
        Pressure, Temperature, Calculator, Shot,
    )
    L = load_308_175smk
    dm = DragModel(L["bc_g7"], TableG7, Weight.Grain(L["mass_grains"]),
                   Distance.Inch(L["diameter_inches"]), Distance.Inch(L["bullet_length_in"]))
    shot = Shot(
        weapon=Weapon(sight_height=Distance.Millimeter(L["sight_height_mm"]),
                      twist=Distance.Inch(L["twist_rate_inches"])),
        ammo=Ammo(dm, Velocity.MPS(L["muzzle_velocity_mps"])),
        atmo=Atmo(altitude=Distance.Meter(0), pressure=Pressure.hPa(1013.25),
                  temperature=Temperature.Celsius(15), humidity=0.0),
        winds=[],
    )
    calc = Calculator()
    calc.set_weapon_zero(shot, Distance.Meter(L["zero_range_m"]))
    res = calc.fire(shot, trajectory_range=Distance.Meter(1000), trajectory_step=Distance.Meter(100))
    ours = calculate_solution(target_range_m=1000.0, **L)
    for r in res.trajectory:
        d = round(r.distance >> Distance.Meter)
        if d < 200 or d % 100:
            continue
        pt = ours.at_range(float(d))
        ref_drop_mrad = (r.height >> Distance.Meter) / d * 1000
        assert pt.drop_mrad == pytest.approx(ref_drop_mrad, abs=max(0.03, abs(ref_drop_mrad) * 0.02))
        assert pt.velocity_mps == pytest.approx(r.velocity >> Velocity.MPS, rel=0.01)
