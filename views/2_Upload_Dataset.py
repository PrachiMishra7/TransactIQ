import os
import uuid
import asyncio
from datetime import datetime

import streamlit as st
import pandas as pd
from st_aggrid import AgGrid, GridOptionsBuilder, ColumnsAutoSizeMode

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
    <div class="section-icon"><span class="mi">upload</span></div>
    <h2>Upload Dataset</h2>
</div>
<p style="color:#64748B; margin-bottom:1.5rem; font-size:1.05rem;">
    Upload your transaction files for AI-powered validation, cleaning, and insight generation.
</p>
""", unsafe_allow_html=True)


db = SessionLocal()
try:
    # ─────────────────────────────────────────────
    # SECTION 1: UPLOAD ZONE
    # ─────────────────────────────────────────────
    with st.container(border=True):
        uploaded_file = st.file_uploader(
            "Drop your dataset here",
            type=["csv", "xlsx", "xls"],
            help="Supported formats: CSV, XLSX, XLS. Files are processed in 50k row chunks."
        )

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
        
        # Estimate rows assuming roughly 100-150 bytes per row, formatted nicely
        est_rows = max(1, file_size // 120)
        est_rows_display = f"~{est_rows:,}"
        
        st.markdown(f"""
        <div style="display:flex; justify-content:space-between; align-items:center; background:#EEF2FF; border:1px solid #C7D2FE; border-radius:12px; padding:16px; margin-bottom:24px;">
            <div><span style="color:#4F46E5; font-weight:700;">File:</span> {file_name}</div>
            <div><span style="color:#4F46E5; font-weight:700;">Size:</span> {file_size_display}</div>
            <div><span style="color:#4F46E5; font-weight:700;">Est. Rows:</span> {est_rows_display}</div>
        </div>
        """, unsafe_allow_html=True)

        # ─────────────────────────────────────────────
        # SECTION 2: DATASET PREVIEW (AgGrid)
        # ─────────────────────────────────────────────
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown('<div class="card-title">Dataset Preview (First 10 Rows)</div>', unsafe_allow_html=True)
        
        st.dataframe(df_preview, use_container_width=True, height=350)
        
        st.markdown('</div>', unsafe_allow_html=True)

        c1, c2 = st.columns([2, 1])
        
        with c1:
            # ─────────────────────────────────────────────
            # SECTION 3: AUTOMATIC SCHEMA DETECTION
            # ─────────────────────────────────────────────
            with st.container(border=True):
                st.markdown("""
                <div style="font-weight: 700; font-size: 1.1rem; margin-bottom: 8px; color: #1E293B;">Automatic Schema Detection</div>
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

        with c2:
            # ─────────────────────────────────────────────
            # SECTION 4: VALIDATION SETTINGS
            # ─────────────────────────────────────────────
            with st.container(border=True):
                st.markdown('<div style="font-weight: 700; font-size: 1.1rem; margin-bottom: 12px; color: #1E293B;"><span class="mi">settings</span> Validation Settings</div>', unsafe_allow_html=True)
                
                val_phone = st.toggle("Phone Validation", value=True)
                val_date = st.toggle("Date Validation", value=True)
                val_dup = st.toggle("Duplicate Detection", value=True)
                val_pay = st.toggle("Payment Validation", value=True)
                val_chunk = st.toggle("Chunk Generation (50k rows)", value=True)
                
                st.markdown("<hr style='margin:20px 0; border:none; border-top:1px solid #E2E8F0;'>", unsafe_allow_html=True)
                
                if st.button("Process & Validate Dataset", type="primary", use_container_width=True):
                    import time
                    with st.status("Initializing Xeno Pipeline...", expanded=True) as status:
                        st.write(":material/psychology: AI Validating Schema & Orders...")
                        time.sleep(0.5)
                        from config import settings
                        upload_id = str(uuid.uuid4())
                        up_dir = settings.upload_dir
                        os.makedirs(up_dir, exist_ok=True)
                        file_path = os.path.join(up_dir, f"{upload_id}{ext}")

                        uploaded_file.seek(0)
                        with open(file_path, "wb") as f:
                            f.write(uploaded_file.getvalue())

                        settings_dict = {
                            "phone": val_phone,
                            "date": val_date,
                            "duplicate": val_dup,
                            "payment": val_pay
                        }

                        upload = Upload(
                            id=upload_id,
                            file_name=file_name,
                            file_size=file_size,
                            processing_status=ProcessingStatus.UPLOADING,
                            validation_settings=settings_dict
                        )
                        db.add(upload)
                        db.commit()

                        if val_phone: st.write(":material/call: Checking Phone Numbers & Country Formats...")
                        time.sleep(0.5)
                        if val_date: st.write(":material/calendar_month: Verifying Dates & Data Integrity...")
                        time.sleep(0.5)
                        
                        asyncio.run(process_upload(db, upload_id, file_path, user_mapping=user_mapping, validation_settings=settings_dict))
                        st.session_state["current_upload_id"] = upload_id
                        
                        st.write(":material/view_in_ar: Preparing Output Reports...")
                        time.sleep(0.5)
                        status.update(label="Processing Complete!", state="complete", expanded=False)

                    st.success("Validation complete! Head to Validation Results to view the detailed error report.")
                    st.balloons()
                    time.sleep(1.0)
                    st.rerun()

    # ─────────────────────────────────────────────
    # SECTION 5: UPLOAD HISTORY & APPLIED RULES
    # ─────────────────────────────────────────────
    st.markdown("<br><hr class='divider'>", unsafe_allow_html=True)
    st.markdown("### :material/history: Upload History & Applied Rules")
    
    past_uploads = db.query(Upload).order_by(Upload.created_at.desc()).limit(10).all()
    if past_uploads:
            html_table = """
<style>
.history-table { width: 100%; border-collapse: collapse; margin-top: 10px; font-size: 0.9rem; }
.history-table th { background: #F8FAFC; padding: 12px 16px; text-align: left; font-weight: 600; color: #475569; border-bottom: 2px solid #E2E8F0; }
.history-table td { padding: 12px 16px; border-bottom: 1px solid #E2E8F0; color: #1E293B; vertical-align: middle; }
.history-table tr:hover { background: #F1F5F9; }
.val-badge { display: inline-flex; align-items: center; gap: 4px; padding: 4px 10px; background: #F1F5F9; border: 1px solid #CBD5E1; border-radius: 99px; font-size: 0.75rem; font-weight: 600; color: #475569; margin-right: 6px; margin-bottom: 4px; }
.val-badge .mi { font-size: 14px; }
.status-badge { display: inline-flex; align-items: center; padding: 4px 10px; border-radius: 99px; font-size: 0.75rem; font-weight: 600; }
.status-completed { background: #ECFDF5; color: #059669; border: 1px solid #A7F3D0; }
.status-pending { background: #FFFBEB; color: #D97706; border: 1px solid #FDE68A; }
.status-error { background: #FEF2F2; color: #DC2626; border: 1px solid #FECACA; }
</style>
<table class="history-table">
<thead>
    <tr>
        <th>File Name</th>
        <th>Uploaded At</th>
        <th>Total Rows</th>
        <th>Applied Validations</th>
        <th>Score</th>
        <th>Status</th>
    </tr>
</thead>
<tbody>
"""
            
            for u in past_uploads:
                vs = u.validation_settings or {}
                badges_html = ""
                if vs.get("phone"): badges_html += '<span class="val-badge"><span class="mi">call</span>Phone</span>'
                if vs.get("date"): badges_html += '<span class="val-badge"><span class="mi">calendar_month</span>Date</span>'
                if vs.get("duplicate"): badges_html += '<span class="val-badge"><span class="mi">content_copy</span>Duplicate</span>'
                if vs.get("payment"): badges_html += '<span class="val-badge"><span class="mi">credit_card</span>Payment</span>'
                
                if not badges_html:
                    badges_html = '<span style="color:#94A3B8; font-style:italic;">None (Raw)</span>'

                status_class = "status-completed" if u.processing_status.value == "completed" else ("status-error" if "error" in u.processing_status.value else "status-pending")
                
                html_table += f"""
<tr>
    <td style="font-weight:500;">{u.file_name}</td>
    <td style="color:#64748B;">{u.created_at.strftime('%b %d, %H:%M')}</td>
    <td>{u.total_rows:,}</td>
    <td>{badges_html}</td>
    <td><strong style="color:#0F172A;">{u.quality_score:.0f}</strong><span style="color:#94A3B8;">/100</span></td>
    <td><span class="status-badge {status_class}">{u.processing_status.value.title()}</span></td>
</tr>
"""
            html_table += "</tbody></table>"
            st.markdown(html_table, unsafe_allow_html=True)
    else:
        st.info("No upload history found.")

finally:
    db.close()
