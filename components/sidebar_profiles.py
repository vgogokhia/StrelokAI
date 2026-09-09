"""
ballistics.ge - Sidebar Profiles Component
Renders rifle/cartridge profile inputs and save/load functionality.
Version: 2.2.0 - unit-aware rifle/ammo inputs, Firestore failures no longer crash
"""
import streamlit as st
from profiles import (
    RifleProfile, CartridgeProfile, FullProfile,
    save_full_profile, load_full_profile, list_full_profiles
)
from ballistics.bullet_library import load_all as load_bullet_library
from ballistics.calibers import (
    CHAMBERINGS, LIBRARY_CALIBER_TO_CHAMBERING, is_compatible, chambering_diameter,
)
from core.units import (
    is_imperial, range_label, velocity_label, temp_label, sight_height_label,
    input_range_from_m, input_range_to_m,
    input_sight_height_from_mm, input_sight_height_to_mm,
    input_velocity_from_mps, input_velocity_to_mps,
    input_temp_from_c, input_temp_to_c, roundtrip,
    pressure_label, input_pressure_from_mbar, input_pressure_to_mbar,
)


def _firestore_call(fn, *args, default=None):
    """Run a Firestore-backed call; on failure show a compact error instead of crashing."""
    try:
        return fn(*args)
    except Exception as exc:
        st.warning(f"Profile storage unavailable: {exc}")
        return default

def render_sidebar_profiles():
    st.markdown("### 📋 Active Profile")
    
    # ------------------ RIFLE PROFILES ------------------
    with st.expander("🔫 Rifle Settings", expanded=True):
        if st.session_state.logged_in:
            from profiles import list_rifle_profiles, load_rifle_profile, save_rifle_profile, RifleProfile
            
            saved_rifles = _firestore_call(list_rifle_profiles, st.session_state.username, default=[])
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
                    loaded = _firestore_call(load_rifle_profile, st.session_state.username, selected_rifle)
                    if loaded:
                        st.session_state.profile.update({
                            "zero_range": loaded.zero_range,
                            "sight_height": loaded.sight_height,
                            "twist_rate": loaded.twist_rate,
                            "twist_direction": getattr(loaded, "twist_direction", "right"),
                            "chambering": getattr(loaded, "chambering", "") or "",
                            "zero_temp_c": getattr(loaded, "zero_temp_c", None),
                            "zero_pressure_mbar": getattr(loaded, "zero_pressure_mbar", None),
                            "zero_humidity_pct": getattr(loaded, "zero_humidity_pct", None),
                            "zero_offset_v_cm": getattr(loaded, "zero_offset_v_cm", 0.0) or 0.0,
                            "zero_offset_h_cm": getattr(loaded, "zero_offset_h_cm", 0.0) or 0.0,
                        })
                        st.session_state._last_loaded_rifle = selected_rifle
                        st.session_state.save_rifle_name = selected_rifle
                        st.rerun()
            
            st.markdown("**Save Rifle Profile**")
            save_rifle_name = st.text_input("Name:", key="save_rifle_name", placeholder="e.g. Rem700 308Win")
            if st.button("💾 Save Rifle", width="stretch"):
                if save_rifle_name:
                    new_rifle = RifleProfile(
                        name=save_rifle_name,
                        zero_range=st.session_state.profile["zero_range"],
                        sight_height=st.session_state.profile["sight_height"],
                        twist_rate=st.session_state.profile["twist_rate"],
                        twist_direction=st.session_state.profile.get("twist_direction", "right"),
                        chambering=st.session_state.profile.get("chambering", ""),
                        zero_temp_c=st.session_state.profile.get("zero_temp_c"),
                        zero_pressure_mbar=st.session_state.profile.get("zero_pressure_mbar"),
                        zero_humidity_pct=st.session_state.profile.get("zero_humidity_pct"),
                        zero_offset_v_cm=st.session_state.profile.get("zero_offset_v_cm", 0.0) or 0.0,
                        zero_offset_h_cm=st.session_state.profile.get("zero_offset_h_cm", 0.0) or 0.0,
                    )
                    success, msg = save_rifle_profile(st.session_state.username, new_rifle)
                    if success:
                        st.toast(f"✅ Rifle '{save_rifle_name}' saved", icon="✅")
                        st.success(f"✅ Rifle '{save_rifle_name}' saved")
                        st.session_state._last_loaded_rifle = save_rifle_name
                    else:
                        st.error(msg)
                else:
                    st.error("Enter a name")
        
        st.divider()
        imp = is_imperial()
        zr_seed = float(round(input_range_from_m(st.session_state.profile["zero_range"]), 0))
        zr_disp = st.number_input(
            f"Zero Range ({range_label()})",
            min_value=25.0, max_value=550.0, value=zr_seed, step=25.0,
        )
        zero_range = roundtrip(st.session_state.profile["zero_range"], zr_seed, zr_disp, input_range_to_m)
        sh_seed = float(round(input_sight_height_from_mm(st.session_state.profile["sight_height"]), 2))
        sh_disp = st.number_input(
            f"Sight Height ({sight_height_label()})",
            min_value=0.5 if imp else 15.0, max_value=4.0 if imp else 100.0,
            value=sh_seed, step=0.05 if imp else 1.0, format="%.2f" if imp else "%.0f",
            help="Centre of scope tube to centre of bore.",
        )
        sight_height = roundtrip(st.session_state.profile["sight_height"], sh_seed, sh_disp, input_sight_height_to_mm)
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
        chamber_names = list(CHAMBERINGS.keys())
        cur_ch = st.session_state.profile.get("chambering") or "Other"
        chambering = st.selectbox(
            "Chambering", chamber_names,
            index=chamber_names.index(cur_ch) if cur_ch in chamber_names else len(chamber_names) - 1,
            help="Used to show only ammo and bullets that fit this rifle.",
        )
        # Written immediately so the ammo section below filters on it this run.
        st.session_state.profile["chambering"] = chambering
        _render_advanced_zero(imp)


    # ------------------ AMMO PROFILES ------------------
    with st.expander("🎯 Ammo Settings", expanded=True):
        if st.session_state.logged_in:
            from profiles import list_cartridge_profiles, load_cartridge_profile, save_cartridge_profile, CartridgeProfile
            
            saved_ammo = _firestore_call(list_cartridge_profiles, st.session_state.username, default=[])
            rifle_ch = chambering
            if saved_ammo and chambering_diameter(rifle_ch) is not None:
                # Only ammo that fits the selected rifle. Needs one read per
                # profile; lists are short.
                fitting = []
                for name in saved_ammo:
                    cp = _firestore_call(load_cartridge_profile, st.session_state.username, name)
                    if cp is None or is_compatible(rifle_ch, cp.diameter, getattr(cp, "cartridge", "")):
                        fitting.append(name)
                hidden = len(saved_ammo) - len(fitting)
                saved_ammo = fitting
                if hidden:
                    st.caption(f"{hidden} saved ammo profile(s) hidden: they don't fit a {rifle_ch} rifle.")
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
                    loaded = _firestore_call(load_cartridge_profile, st.session_state.username, selected_ammo)
                    if loaded:
                        # The UI reuses the "bc_g7" session key for whichever BC
                        # is active, regardless of drag_model. Saves zero out the
                        # inactive side, so on load we have to pick whichever
                        # side actually holds the value.
                        active_bc = loaded.bc_g7 if loaded.drag_model == "G7" else (loaded.bc_g1 or 0.0)
                        if active_bc <= 0:
                            active_bc = loaded.bc_g7 or loaded.bc_g1 or 0.100
                        st.session_state.profile.update({
                            "drag_model": loaded.drag_model,
                            "bc_g7": active_bc,
                            "mass_grains": loaded.mass_grains,
                            "diameter": loaded.diameter,
                            "muzzle_velocity": loaded.muzzle_velocity,
                            "mv_temp_c": getattr(loaded, "mv_temp_c", 15.0),
                            "temp_sensitivity": getattr(loaded, "temp_sensitivity", 0.1),
                            "bullet_length_in": getattr(loaded, "bullet_length_in", 1.0),
                            "cartridge": getattr(loaded, "cartridge", "") or "",
                            "bc_segments": getattr(loaded, "bc_segments", None),
                        })
                        st.session_state._last_loaded_ammo = selected_ammo
                        st.session_state.save_ammo_name = selected_ammo
                        st.rerun()
            
            st.markdown("**Save Ammo Profile**")
            save_ammo_name = st.text_input("Name:", key="save_ammo_name", placeholder="e.g. Hornady 175gr")
            if st.button("💾 Save Ammo", width="stretch"):
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
                        bullet_length_in=st.session_state.profile.get("bullet_length_in", 1.0),
                        mv_temp_c=st.session_state.profile.get("mv_temp_c", 15.0),
                        temp_sensitivity=st.session_state.profile.get("temp_sensitivity", 0.1),
                        cartridge=st.session_state.profile.get("cartridge", ""),
                        bc_segments=st.session_state.profile.get("bc_segments"),
                    )
                    success, msg = save_cartridge_profile(st.session_state.username, new_ammo)
                    if success:
                        st.toast(f"✅ Ammo '{save_ammo_name}' saved", icon="✅")
                        st.success(f"✅ Ammo '{save_ammo_name}' saved")
                        st.session_state._last_loaded_ammo = save_ammo_name
                    else:
                        st.error(msg)
                else:
                    st.error("Enter a name")
        
        st.divider()

        # Cartridge of the loaded ammo (drives rifle/ammo compatibility)
        chamber_names = list(CHAMBERINGS.keys())
        cur_cart = st.session_state.profile.get("cartridge") or "Other"
        cartridge = st.selectbox(
            "Cartridge", chamber_names,
            index=chamber_names.index(cur_cart) if cur_cart in chamber_names else len(chamber_names) - 1,
        )
        rifle_ch = chambering
        if not is_compatible(rifle_ch, st.session_state.profile.get("diameter"), cartridge):
            st.warning(f"⚠️ This ammo ({cartridge}) doesn't fit a {rifle_ch} rifle.")

        # Bullet library preset picker (read-only; populates the fields below),
        # filtered to bullets that fit the selected rifle.
        library = load_bullet_library()
        if chambering_diameter(rifle_ch) is not None:
            library = [b for b in library if is_compatible(rifle_ch, b.diameter_in)]
        if library:
            preset_labels = ["-- Load Preset --"] + [b.label for b in library]
            picked = st.selectbox(
                "📚 Bullet Library",
                preset_labels,
                key="bullet_preset_selector",
                help="Published bullet specs that fit the selected rifle. Edit anything below and save as your own profile.",
            )
            if picked != "-- Load Preset --":
                if st.button("⬇ Apply Preset", width="stretch", key="apply_bullet_preset"):
                    preset = next((b for b in library if b.label == picked), None)
                    if preset is not None:
                        use_g7 = preset.bc_g7 is not None
                        st.session_state.profile.update({
                            "drag_model": "G7" if use_g7 else "G1",
                            "bc_g7": preset.bc_g7 if use_g7 else preset.bc_g1,
                            "mass_grains": preset.mass_grains,
                            "diameter": preset.diameter_in,
                            "bullet_length_in": preset.length_in,
                            "muzzle_velocity": preset.default_mv_mps,
                            "twist_rate": preset.default_twist_in,
                            "cartridge": LIBRARY_CALIBER_TO_CHAMBERING.get(preset.caliber, rifle_ch),
                        })
                        st.success(f"Applied: {preset.bullet}")
                        st.rerun()
        else:
            st.caption("No library bullets for this chambering yet — enter the specs manually.")

        drag_model = st.radio(
            "Drag Model",
            options=["G1", "G7"],
            index=0 if st.session_state.profile.get("drag_model") == "G1" else 1,
            horizontal=True
        )
        
        bc_val = st.number_input(
            f"Ballistic Coefficient ({drag_model})",
            min_value=0.050, max_value=1.500,
            value=st.session_state.profile["bc_g7"],  # Reusing this key for the UI input temporarily, handled in state update below
            step=0.001,
            format="%.3f"
        )
        mass_grains = st.number_input(
            "Bullet Weight (grains)",
            min_value=15.0, max_value=800.0,
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

        _render_advanced_bc(drag_model)

        st.divider()
        st.markdown("**Velocity & Temperature Settings**")
        imp = is_imperial()
        col1, col2 = st.columns(2)
        with col1:
            mv_seed = float(round(input_velocity_from_mps(st.session_state.profile["muzzle_velocity"]), 0 if imp else 1))
            mv_disp = st.number_input(
                f"Muzzle Velocity ({velocity_label()})",
                min_value=600.0 if imp else 200.0, max_value=5000.0 if imp else 1500.0,
                value=mv_seed, step=5.0 if imp else 1.0,
            )
            muzzle_velocity = roundtrip(st.session_state.profile["muzzle_velocity"], mv_seed, mv_disp, input_velocity_to_mps)
        with col2:
            mvt_seed = float(round(input_temp_from_c(st.session_state.profile.get("mv_temp_c", 15.0)), 0))
            mvt_disp = st.number_input(
                f"MV measured at ({temp_label()})",
                min_value=-60.0 if imp else -50.0, max_value=140.0 if imp else 60.0,
                value=mvt_seed, step=1.0,
            )
            mv_temp_c = roundtrip(st.session_state.profile.get("mv_temp_c", 15.0), mvt_seed, mvt_disp, input_temp_to_c)
        temp_sensitivity = st.number_input(
            "Powder temp sensitivity (%/°C)",
            min_value=0.0, max_value=5.0, value=st.session_state.profile.get("temp_sensitivity", 0.1),
            step=0.05, format="%.2f",
            help="MV change per °C of powder temperature. ~0.1 %/°C is typical for temp-stable powders; set 0 to disable.",
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
        "chambering": chambering,
        "cartridge": cartridge,
    })


# ---------------------------------------------------------------------------
# Advanced settings
# ---------------------------------------------------------------------------

def _render_advanced_zero(imp: bool):
    """Zeroing conditions + point-of-impact offset at the zero range."""
    prof = st.session_state.profile
    with st.expander("⚙ Advanced zero", expanded=False):
        st.caption(
            "**Zeroed in different conditions** — e.g. zeroed in summer at sea level, "
            "shooting in winter in the mountains. The zero is recomputed under the zeroing "
            "weather, the trajectory under today's."
        )
        differs = st.checkbox(
            "Zero conditions differ from today's", value=prof.get("zero_temp_c") is not None,
            key="adv_zero_differs",
        )
        if differs:
            zt_seed = float(round(input_temp_from_c(prof.get("zero_temp_c") if prof.get("zero_temp_c") is not None else 15.0), 0))
            zt = st.number_input(f"Zero temp ({temp_label()})", -40.0, 130.0 if imp else 55.0, zt_seed, 1.0, key="adv_zero_temp")
            zp_seed = float(round(input_pressure_from_mbar(prof.get("zero_pressure_mbar") or 1013.25), 2))
            zp = st.number_input(f"Zero station pressure ({pressure_label()})",
                                 17.0 if imp else 580.0, 32.5 if imp else 1100.0, zp_seed,
                                 0.01 if imp else 1.0, format="%.2f" if imp else "%.0f", key="adv_zero_press")
            zh = st.number_input("Zero humidity (%)", 0.0, 100.0,
                                 float(prof.get("zero_humidity_pct") if prof.get("zero_humidity_pct") is not None else 50.0),
                                 5.0, key="adv_zero_hum")
            prof["zero_temp_c"] = roundtrip(prof.get("zero_temp_c") or 15.0, zt_seed, zt, input_temp_to_c)
            prof["zero_pressure_mbar"] = roundtrip(prof.get("zero_pressure_mbar") or 1013.25, zp_seed, zp, input_pressure_to_mbar)
            prof["zero_humidity_pct"] = zh
        else:
            prof["zero_temp_c"] = None
            prof["zero_pressure_mbar"] = None
            prof["zero_humidity_pct"] = None

        st.caption(
            "**Zero offset** — where the group actually sits at the zero range "
            "(e.g. 2 cm high, 1 cm right). Leave 0 if it's dead centre."
        )
        unit = "in" if imp else "cm"
        k = 1 / 2.54 if imp else 1.0
        c1, c2 = st.columns(2)
        ov = c1.number_input(f"Vertical ({unit}, + high)", -30.0, 30.0,
                             float(round((prof.get("zero_offset_v_cm") or 0.0) * k, 2)),
                             0.1 if imp else 0.5, key="adv_zero_off_v")
        oh = c2.number_input(f"Horizontal ({unit}, + right)", -30.0, 30.0,
                             float(round((prof.get("zero_offset_h_cm") or 0.0) * k, 2)),
                             0.1 if imp else 0.5, key="adv_zero_off_h")
        prof["zero_offset_v_cm"] = ov / k
        prof["zero_offset_h_cm"] = oh / k


def _render_advanced_bc(drag_model: str):
    """Velocity-banded BC (Berger/Sierra publish 2-3 bands per bullet)."""
    prof = st.session_state.profile
    with st.expander("⚙ Advanced BC (velocity bands)", expanded=False):
        st.caption(
            f"Some makers publish the {drag_model} BC in velocity bands, e.g. Sierra: "
            "0.505 above 2800 fps, 0.496 2800–1800 fps, 0.485 below. Enter them high to low; "
            "the single BC above is ignored while this is on."
        )
        imp = is_imperial()
        use = st.checkbox("Use velocity bands", value=bool(prof.get("bc_segments")), key="adv_bc_use")
        if not use:
            prof["bc_segments"] = None
            return
        existing = list(prof.get("bc_segments") or [])
        vlabel = "fps" if imp else "m/s"
        rows = []
        for i in range(3):
            v_fps, bc = (existing[i] if i < len(existing) else (0.0, 0.0))
            v_disp = v_fps if imp else v_fps * 0.3048
            c1, c2 = st.columns(2)
            v_in = c1.number_input(f"Above ({vlabel})", 0.0, 5000.0 if imp else 1600.0,
                                   float(round(v_disp, 0)), 50.0 if imp else 10.0, key=f"adv_bc_v{i}",
                                   help="Velocity floor of this band; 0 = lowest band.")
            bc_in = c2.number_input("BC", 0.0, 1.5, float(bc), 0.001, format="%.3f", key=f"adv_bc_b{i}")
            if bc_in > 0:
                rows.append([v_in if imp else v_in / 0.3048, bc_in])
        prof["bc_segments"] = sorted(rows, key=lambda r: -r[0]) or None
