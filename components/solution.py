"""
StrelokAI - Ballistic Solution Component
Renders the firing solution for the current session state.
Version: 2.0.0 - shared cached solver, MRAD/MOA + click-value aware, unit-aware
"""
import streamlit as st

from ballistics.truing import true_muzzle_velocity
from core.solve import solve_current, CurrentInputs
from core.units import (
    fmt_velocity, fmt_energy, fmt_range, is_imperial, range_label,
    angular_unit, fmt_angular, clicks_for, click_value_mrad, fmt_drop_linear,
    velocity_label, input_velocity_from_mps,
)


def render_solution_section():
    try:
        inputs, solution = solve_current()
    except Exception as e:
        st.error(f"Calculation error: {e}")
        st.exception(e)
        return

    temp_diff = inputs.temp_c - inputs.mv_temp_c
    if abs(inputs.muzzle_velocity - inputs.base_mv) > 0.05:
        st.caption(
            f"🔥 Temperature-adjusted MV: **{fmt_velocity(inputs.muzzle_velocity, 1)}** "
            f"(base {fmt_velocity(inputs.base_mv, 0)} at {inputs.mv_temp_c:.0f}°C, "
            f"Δ {temp_diff:+.0f}°C)"
        )

    target_point = solution.at_range(inputs.target_range)
    if target_point is None:
        st.warning("No trajectory point at the target range.")
        return

    elevation_clicks = clicks_for(target_point.drop_mrad)
    windage_clicks = clicks_for(target_point.windage_mrad)
    # drop_mrad / windage_mrad are IMPACT offsets; the correction is the opposite.
    elev_dir = "UP" if target_point.drop_mrad < 0 else "DOWN"
    wind_dial = "RIGHT" if target_point.windage_mrad < 0 else "LEFT"
    impact_side = "left" if target_point.windage_mrad < 0 else "right"
    click_label = st.session_state.get("click_value", "0.1 MRAD")
    elev_txt = fmt_angular(target_point.drop_mrad).replace("-", "")
    wind_txt = fmt_angular(target_point.windage_mrad).replace("-", "")

    st.markdown(f"""
    <div class="main-solution">
        <div class="elevation-display">{elevation_clicks} {elev_dir}</div>
        <div style="font-size: 15px; color: #888; letter-spacing:1px;">
            ELEVATION · dial {elev_dir} {elev_txt} · {click_label} clicks
        </div>
        <div style="margin-top: 10px;"></div>
        <div class="windage-display">{windage_clicks} {wind_dial[0]}</div>
        <div style="font-size: 13px; color: #666; letter-spacing:1px;">
            WINDAGE · dial {wind_dial} {wind_txt} (impact {impact_side})
        </div>
        <div style="font-size: 12px; color: #555; margin-top: 8px;">
            {fmt_range(inputs.target_range)} · bullet impacts {fmt_drop_linear(abs(target_point.drop_m))}
            {'low' if target_point.drop_m < 0 else 'high'} ·
            {fmt_drop_linear(abs(target_point.windage_m))} {impact_side}
        </div>
    </div>
    """, unsafe_allow_html=True)

    if target_point.mach < 1.2:
        st.warning(
            f"⚠️ Bullet is transonic/subsonic at target (Mach {target_point.mach:.2f}). "
            "Expect reduced accuracy of any calculator here."
        )
    if solution.stability_factor and solution.stability_factor < 1.3:
        st.warning(
            f"⚠️ Marginal gyroscopic stability (SG {solution.stability_factor:.2f}). "
            "Check twist rate and bullet length."
        )

    with st.expander("📈 Trajectory Graph", expanded=False):
        _render_trajectory_graph(solution, inputs.target_range)

    with st.expander("🎯 True MV (match observed drop)", expanded=False):
        _render_truing_block(inputs)

    with st.expander("📊 Details", expanded=False):
        data_cols = st.columns(4)
        data_cols[0].metric("ToF", f"{target_point.time_s:.2f} s")
        data_cols[1].metric("Velocity", fmt_velocity(target_point.velocity_mps))
        data_cols[2].metric("Energy", fmt_energy(target_point.energy_j))
        data_cols[3].metric("Mach", f"{target_point.mach:.2f}")
        spin_mrad = solution.spin_drift_m * 1000 / inputs.target_range if inputs.target_range else 0.0
        st.caption(
            f"SG={solution.stability_factor:.2f}  ·  "
            f"Aero jump {fmt_angular(solution.aero_jump_mrad, 3, signed=True)}  ·  "
            f"Spin drift {fmt_angular(spin_mrad, 2, signed=True)}  ·  "
            f"Coriolis H {solution.coriolis_horizontal_m*100:+.1f} cm / "
            f"V {solution.coriolis_vertical_m*100:+.1f} cm  ·  "
            f"Wind relative {inputs.wind_deg_relative:.0f}°"
        )


# ---------------------------------------------------------------------------
# Trajectory graph
# ---------------------------------------------------------------------------

def _render_trajectory_graph(solution, target_range: float):
    try:
        import plotly.graph_objects as go
        from plotly.subplots import make_subplots
    except ImportError:
        st.info("Install plotly to see trajectory graphs (pip install plotly).")
        return

    imperial = is_imperial()
    rng_scale = 1.09361 if imperial else 1.0
    rng_label = range_label()
    ang = angular_unit()
    from core.units import to_angular

    ranges = [pt.range_m * rng_scale for pt in solution.trajectory]
    drops = [to_angular(pt.drop_mrad) for pt in solution.trajectory]
    winds = [to_angular(pt.windage_mrad) for pt in solution.trajectory]
    velocities = [input_velocity_from_mps(pt.velocity_mps) for pt in solution.trajectory]

    fig = make_subplots(
        rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.08,
        subplot_titles=(f"Drop ({ang}) & Velocity", f"Windage ({ang})"),
        specs=[[{"secondary_y": True}], [{}]],
    )
    fig.add_trace(go.Scatter(
        x=ranges, y=drops, name=f"Drop ({ang})", line=dict(color="#ff4444", width=2),
        hovertemplate="%{x:.0f} " + rng_label + "<br>%{y:.2f} " + ang + "<extra></extra>",
    ), row=1, col=1, secondary_y=False)
    fig.add_trace(go.Scatter(
        x=ranges, y=velocities, name="Velocity", line=dict(color="#4488ff", width=1.5, dash="dot"),
        hovertemplate="%{x:.0f} " + rng_label + "<br>%{y:.0f} " + velocity_label() + "<extra></extra>",
    ), row=1, col=1, secondary_y=True)
    fig.add_trace(go.Scatter(
        x=ranges, y=winds, name="Windage", line=dict(color="#44dd88", width=2),
        hovertemplate="%{x:.0f} " + rng_label + "<br>%{y:.2f} " + ang + "<extra></extra>",
    ), row=2, col=1)

    target_pt = solution.at_range(target_range)
    if target_pt is not None:
        tr = target_range * rng_scale
        fig.add_vline(x=tr, line_dash="dash", line_color="#ffaa00", row="all")
        fig.add_annotation(
            x=tr, y=to_angular(target_pt.drop_mrad), text=f"Target {int(tr)}",
            showarrow=True, arrowhead=2, row=1, col=1, font=dict(color="#ffaa00"),
        )

    fig.update_layout(
        height=460, margin=dict(l=10, r=10, t=40, b=10), hovermode="x unified",
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(255,255,255,0.03)",
        font=dict(color="#cccccc"), showlegend=True,
        legend=dict(orientation="h", y=-0.12, x=0),
    )
    grid = "rgba(255,255,255,0.1)"
    fig.update_xaxes(title_text=f"Range ({rng_label})", row=2, col=1, gridcolor=grid)
    fig.update_xaxes(gridcolor=grid, row=1, col=1)
    fig.update_yaxes(title_text=f"Drop ({ang})", row=1, col=1, secondary_y=False, gridcolor=grid)
    fig.update_yaxes(title_text=velocity_label(), row=1, col=1, secondary_y=True,
                     gridcolor="rgba(255,255,255,0.05)")
    fig.update_yaxes(title_text=f"Windage ({ang})", row=2, col=1, gridcolor=grid)
    st.plotly_chart(fig, width="stretch")


# ---------------------------------------------------------------------------
# Truing UI
# ---------------------------------------------------------------------------

def _render_truing_block(inputs: CurrentInputs):
    """Back-solve the muzzle velocity from an observed come-up at the target range."""
    ang = angular_unit()
    from core.units import MRAD_TO_MOA
    st.caption(
        f"Using current target range **{fmt_range(inputs.target_range)}**. "
        f"Enter the elevation ({ang}) you ACTUALLY dialed to hit the target; "
        "the muzzle velocity that reproduces it is back-solved."
    )

    dial_up = st.number_input(
        f"Actual dialed UP elevation ({ang})",
        min_value=0.0, max_value=100.0 if ang == "MOA" else 30.0,
        value=float(st.session_state.get("_truing_dial", 2.50)),
        step=0.25 if ang == "MOA" else 0.05, format="%.2f",
        key="truing_dial_input",
        help="If the bullet hit LOW, add the extra you had to dial; if HIGH, subtract.",
    )
    dial_up_mrad = dial_up / MRAD_TO_MOA if ang == "MOA" else dial_up

    if st.button("🔧 Compute True MV", width="stretch", key="truing_btn"):
        try:
            result = true_muzzle_velocity(
                observed_drop_mrad=-dial_up_mrad,
                observed_range_m=float(inputs.target_range),
                initial_mv_guess_mps=inputs.muzzle_velocity,
                bc_g7=inputs.bc_val if inputs.drag_model == "G7" else None,
                bc_g1=inputs.bc_val if inputs.drag_model == "G1" else None,
                mass_grains=inputs.mass_grains,
                diameter_inches=inputs.diameter,
                zero_range_m=inputs.zero_range,
                temperature_c=inputs.temp_c,
                pressure_mbar=inputs.pressure,
                humidity_pct=inputs.humidity,
                bullet_length_in=inputs.bullet_length_in,
                twist_rate_inches=inputs.twist_rate_inches,
                twist_direction=inputs.twist_direction,
                sight_height_mm=inputs.sight_height_mm,
            )
        except Exception as exc:
            st.error(f"Truing failed: {exc}")
            return
        st.session_state._truing_dial = dial_up
        st.session_state._truing_result = result

    result = st.session_state.get("_truing_result")
    if not result:
        return

    trued = result["trued_mv_mps"]
    delta = trued - inputs.muzzle_velocity
    if result["converged"]:
        st.success(
            f"✅ True MV ≈ **{fmt_velocity(trued, 1)}**  "
            f"(Δ {input_velocity_from_mps(delta):+.1f} {velocity_label()} vs current, "
            f"residual {result['residual_mrad']:+.3f} MRAD)"
        )
        if st.button("✔ Apply to ammo profile", width="stretch", key="truing_apply"):
            # The profile stores the base MV at mv_temp_c; undo the temperature
            # compensation so the trued value round-trips through apply_mv_curve.
            comp = inputs.muzzle_velocity / inputs.base_mv if inputs.base_mv else 1.0
            st.session_state.profile["muzzle_velocity"] = round(trued / comp, 1)
            st.session_state._truing_result = None
            st.toast("Muzzle velocity updated in the ammo profile", icon="✅")
            st.rerun()
    else:
        st.warning(
            f"Did not converge. Best guess: {fmt_velocity(trued, 1)} "
            f"(residual {result['residual_mrad']:+.3f} MRAD). "
            "Check that the observed drop is realistic for this load."
        )
