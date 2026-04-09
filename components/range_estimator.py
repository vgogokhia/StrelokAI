"""
StrelokAI - Mildot Range Estimator
Estimates range from a known target dimension and angular size in mils.
Version: 1.0.0
"""
import streamlit as st


def render_range_estimator():
    st.markdown("### 📏 Mildot Rangefinder")
    st.caption("Estimate range from a known target dimension.")

    col1, col2 = st.columns(2)
    with col1:
        height_cm = st.number_input(
            "Target size (cm)", min_value=1.0, max_value=500.0,
            value=45.0, step=1.0,
            help="Known dimension of the target (e.g. 45 cm for a human torso).",
        )
    with col2:
        mils = st.number_input(
            "Observed size (mils)", min_value=0.1, max_value=50.0,
            value=1.0, step=0.1,
            format="%.1f",
            help="Angular size through the reticle in mils (MRAD).",
        )

    if mils > 0:
        range_m = (height_cm * 10.0) / mils  # cm*10 / mils → meters
        st.markdown(f"### Estimated range: **{range_m:.0f} m**")

        if st.button("🎯 Use this range", use_container_width=True):
            st.session_state.target_range = int(round(range_m))
            recents = [r for r in st.session_state.get("recent_ranges", []) if r != int(round(range_m))]
            recents.insert(0, int(round(range_m)))
            st.session_state.recent_ranges = recents[:5]
            st.success(f"Set target range to {int(round(range_m))} m")
            st.rerun()

    with st.expander("Common target sizes"):
        st.markdown("""
- **Human torso**: ~45 cm
- **Human head**: ~18 cm
- **Deer (chest)**: ~50 cm
- **IPSC steel plate**: ~30 × 45 cm
- **12" steel gong**: ~30 cm
        """)
