"""
SkyNex UI Bottom Product Value Strip Component
Renders the 4 aerospace core capability pillars at the bottom of the dashboard.
"""

import streamlit as st


def render_bottom_value_strip():
    """
    Renders the four compact product capability cards matching the reference image.
    """
    st.markdown(
        """
        <style>
        .bottom-strip-card {
            background: #FFFFFF;
            border: 1px solid #E2E8F0;
            border-radius: 14px;
            padding: 14px 18px;
            box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04);
            margin-top: 14px;
            margin-bottom: 20px;
        }
        .pillar-item {
            display: flex;
            align-items: center;
            gap: 14px;
        }
        .pillar-icon-box {
            width: 40px;
            height: 40px;
            border-radius: 10px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 18px;
            flex-shrink: 0;
        }
        .pillar-title {
            font-size: 13px;
            font-weight: 700;
            color: #0F172A;
            line-height: 1.2;
        }
        .pillar-subtitle {
            font-size: 11px;
            color: #64748B;
            font-weight: 500;
            margin-top: 2px;
            line-height: 1.2;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    st.markdown('<div class="bottom-strip-card">', unsafe_allow_html=True)
    cols = st.columns(4)

    # Pillar 1: Real-time Monitoring
    with cols[0]:
        st.markdown(
            """
            <div class="pillar-item">
                <div class="pillar-icon-box" style="background:#EFF6FF; color:#1D63FF;">⚡</div>
                <div>
                    <div class="pillar-title">Real-time Monitoring</div>
                    <div class="pillar-subtitle">Continuous burn-in tracking</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # Pillar 2: AI-Powered Insights
    with cols[1]:
        st.markdown(
            """
            <div class="pillar-item">
                <div class="pillar-icon-box" style="background:#F5F3FF; color:#8B5CF6;">🧠</div>
                <div>
                    <div class="pillar-title">AI-Powered Insights</div>
                    <div class="pillar-subtitle">Advanced anomaly detection</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # Pillar 3: Predict & Prevent
    with cols[2]:
        st.markdown(
            """
            <div class="pillar-item">
                <div class="pillar-icon-box" style="background:#ECFDF5; color:#10B981;">🛡️</div>
                <div>
                    <div class="pillar-title">Predict & Prevent</div>
                    <div class="pillar-subtitle">Early risk identification</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # Pillar 4: Human-in-the-Loop
    with cols[3]:
        st.markdown(
            """
            <div class="pillar-item">
                <div class="pillar-icon-box" style="background:#FFF7ED; color:#F97316;">👥</div>
                <div>
                    <div class="pillar-title">Human-in-the-Loop</div>
                    <div class="pillar-subtitle">AI + Engineer collaboration</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("</div>", unsafe_allow_html=True)

