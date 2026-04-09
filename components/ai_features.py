"""
StrelokAI - AI Features Component
Scope recognition file uploader and supported scopes list.
Version: 1.0.0
"""
import streamlit as st
from ai.scope_recognition import identify_scope, list_supported_scopes
from config import GEMINI_API_KEY

def render_ai_features():
    st.markdown("### 🤖 AI Features")
    
    ai_cols = st.columns(2)
    
    with ai_cols[0]:
        st.markdown("#### 📷 Scope Recognition")
        uploaded_file = st.file_uploader("Upload scope photo", type=["jpg", "jpeg", "png"])
        
        if uploaded_file:
            try:
                with st.spinner("Analyzing scope image with Gemini..."):
                    scope_info = identify_scope(
                        image_bytes=uploaded_file.getvalue(),
                        api_key=GEMINI_API_KEY,
                    )
            except Exception as e:
                st.error(f"Scope recognition failed: {e}")
                scope_info = None

            if scope_info and scope_info.manufacturer not in ("Demo", "Unknown"):
                st.success(f"Identified: **{scope_info.manufacturer} {scope_info.model}**")
                st.write(f"- Click Value: {scope_info.click_value_mrad} MRAD")
                st.write(f"- Max Elevation: {scope_info.max_elevation_mrad} MRAD")
                st.write(f"- Reticles: {', '.join(scope_info.reticle_options)}")
                st.caption(f"Confidence: {scope_info.confidence*100:.0f}%")
            elif scope_info and scope_info.manufacturer == "Unknown":
                st.warning(
                    "Gemini couldn't read a brand/model off this image. "
                    "Try a closer shot of the turret or magnification ring where the markings are legible."
                )
    
    with ai_cols[1]:
        st.markdown("#### 🔭 Supported Scopes")
        scopes = list_supported_scopes()
        for scope in scopes[:5]:
            st.write(f"✓ {scope}")
        if len(scopes) > 5:
            st.caption(f"...and {len(scopes) - 5} more")
