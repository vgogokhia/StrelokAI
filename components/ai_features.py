"""
StrelokAI - AI Features Component
Scope recognition file uploader and supported scopes list.
Version: 1.0.0
"""
import streamlit as st
from ai.scope_recognition import identify_scope, list_supported_scopes

def render_ai_features():
    st.markdown("### 🤖 AI Features")
    
    ai_cols = st.columns(2)
    
    with ai_cols[0]:
        st.markdown("#### 📷 Scope Recognition")
        uploaded_file = st.file_uploader("Upload scope photo", type=["jpg", "jpeg", "png"])
        
        if uploaded_file:
            scope_info = identify_scope(image_bytes=uploaded_file.getvalue())
            if scope_info:
                st.success(f"Identified: **{scope_info.manufacturer} {scope_info.model}**")
                st.write(f"- Click Value: {scope_info.click_value_mrad} MRAD")
                st.write(f"- Max Elevation: {scope_info.max_elevation_mrad} MRAD")
                st.write(f"- Reticles: {', '.join(scope_info.reticle_options)}")
    
    with ai_cols[1]:
        st.markdown("#### 🔭 Supported Scopes")
        scopes = list_supported_scopes()
        for scope in scopes[:5]:
            st.write(f"✓ {scope}")
        if len(scopes) > 5:
            st.caption(f"...and {len(scopes) - 5} more")
