"""
dashboard/live_dashboard.py

Run with:
    streamlit run dashboard/live_dashboard.py
"""

import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from database.engine import engine

st.set_page_config(
    page_title="Mental Health Admin",
    page_icon="🧠",
    layout="wide",
)

st.title("🧠 Mental Health Admin Dashboard")

# ── Helpers ─────────────────────────────────────────────────────────────────

RISK_THRESHOLDS = {"Low": 6, "Moderate": 10, "High": 15}


def risk_badge(score):
    if score is None:
        return "—"
    if score >= 15:
        return "🔴 Critical"
    if score >= 10:
        return "🟠 High"
    if score >= 6:
        return "🟡 Moderate"
    return "🟢 Low"


@st.cache_data(ttl=30)
def load_users() -> pd.DataFrame:
    return pd.read_sql_query(
        """
        SELECT
            u.id,
            COALESCE(u.username, u.first_name, 'Unknown') AS username,
            COUNT(e.id)          AS total_logs,
            ROUND(AVG(e.risk_score)::numeric, 2)  AS avg_risk,
            ROUND(MAX(e.risk_score)::numeric, 2)  AS peak_risk,
            MAX(e.created_at)    AS last_activity
        FROM telegram_users u
        LEFT JOIN emotional_logs e ON u.telegram_user_id = e.telegram_user_id
        GROUP BY u.id, u.username, u.first_name
        ORDER BY avg_risk DESC NULLS LAST;
        """,
        engine,
    )


@st.cache_data(ttl=15)
def load_user_details(user_id: int) -> pd.DataFrame:
    return pd.read_sql_query(
        """
        SELECT
            created_at,
            risk_score,
            sadness,
            anger,
            fear,
            joy,
            llm_risk,
            hopelessness,
            emotional_intensity
        FROM emotional_logs
        WHERE telegram_user_id = %s
        ORDER BY created_at ASC;
        """,
        engine,
        params=(user_id,),
    )


@st.cache_data(ttl=30)
def load_recent_critical() -> pd.DataFrame:
    return pd.read_sql_query(
        """
        SELECT
            e.created_at,
            COALESCE(u.username, u.first_name, CAST(u.telegram_user_id AS TEXT)) AS username,
            e.risk_score,
            e.sadness,
            e.anger,
            e.fear
        FROM emotional_logs e
        JOIN telegram_users u ON e.telegram_user_id = u.telegram_user_id
        WHERE e.risk_score >= 15
        ORDER BY e.created_at DESC
        LIMIT 50;
        """,
        engine,
    )


@st.cache_data(ttl=60)
def load_global_risk_trend() -> pd.DataFrame:
    return pd.read_sql_query(
        """
        SELECT
            DATE_TRUNC('hour', created_at) AS hour,
            ROUND(AVG(risk_score)::numeric, 2) AS avg_risk,
            COUNT(*) AS events
        FROM emotional_logs
        WHERE created_at > NOW() - INTERVAL '7 days'
        GROUP BY 1
        ORDER BY 1;
        """,
        engine,
    )


# ── Sidebar Controls ─────────────────────────────────────────────────────────

with st.sidebar:
    st.header("⚙️ Controls")
    auto_refresh = st.checkbox("Auto-refresh (30s)", value=False)
    if auto_refresh:
        import time
        time.sleep(30)
        st.cache_data.clear()
        st.rerun()

    if st.button("🔄 Refresh Now"):
        st.cache_data.clear()
        st.rerun()

    st.markdown("---")
    st.caption("Risk Thresholds")
    st.markdown("🔴 Critical ≥ 15  \n🟠 High ≥ 10  \n🟡 Moderate ≥ 6  \n🟢 Low < 6")


# ── Top-level Metrics ────────────────────────────────────────────────────────

users_df = load_users()

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Total Users", len(users_df))

with col2:
    high_risk_count = len(users_df[users_df["avg_risk"] >= 10])
    st.metric("High-Risk Users", high_risk_count, delta_color="inverse")

with col3:
    critical = len(users_df[users_df["peak_risk"] >= 15])
    st.metric("Ever Critical", critical, delta_color="inverse")

with col4:
    avg = users_df["avg_risk"].mean()
    st.metric("Platform Avg Risk", f"{avg:.1f}" if pd.notna(avg) else "—")

st.markdown("---")

# ── Global Risk Trend ────────────────────────────────────────────────────────

st.subheader("📈 Platform Risk Trend (Last 7 Days)")

trend_df = load_global_risk_trend()

if not trend_df.empty:
    fig_trend = go.Figure()
    fig_trend.add_trace(
        go.Scatter(
            x=trend_df["hour"],
            y=trend_df["avg_risk"],
            mode="lines+markers",
            name="Avg Risk",
            line=dict(color="#EF553B", width=2),
            fill="tozeroy",
            fillcolor="rgba(239,85,59,0.15)",
        )
    )
    # Threshold lines
    for label, val, color in [
        ("Moderate", 6, "gold"),
        ("High", 10, "orange"),
        ("Critical", 15, "red"),
    ]:
        fig_trend.add_hline(
            y=val,
            line_dash="dot",
            line_color=color,
            annotation_text=label,
            annotation_position="bottom right",
        )
    fig_trend.update_layout(
        xaxis_title="Time",
        yaxis_title="Avg Risk Score",
        height=300,
        margin=dict(t=20, b=20),
    )
    st.plotly_chart(fig_trend, use_container_width=True)
else:
    st.info("No trend data yet.")

st.markdown("---")

# ── Users Table ──────────────────────────────────────────────────────────────

st.subheader("👥 Users Overview")

if users_df.empty:
    st.info("No users found.")
else:
    display_df = users_df.copy()
    display_df["risk_level"] = display_df["avg_risk"].apply(risk_badge)
    display_df["last_activity"] = pd.to_datetime(
        display_df["last_activity"]
    ).dt.strftime("%Y-%m-%d %H:%M")

    # Highlight critical rows
    def highlight_risk(row):
        val = row.get("avg_risk")
        if pd.isna(val):
            return [""] * len(row)
        if val >= 15:
            return ["background-color: #ffcccc"] * len(row)
        if val >= 10:
            return ["background-color: #ffe8cc"] * len(row)
        if val >= 6:
            return ["background-color: #fffacc"] * len(row)
        return [""] * len(row)

    st.dataframe(
        display_df[
            ["id", "username", "total_logs", "avg_risk", "peak_risk", "risk_level", "last_activity"]
        ].style.apply(highlight_risk, axis=1),
        use_container_width=True,
        hide_index=True,
    )

    # ── Critical Alerts ──────────────────────────────────────────────────────

    critical_df = load_recent_critical()

    if not critical_df.empty:
        with st.expander("🚨 Recent Critical Events", expanded=True):
            st.dataframe(critical_df, use_container_width=True, hide_index=True)

    st.markdown("---")

    # ── Per-User Deep Dive ───────────────────────────────────────────────────

    st.subheader("🔍 User Deep Dive")

    user_options = {
        f"{row['username']} (id: {row['id']})": row["id"]
        for _, row in users_df.iterrows()
    }

    selected_label = st.selectbox("Select a user", list(user_options.keys()))
    selected_id = user_options[selected_label]

    user_data = load_user_details(selected_id)

    if user_data.empty:
        st.info("No emotional data recorded for this user yet.")
    else:
        # Summary metrics for selected user
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Total Events", len(user_data))
        m2.metric("Avg Risk", f"{user_data['risk_score'].mean():.1f}")
        m3.metric("Peak Risk", f"{user_data['risk_score'].max():.1f}")
        m4.metric(
            "Critical Events",
            int((user_data["risk_score"] >= 15).sum()),
        )

        # ── Risk Over Time ───────────────────────────────────────────────────
        st.markdown("#### Risk Score Over Time")

        fig_risk = go.Figure()
        fig_risk.add_trace(
            go.Scatter(
                x=user_data["created_at"],
                y=user_data["risk_score"],
                mode="lines+markers",
                name="Risk Score",
                line=dict(color="#EF553B"),
            )
        )
        for label, val, color in [
            ("Moderate", 6, "gold"),
            ("High", 10, "orange"),
            ("Critical", 15, "red"),
        ]:
            fig_risk.add_hline(
                y=val,
                line_dash="dot",
                line_color=color,
                annotation_text=label,
                annotation_position="right",
            )
        fig_risk.update_layout(
            xaxis_title="Time",
            yaxis_title="Risk Score",
            height=320,
            margin=dict(t=10, b=10),
        )
        st.plotly_chart(fig_risk, use_container_width=True)

        # ── Emotion Breakdown ────────────────────────────────────────────────
        col_a, col_b = st.columns(2)

        with col_a:
            st.markdown("#### Emotion Trends")
            fig_emo = px.line(
                user_data,
                x="created_at",
                y=["sadness", "anger", "fear", "joy"],
                labels={"value": "Score", "variable": "Emotion", "created_at": "Time"},
                color_discrete_map={
                    "sadness": "#636EFA",
                    "anger": "#EF553B",
                    "fear": "#AB63FA",
                    "joy": "#00CC96",
                },
            )
            fig_emo.update_layout(height=300, margin=dict(t=10, b=10))
            st.plotly_chart(fig_emo, use_container_width=True)

        with col_b:
            st.markdown("#### Average Emotion Distribution")
            avg_emotions = user_data[["sadness", "anger", "fear", "joy"]].mean()
            fig_pie = px.pie(
                values=avg_emotions.values,
                names=avg_emotions.index,
                color_discrete_map={
                    "sadness": "#636EFA",
                    "anger": "#EF553B",
                    "fear": "#AB63FA",
                    "joy": "#00CC96",
                },
            )
            fig_pie.update_layout(height=300, margin=dict(t=10, b=10))
            st.plotly_chart(fig_pie, use_container_width=True)

        # ── LLM Signals ──────────────────────────────────────────────────────
        st.markdown("#### LLM Psychological Signals")
        fig_llm = px.line(
            user_data,
            x="created_at",
            y=["llm_risk", "hopelessness", "emotional_intensity"],
            labels={"value": "Score (0–10)", "variable": "Signal", "created_at": "Time"},
            color_discrete_map={
                "llm_risk": "#EF553B",
                "hopelessness": "#636EFA",
                "emotional_intensity": "#FFA15A",
            },
        )
        fig_llm.update_layout(height=300, margin=dict(t=10, b=10))
        st.plotly_chart(fig_llm, use_container_width=True)

        # ── Raw Log ──────────────────────────────────────────────────────────
        with st.expander("📋 Raw Log"):
            st.dataframe(user_data, use_container_width=True, hide_index=True)
