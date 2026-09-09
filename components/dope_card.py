"""
ballistics.ge - Dope Card Component
Printable range card with CSV export, in the user's units.
Version: 1.1.0 - unit-aware ranges, MRAD/MOA, wind reference in user units
"""
import streamlit as st

from ballistics.dope_card import build_dope_table, rows_to_csv
from core.units import (
    is_imperial, range_label, velocity_label, angular_unit, to_angular,
    input_range_from_m, input_range_to_m, input_speed_from_mps, input_speed_to_mps,
    speed_label, input_velocity_from_mps,
)


def render_dope_card():
    st.markdown("### 📋 Dope Card")
    st.caption("Generated from the currently loaded rifle/ammo profile and current atmosphere.")

    profile = st.session_state.profile
    unit = range_label()
    imp = is_imperial()
    ang = angular_unit()

    with st.expander("⚙ Card settings", expanded=False):
        col1, col2, col3 = st.columns(3)
        with col1:
            start = st.number_input(
                f"Start ({unit})", min_value=50, max_value=2000, value=100, step=50, key="dope_start",
            )
        with col2:
            end = st.number_input(
                f"End ({unit})", min_value=100, max_value=2500,
                value=1200 if not imp else 1300, step=50, key="dope_end",
            )
        with col3:
            step = st.number_input(
                f"Step ({unit})", min_value=25, max_value=200, value=50, step=25, key="dope_step",
            )
        ref_wind_disp = st.number_input(
            f"Reference wind ({speed_label()}), full value from 9/3 o'clock",
            min_value=1.0, max_value=30.0,
            value=10.0 if imp else 4.0, step=1.0, key="dope_ref_wind",
        )
        use_current = st.checkbox(
            "Use current atmosphere", value=True, key="dope_use_current_atmo",
            help="When on, uses temperature/pressure/humidity from the Calculator tab. Otherwise ICAO standard.",
        )

    if end <= start:
        st.warning("End range must be greater than start range.")
        return

    if use_current:
        temp_c = float(st.session_state.get("temp_c", 15.0))
        pressure = float(st.session_state.get("pressure", 1013.0))
        humidity = float(st.session_state.get("humidity", 50.0))
    else:
        temp_c, pressure, humidity = 15.0, 1013.25, 0.0

    # Sample exactly at the user's unit multiples (converted to metres);
    # the solver interpolates between its integration points.
    disp_ranges = list(range(int(start), int(end) + 1, int(step)))
    rows = build_dope_table(
        muzzle_velocity_mps=profile["muzzle_velocity"],
        drag_model=profile.get("drag_model", "G7"),
        bc_val=profile["bc_g7"],
        mass_grains=profile["mass_grains"],
        diameter_in=profile["diameter"],
        zero_range_m=profile["zero_range"],
        temp_c=temp_c, pressure_mbar=pressure, humidity_pct=humidity,
        wind_reference_mps=input_speed_to_mps(ref_wind_disp),
        bullet_length_in=profile.get("bullet_length_in", 1.0),
        twist_rate_inches=profile["twist_rate"],
        twist_direction=profile.get("twist_direction", "right"),
        sight_height_mm=profile["sight_height"],
        ranges_m=[input_range_to_m(d) for d in disp_ranges],
    )
    if not rows:
        st.warning("No trajectory data produced; check inputs.")
        return
    picked = list(zip(disp_ranges, rows))
    start_m = int(round(input_range_to_m(start)))
    end_m = int(round(input_range_to_m(end)))

    wind_col = f"Wind {ref_wind_disp:.0f} {speed_label()} ({ang})"
    table_data = {
        f"Range ({unit})": [d for d, _ in picked],
        f"Drop ({ang})": [f"{to_angular(r.drop_mrad):.2f}" for _, r in picked],
        f"Drop ({'MOA' if ang == 'MRAD' else 'MRAD'})": [
            f"{(r.drop_moa if ang == 'MRAD' else r.drop_mrad):.2f}" for _, r in picked
        ],
        wind_col: [f"{abs(to_angular(r.wind_mrad)):.2f}" for _, r in picked],
        f"Wind ½ ({ang})": [f"{abs(to_angular(r.wind_half_mrad)):.2f}" for _, r in picked],
        f"Vel ({velocity_label()})": [f"{input_velocity_from_mps(r.velocity_mps):.0f}" for _, r in picked],
        "Mach": [f"{r.mach:.2f}" for _, r in picked],
        "TOF (s)": [f"{r.tof_s:.2f}" for _, r in picked],
    }
    st.dataframe(table_data, width="stretch", hide_index=True)

    csv_text = rows_to_csv([r for _, r in picked])
    st.download_button(
        label="⬇ Download CSV (metric, full precision)",
        data=csv_text,
        file_name=f"dope_card_{profile.get('name', 'profile').replace(' ', '_')}_{start_m}_{end_m}m.csv",
        mime="text/csv",
        width="stretch",
    )
