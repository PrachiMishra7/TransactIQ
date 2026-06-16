import streamlit as st
import requests
import pandas as pd
import os
from dotenv import load_dotenv

load_dotenv()
API_URL = os.getenv("API_URL", "http://localhost:8000/api")

st.set_page_config(page_title="Upload History", page_icon="🕒", layout="wide")

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
