"""Backward-compatibility tests for profile loading.

Ensures that legacy profile JSON (written before bullet_length_in and
bc_segments existed) still deserializes cleanly, and that unknown future
keys are ignored instead of raising.
"""
from profiles import CartridgeProfile, RifleProfile, FullProfile


def test_legacy_cartridge_profile_loads_without_bullet_length():
    legacy = {
        "name": "Test Cartridge",
        "muzzle_velocity": 800.0,
        "drag_model": "G7",
        "bc_g7": 0.243,
        "mass_grains": 175.0,
        "diameter": 0.308,
        "mv_temp_c": 15.0,
        "temp_sensitivity": 0.1,
        "description": "",
        "bc_g1": None,
        "created_at": "2025-01-01T00:00:00",
        "updated_at": "2025-01-01T00:00:00",
    }
    prof = CartridgeProfile.from_dict(legacy)
    assert prof.bullet_length_in == 1.0  # default
    assert prof.bc_segments is None


def test_cartridge_profile_ignores_unknown_keys():
    data = {
        "name": "Test",
        "muzzle_velocity": 800.0,
        "drag_model": "G7",
        "bc_g7": 0.243,
        "mass_grains": 175.0,
        "diameter": 0.308,
        "future_field_we_dont_know_about": 42,
    }
    prof = CartridgeProfile.from_dict(data)
    assert prof.name == "Test"


def test_legacy_rifle_profile_without_twist_direction():
    legacy = {
        "name": "Test Rifle",
        "zero_range": 100.0,
        "sight_height": 40.0,
        "twist_rate": 11.25,
    }
    prof = RifleProfile.from_dict(legacy)
    assert prof.twist_direction == "right"


def test_legacy_full_profile_with_muzzle_velocity_in_rifle():
    """
    Pre-1.1 profiles stored muzzle_velocity in Rifle instead of Cartridge.
    FullProfile.from_dict must migrate this.
    """
    legacy = {
        "name": "Old Profile",
        "rifle": {
            "name": "Old Rifle",
            "zero_range": 100.0,
            "sight_height": 40.0,
            "twist_rate": 11.25,
            "muzzle_velocity": 800.0,  # legacy location
        },
        "cartridge": {
            "name": "Old Cart",
            "drag_model": "G7",
            "bc_g7": 0.243,
            "mass_grains": 175.0,
            "diameter": 0.308,
        },
    }
    prof = FullProfile.from_dict(legacy)
    assert prof.cartridge.muzzle_velocity == 800.0
