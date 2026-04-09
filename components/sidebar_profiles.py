"""
StrelokAI - Sidebar Profiles Component
Renders rifle/cartridge profile inputs and save/load functionality.
Version: 2.1.0
"""
import streamlit as st
from profiles import (
    RifleProfile, CartridgeProfile, FullProfile,
    save_full_profile, load_full_profile, list_full_profiles
)
from ballistics.bullet_library import load_all as load_bullet_library

def render_sidebar_profiles():
    st.markdown("### 📋 Active Profile")
    
    # ------------------ RIFLE PROFILES ------------------
    with st.expander("🔫 Rifle Settings", expanded=True):
        if st.session_state.logged_in:
            from profiles import list_rifle_profiles, load_rifle_profile, save_rifle_profile, RifleProfile
            
            saved_rifles = list_rifle_profiles(st.session_state.username)
            if saved_rifles:
                st.markdown("**Load Rifle Profile**")
                selected_rifle = st.selectbox(
                    "Select rifle:",
                    ["-- Select --"] + saved_rifles,
                    key="rifle_selector",
                    label_visibility="collapsed"
                )
                # Auto-load on selection change. Track the last loaded name
                # so re-renders don't keep reloading (and clobbering edits).
                if selected_rifle != "-- Select --" and \
                        st.session_state.get("_last_loaded_rifle") != selected_rifle:
                    loaded = load_rifle_profile(st.session_state.username, selected_rifle)
                    if loaded:
                        st.session_state.profile.update({
                            "zero_range": loaded.zero_range,
                            "sight_height": loaded.sight_height,
                            "twist_rate": loaded.twist_rate,
                            "twist_direction": getattr(loaded, "twist_direction", "right"),
                        })
                        st.session_state._last_loaded_rifle = selected_rifle
                        st.rerun()
            
            st.markdown("**Save Rifle Profile**")
            save_rifle_name = st.text_input("Name:", key="save_rifle_name", placeholder="e.g. Rem700 308Win")
            if st.button("💾 Save Rifle", use_container_width=True):
                if save_rifle_name:
                    new_rifle = RifleProfile(
                        name=save_rifle_name,
                        zero_range=st.session_state.profile["zero_range"],
                        sight_height=st.session_state.profile["sight_height"],
                        twist_rate=st.session_state.profile["twist_rate"]
                    )
                    success, msg = save_rifle_profile(st.session_state.username, new_rifle)
                    if success:
                        st.success("Saved!")
                        st.rerun()
                    else:
                        st.error(msg)
                else:
                    st.error("Enter a name")
        
        st.divider()
        zero_range = st.number_input(
            "Zero Range (m)",
            min_value=25.0, max_value=500.0, value=st.session_state.profile["zero_range"], step=25.0
        )
        sight_height = st.number_input(
            "Sight Height (mm)",
            min_value=20.0, max_value=80.0, value=st.session_state.profile["sight_height"], step=1.0
        )
        twist_rate = st.number_input(
            "Twist Rate (1:X inches)",
            min_value=6.0, max_value=20.0, value=st.session_state.profile["twist_rate"], step=0.25
        )
        twist_direction = st.radio(
            "Twist Direction",
            options=["right", "left"],
            index=0 if st.session_state.profile.get("twist_direction", "right") == "right" else 1,
            horizontal=True,
            help="Right twist (most rifles) drifts bullets right; left twist drifts left."
        )


    # ------------------ AMMO PROFILES ------------------
    with st.expander("🎯 Ammo Settings", expanded=True):
        if st.session_state.logged_in:
            from profiles import list_cartridge_profiles, load_cartridge_profile, save_cartridge_profile, CartridgeProfile
            
            saved_ammo = list_cartridge_profiles(st.session_state.username)
            if saved_ammo:
                st.markdown("**Load Ammo Profile**")
                selected_ammo = st.selectbox(
                    "Select ammo:",
                    ["-- Select --"] + saved_ammo,
                    key="ammo_selector",
                    label_visibility="collapsed"
                )
                if selected_ammo != "-- Select --" and \
                        st.session_state.get("_last_loaded_ammo") != selected_ammo:
                    loaded = load_cartridge_profile(st.session_state.username, selected_ammo)
                    if loaded:
                        st.session_state.profile.update({
                            "drag_model": loaded.drag_model,
                            "bc_g7": loaded.bc_g7,
                            "mass_grains": loaded.mass_grains,
                            "diameter": loaded.diameter,
                            "muzzle_velocity": loaded.muzzle_velocity,
                            "mv_temp_c": getattr(loaded, "mv_temp_c", 15.0),
                            "temp_sensitivity": getattr(loaded, "temp_sensitivity", 0.1),
                            "bullet_length_in": getattr(loaded, "bullet_length_in", 1.0),
                        })
                        # Legacy support for profiles saved before G1/G7 update
                        if hasattr(loaded, 'bc_g1') and loaded.bc_g1 is not None:
                            st.session_state.profile["bc_g1"] = loaded.bc_g1
                        st.session_state._last_loaded_ammo = selected_ammo
                        st.rerun()
            
            st.markdown("**Save Ammo Profile**")
            save_ammo_name = st.text_input("Name:", key="save_ammo_name", placeholder="e.g. Hornady 175gr")
            if st.button("💾 Save Ammo", use_container_width=True):
                if save_ammo_name:
                    # In current state, bc_g7 key maps to whatever BC input is currently active. 
                    # We might want to separate them later, but for now we'll just save it based on drag_model
                    bc_val = st.session_state.profile.get("bc_g7", 0.0)
                    model = st.session_state.profile.get("drag_model", "G7")
                    
                    new_ammo = CartridgeProfile(
                        name=save_ammo_name,
                        muzzle_velocity=st.session_state.profile["muzzle_velocity"],
                        drag_model=model,
                        bc_g7=bc_val if model == "G7" else 0.0,  
                        bc_g1=bc_val if model == "G1" else None,
                        mass_grains=st.session_state.profile["mass_grains"],
                        diameter=st.session_state.profile["diameter"],
                        mv_temp_c=st.session_state.profile.get("mv_temp_c", 15.0),
                        temp_sensitivity=st.session_state.profile.get("temp_sensitivity", 0.1)
                    )
                    success, msg = save_cartridge_profile(st.session_state.username, new_ammo)
                    if success:
                        st.success("Saved!")
                        st.rerun()
                    else:
                        st.error(msg)
                else:
                    st.error("Enter a name")
        
        st.divider()

        # Bullet library preset picker (read-only; populates the fields below)
        library = load_bullet_library()
        if library:
            preset_labels = ["-- Load Preset --"] + [b.label for b in library]
            picked = st.selectbox(
                "📚 Bullet Library",
                preset_labels,
                key="bullet_preset_selector",
                help="Load published bullet specs. You can still edit anything below and save as your own profile.",
            )
            if picked != "-- Load Preset --":
                if st.button("⬇ Apply Preset", use_container_width=True, key="apply_bullet_preset"):
                    preset = next((b for b in library if b.label == picked), None)
                    if preset is not None:
                        st.session_state.profile.update({
                            "drag_model": "G7",
                            "bc_g7": preset.bc_g7,
                            "mass_grains": preset.mass_grains,
                            "diameter": preset.diameter_in,
                            "bullet_length_in": preset.length_in,
                            "muzzle_velocity": preset.default_mv_mps,
                            "twist_rate": preset.default_twist_in,
                        })
                        st.success(f"Applied: {preset.bullet}")
                        st.rerun()

        drag_model = st.radio(
            "Drag Model",
            options=["G1", "G7"],
            index=0 if st.session_state.profile.get("drag_model") == "G1" else 1,
            horizontal=True
        )
        
        bc_val = st.number_input(
            f"Ballistic Coefficient ({drag_model})",
            min_value=0.100, max_value=1.500,
            value=st.session_state.profile["bc_g7"],  # Reusing this key for the UI input temporarily, handled in state update below
            step=0.001,
            format="%.3f"
        )
        mass_grains = st.number_input(
            "Bullet Weight (grains)",
            min_value=50.0, max_value=400.0,
            value=st.session_state.profile["mass_grains"],
            step=1.0
        )
        diameter = st.number_input(
            "Bullet Diameter (inches)",
            min_value=0.172, max_value=0.510,
            value=st.session_state.profile["diameter"],
            step=0.001,
            format="%.3f"
        )
        bullet_length_in = st.number_input(
            "Bullet Length (inches)",
            min_value=0.300, max_value=3.000,
            value=st.session_state.profile.get("bullet_length_in", 1.240),
            step=0.001,
            format="%.3f",
            help="Used for Miller gyroscopic stability calculation."
        )

        st.divider()
        st.markdown("**Velocity & Temperature Settings**")
        col1, col2, col3 = st.columns(3)
        with col1:
            muzzle_velocity = st.number_input(
                "Muzzle Velocity (m/s)", 
                min_value=200.0, max_value=1500.0, value=st.session_state.profile["muzzle_velocity"], step=1.0
            )
        with col2:
            mv_temp_c = st.number_input(
                "MV At Temp (°C)", 
                min_value=-50.0, max_value=60.0, value=st.session_state.profile.get("mv_temp_c", 15.0), step=1.0
            )
        with col3:
            temp_sensitivity = st.number_input(
                "Sensitivity (%/°C)", 
                min_value=0.0, max_value=5.0, value=st.session_state.profile.get("temp_sensitivity", 0.1), step=0.05, format="%.2f"
            )
    
    # Update profile tracking
    st.session_state.profile.update({
        "muzzle_velocity": muzzle_velocity,
        "mv_temp_c": mv_temp_c,
        "temp_sensitivity": temp_sensitivity,
        "drag_model": drag_model,
        "bc_g7": bc_val,  # Unifying BC value under one key for ease of use in ballistics, with drag_model indicating its type
        "mass_grains": mass_grains,
        "diameter": diameter,
        "bullet_length_in": bullet_length_in,
        "zero_range": zero_range,
        "sight_height": sight_height,
        "twist_rate": twist_rate,
        "twist_direction": twist_direction,
    })
