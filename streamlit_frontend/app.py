import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import os
from dotenv import load_dotenv

load_dotenv()
API_URL = os.getenv("API_URL", "http://localhost:8000/api")

st.set_page_config(page_title="TransactIQ Dashboard", page_icon="📊", layout="wide")

st.title("📊 TransactIQ Dashboard")
st.markdown("Overview of your transaction data quality.")

# Fetch stats
try:
    stats_res = requests.get(f"{API_URL}/dashboard/stats")
    stats_res.raise_for_status()
    stats = stats_res.json()
    
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Files Processed", stats.get("total_files_processed", 0))
    col2.metric("Total Records Validated", stats.get("total_records_validated", 0))
    col3.metric("Avg Quality Score", f"{stats.get('average_quality_score', 0)} / 100")
    col4.metric("Active Rules", stats.get("active_validation_rules", 0))
except Exception as e:
    st.error(f"Failed to fetch stats: {e}")

st.markdown("---")

col_left, col_right = st.columns(2)

with col_left:
    st.subheader("Errors by Type")
    try:
        res = requests.get(f"{API_URL}/dashboard/charts/errors-by-type")
        if res.status_code == 200 and res.json():
            df = pd.DataFrame(res.json())
            fig = px.bar(df, x="type", y="count", color="type")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No error data available yet.")
    except Exception:
        st.error("Could not load chart data.")

    st.subheader("Quality Trend")
    try:
        res = requests.get(f"{API_URL}/dashboard/charts/quality-trend")
        if res.status_code == 200 and res.json():
            df = pd.DataFrame(res.json())
            fig = px.line(df, x="date", y="score", hover_data=["file_name"], markers=True)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No trend data available yet.")
    except Exception:
        st.error("Could not load chart data.")

with col_right:
    st.subheader("Files Processed per Day")
    try:
        res = requests.get(f"{API_URL}/dashboard/charts/files-per-day")
        if res.status_code == 200 and res.json():
            df = pd.DataFrame(res.json())
            fig = px.bar(df, x="date", y="count")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No daily data available yet.")
    except Exception:
        st.error("Could not load chart data.")

    st.subheader("Errors by Country")
    try:
        res = requests.get(f"{API_URL}/dashboard/charts/country-errors")
        if res.status_code == 200 and res.json():
            df = pd.DataFrame(res.json())
            fig = px.pie(df, names="country", values="count", hole=0.4)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No country error data available yet.")
    except Exception:
        st.error("Could not load chart data.")
