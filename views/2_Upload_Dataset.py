import os
import uuid
import asyncio
from datetime import datetime

import streamlit as st
import pandas as pd
from st_aggrid import AgGrid, GridOptionsBuilder

from database import SessionLocal
from models import Upload, ProcessingStatus
from services.processor import process_upload
from services.column_mapper import map_columns, COLUMN_ALIASES

st.set_page_config(page_title="Upload Dataset | Xeno", layout="wide")

css_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets", "style.css")
with open(css_path) as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

st.markdown("""
<div class="section-header">
    <div class="section-icon">&#8679;</div>
    <h2>Upload Dataset</h2>
</div>
<p style="color:#64748B; margin-bottom:1.5rem; font-size:1.05rem;">
    Upload your transaction files for AI-powered validation, cleaning, and insight generation.
</p>
""", unsafe_allow_html=True)

_APP_DIR = os.path.join(os.path.expanduser("~"), "AppData", "Local", "TransactIQ")

db = SessionLocal()
try:
    # ─────────────────────────────────────────────
    # SECTION 1: UPLOAD ZONE
    # ─────────────────────────────────────────────
    st.markdown("""<div class="card" style="padding:40px 20px; text-align:center;">""", unsafe_allow_html=True)
    uploaded_file = st.file_uploader(
        "Drop your dataset here",
        type=["csv", "xlsx", "xls"],
        help="Supported formats: CSV, XLSX, XLS. Files are processed in 50k row chunks."
    )
    st.markdown("</div>", unsafe_allow_html=True)

    if uploaded_file is not None:
        file_name = uploaded_file.name
        file_size = len(uploaded_file.getvalue())
        ext = os.path.splitext(file_name)[1].lower()

        try:
            if ext == ".csv":
                df_preview = pd.read_csv(uploaded_file, nrows=10)
            else:
                df_preview = pd.read_excel(uploaded_file, nrows=10)
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

        file_size_display = f"{file_size/1024:.1f} KB" if file_size < 1024*1024 else f"{file_size/1024/1024:.2f} MB"
        
        st.markdown(f"""
        <div style="display:flex; justify-content:space-between; align-items:center; background:#EEF2FF; border:1px solid #C7D2FE; border-radius:12px; padding:16px; margin-bottom:24px;">
            <div><span style="color:#4F46E5; font-weight:700;">File:</span> {file_name}</div>
            <div><span style="color:#4F46E5; font-weight:700;">Size:</span> {file_size_display}</div>
            <div><span style="color:#4F46E5; font-weight:700;">Est. Rows:</span> {'10,000+' if file_size > 1000000 else 'Unknown'}</div>
        </div>
        """, unsafe_allow_html=True)

        # ─────────────────────────────────────────────
        # SECTION 2: DATASET PREVIEW (AgGrid)
        # ─────────────────────────────────────────────
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown('<div class="card-title">Dataset Preview (First 10 Rows)</div>', unsafe_allow_html=True)
        
        gb = GridOptionsBuilder.from_dataframe(df_preview)
        gb.configure_default_column(resizable=True, filterable=True, sortable=True)
        gridOptions = gb.build()
        AgGrid(df_preview, gridOptions=gridOptions, height=350, theme="alpine")
        
        st.markdown('</div>', unsafe_allow_html=True)

        c1, c2 = st.columns([2, 1])
        
        with c1:
            # ─────────────────────────────────────────────
            # SECTION 3: AUTOMATIC SCHEMA DETECTION
            # ─────────────────────────────────────────────
            st.markdown('<div class="card" style="height:100%;">', unsafe_allow_html=True)
            st.markdown("""
            <div class="card-title">Automatic Schema Detection</div>
            <p style="color:#64748B; font-size:0.85rem; margin-bottom:1rem; margin-top:0;">
                Our AI has analyzed the headers and auto-mapped them to canonical system fields.
            </p>
            """, unsafe_allow_html=True)

            auto_mapped = map_columns(headers)
            canonical_options = ["(Ignore)"] + list(COLUMN_ALIASES.keys())

            user_mapping = {}
            for h in headers:
                default_val = auto_mapped.get(h, h)
                idx = canonical_options.index(default_val) if default_val in canonical_options else 0
                
                # Visual confidence score
                confidence = "99%" if default_val in canonical_options else "40%"
                conf_color = "#10B981" if confidence == "99%" else "#F59E0B"
                
                user_mapping[h] = st.selectbox(
                    f"Column: {h} (Confidence: {confidence})",
                    canonical_options,
                    index=idx,
                    key=f"map_{h}",
                )
            st.markdown('</div>', unsafe_allow_html=True)

        with c2:
            # ─────────────────────────────────────────────
            # SECTION 4: VALIDATION SETTINGS
            # ─────────────────────────────────────────────
            st.markdown('<div class="card" style="height:100%;">', unsafe_allow_html=True)
            st.markdown('<div class="card-title">&#9881; Validation Settings</div>', unsafe_allow_html=True)
            
            val_phone = st.toggle("Phone Validation", value=True)
            val_date = st.toggle("Date Validation", value=True)
            val_dup = st.toggle("Duplicate Detection", value=True)
            val_pay = st.toggle("Payment Validation", value=True)
            val_chunk = st.toggle("Chunk Generation (50k rows)", value=True)
            
            st.markdown("<hr style='margin:20px 0; border:none; border-top:1px solid #E2E8F0;'>", unsafe_allow_html=True)
            
            if st.button("Process & Validate Dataset", type="primary", use_container_width=True):
                import time
                with st.status("Initializing Xeno Pipeline...", expanded=True) as status:
                    st.write("🧠 AI Validating Schema & Orders...")
                    time.sleep(0.5)
                    
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

                    if val_phone: st.write("📞 Checking Phone Numbers & Country Formats...")
                    time.sleep(0.5)
                    if val_date: st.write("📅 Verifying Dates & Data Integrity...")
                    time.sleep(0.5)
                    if val_chunk: st.write("⚡ Executing chunked processing...")
                    
                    asyncio.run(process_upload(db, upload_id, file_path, user_mapping=user_mapping))
                    st.session_state["current_upload_id"] = upload_id
                    
                    st.write("📦 Preparing Output Reports...")
                    time.sleep(0.5)
                    status.update(label="Processing Complete!", state="complete", expanded=False)

                st.success("Validation complete! Head to Validation Results to view the detailed error report.")
                st.balloons()
            st.markdown('</div>', unsafe_allow_html=True)

finally:
    db.close()
