import os
import uuid
import asyncio
from datetime import datetime
import streamlit as st
import pandas as pd

from database import SessionLocal
from models import Upload, ProcessingStatus
from services.processor import process_upload
from services.column_mapper import map_columns, COLUMN_ALIASES

st.set_page_config(page_title="Upload Dataset | TransactIQ", page_icon="📤", layout="wide")

css_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets", "style.css")
with open(css_path) as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

st.title("📤 Upload Dataset")
st.markdown("Upload a CSV or XLSX file for validation and cleaning.")

_APP_DIR = os.path.join(os.path.expanduser("~"), "AppData", "Local", "TransactIQ")

db = SessionLocal()
try:
    uploaded_file = st.file_uploader("Drag and drop file here", type=["csv", "xlsx", "xls"])

    if uploaded_file is not None:
        file_name = uploaded_file.name
        file_size = len(uploaded_file.getvalue())
        ext = os.path.splitext(file_name)[1].lower()

        try:
            if ext == ".csv":
                df_preview = pd.read_csv(uploaded_file, nrows=5)
            else:
                df_preview = pd.read_excel(uploaded_file, nrows=5)
        except Exception as e:
            st.error(f"Error reading file: {e}")
            st.stop()

        if df_preview.empty:
            st.error("Error: The uploaded file is empty.")
            st.stop()
        
        headers = list(df_preview.columns)
        if any(pd.isna(h) or str(h).strip() == "" or "Unnamed" in str(h) for h in headers):
            st.error("Error: Missing or invalid column headers detected.")
            st.stop()
        
        if len(set(headers)) != len(headers):
            st.error("Error: Duplicate column headers detected.")
            st.stop()

        st.markdown(f"""
        <div class="saas-card" style="margin-bottom: 2rem;">
            <h4>File Details</h4>
            <p><b>Filename:</b> {file_name}</p>
            <p><b>File Size:</b> {file_size/1024:.2f} KB</p>
            <p><b>Uploaded at:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("### 🛠️ Schema Mapping")
        st.write("We automatically detected your columns. Review or change them before processing.")

        auto_mapped = map_columns(headers)
        canonical_options = ["(Ignore)"] + list(COLUMN_ALIASES.keys())
        
        user_mapping = {}
        cols = st.columns(3)
        for i, h in enumerate(headers):
            with cols[i % 3]:
                default_val = auto_mapped.get(h, h)
                idx = canonical_options.index(default_val) if default_val in canonical_options else 0
                user_mapping[h] = st.selectbox(f"Map '{h}' to:", canonical_options, index=idx, key=f"map_{h}")

        if st.button("Upload and Process", type="primary"):
            with st.spinner("Processing... large files will be automatically chunked."):
                upload_id = str(uuid.uuid4())
                up_dir    = os.path.join(_APP_DIR, "uploads")
                os.makedirs(up_dir, exist_ok=True)
                file_path = os.path.join(up_dir, f"{upload_id}{ext}")

                uploaded_file.seek(0)
                with open(file_path, "wb") as f:
                    f.write(uploaded_file.getvalue())

                upload = Upload(
                    id=upload_id,
                    file_name=uploaded_file.name,
                    file_size=file_size,
                    processing_status=ProcessingStatus.UPLOADING,
                )
                db.add(upload)
                db.commit()

                asyncio.run(process_upload(db, upload_id, file_path, user_mapping=user_mapping))
                st.session_state["current_upload_id"] = upload_id
                st.success("Processing completed! Head to Validation Results to see the outcome.")

finally:
    db.close()
