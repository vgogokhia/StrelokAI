"""
StrelokAI - Ballistic Solution Component
Executes ballistic calculations and renders elevation/windage results and trajectory table.
Version: 1.0.0
"""
import streamlit as st
from ballistics.solver import calculate_solution
from config import DEFAULT_LATITUDE

def render_solution_section(
    muzzle_velocity, drag_model, bc_val, mass_grains, diameter, zero_range, 
    target_range, temp_c, pressure, humidity, altitude, 
    wind_speed, wind_deg, **kwargs
):
    try:
        # Safely extract new variables from **kwargs to bypass Streamlit cached module signatures
        mv_temp_c = kwargs.get('mv_temp_c', 15.0)
        temp_sensitivity = kwargs.get('temp_sensitivity', 0.1)
        
        # Calculate actual muzzle velocity based on powder temperature sensitivity
        # Formula: MV + MV * (Sensitivity% / 100) * (Current Temp - MV Temp)
        temp_diff = temp_c - mv_temp_c
        actual_mv = muzzle_velocity + muzzle_velocity * (temp_sensitivity / 100.0) * temp_diff
        
        # Display the calculated MV offset above the solution if it's different from the base profile
        if abs(temp_diff) > 0.1 and temp_sensitivity > 0:
            st.caption(f"🔥 Adjusted MV: **{actual_mv:.1f} m/s** (Base: {muzzle_velocity}m/s @ {mv_temp_c}°C)")
            
        solution = calculate_solution(
            muzzle_velocity_mps=actual_mv,
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
            latitude_deg=DEFAULT_LATITUDE,
            azimuth_deg=0
        )
        
        # Get point at target
        target_point = solution.at_range(target_range)
        
        if target_point:
            # Calculate clicks (0.1 MRAD per click)
            click_value = 0.1
            elevation_clicks = int(abs(target_point.drop_mrad) / click_value)
            windage_clicks = int(abs(target_point.windage_mrad) / click_value)
            elev_dir = 'UP' if target_point.drop_mrad < 0 else 'DOWN'
            wind_dir = 'L' if target_point.windage_mrad < 0 else 'R'
            
            # Main Solution Display - CLICKS
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
            
            # Compact metrics in expander
            with st.expander("📊 Details", expanded=False):
                data_cols = st.columns(4)
                with data_cols[0]:
                    st.metric("ToF", f"{target_point.time_s:.2f}s")
                with data_cols[1]:
                    st.metric("Velocity", f"{target_point.velocity_mps:.0f} m/s")
                with data_cols[2]:
                    st.metric("Energy", f"{target_point.energy_j:.0f} J")
                with data_cols[3]:
                    st.metric("Mach", f"{target_point.mach:.2f}")
            
            # Trajectory Table
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
