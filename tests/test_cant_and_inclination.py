"""Cant angle and shooting-angle tests."""
import math
import pytest

from ballistics.solver import calculate_solution


def test_cant_zero_is_identity(load_308_175smk):
    base = calculate_solution(target_range_m=800, **load_308_175smk)
    canted = calculate_solution(target_range_m=800, cant_angle_deg=0.0, **load_308_175smk)
    b = base.at_range(800)
    c = canted.at_range(800)
    assert b.drop_m == pytest.approx(c.drop_m, abs=1e-6)
    assert b.windage_m == pytest.approx(c.windage_m, abs=1e-6)


def test_cant_right_tilts_windage_positive(load_308_175smk):
    """
    Canting the rifle right while dialing pure elevation should make the POI
    drift left in the world frame, which the post-process encodes as positive
    scope-frame windage contribution from the drop component.
    """
    # Use a no-wind case so only drop contributes
    params = dict(load_308_175smk)
    params["wind_speed_mps"] = 0.0
    params["wind_direction_deg"] = 0.0

    base = calculate_solution(target_range_m=800, **params)
    canted = calculate_solution(target_range_m=800, cant_angle_deg=5.0, **params)
    b = base.at_range(800)
    c = canted.at_range(800)

    # Drop magnitude largely preserved (cos(5°) ≈ 0.996)
    assert c.drop_m == pytest.approx(b.drop_m * math.cos(math.radians(5)), abs=0.02)
    # A horizontal offset emerges proportional to drop * sin(cant)
    expected_wind = b.drop_m * math.sin(math.radians(5))
    assert c.windage_m == pytest.approx(b.windage_m + expected_wind, abs=0.02)


def test_cant_preserves_magnitude(load_308_175smk):
    """The (drop, windage) vector magnitude is invariant under scope rotation."""
    params = dict(load_308_175smk)
    base = calculate_solution(target_range_m=800, cant_angle_deg=0.0, **params)
    canted = calculate_solution(target_range_m=800, cant_angle_deg=15.0, **params)
    b = base.at_range(800)
    c = canted.at_range(800)
    mag_b = math.hypot(b.drop_m, b.windage_m)
    mag_c = math.hypot(c.drop_m, c.windage_m)
    assert mag_b == pytest.approx(mag_c, rel=0.01)


def test_inclined_shot_reduces_effective_drop(load_308_175smk):
    """
    Shooting 30° uphill reduces the effective vertical drop relative to the
    bore line (the rifleman's rule: multiply by cos(angle)).
    """
    flat = calculate_solution(target_range_m=600, elevation_angle_deg=0.0, **load_308_175smk)
    uphill = calculate_solution(target_range_m=600, elevation_angle_deg=30.0, **load_308_175smk)
    f = flat.at_range(600)
    u = uphill.at_range(600)
    # Uphill shot must require less elevation dial than flat
    assert abs(u.drop_m) < abs(f.drop_m)
    # Roughly cos(30°)=0.866 scaling (solver is more accurate than this, so loose)
    ratio = abs(u.drop_m) / abs(f.drop_m)
    assert 0.80 < ratio < 0.95
