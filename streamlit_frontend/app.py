import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import time
import os
from dotenv import load_dotenv

load_dotenv()
API_URL = os.getenv("API_URL", "http://localhost:8000/api")

st.set_page_config(page_title="TransactIQ", page_icon="📊", layout="wide")

page = st.sidebar.radio("Navigation", ["Dashboard", "Upload Data", "Validation Rules", "Upload History"])

if page == "Dashboard":
    st.title("📊 TransactIQ Dashboard")
    st.markdown("Overview of your transaction data quality.")

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

elif page == "Upload Data":
    st.title("📤 Upload Data")
    st.markdown("Upload a CSV or XLSX file for validation and cleaning.")

    uploaded_file = st.file_uploader("Choose a file", type=["csv", "xlsx", "xls"])

    if uploaded_file is not None:
        if st.button("Upload and Process"):
            with st.spinner("Uploading..."):
                files = {"file": (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)}
                try:
                    res = requests.post(f"{API_URL}/uploads", files=files)
                    res.raise_for_status()
                    upload_data = res.json()
                    upload_id = upload_data["upload_id"]
                    st.session_state["current_upload_id"] = upload_id
                    st.success("File uploaded successfully! Processing...")
                except Exception as e:
                    st.error(f"Upload failed: {e}")

    if "current_upload_id" in st.session_state:
        upload_id = st.session_state["current_upload_id"]
        
        status_placeholder = st.empty()
        progress_bar = st.progress(0)
        
        status = "PENDING"
        progress = 0
        while status not in ["COMPLETED", "FAILED"]:
            try:
                status_res = requests.get(f"{API_URL}/uploads/{upload_id}/status")
                if status_res.status_code == 200:
                    data = status_res.json()
                    status = data.get("status", "UNKNOWN")
                    progress = data.get("progress", 0)
                    status_placeholder.info(f"Status: **{status}**")
                    progress_bar.progress(progress / 100.0)
                else:
                    break
            except Exception:
                break
            
            if status in ["COMPLETED", "FAILED"]:
                break
            time.sleep(1)
            
        if status == "FAILED":
            st.error("Processing failed.")
        elif status == "COMPLETED":
            st.success("Processing completed!")
            
            st.markdown("### 📋 Results Summary")
            try:
                res = requests.get(f"{API_URL}/uploads/{upload_id}/results")
                if res.status_code == 200:
                    results = res.json()
                    
                    col1, col2, col3, col4 = st.columns(4)
                    col1.metric("Quality Score", f"{results['quality_score']} / 100", results['quality_label'])
                    col2.metric("Total Records", results['total_records'])
                    col3.metric("Valid Records", results['valid_records'])
                    col4.metric("Invalid Records", results['invalid_records'])
                    
                    if results.get('summary'):
                        st.markdown("#### AI Insights")
                        st.write(results['summary'])
                    
                    st.markdown("### 📥 Downloads")
                    col_d1, col_d2, col_d3 = st.columns(3)
                    
                    def download_btn(label, file_type):
                        dl_url = f"{API_URL}/uploads/{upload_id}/download/{file_type}"
                        return f'<a href="{dl_url}" target="_blank"><button style="padding:0.5rem 1rem; border-radius:5px; border:1px solid #ccc;">{label}</button></a>'
                    
                    col_d1.markdown(download_btn("Download Cleaned CSV", "cleaned"), unsafe_allow_html=True)
                    col_d2.markdown(download_btn("Download Errors CSV", "errors"), unsafe_allow_html=True)
                    col_d3.markdown(download_btn("Download PDF Report", "report"), unsafe_allow_html=True)
                    
                    st.markdown("### ⚠️ Errors")
                    errors_res = requests.get(f"{API_URL}/uploads/{upload_id}/errors?page_size=100")
                    if errors_res.status_code == 200:
                        errors_data = errors_res.json()
                        if errors_data.get("errors"):
                            df_err = pd.DataFrame(errors_data["errors"])
                            st.dataframe(df_err, use_container_width=True)
                        else:
                            st.success("No errors found in this file!")
            except Exception as e:
                st.error(f"Failed to fetch results: {e}")

elif page == "Validation Rules":
    st.title("⚙️ Validation Rules")
    st.markdown("Manage the rules used to validate transaction data.")

    with st.expander("➕ Add New Rule"):
        with st.form("new_rule_form"):
            col1, col2 = st.columns(2)
            country_name = col1.text_input("Country Name (e.g., India, Global)")
            country_code = col2.text_input("Country Code (e.g., +91)")
            field_name = col1.text_input("Field Name (e.g., phone, email)")
            validation_type = col2.selectbox("Validation Type", ["phone_length", "email_format", "enum", "regex", "custom"])
            rule_value = st.text_input("Rule Value (e.g., 10, standard, UPI,Card)")
            
            submitted = st.form_submit_button("Add Rule")
            if submitted:
                if not country_name or not field_name or not rule_value:
                    st.error("Please fill in required fields.")
                else:
                    try:
                        payload = {
                            "country_name": country_name,
                            "country_code": country_code,
                            "field_name": field_name,
                            "validation_type": validation_type,
                            "rule_value": rule_value,
                            "is_active": True
                        }
                        res = requests.post(f"{API_URL}/rules", json=payload)
                        res.raise_for_status()
                        st.success("Rule added successfully!")
                    except Exception as e:
                        st.error(f"Failed to add rule: {e}")

    st.markdown("---")
    st.subheader("Current Rules")

    try:
        res = requests.get(f"{API_URL}/rules")
        res.raise_for_status()
        rules = res.json()
        
        if rules:
            df = pd.DataFrame(rules)
            df = df[["country_name", "country_code", "field_name", "validation_type", "rule_value", "is_active", "version"]]
            st.dataframe(df, use_container_width=True)
        else:
            st.info("No rules found.")
    except Exception as e:
        st.error(f"Failed to load rules: {e}")

elif page == "Upload History":
    st.title("🕒 Upload History")
    st.markdown("View past uploads and download their reports.")

    try:
        res = requests.get(f"{API_URL}/uploads?page=1&page_size=50")
        res.raise_for_status()
        data = res.json()
        uploads = data.get("uploads", [])
        
        if uploads:
            for u in uploads:
                with st.expander(f"{u['file_name']} - Score: {u['quality_score']} - {u['status']}"):
                    col1, col2, col3 = st.columns(3)
                    col1.metric("Date", u['created_at'][:10])
                    col2.metric("Total Rows", u['total_rows'])
                    col3.metric("Invalid", u['invalid_rows'])
                    
                    if u['status'] == 'COMPLETED':
                        col_d1, col_d2, col_d3 = st.columns(3)
                        
                        def download_btn(label, file_type):
                            dl_url = f"{API_URL}/uploads/{u['id']}/download/{file_type}"
                            return f'<a href="{dl_url}" target="_blank"><button style="padding:0.5rem 1rem; border-radius:5px; border:1px solid #ccc;">{label}</button></a>'
                        
                        col_d1.markdown(download_btn("Cleaned CSV", "cleaned"), unsafe_allow_html=True)
                        col_d2.markdown(download_btn("Errors CSV", "errors"), unsafe_allow_html=True)
                        col_d3.markdown(download_btn("PDF Report", "report"), unsafe_allow_html=True)
        else:
            st.info("No uploads found.")
    except Exception as e:
        st.error(f"Failed to fetch history: {e}")
