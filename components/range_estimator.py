"""
StrelokAI - Mildot Range Estimator
Estimates range from a known target dimension and angular size.
Version: 1.1.0 - unit-aware (cm/in, m/yd), MOA input supported
"""
import streamlit as st

from core.units import is_imperial, fmt_range, angular_unit, MRAD_TO_MOA


def render_range_estimator():
    st.markdown("### 📏 Reticle Rangefinder")
    st.caption("Estimate range from a known target dimension and its size in your reticle.")

    imp = is_imperial()
    ang = angular_unit()
    size_unit = "in" if imp else "cm"

    col1, col2 = st.columns(2)
    with col1:
        size = st.number_input(
            f"Target size ({size_unit})", min_value=0.5, max_value=500.0,
            value=18.0 if imp else 45.0, step=1.0,
            help="Known dimension of the target (e.g. ~45 cm / 18 in for a human torso).",
        )
    with col2:
        observed = st.number_input(
            f"Observed size ({ang})", min_value=0.05, max_value=100.0,
            value=1.0, step=0.1, format="%.2f",
            help="Angular size of the target as read through the reticle.",
        )

    size_m = size * 0.0254 if imp else size / 100.0
    observed_mrad = observed / MRAD_TO_MOA if ang == "MOA" else observed
    if observed_mrad > 0:
        range_m = size_m * 1000.0 / observed_mrad
        st.markdown(f"### Estimated range: **{fmt_range(range_m)}**")

        if st.button("🎯 Use this range in Calculator", width="stretch"):
            r = int(round(range_m))
            st.session_state.target_range = max(50, min(2000, r))
            recents = [x for x in st.session_state.get("recent_ranges", []) if x != r]
            recents.insert(0, r)
            st.session_state.recent_ranges = recents[:5]
            st.toast(f"Target range set to {fmt_range(range_m)}", icon="🎯")
            st.rerun()

    with st.expander("Common target sizes"):
        st.markdown("""
- **Human torso** (shoulders): ~45 cm / 18 in
- **Human head**: ~18 cm / 7 in
- **Deer chest** (brisket to back): ~45–50 cm / 18–20 in
- **IPSC steel**: 30 × 45 cm / 12 × 18 in
- **12" gong**: 30 cm
        """)
