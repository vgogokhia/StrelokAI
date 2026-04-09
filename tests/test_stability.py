"""Miller gyroscopic stability factor tests.

Reference values from Berger/Litz published data:
- .308 175 gr SMK @ 2600 fps in 1:11.25" twist, ICAO std: SG ~1.8
- .308 175 gr SMK @ 2600 fps in 1:12.0" twist, ICAO std: SG ~1.55
- .308 175 gr SMK @ 2600 fps in 1:10.0" twist, ICAO std: SG ~2.2
- 6.5mm 140 gr ELD-M in 1:8" twist @ 2700 fps: SG ~2.0
"""
import pytest

from ballistics.solver import (
    Atmosphere,
    AtmosphericConditions,
    BallisticSolver,
    Projectile,
    Rifle,
    ShootingConditions,
    Wind,
)


def _solver(mass_gr, diameter_in, length_in, twist_in, v_mps):
    proj = Projectile(
        mass_grains=mass_gr,
        diameter_inches=diameter_in,
        bc_g7=0.243,
        length_inches=length_in,
    )
    rifle = Rifle(
        muzzle_velocity_mps=v_mps,
        zero_range_m=100.0,
        twist_rate_inches=twist_in,
    )
    atm = Atmosphere(AtmosphericConditions(15.0, 1013.25, 0.0, 0.0))
    return BallisticSolver(ShootingConditions(proj, rifle, atm, Wind()))


def test_sg_308_175smk_twist_1125():
    sg = _solver(175, 0.308, 1.24, 11.25, 792.48)._miller_stability()
    assert sg == pytest.approx(1.85, abs=0.15)


def test_sg_308_175smk_twist_10():
    sg = _solver(175, 0.308, 1.24, 10.0, 792.48)._miller_stability()
    assert sg == pytest.approx(2.35, abs=0.20)


def test_sg_308_175smk_twist_12_marginal():
    sg = _solver(175, 0.308, 1.24, 12.0, 792.48)._miller_stability()
    # 1:12 is marginal but still > 1.4 at 2600 fps standard conditions
    assert 1.3 < sg < 1.8


def test_sg_increases_with_muzzle_velocity():
    slow = _solver(175, 0.308, 1.24, 11.25, 700)._miller_stability()
    fast = _solver(175, 0.308, 1.24, 11.25, 900)._miller_stability()
    assert fast > slow


def test_sg_decreases_in_cold_dense_air():
    """Cold dense air reduces SG (shorter stability). Hot thin air raises SG."""
    proj = Projectile(175, 0.308, bc_g7=0.243, length_inches=1.24)
    rifle = Rifle(792.48, 100.0, twist_rate_inches=11.25)
    hot = Atmosphere(AtmosphericConditions(35.0, 900.0, 0.0, 0.0))
    cold = Atmosphere(AtmosphericConditions(-10.0, 1050.0, 0.0, 0.0))
    sg_hot = BallisticSolver(ShootingConditions(proj, rifle, hot, Wind()))._miller_stability()
    sg_cold = BallisticSolver(ShootingConditions(proj, rifle, cold, Wind()))._miller_stability()
    assert sg_hot > sg_cold
