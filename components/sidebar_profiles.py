"""
StrelokAI - Sidebar Profiles Component
Renders rifle/cartridge profile inputs and save/load functionality.
Version: 1.0.0
"""
import streamlit as st
from profiles import (
    RifleProfile, CartridgeProfile, FullProfile,
    save_full_profile, load_full_profile, list_full_profiles
)

def render_sidebar_profiles():
    st.markdown("### 📋 Active Profile")
    
    # Profile save/load (only when logged in)
    if st.session_state.logged_in:
        saved_profiles = list_full_profiles(st.session_state.username)
        
        with st.expander("💾 Save / Load Profile", expanded=False):
            # Load existing profile
            if saved_profiles:
                selected_profile = st.selectbox(
                    "Load profile:",
                    ["-- Select --"] + saved_profiles,
                    key="profile_selector"
                )
                
                if selected_profile != "-- Select --":
                    if st.button("📂 Load", use_container_width=True):
                        loaded = load_full_profile(st.session_state.username, selected_profile)
                        if loaded:
                            # Update session state with loaded profile
                            st.session_state.profile = {
                                "name": loaded.name,
                                "muzzle_velocity": loaded.rifle.muzzle_velocity,
                                "bc_g7": loaded.cartridge.bc_g7,
                                "mass_grains": loaded.cartridge.mass_grains,
                                "diameter": loaded.cartridge.diameter,
                                "zero_range": loaded.rifle.zero_range,
                                "sight_height": loaded.rifle.sight_height,
                                "twist_rate": loaded.rifle.twist_rate,
                            }
                            st.success(f"✅ Loaded '{selected_profile}'")
                            st.rerun()
            else:
                st.caption("No saved profiles yet")
            
            st.divider()
            
            # Save current profile
            save_name = st.text_input("Save as:", st.session_state.profile["name"], key="save_profile_name")
            if st.button("💾 Save Current Profile", use_container_width=True):
                # Create profile objects
                rifle = RifleProfile(
                    name=save_name,
                    muzzle_velocity=st.session_state.profile["muzzle_velocity"],
                    zero_range=st.session_state.profile["zero_range"],
                    sight_height=st.session_state.profile["sight_height"],
                    twist_rate=st.session_state.profile["twist_rate"]
                )
                cartridge = CartridgeProfile(
                    name=save_name,
                    bc_g7=st.session_state.profile["bc_g7"],
                    mass_grains=st.session_state.profile["mass_grains"],
                    diameter=st.session_state.profile["diameter"]
                )
                full_profile = FullProfile(
                    name=save_name,
                    rifle=rifle,
                    cartridge=cartridge
                )
                
                success, message = save_full_profile(st.session_state.username, full_profile)
                if success:
                    st.success(f"✅ Profile '{save_name}' saved!")
                    st.rerun()
                else:
                    st.error(message)
    
    profile_name = st.text_input("Profile Name", st.session_state.profile["name"])
    
    st.markdown("#### Rifle")
    muzzle_velocity = st.number_input(
        "Muzzle Velocity (m/s)", 
        min_value=200.0, max_value=1500.0,
        value=st.session_state.profile["muzzle_velocity"],
        step=1.0
    )
    zero_range = st.number_input(
        "Zero Range (m)",
        min_value=25.0, max_value=500.0,
        value=st.session_state.profile["zero_range"],
        step=25.0
    )
    sight_height = st.number_input(
        "Sight Height (mm)",
        min_value=20.0, max_value=80.0,
        value=st.session_state.profile["sight_height"],
        step=1.0
    )
    twist_rate = st.number_input(
        "Twist Rate (1:X inches)",
        min_value=6.0, max_value=20.0,
        value=st.session_state.profile["twist_rate"],
        step=0.5
    )
    
    st.markdown("#### Bullet")
    bc_g7 = st.number_input(
        "Ballistic Coefficient (G7)",
        min_value=0.100, max_value=0.500,
        value=st.session_state.profile["bc_g7"],
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
    
    # Update profile
    st.session_state.profile.update({
        "name": profile_name,
        "muzzle_velocity": muzzle_velocity,
        "bc_g7": bc_g7,
        "mass_grains": mass_grains,
        "diameter": diameter,
        "zero_range": zero_range,
        "sight_height": sight_height,
        "twist_rate": twist_rate,
    })
