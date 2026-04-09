"""
StrelokAI - Theme & CSS Injection
Applies custom CSS themes (Dark, Red/NVG) to the Streamlit UI.
Version: 1.0.0
"""
import streamlit as st

def apply_theme(theme: str = "dark"):
    """Apply custom CSS based on the selected theme."""
    if theme == "dark":
        st.markdown("""
        <style>
        .stApp {
            background-color: #121212;
            color: #E0E0E0;
        }
        .main-solution {
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            border-radius: 14px;
            padding: 16px 14px;
            text-align: center;
            margin: 12px 0;
            border: 1px solid #0f3460;
        }
        .elevation-display {
            font-size: 48px;
            line-height: 1.05;
            font-weight: 700;
            color: #4CAF50;
            text-shadow: 0 0 14px rgba(76, 175, 80, 0.45);
        }
        .windage-display {
            font-size: 28px;
            line-height: 1.1;
            font-weight: 600;
            color: #42A5F5;
        }
        @media (max-width: 640px) {
            .main-solution { padding: 12px 10px; margin: 8px 0; }
            .elevation-display { font-size: 36px; }
            .windage-display { font-size: 22px; }
        }
        .metric-card {
            background: #1E1E1E;
            border-radius: 12px;
            padding: 15px;
            margin: 5px;
            border-left: 4px solid #4CAF50;
        }
        .section-header {
            color: #BB86FC;
            font-size: 18px;
            font-weight: 600;
            margin-bottom: 10px;
            border-bottom: 1px solid #333;
            padding-bottom: 5px;
        }
        /* Make the sidebar collapse/expand control unmistakable — target
           every selector Streamlit has used for it across versions plus a
           custom .strelok-sidebar-toggle class we tag via JS below. */
        .strelok-sidebar-toggle,
        button[data-testid="stSidebarCollapseButton"],
        button[data-testid="stSidebarCollapsedControl"],
        button[data-testid="collapsedControl"],
        button[aria-label="Close sidebar"],
        button[aria-label="Open sidebar"],
        div[data-testid="stSidebarCollapsedControl"] button,
        [data-testid="stSidebar"] button[kind="headerNoPadding"],
        header button[kind="headerNoPadding"]:first-of-type {
            background: #2a2a2a !important;
            border: 1px solid #555 !important;
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
        }
        .strelok-sidebar-toggle svg,
        button[data-testid="stSidebarCollapseButton"] svg,
        button[data-testid="stSidebarCollapsedControl"] svg,
        button[data-testid="collapsedControl"] svg,
        button[aria-label="Close sidebar"] svg,
        button[aria-label="Open sidebar"] svg,
        div[data-testid="stSidebarCollapsedControl"] button svg,
        [data-testid="stSidebar"] button[kind="headerNoPadding"] svg,
        header button[kind="headerNoPadding"]:first-of-type svg {
            width: 20px !important;
            height: 20px !important;
            color: #d0d0d0 !important;
            fill: #d0d0d0 !important;
            stroke: #d0d0d0 !important;
            stroke-width: 2 !important;
        }
        .strelok-sidebar-toggle:hover,
        button[data-testid="stSidebarCollapseButton"]:hover,
        button[data-testid="stSidebarCollapsedControl"]:hover,
        button[data-testid="collapsedControl"]:hover,
        button[aria-label="Close sidebar"]:hover,
        button[aria-label="Open sidebar"]:hover {
            background: #3a3a3a !important;
            border-color: #4CAF50 !important;
            opacity: 1 !important;
        }
        </style>
        <script>
        // Tag the sidebar collapse/expand button with a stable class so the
        // CSS above catches it even if Streamlit renames data-testids.
        (function tagSidebarToggle() {
            const label = /sidebar/i;
            const tag = () => {
                try {
                    const parentDoc = window.parent && window.parent.document;
                    if (!parentDoc) return;
                    const candidates = parentDoc.querySelectorAll('button');
                    candidates.forEach(btn => {
                        const aria = btn.getAttribute('aria-label') || '';
                        const tid = btn.getAttribute('data-testid') || '';
                        if (label.test(aria) || label.test(tid) || tid === 'collapsedControl') {
                            btn.classList.add('strelok-sidebar-toggle');
                        }
                    });
                } catch (_) {}
            };
            tag();
            // Re-tag after Streamlit rerenders (it replaces DOM nodes often).
            const obs = new MutationObserver(tag);
            try {
                obs.observe(window.parent.document.body, { childList: true, subtree: true });
            } catch (_) {}
        })();
        </script>
        """, unsafe_allow_html=True)
    elif theme == "red":
        st.markdown("""
        <style>
        .stApp {
            background-color: #000000;
            color: #660000;
        }
        .main-solution {
            background: #0a0000;
            border-radius: 14px;
            padding: 16px 14px;
            text-align: center;
            margin: 12px 0;
            border: 1px solid #330000;
        }
        .elevation-display {
            font-size: 48px;
            line-height: 1.05;
            font-weight: 700;
            color: #990000;
        }
        .windage-display {
            font-size: 28px;
            line-height: 1.1;
            font-weight: 600;
            color: #660000;
        }
        @media (max-width: 640px) {
            .main-solution { padding: 12px 10px; margin: 8px 0; }
            .elevation-display { font-size: 36px; }
            .windage-display { font-size: 22px; }
        }
        </style>
        """, unsafe_allow_html=True)
