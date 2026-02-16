import sys
import os

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


import streamlit as st
import pandas as pd
import plotly.express as px
from database.engine import engine


st.set_page_config(layout="wide")
st.title("🧠 Mental Health Admin Dashboard")


def load_users():
    df = pd.read_sql_query("""SELECT 
            u.id,
            u.username,
            COUNT(e.id) AS total_logs,
            AVG(e.risk_score) AS avg_risk,
            MAX(e.risk_score) AS latest_risk
        FROM users u
        LEFT JOIN emotional_logs e
        ON u.id = e.telegram_user_id
        GROUP BY u.id, u.username
        ORDER BY avg_risk DESC NULLS LAST;""", engine)
    
    return df


def load_user_details(user_id):
    df = pd.read_sql_query(..., engine)
    return df


# ---- MAIN UI ----

users_df = load_users()

st.subheader("👥 Users Overview")

if users_df.empty:
    st.info("No users found.")
else:
    st.dataframe(users_df, use_container_width=True)

    # Highlight high-risk users
    high_risk_users = users_df[users_df["avg_risk"] > 8]

    if not high_risk_users.empty:
        st.error("⚠ High Risk Users Detected")
        st.dataframe(high_risk_users)


    selected_user = st.selectbox(
        "Select User ID to View Details",
        users_df["id"]
    )

    if selected_user:
        user_data = load_user_details(selected_user)

        if not user_data.empty:
            col1, col2 = st.columns(2)

            with col1:
                fig = px.line(
                    user_data,
                    x="created_at",
                    y="risk_score",
                    title="Risk Score Over Time"
                )
                st.plotly_chart(fig, use_container_width=True)

            with col2:
                fig2 = px.line(
                    user_data,
                    x="created_at",
                    y=["sadness", "anger", "fear", "joy"],
                    title="Emotion Breakdown"
                )
                st.plotly_chart(fig2, use_container_width=True)

        else:
            st.info("No emotional data for this user.")

