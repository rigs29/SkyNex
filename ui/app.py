"""
SkyNex: AI-Driven Anomaly Detection in Component Burn-In & Screening
Primary Streamlit Application Entrypoint
SIH 2026 Problem Statement 26170
"""

import sys
from pathlib import Path

# Add project root to sys.path for robust relative/absolute imports
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import streamlit as st
import pandas as pd

from engine.skynex_engine import get_engine
from ui.components.sidebar import render_sidebar
from ui.components.kpi_cards import render_kpi_cards
from ui.components.charts import render_summary_charts
from ui.components.priority_table import render_priority_table
from ui.components.bottom_strip import render_bottom_value_strip

# Initialize page config
st.set_page_config(
    page_title="SkyNex | Anomaly Detection System",
    page_icon="🛰️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Global custom theme & typography CSS
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    }
    
    /* Main Background */
    .stApp {
        background-color: #F4F7FC !important;
        color: #0F172A !important;
    }
    
    /* Hide Default Streamlit Header Obstructions */
    header[data-testid="stHeader"] {
        background: transparent !important;
        height: 1.5rem !important;
        z-index: 10 !important;
    }
    [data-testid="stDeployButton"] {
        display: none !important;
    }
    #MainMenu {
        visibility: hidden !important;
    }
    footer {
        visibility: hidden !important;
    }
    
    /* Main Container Padding */
    .block-container {
        padding-top: 2.2rem !important;
        padding-bottom: 2rem !important;
        max-width: 98% !important;
    }
    
    /* Top Header & App Structure */
    .main-header-title {
        font-size: 26px;
        font-weight: 800;
        color: #0F172A;
        letter-spacing: -0.5px;
        margin-bottom: 2px;
        line-height: 1.2;
    }
    .main-header-sub {
        font-size: 13px;
        color: #64748B;
        font-weight: 500;
    }
    .notif-badge {
        background: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 10px;
        height: 38px;
        padding: 0 12px;
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 6px;
        font-size: 13px;
        font-weight: 700;
        color: #0F172A;
        box-shadow: 0 1px 2px rgba(0, 0, 0, 0.04);
    }
    .notif-circle {
        background: #EF4444;
        color: #FFFFFF;
        font-size: 10px;
        font-weight: 800;
        width: 18px;
        height: 18px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
    }
    
    /* Selectbox Styling */
    div[data-baseweb="select"] > div {
        background-color: #FFFFFF !important;
        border: 1px solid #E2E8F0 !important;
        border-radius: 10px !important;
        color: #0F172A !important;
        height: 38px !important;
        min-height: 38px !important;
        box-shadow: 0 1px 2px rgba(0, 0, 0, 0.04) !important;
    }
    div[data-baseweb="select"] span {
        color: #0F172A !important;
        font-size: 13px !important;
        font-weight: 600 !important;
    }
    
    /* Buttons */
    .stButton > button {
        height: 38px !important;
        border-radius: 10px !important;
        font-size: 13px !important;
        font-weight: 600 !important;
    }
    button[kind="primary"] {
        background-color: #1D63FF !important;
        border-color: #1D63FF !important;
        color: #FFFFFF !important;
    }
    button[kind="secondary"] {
        background-color: #FFFFFF !important;
        border: 1px solid #E2E8F0 !important;
        color: #0F172A !important;
        box-shadow: 0 1px 2px rgba(0, 0, 0, 0.04) !important;
    }
    button[kind="secondary"]:hover {
        border-color: #1D63FF !important;
        color: #1D63FF !important;
    }

    /* Keep HTML card grids from being clipped by Streamlit wrappers */
    .stMarkdown, .stMarkdown p {
        width: 100%;
    }
    div[data-testid="stVerticalBlock"] > div:has(.summary-grid),
    div[data-testid="stVerticalBlock"] > div:has(.kpi-grid) {
        width: 100%;
    }
    iframe[title*="html"] {
        overflow: visible !important;
    }
    iframe {
        border: none !important;
    }
    [data-testid="stIFrame"] iframe {
        border: none !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


def main():
    # Load / Cache backend engine
    engine = get_engine()
    df = engine.processed_df

    # 1. Render Left Sidebar Navigation
    current_page = render_sidebar(current_page="Dashboard")

    # If user navigates to another page, display the dedicated module placeholder
    if current_page != "Dashboard":
        st.markdown(f"## 🛰️ SkyNex / {current_page}")
        st.info(f"The **{current_page}** module is active and connected to the backend. Dedicated workspace view is ready for upcoming features.")
        if st.button("⬅ Return to Dashboard Overview", type="primary"):
            st.session_state.nav_page = "Dashboard"
            st.rerun()
        return

    # 2. Main Workspace Header
    head_col_left, head_col_right = st.columns([2.8, 2.2])

    with head_col_left:
        st.markdown(
            """
            <div>
                <div class="main-header-title">Dashboard Overview</div>
                <div class="main-header-sub">Real-time summary of burn-in screening and anomaly detection</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with head_col_right:
        ctrl_col1, ctrl_col2, ctrl_col3 = st.columns([2.2, 1.2, 0.9])
        with ctrl_col1:
            st.selectbox(
                "Date Range",
                ["All Components", "Top Risk Only"],
                label_visibility="collapsed",
                key="date_range_picker",
            )
        with ctrl_col2:
            if st.button("🔄 Refresh", key="btn_refresh_dashboard", use_container_width=True):
                st.rerun()
        with ctrl_col3:
            high_risk_count = int(df["risk_level"].isin(["HIGH", "CRITICAL"]).sum())
            st.markdown(
                f"""
                <div class="notif-badge">
                    <span>🔔</span>
                    <span class="notif-circle">{high_risk_count}</span>
                </div>
                """,
                unsafe_allow_html=True,
            )

    st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)

    # 3. Six KPI Cards Row (Driven by backend data)
    render_kpi_cards(df)

    st.markdown("<div style='height: 14px;'></div>", unsafe_allow_html=True)

    # 4. Three Donut Summary Cards (Lots Summary, QA Status, Risk Distribution)
    render_summary_charts(df)

    # 5. Priority Components Table with REVIEW interaction (Driven by backend data)
    render_priority_table(df)

    # 6. Bottom Product Value Strip
    render_bottom_value_strip()


if __name__ == "__main__":
    main()
