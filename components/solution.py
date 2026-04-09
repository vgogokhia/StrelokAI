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
from ballistics.truing import true_muzzle_velocity
from config import DEFAULT_LATITUDE
from core.units import fmt_velocity, fmt_energy, fmt_range, is_imperial, range_label


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
                <div style="font-size: 15px; color: #888; letter-spacing:1px;">ELEVATION {elev_dir} · {abs(target_point.drop_mrad):.2f} MRAD</div>
                <div style="margin-top: 10px;"></div>
                <div class="windage-display">{windage_clicks} {wind_dir}</div>
                <div style="font-size: 13px; color: #666; letter-spacing:1px;">WINDAGE · {abs(target_point.windage_mrad):.2f} MRAD</div>
            </div>
            """, unsafe_allow_html=True)

            # Trajectory graph
            with st.expander("📈 Trajectory Graph", expanded=False):
                _render_trajectory_graph(solution, target_range)

            with st.expander("🎯 True MV (match observed drop)", expanded=False):
                _render_truing_block(
                    muzzle_velocity=actual_mv,
                    drag_model=drag_model,
                    bc_val=bc_val,
                    mass_grains=mass_grains,
                    diameter=diameter,
                    zero_range=zero_range,
                    target_range=target_range,
                    temp_c=temp_c,
                    pressure=pressure,
                    humidity=humidity,
                    bullet_length_in=bullet_length_in,
                    twist_rate_inches=twist_rate_inches,
                    twist_direction=twist_direction,
                    sight_height_mm=sight_height_mm,
                )

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

    except Exception as e:
        st.error(f"Calculation error: {e}")
        st.exception(e)


# ---------------------------------------------------------------------------
# Trajectory graph
# ---------------------------------------------------------------------------

def _render_trajectory_graph(solution, target_range: float):
    """Two-panel Plotly chart: drop (primary) and windage (secondary)."""
    try:
        import plotly.graph_objects as go
        from plotly.subplots import make_subplots
    except ImportError:
        st.info("Install plotly to see trajectory graphs (pip install plotly).")
        return

    imperial = is_imperial()
    rng_scale = 1.09361 if imperial else 1.0
    rng_label = range_label()

    ranges = [pt.range_m * rng_scale for pt in solution.trajectory]
    drops_mrad = [pt.drop_mrad for pt in solution.trajectory]
    wind_mrad = [pt.windage_mrad for pt in solution.trajectory]
    velocities = [pt.velocity_mps * (3.28084 if imperial else 1.0) for pt in solution.trajectory]

    fig = make_subplots(
        rows=2, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.08,
        subplot_titles=("Drop (MRAD) & Velocity", "Windage (MRAD)"),
        specs=[[{"secondary_y": True}], [{}]],
    )

    # Top: drop
    fig.add_trace(
        go.Scatter(
            x=ranges, y=drops_mrad,
            name="Drop (MRAD)",
            line=dict(color="#ff4444", width=2),
            hovertemplate="%{x:.0f} " + rng_label + "<br>%{y:.2f} MRAD<extra></extra>",
        ),
        row=1, col=1, secondary_y=False,
    )
    # Top: velocity on secondary axis
    fig.add_trace(
        go.Scatter(
            x=ranges, y=velocities,
            name="Velocity",
            line=dict(color="#4488ff", width=1.5, dash="dot"),
            hovertemplate="%{x:.0f} " + rng_label + "<br>%{y:.0f} " + ("fps" if imperial else "m/s") + "<extra></extra>",
        ),
        row=1, col=1, secondary_y=True,
    )
    # Bottom: windage
    fig.add_trace(
        go.Scatter(
            x=ranges, y=wind_mrad,
            name="Windage",
            line=dict(color="#44dd88", width=2),
            hovertemplate="%{x:.0f} " + rng_label + "<br>%{y:.2f} MRAD<extra></extra>",
        ),
        row=2, col=1,
    )

    # Target marker
    target_pt = solution.at_range(target_range)
    if target_pt is not None:
        tr = target_range * rng_scale
        fig.add_vline(x=tr, line_dash="dash", line_color="#ffaa00", row="all")
        fig.add_annotation(
            x=tr, y=target_pt.drop_mrad,
            text=f"Target {int(tr)}",
            showarrow=True, arrowhead=2,
            row=1, col=1,
            font=dict(color="#ffaa00"),
        )

    fig.update_layout(
        height=460,
        margin=dict(l=10, r=10, t=40, b=10),
        hovermode="x unified",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(255,255,255,0.03)",
        font=dict(color="#cccccc"),
        showlegend=True,
        legend=dict(orientation="h", y=-0.12, x=0),
    )
    fig.update_xaxes(title_text=f"Range ({rng_label})", row=2, col=1,
                     gridcolor="rgba(255,255,255,0.1)")
    fig.update_xaxes(gridcolor="rgba(255,255,255,0.1)", row=1, col=1)
    fig.update_yaxes(title_text="Drop (MRAD)", row=1, col=1, secondary_y=False,
                     gridcolor="rgba(255,255,255,0.1)")
    fig.update_yaxes(title_text=("fps" if imperial else "m/s"), row=1, col=1, secondary_y=True,
                     gridcolor="rgba(255,255,255,0.05)")
    fig.update_yaxes(title_text="Windage (MRAD)", row=2, col=1,
                     gridcolor="rgba(255,255,255,0.1)")

    st.plotly_chart(fig, use_container_width=True)


# ---------------------------------------------------------------------------
# Truing UI
# ---------------------------------------------------------------------------

def _render_truing_block(
    muzzle_velocity: float,
    drag_model: str,
    bc_val: float,
    mass_grains: float,
    diameter: float,
    zero_range: float,
    target_range: float,
    temp_c: float,
    pressure: float,
    humidity: float,
    bullet_length_in: float,
    twist_rate_inches: float,
    twist_direction: str,
    sight_height_mm: float,
):
    """
    Back-solve the muzzle velocity from an observed drop at the current
    target range.

    Workflow: set the target distance at the top of the page to match
    where you actually shot, enter the real come-up that hit the target,
    and this computes the "true" MV.
    """
    st.caption(
        f"Using current target range: **{int(target_range)} m**. "
        "Enter the elevation (MRAD) you ACTUALLY dialed or held UP to hit the target. "
        "We'll back-solve the muzzle velocity that matches."
    )

    dial_up_mrad = st.number_input(
        "Actual dialed UP Elevation (MRAD)",
        min_value=0.0, max_value=30.0,
        value=float(st.session_state.get("_truing_dial", 2.50)),
        step=0.05, format="%.2f",
        key="truing_dial_input",
        help=(
            "The actual come-up you used (positive number). "
            "If you had to dial UP an additional amount because the bullet "
            "hit LOW, add that to your original come-up. "
            "If the bullet hit HIGH, subtract."
        ),
    )
    # The solver reports drop_mrad as negative when the bullet is below
    # the line of sight (i.e. you had to dial UP), so the observed drop
    # the back-solver needs is -dial_up.
    obs_drop = -dial_up_mrad
    obs_range = float(target_range)

    if st.button("🔧 Compute True MV", use_container_width=True, key="truing_btn"):
        try:
            result = true_muzzle_velocity(
                observed_drop_mrad=obs_drop,
                observed_range_m=obs_range,
                initial_mv_guess_mps=muzzle_velocity,
                bc_g7=bc_val if drag_model == "G7" else None,
                bc_g1=bc_val if drag_model == "G1" else None,
                mass_grains=mass_grains,
                diameter_inches=diameter,
                zero_range_m=zero_range,
                temperature_c=temp_c,
                pressure_mbar=pressure,
                humidity_pct=humidity,
                bullet_length_in=bullet_length_in,
                twist_rate_inches=twist_rate_inches,
                twist_direction=twist_direction,
                sight_height_mm=sight_height_mm,
            )
        except Exception as exc:
            st.error(f"Truing failed: {exc}")
            return

        delta = result["trued_mv_mps"] - muzzle_velocity
        if result["converged"]:
            st.success(
                f"✅ True MV ≈ **{result['trued_mv_mps']:.1f} m/s**  "
                f"(Δ {delta:+.1f} m/s vs current, "
                f"{result['iterations']} iters, residual {result['residual_mrad']:+.3f} MRAD)"
            )
            st.caption(
                "To apply: copy this value into the Muzzle Velocity field in the Ammo Settings sidebar."
            )
            # Stash dial value for next render so the value sticks
            st.session_state._truing_dial = dial_up_mrad
        else:
            st.warning(
                f"Did not converge. Best guess: {result['trued_mv_mps']:.1f} m/s "
                f"(residual {result['residual_mrad']:+.3f} MRAD). "
                "Check that the observed drop is realistic for this load."
            )
