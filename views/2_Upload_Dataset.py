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


css_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets", "style.css")
with open(css_path) as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

st.markdown("""
<div class="section-header">
    <div class="section-icon">&#8679;</div>
    <h2>Upload Dataset</h2>
</div>
<p style="color:#64748B; margin-bottom:1.5rem; font-size:0.9rem;">
    Upload a CSV or Excel file. We auto-detect columns, allow schema overrides, and process even 1M+ row files via chunking.
</p>
""", unsafe_allow_html=True)

_APP_DIR = os.path.join(os.path.expanduser("~"), "AppData", "Local", "TransactIQ")

# Supported formats callout
st.markdown("""
<div class="card" style="margin-bottom:1.5rem;">
    <div class="card-title">Supported Formats</div>
    <div style="display:flex; gap:1rem; flex-wrap:wrap;">
        <span class="status-badge status-info">CSV (.csv)</span>
        <span class="status-badge status-info">Excel (.xlsx)</span>
        <span class="status-badge status-info">Excel 97 (.xls)</span>
    </div>
    <p style="color:#64748B; font-size:0.82rem; margin-top:12px; margin-bottom:0;">
        Files are processed in 50,000-row chunks. Large files are handled automatically — no size limits.
    </p>
</div>
""", unsafe_allow_html=True)

db = SessionLocal()
try:
    uploaded_file = st.file_uploader(
        "Drag and drop your file here, or click to browse",
        type=["csv", "xlsx", "xls"],
        help="Supports CSV and Excel files of any size"
    )

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
            st.error("The uploaded file appears to be empty.")
            st.stop()

        headers = list(df_preview.columns)
        if any(pd.isna(h) or str(h).strip() == "" or "Unnamed" in str(h) for h in headers):
            st.error("Missing or invalid column headers detected. Please check your file.")
            st.stop()
        if len(set(headers)) != len(headers):
            st.error("Duplicate column headers detected. Please ensure all columns are unique.")
            st.stop()

        # File Details Card
        file_size_display = f"{file_size/1024:.1f} KB" if file_size < 1024*1024 else f"{file_size/1024/1024:.2f} MB"
        st.markdown(f"""
        <div class="card" style="margin-bottom:1.5rem;">
            <div class="card-title">File Details</div>
            <div style="display:grid; grid-template-columns: repeat(auto-fit, minmax(160px, 1fr)); gap:1rem;">
                <div>
                    <div class="kpi-label">Filename</div>
                    <div style="color:#E2E8F0; font-weight:600; font-size:0.9rem; margin-top:4px;">{file_name}</div>
                </div>
                <div>
                    <div class="kpi-label">File Size</div>
                    <div style="color:#818CF8; font-weight:700; font-size:1.1rem; margin-top:4px;">{file_size_display}</div>
                </div>
                <div>
                    <div class="kpi-label">Columns Detected</div>
                    <div style="color:#34D399; font-weight:700; font-size:1.1rem; margin-top:4px;">{len(headers)}</div>
                </div>
                <div>
                    <div class="kpi-label">Uploaded At</div>
                    <div style="color:#E2E8F0; font-weight:600; font-size:0.9rem; margin-top:4px;">{datetime.now().strftime('%H:%M:%S')}</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # Data Preview
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown('<div class="card-title">Data Preview (first 5 rows)</div>', unsafe_allow_html=True)
        st.dataframe(df_preview, use_container_width=True, hide_index=True)
        st.markdown('</div>', unsafe_allow_html=True)

        # Schema Mapping
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown("""
        <div class="card-title">Schema Mapping</div>
        <p style="color:#64748B; font-size:0.85rem; margin-bottom:1rem; margin-top:0;">
            We auto-mapped your columns. Review and adjust if any mapping is incorrect before processing.
        </p>
        """, unsafe_allow_html=True)

        auto_mapped = map_columns(headers)
        canonical_options = ["(Ignore)"] + list(COLUMN_ALIASES.keys())

        user_mapping = {}
        cols = st.columns(3)
        for i, h in enumerate(headers):
            with cols[i % 3]:
                default_val = auto_mapped.get(h, h)
                idx = canonical_options.index(default_val) if default_val in canonical_options else 0
                user_mapping[h] = st.selectbox(
                    f"`{h}`  →",
                    canonical_options,
                    index=idx,
                    key=f"map_{h}",
                )
        st.markdown('</div>', unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("Process & Validate Dataset", type="primary"):
            with st.spinner("Processing your file... large files are automatically chunked."):
                upload_id = str(uuid.uuid4())
                up_dir = os.path.join(_APP_DIR, "uploads")
                os.makedirs(up_dir, exist_ok=True)
                file_path = os.path.join(up_dir, f"{upload_id}{ext}")

                uploaded_file.seek(0)
                with open(file_path, "wb") as f:
                    f.write(uploaded_file.getvalue())

                upload = Upload(
                    id=upload_id,
                    file_name=file_name,
                    file_size=file_size,
                    processing_status=ProcessingStatus.UPLOADING,
                )
                db.add(upload)
                db.commit()

                asyncio.run(process_upload(db, upload_id, file_path, user_mapping=user_mapping))
                st.session_state["current_upload_id"] = upload_id

            st.success("Processing complete! Head to Validation Results or Analytics in the sidebar.")
            st.balloons()

finally:
    db.close()
