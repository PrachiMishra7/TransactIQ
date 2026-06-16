import streamlit as st
import requests
import pandas as pd
import time
import os
from dotenv import load_dotenv

load_dotenv()
API_URL = os.getenv("API_URL", "http://localhost:8000/api")

st.set_page_config(page_title="Upload Data", page_icon="📤", layout="wide")

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
    
    # Poll status
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
        
        # Fetch results
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
