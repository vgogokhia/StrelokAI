"""
StrelokAI - Dope Card Component
Renders a printable range card with CSV export.
Version: 1.0.0
"""
import streamlit as st

from ballistics.dope_card import build_dope_table, rows_to_csv
from core.units import is_imperial, range_label, velocity_label


def render_dope_card():
    st.markdown("### 📋 Dope Card")
    st.caption("Generated from the currently loaded rifle/ammo profile.")

    profile = st.session_state.profile

    with st.expander("⚙ Card settings", expanded=False):
        col1, col2, col3 = st.columns(3)
        with col1:
            start = st.number_input(
                "Start (m)", min_value=50, max_value=2000, value=100, step=50,
                key="dope_start",
            )
        with col2:
            end = st.number_input(
                "End (m)", min_value=100, max_value=2500, value=1200, step=50,
                key="dope_end",
            )
        with col3:
            step = st.number_input(
                "Step (m)", min_value=25, max_value=200, value=50, step=25,
                key="dope_step",
            )

        use_current = st.checkbox(
            "Use current atmosphere",
            value=True,
            help="When on, uses the temperature/pressure/humidity from the main Calculator tab. Otherwise uses ICAO standard.",
            key="dope_use_current_atmo",
        )

    if use_current:
        temp_c = float(st.session_state.get("temp_c", 15.0))
        pressure = float(st.session_state.get("pressure", 1013.0))
        humidity = float(st.session_state.get("humidity", 50.0))
    else:
        temp_c, pressure, humidity = 15.0, 1013.25, 0.0

    rows = build_dope_table(
        muzzle_velocity_mps=profile["muzzle_velocity"],
        drag_model=profile.get("drag_model", "G7"),
        bc_val=profile["bc_g7"],
        mass_grains=profile["mass_grains"],
        diameter_in=profile["diameter"],
        zero_range_m=profile["zero_range"],
        temp_c=temp_c,
        pressure_mbar=pressure,
        humidity_pct=humidity,
        bullet_length_in=profile.get("bullet_length_in", 1.0),
        twist_rate_inches=profile["twist_rate"],
        twist_direction=profile.get("twist_direction", "right"),
        sight_height_mm=profile["sight_height"],
        range_start_m=int(start),
        range_end_m=int(end),
        range_step_m=int(step),
    )

    if not rows:
        st.warning("No trajectory data produced; check inputs.")
        return

    # Build a simple tabular view (respects unit system)
    imperial = is_imperial()
    rng_scale = 1.09361 if imperial else 1.0
    vel_scale = 3.28084 if imperial else 1.0
    table_data = {
        f"Range ({range_label()})": [int(round(r.range_m * rng_scale)) for r in rows],
        "Drop (MRAD)": [f"{r.drop_mrad:.2f}" for r in rows],
        "Drop (MOA)": [f"{r.drop_moa:.1f}" for r in rows],
        "Wind 10mph (MRAD)": [f"{r.wind_mrad:.2f}" for r in rows],
        "Wind 5mph (MRAD)": [f"{r.wind_half_mrad:.2f}" for r in rows],
        f"Vel ({velocity_label()})": [f"{r.velocity_mps * vel_scale:.0f}" for r in rows],
        "Mach": [f"{r.mach:.2f}" for r in rows],
        "TOF (s)": [f"{r.tof_s:.2f}" for r in rows],
    }
    st.dataframe(table_data, use_container_width=True, hide_index=True)

    csv_text = rows_to_csv(rows)
    st.download_button(
        label="⬇ Download CSV",
        data=csv_text,
        file_name=f"dope_card_{int(start)}_{int(end)}m.csv",
        mime="text/csv",
        use_container_width=True,
    )
