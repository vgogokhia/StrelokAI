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
            border-radius: 16px;
            padding: 30px;
            text-align: center;
            margin: 20px 0;
            border: 1px solid #0f3460;
        }
        .elevation-display {
            font-size: 72px;
            font-weight: 700;
            color: #4CAF50;
            text-shadow: 0 0 20px rgba(76, 175, 80, 0.5);
        }
        .windage-display {
            font-size: 36px;
            font-weight: 600;
            color: #42A5F5;
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
        </style>
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
            border-radius: 16px;
            padding: 30px;
            text-align: center;
            margin: 20px 0;
            border: 1px solid #330000;
        }
        .elevation-display {
            font-size: 72px;
            font-weight: 700;
            color: #990000;
        }
        .windage-display {
            font-size: 36px;
            font-weight: 600;
            color: #660000;
        }
        </style>
        """, unsafe_allow_html=True)
