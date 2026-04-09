"""
StrelokAI - Ballistic Solution Component
Executes ballistic calculations and renders elevation/windage results.
Wraps the solver with st.cache_data so UI reruns don't recompute an
unchanged trajectory.
Version: 1.2.0
"""
import streamlit as st

from ballistics.solver import calculate_solution
from ballistics.mv_curve import apply_mv_curve
from config import DEFAULT_LATITUDE
from core.units import fmt_velocity, fmt_energy, fmt_range


@st.cache_data(ttl=600, show_spinner=False)
def _cached_solution(
    muzzle_velocity_mps: float,
    drag_model: str,
    bc_val: float,
    mass_grains: float,
    diameter: float,
    zero_range: float,
    target_range: float,
    temp_c: float,
    pressure: float,
    humidity: float,
    altitude: float,
    wind_speed: float,
    wind_deg: float,
    bullet_length_in: float,
    twist_rate_inches: float,
    twist_direction: str,
    sight_height_mm: float,
    elevation_angle_deg: float,
    cant_angle_deg: float,
    latitude_deg: float,
    azimuth_deg: float,
):
    """Cached wrapper around calculate_solution.

    Arguments are rounded upstream to reduce cache churn. Returns a
    BallisticSolution. TTL=600s bounds memory usage; results are per-session
    by default since st.cache_data is process-scoped.
    """
    return calculate_solution(
        muzzle_velocity_mps=muzzle_velocity_mps,
        bc_g7=bc_val if drag_model == "G7" else None,
        bc_g1=bc_val if drag_model == "G1" else None,
        mass_grains=mass_grains,
        diameter_inches=diameter,
        zero_range_m=zero_range,
        target_range_m=target_range,
        temperature_c=temp_c,
        pressure_mbar=pressure,
        humidity_pct=humidity,
        altitude_m=altitude,
        wind_speed_mps=wind_speed,
        wind_direction_deg=wind_deg,
        latitude_deg=latitude_deg,
        azimuth_deg=azimuth_deg,
        bullet_length_in=bullet_length_in,
        twist_rate_inches=twist_rate_inches,
        twist_direction=twist_direction,
        sight_height_mm=sight_height_mm,
        elevation_angle_deg=elevation_angle_deg,
        cant_angle_deg=cant_angle_deg,
    )


def _q(value: float, step: float) -> float:
    """Quantize to reduce cache key churn on tiny widget jitter."""
    return round(value / step) * step


def render_solution_section(
    muzzle_velocity, drag_model, bc_val, mass_grains, diameter, zero_range,
    target_range, temp_c, pressure, humidity, altitude,
    wind_speed, wind_deg, **kwargs
):
    try:
        mv_temp_c = kwargs.get('mv_temp_c', 15.0)
        temp_sensitivity = kwargs.get('temp_sensitivity', 0.1)
        bullet_length_in = kwargs.get('bullet_length_in', 1.0)
        twist_rate_inches = kwargs.get('twist_rate_inches', 10.0)
        twist_direction = kwargs.get('twist_direction', 'right')
        sight_height_mm = kwargs.get('sight_height_mm', 40.0)
        elevation_angle_deg = kwargs.get('elevation_angle_deg', 0.0)
        cant_angle_deg = kwargs.get('cant_angle_deg', 0.0)

        # Powder-temperature compensated muzzle velocity.
        mv_curve = kwargs.get('mv_curve')  # Optional {temp_c: mv_mps}
        actual_mv = apply_mv_curve(
            base_mv=muzzle_velocity,
            base_temp_c=mv_temp_c,
            current_temp_c=temp_c,
            temp_sensitivity_pct_per_c=temp_sensitivity,
            mv_curve=mv_curve,
        )
        temp_diff = temp_c - mv_temp_c

        if mv_curve:
            st.caption(
                f"🔥 MV from curve: **{actual_mv:.1f} m/s** at {temp_c:.1f}°C"
            )
        elif abs(temp_diff) > 0.1 and temp_sensitivity > 0:
            st.caption(
                f"🔥 Adjusted MV: **{actual_mv:.1f} m/s** "
                f"(Base: {muzzle_velocity}m/s @ {mv_temp_c}°C)"
            )

        solution = _cached_solution(
            muzzle_velocity_mps=_q(actual_mv, 0.1),
            drag_model=drag_model,
            bc_val=_q(bc_val, 0.001),
            mass_grains=_q(mass_grains, 0.1),
            diameter=_q(diameter, 0.001),
            zero_range=_q(zero_range, 1.0),
            target_range=_q(target_range, 1.0),
            temp_c=_q(temp_c, 0.1),
            pressure=_q(pressure, 0.1),
            humidity=_q(humidity, 1.0),
            altitude=_q(altitude, 1.0),
            wind_speed=_q(wind_speed, 0.1),
            wind_deg=_q(wind_deg, 1.0),
            bullet_length_in=_q(bullet_length_in, 0.01),
            twist_rate_inches=_q(twist_rate_inches, 0.1),
            twist_direction=twist_direction,
            sight_height_mm=_q(sight_height_mm, 0.5),
            elevation_angle_deg=_q(elevation_angle_deg, 0.5),
            cant_angle_deg=_q(cant_angle_deg, 0.5),
            latitude_deg=_q(DEFAULT_LATITUDE, 0.1),
            azimuth_deg=_q(float(st.session_state.get("compass_heading", 0.0)), 5.0),
        )

        target_point = solution.at_range(target_range)

        if target_point:
            click_value = 0.1
            elevation_clicks = int(abs(target_point.drop_mrad) / click_value)
            windage_clicks = int(abs(target_point.windage_mrad) / click_value)
            elev_dir = 'UP' if target_point.drop_mrad < 0 else 'DOWN'
            wind_dir = 'L' if target_point.windage_mrad < 0 else 'R'

            st.markdown(f"""
            <div class="main-solution">
                <div class="elevation-display">{elevation_clicks} CLICKS</div>
                <div style="font-size: 24px; color: #888;">ELEVATION {elev_dir}</div>
                <div style="font-size: 14px; color: #666;">({abs(target_point.drop_mrad):.2f} MRAD)</div>
                <div style="margin-top: 20px;"></div>
                <div class="windage-display">{windage_clicks} {wind_dir}</div>
                <div style="font-size: 18px; color: #666;">WINDAGE</div>
                <div style="font-size: 14px; color: #555;">({abs(target_point.windage_mrad):.2f} MRAD)</div>
            </div>
            """, unsafe_allow_html=True)

            with st.expander("📊 Details", expanded=False):
                data_cols = st.columns(4)
                with data_cols[0]:
                    st.metric("ToF", f"{target_point.time_s:.2f}s")
                with data_cols[1]:
                    st.metric("Velocity", fmt_velocity(target_point.velocity_mps))
                with data_cols[2]:
                    st.metric("Energy", fmt_energy(target_point.energy_j))
                with data_cols[3]:
                    st.metric("Mach", f"{target_point.mach:.2f}")
                st.caption(
                    f"SG={solution.stability_factor:.2f}  "
                    f"Aero Jump={solution.aero_jump_mrad:+.3f} MRAD  "
                    f"Spin Drift={solution.spin_drift_m*1000/target_range:+.2f} MRAD"
                )

            with st.expander("📊 Full Trajectory Table"):
                st.markdown("| Range | Drop | Drop | Windage | Velocity | ToF |")
                st.markdown("|:---:|:---:|:---:|:---:|:---:|:---:|")
                st.markdown("| (m) | (m) | (MRAD) | (MRAD) | (m/s) | (s) |")
                for pt in solution.trajectory:
                    if pt.range_m % 100 == 0 or pt.range_m == target_range:
                        st.markdown(
                            f"| {pt.range_m:.0f} | {pt.drop_m:.3f} | {pt.drop_mrad:.2f} | "
                            f"{pt.windage_mrad:.2f} | {pt.velocity_mps:.0f} | {pt.time_s:.3f} |"
                        )

    except Exception as e:
        st.error(f"Calculation error: {e}")
        st.exception(e)
