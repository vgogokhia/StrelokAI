"""
StrelokAI - Sidebar Profiles Component
Renders rifle/cartridge profile inputs and save/load functionality.
Version: 2.0.0
"""
import streamlit as st
from profiles import (
    RifleProfile, CartridgeProfile, FullProfile,
    save_full_profile, load_full_profile, list_full_profiles
)

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
                if selected_rifle != "-- Select --":
                    if st.button("📂 Load Rifle", use_container_width=True):
                        loaded = load_rifle_profile(st.session_state.username, selected_rifle)
                        if loaded:
                            st.session_state.profile.update({
                                "muzzle_velocity": loaded.muzzle_velocity,
                                "zero_range": loaded.zero_range,
                                "sight_height": loaded.sight_height,
                                "twist_rate": loaded.twist_rate,
                            })
                            st.success(f"Loaded '{selected_rifle}'")
                            st.rerun()
            
            st.markdown("**Save Rifle Profile**")
            save_rifle_name = st.text_input("Name:", key="save_rifle_name", placeholder="e.g. Rem700 308Win")
            if st.button("💾 Save Rifle", use_container_width=True):
                if save_rifle_name:
                    new_rifle = RifleProfile(
                        name=save_rifle_name,
                        muzzle_velocity=st.session_state.profile["muzzle_velocity"],
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
        muzzle_velocity = st.number_input(
            "Muzzle Velocity (m/s)", 
            min_value=200.0, max_value=1500.0, value=st.session_state.profile["muzzle_velocity"], step=1.0
        )
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
            min_value=6.0, max_value=20.0, value=st.session_state.profile["twist_rate"], step=0.5
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
                if selected_ammo != "-- Select --":
                    if st.button("📂 Load Ammo", use_container_width=True):
                        loaded = load_cartridge_profile(st.session_state.username, selected_ammo)
                        if loaded:
                            st.session_state.profile.update({
                                "drag_model": loaded.drag_model,
                                "bc_g7": loaded.bc_g7,
                                "mass_grains": loaded.mass_grains,
                                "diameter": loaded.diameter,
                            })
                            # Legacy support for profiles saved before G1/G7 update
                            if hasattr(loaded, 'bc_g1') and loaded.bc_g1 is not None:
                                st.session_state.profile["bc_g1"] = loaded.bc_g1
                            st.success(f"Loaded '{selected_ammo}'")
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
                        drag_model=model,
                        bc_g7=bc_val if model == "G7" else 0.0,  
                        bc_g1=bc_val if model == "G1" else None,
                        mass_grains=st.session_state.profile["mass_grains"],
                        diameter=st.session_state.profile["diameter"]
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
    
    # Update profile tracking
    st.session_state.profile.update({
        "muzzle_velocity": muzzle_velocity,
        "drag_model": drag_model,
        "bc_g7": bc_val,  # Unifying BC value under one key for ease of use in ballistics, with drag_model indicating its type
        "mass_grains": mass_grains,
        "diameter": diameter,
        "zero_range": zero_range,
        "sight_height": sight_height,
        "twist_rate": twist_rate,
    })
