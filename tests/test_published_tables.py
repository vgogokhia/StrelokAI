"""
Published-table validation harness.

Runs the solver against published dope tables bundled as JSON fixtures
in ``tests/fixtures/published_tables``. Each fixture defines a load
and a list of range bands with min/max acceptable drop and velocity
windows. Fixtures carry either exact reference values (``drop_mrad``/``vel_mps``
with a ``tolerance`` block; generated from py_ballisticcalc on the same
BRL/JBM drag tables) or legacy min/max windows.

Adding a new table is a fixture-only change — drop a JSON file in the
fixtures directory with the schema in ``308_175_smk_icao.json`` and
this test will pick it up automatically.
"""
import json
from pathlib import Path

import pytest

from ballistics.solver import calculate_solution


_FIXTURE_DIR = Path(__file__).parent / "fixtures" / "published_tables"


def _load_fixtures():
    if not _FIXTURE_DIR.exists():
        return []
    out = []
    for path in sorted(_FIXTURE_DIR.glob("*.json")):
        with path.open("r", encoding="utf-8") as f:
            data = json.load(f)
        out.append(pytest.param(data, id=path.stem))
    return out


@pytest.mark.parametrize("fixture", _load_fixtures())
def test_published_table_rows(fixture):
    label = fixture.get("label", "unnamed")
    inputs = fixture["inputs"]
    expected_rows = fixture["expected"]

    # Use the farthest expected range as the solve target.
    max_range = max(row["range_m"] for row in expected_rows)

    solution = calculate_solution(
        muzzle_velocity_mps=inputs["muzzle_velocity_mps"],
        bc_g7=inputs.get("bc_g7"),
        bc_g1=inputs.get("bc_g1"),
        mass_grains=inputs["mass_grains"],
        diameter_inches=inputs["diameter_inches"],
        zero_range_m=inputs["zero_range_m"],
        target_range_m=max_range,
        temperature_c=inputs.get("temperature_c", 15.0),
        pressure_mbar=inputs.get("pressure_mbar", 1013.25),
        humidity_pct=inputs.get("humidity_pct", 0.0),
        wind_speed_mps=inputs.get("wind_speed_mps", 0.0),
        wind_direction_deg=inputs.get("wind_direction_deg", 90.0),
        latitude_deg=inputs.get("latitude_deg", 41.7),
        bullet_length_in=inputs.get("bullet_length_in", 1.0),
        twist_rate_inches=inputs.get("twist_rate_inches", 10.0),
    )

    tol = fixture.get("tolerance", {})
    drop_rel = float(tol.get("drop_mrad_rel", 0.03))
    drop_abs = float(tol.get("drop_mrad_abs", 0.05))
    vel_rel = float(tol.get("vel_mps_rel", 0.02))

    for row in expected_rows:
        r = row["range_m"]
        pt = solution.at_range(float(r))
        assert pt is not None, f"{label}: no trajectory point at {r} m"

        if "drop_mrad" in row:
            ref = float(row["drop_mrad"])
            assert pt.drop_mrad == pytest.approx(ref, abs=max(drop_abs, abs(ref) * drop_rel)), (
                f"{label} @ {r} m: drop {pt.drop_mrad:.3f} MRAD vs reference {ref}"
            )
        else:
            drop_min, drop_max = row["drop_mrad_min"], row["drop_mrad_max"]
            assert drop_min <= pt.drop_mrad <= drop_max, (
                f"{label} @ {r} m: drop {pt.drop_mrad:.3f} MRAD outside [{drop_min}, {drop_max}]"
            )

        if "vel_mps" in row:
            assert pt.velocity_mps == pytest.approx(float(row["vel_mps"]), rel=vel_rel), (
                f"{label} @ {r} m: velocity {pt.velocity_mps:.0f} m/s vs reference {row['vel_mps']}"
            )
        elif "vel_mps_min" in row and "vel_mps_max" in row:
            vmin, vmax = row["vel_mps_min"], row["vel_mps_max"]
            assert vmin <= pt.velocity_mps <= vmax, (
                f"{label} @ {r} m: velocity {pt.velocity_mps:.0f} m/s outside [{vmin}, {vmax}]"
            )
