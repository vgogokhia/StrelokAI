"""Shared fixtures for StrelokAI test suite."""
import sys
from pathlib import Path

import pytest

# Make the project root importable when running `pytest` from anywhere.
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


@pytest.fixture
def std_atmosphere_kwargs():
    """ICAO standard atmosphere kwargs for calculate_solution."""
    return dict(
        temperature_c=15.0,
        pressure_mbar=1013.25,
        humidity_pct=0.0,
        altitude_m=0.0,
    )


@pytest.fixture
def load_308_175smk(std_atmosphere_kwargs):
    """.308 Win 175 gr SMK reference load (Berger/Sierra published)."""
    return dict(
        muzzle_velocity_mps=792.48,   # 2600 fps
        bc_g7=0.243,
        mass_grains=175.0,
        diameter_inches=0.308,
        bullet_length_in=1.24,
        twist_rate_inches=11.25,
        twist_direction="right",
        zero_range_m=100.0,
        sight_height_mm=40.0,
        **std_atmosphere_kwargs,
    )


@pytest.fixture
def load_65cm_140eldm(std_atmosphere_kwargs):
    """6.5 Creedmoor 140 gr ELD-M reference load (Hornady published)."""
    return dict(
        muzzle_velocity_mps=825.0,    # ~2707 fps
        bc_g7=0.315,
        mass_grains=140.0,
        diameter_inches=0.264,
        bullet_length_in=1.40,
        twist_rate_inches=8.0,
        twist_direction="right",
        zero_range_m=100.0,
        sight_height_mm=40.0,
        **std_atmosphere_kwargs,
    )
