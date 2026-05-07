"""
StrelokAI - Theme & CSS Injection
Applies custom CSS themes (Dark, Light, Red/NVG) to the Streamlit UI.
Version: 1.1.0
"""
import streamlit as st


PALETTES: dict[str, dict[str, str]] = {
    "dark": {
        "bg": "#121212",
        "fg": "#E0E0E0",
        "card_bg": "#1E1E1E",
        "card_border_dim": "#333",
        "solution_grad_a": "#1a1a2e",
        "solution_grad_b": "#16213e",
        "solution_border": "#0f3460",
        "elev": "#4CAF50",
        "elev_glow": "rgba(76, 175, 80, 0.45)",
        "wind": "#42A5F5",
        "accent": "#BB86FC",
        "toggle_bg": "#2a2a2a",
        "toggle_border": "#555",
        "toggle_hover_bg": "#3a3a3a",
        "toggle_hover_border": "#4CAF50",
        "toggle_icon": "#d0d0d0",
    },
    "light": {
        "bg": "#F7F7F8",
        "fg": "#1A1A1A",
        "card_bg": "#FFFFFF",
        "card_border_dim": "#D0D7DE",
        "solution_grad_a": "#FFFFFF",
        "solution_grad_b": "#EEF2FF",
        "solution_border": "#C5CAE9",
        "elev": "#2E7D32",
        "elev_glow": "rgba(46, 125, 50, 0.18)",
        "wind": "#1565C0",
        "accent": "#6A1B9A",
        "toggle_bg": "#FFFFFF",
        "toggle_border": "#C8C8C8",
        "toggle_hover_bg": "#F0F0F0",
        "toggle_hover_border": "#2E7D32",
        "toggle_icon": "#333333",
    },
    "red": {
        "bg": "#000000",
        "fg": "#660000",
        "card_bg": "#0a0000",
        "card_border_dim": "#330000",
        "solution_grad_a": "#0a0000",
        "solution_grad_b": "#0a0000",
        "solution_border": "#330000",
        "elev": "#990000",
        "elev_glow": "rgba(153, 0, 0, 0.35)",
        "wind": "#660000",
        "accent": "#660000",
        "toggle_bg": "#0a0000",
        "toggle_border": "#330000",
        "toggle_hover_bg": "#1a0000",
        "toggle_hover_border": "#660000",
        "toggle_icon": "#660000",
    },
}


_CSS_TEMPLATE = """
<style>
.stApp {{
    background-color: {bg};
    color: {fg};
}}
.main-solution {{
    background: linear-gradient(135deg, {solution_grad_a} 0%, {solution_grad_b} 100%);
    border-radius: 14px;
    padding: 16px 14px;
    text-align: center;
    margin: 12px 0;
    border: 1px solid {solution_border};
}}
.elevation-display {{
    font-size: 48px;
    line-height: 1.05;
    font-weight: 700;
    color: {elev};
    text-shadow: 0 0 14px {elev_glow};
}}
.windage-display {{
    font-size: 28px;
    line-height: 1.1;
    font-weight: 600;
    color: {wind};
}}
@media (max-width: 640px) {{
    .main-solution {{ padding: 12px 10px; margin: 8px 0; }}
    .elevation-display {{ font-size: 36px; }}
    .windage-display {{ font-size: 22px; }}
}}
.metric-card {{
    background: {card_bg};
    border-radius: 12px;
    padding: 15px;
    margin: 5px;
    border-left: 4px solid {elev};
}}
.section-header {{
    color: {accent};
    font-size: 18px;
    font-weight: 600;
    margin-bottom: 10px;
    border-bottom: 1px solid {card_border_dim};
    padding-bottom: 5px;
}}
/* Make the sidebar collapse/expand control unmistakable - target every
   selector Streamlit has used for it across versions plus a custom
   .strelok-sidebar-toggle class we tag via JS below. */
.strelok-sidebar-toggle,
button[data-testid="stSidebarCollapseButton"],
button[data-testid="stSidebarCollapsedControl"],
button[data-testid="collapsedControl"],
button[aria-label="Close sidebar"],
button[aria-label="Open sidebar"],
div[data-testid="stSidebarCollapsedControl"] button,
[data-testid="stSidebar"] button[kind="headerNoPadding"],
header button[kind="headerNoPadding"]:first-of-type {{
    background: {toggle_bg} !important;
    border: 1px solid {toggle_border} !important;
    border-radius: 8px !important;
    width: 36px !important;
    height: 36px !important;
    min-width: 36px !important;
    min-height: 36px !important;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.4) !important;
    opacity: 0.9 !important;
    visibility: visible !important;
    z-index: 999999 !important;
    padding: 5px !important;
}}
.strelok-sidebar-toggle svg,
button[data-testid="stSidebarCollapseButton"] svg,
button[data-testid="stSidebarCollapsedControl"] svg,
button[data-testid="collapsedControl"] svg,
button[aria-label="Close sidebar"] svg,
button[aria-label="Open sidebar"] svg,
div[data-testid="stSidebarCollapsedControl"] button svg,
[data-testid="stSidebar"] button[kind="headerNoPadding"] svg,
header button[kind="headerNoPadding"]:first-of-type svg {{
    width: 20px !important;
    height: 20px !important;
    color: {toggle_icon} !important;
    fill: {toggle_icon} !important;
    stroke: {toggle_icon} !important;
    stroke-width: 2 !important;
}}
.strelok-sidebar-toggle:hover,
button[data-testid="stSidebarCollapseButton"]:hover,
button[data-testid="stSidebarCollapsedControl"]:hover,
button[data-testid="collapsedControl"]:hover,
button[aria-label="Close sidebar"]:hover,
button[aria-label="Open sidebar"]:hover {{
    background: {toggle_hover_bg} !important;
    border-color: {toggle_hover_border} !important;
    opacity: 1 !important;
}}
</style>
<script>
// Tag the sidebar collapse/expand button with a stable class so the CSS
// above catches it even if Streamlit renames data-testids.
(function tagSidebarToggle() {{
    const label = /sidebar/i;
    const tag = () => {{
        try {{
            const parentDoc = window.parent && window.parent.document;
            if (!parentDoc) return;
            const candidates = parentDoc.querySelectorAll('button');
            candidates.forEach(btn => {{
                const aria = btn.getAttribute('aria-label') || '';
                const tid = btn.getAttribute('data-testid') || '';
                if (label.test(aria) || label.test(tid) || tid === 'collapsedControl') {{
                    btn.classList.add('strelok-sidebar-toggle');
                }}
            }});
        }} catch (_) {{}}
    }};
    tag();
    const obs = new MutationObserver(tag);
    try {{
        obs.observe(window.parent.document.body, {{ childList: true, subtree: true }});
    }} catch (_) {{}}
}})();
</script>
"""


def apply_theme(theme: str = "dark") -> None:
    """Apply custom CSS based on the selected theme."""
    palette = PALETTES.get(theme, PALETTES["dark"])
    st.markdown(_CSS_TEMPLATE.format(**palette), unsafe_allow_html=True)
