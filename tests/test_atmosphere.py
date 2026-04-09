"""Atmosphere model sanity tests."""
import math

import pytest

from ballistics.atmosphere import Atmosphere, AtmosphericConditions


def test_icao_standard_density():
    atm = Atmosphere.standard()
    # ICAO standard sea-level air density
    assert atm.air_density() == pytest.approx(1.225, abs=0.002)


def test_speed_of_sound_at_15c():
    atm = Atmosphere.standard()
    # c = sqrt(1.4 * 287.05 * 288.15) ≈ 340.29 m/s
    assert atm.speed_of_sound() == pytest.approx(340.29, abs=0.2)


def test_density_decreases_with_temperature():
    cold = Atmosphere(AtmosphericConditions(-10.0, 1013.25, 0.0, 0.0)).air_density()
    hot = Atmosphere(AtmosphericConditions(35.0, 1013.25, 0.0, 0.0)).air_density()
    assert cold > hot


def test_density_decreases_with_humidity():
    dry = Atmosphere(AtmosphericConditions(25.0, 1013.25, 0.0, 0.0)).air_density()
    wet = Atmosphere(AtmosphericConditions(25.0, 1013.25, 100.0, 0.0)).air_density()
    assert dry > wet


def test_mach_number_at_muzzle():
    atm = Atmosphere.standard()
    # 850 m/s at 15 C should be ~mach 2.5
    assert atm.mach_number(850) == pytest.approx(2.50, abs=0.02)
