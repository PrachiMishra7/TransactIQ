import os
import streamlit as st

from database import SessionLocal
from models import Upload, ProcessingStatus


css_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets", "style.css")
with open(css_path) as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

st.markdown("""
<div class="section-header">
<div class="section-icon"><span class="mi">download</span></div>
    <h2>Export Center</h2>
</div>
<p style="color:#64748B; margin-bottom:1.5rem; font-size:0.9rem;">
    Download the outputs generated for your processed dataset — cleaned file, error log, and summary report.
</p>
""", unsafe_allow_html=True)

db = SessionLocal()
try:
db = SessionLocal()
try:
    upload_id = st.session_state.get("current_upload_id")
    upload = db.query(Upload).filter(Upload.id == upload_id).first() if upload_id else None

    if not upload:
        st.warning("⚠️ No active dataset selected. Showing layout template. Please upload and process a dataset on the 'Upload Dataset' page to generate downloads.")
        
        file_name = "No Active File"
        total_rows = 0
        valid_rows = 0
        quality_score = 0.0
        file_size = 0
        invalid_rows = 0
        cleaned_file_path = None
        error_file_path = None
        report_file_path = None
    else:
        if upload.processing_status != ProcessingStatus.COMPLETED:
            st.warning("Dataset processing is not complete. Please wait for it to finish.")
            st.stop()
            
        file_name = upload.file_name
        total_rows = upload.total_rows
        valid_rows = upload.valid_rows
        quality_score = upload.quality_score
        file_size = upload.file_size
        invalid_rows = upload.invalid_rows
        cleaned_file_path = upload.cleaned_file_path
        error_file_path = upload.error_file_path
        report_file_path = upload.report_file_path

    # Summary Bar
    st.markdown(f"""
<div class="card" style="margin-bottom:1.5rem;">
<div class="card-title">Current Dataset</div>
<div style="display:flex; align-items:center; gap:1.5rem; flex-wrap:wrap;">
<div>
<div class="kpi-label">File Name</div>
<div style="color:#1E293B; font-weight:600; font-size:0.95rem;">{file_name}</div>
</div>
<div>
<div class="kpi-label">Total Rows</div>
<div style="color:#4F46E5; font-weight:700; font-size:1.1rem;">{total_rows:,}</div>
</div>
<div>
<div class="kpi-label">Valid Rows</div>
<div style="color:#059669; font-weight:700; font-size:1.1rem;">{valid_rows:,}</div>
</div>
<div>
<div class="kpi-label">Quality Score</div>
<div style="color:#D97706; font-weight:700; font-size:1.1rem;">{quality_score:.0f}/100</div>
</div>
</div>
</div>
    """, unsafe_allow_html=True)

    # Visual File Info / Chunking Module
    import math
    CHUNK_SIZE = 50_000
    file_size_display = f"{file_size/1024:.1f} KB" if file_size < 1024*1024 else f"{file_size/1024/1024:.2f} MB"

    if total_rows > CHUNK_SIZE:
        chunks = math.ceil(total_rows / CHUNK_SIZE)
        st.markdown(f"""
<div class="card" style="margin-bottom:1.5rem; display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:1rem;">
<div style="text-align:center;">
<div style="font-size:3rem; display:flex; justify-content:center;"><span class="mi" style="font-size:3rem;">description</span></div>
<div style="font-weight:700;">Original File</div>
<div style="color:#4F46E5;">{file_size_display} &bull; {total_rows:,} rows</div>
</div>
<div style="font-size:2rem; color:#64748B;">&rarr; Split &rarr;</div>
<div style="text-align:center; background:rgba(79,70,229,0.05); border:1px solid rgba(79,70,229,0.15); border-radius:12px; padding:16px;">
<div style="font-size:1.5rem; margin-bottom:8px; display:flex; align-items:center; justify-content:center; gap:8px;"><span class="mi" style="font-size:1.5rem;">view_in_ar</span> Chunked Output</div>
<div style="display:flex; flex-direction:column; gap:4px; font-family:monospace; color:#4F46E5; font-size:0.9rem;">
{'<br>'.join([f"Chunk_{i+1}.csv" for i in range(min(chunks, 4))])}
{f"<br>... and {chunks-4} more" if chunks > 4 else ""}
</div>
</div>
<div style="text-align:center;">
<div class="kpi-label">Rows per chunk:</div>
<div style="font-size:1.5rem; font-weight:800; color:#34D399;">{CHUNK_SIZE:,}</div>
</div>
</div>
    """, unsafe_allow_html=True)
    else:
        st.markdown(f"""
<div class="card" style="margin-bottom:1.5rem; display:flex; align-items:center; gap:2rem; flex-wrap:wrap;">
<div style="display:flex; justify-content:center;"><span class="mi" style="font-size:3rem; color:#4F46E5;">description</span></div>
<div>
<div style="font-weight:700; font-size:1.05rem;">{file_name}</div>
<div style="color:#64748B; font-size:0.9rem; margin-top:4px;">{file_size_display} &bull; {total_rows:,} total rows &bull; {valid_rows:,} valid &bull; {invalid_rows:,} invalid</div>
<div style="margin-top:8px; display:flex; gap:8px;">
<span style="background:#DCFCE7; color:#16A34A; padding:3px 10px; border-radius:20px; font-size:0.8rem; font-weight:600;">{valid_rows} valid rows ready to download</span>
<span style="background:#FEE2E2; color:#DC2626; padding:3px 10px; border-radius:20px; font-size:0.8rem; font-weight:600;">{invalid_rows} error rows logged</span>
</div>
</div>
</div>
    """, unsafe_allow_html=True)

    # Download Cards
    d1, d2, d3 = st.columns(3)

    with d1:
        st.markdown("""
<div class="card" style="text-align:center; min-height:200px;">
<div style="font-size:2.5rem; margin-bottom:12px; color:#34D399; display:flex; justify-content:center;"><span class="mi" style="font-size:2.5rem;">check_circle</span></div>
<div style="font-weight:700; color:#34D399; font-size:1.05rem; margin-bottom:8px;">Cleaned Dataset</div>
<div style="color:#64748B; font-size:0.82rem; margin-bottom:20px; line-height:1.5;">
                All validated and cleaned records. Invalid rows removed, data normalized.
</div>
</div>
        """, unsafe_allow_html=True)
        excel_path = cleaned_file_path.replace(".csv", ".xlsx") if cleaned_file_path else None
        if excel_path and os.path.exists(excel_path):
            with open(excel_path, "rb") as f:
                st.download_button(
                    "Download Cleaned Excel",
                    f, file_name="validated_transactions.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", use_container_width=True,
                )
        elif cleaned_file_path and os.path.exists(cleaned_file_path):
            with open(cleaned_file_path, "rb") as f:
                st.download_button(
                    "Download Cleaned CSV (Old)",
                    f, file_name="validated_transactions.csv",
                    mime="text/csv", use_container_width=True,
                )
        else:
            st.caption("File not generated.")

    with d2:
        st.markdown("""
<div class="card" style="text-align:center; min-height:200px;">
<div style="font-size:2.5rem; margin-bottom:12px; color:#F87171; display:flex; justify-content:center;"><span class="mi" style="font-size:2.5rem;">edit_note</span></div>
<div style="font-weight:700; color:#F87171; font-size:1.05rem; margin-bottom:8px;">Validation Errors Log</div>
<div style="color:#64748B; font-size:0.82rem; margin-bottom:20px; line-height:1.5;">
                All rows that failed validation with row number, column, and error message.
</div>
</div>
        """, unsafe_allow_html=True)
        err_excel_path = error_file_path.replace(".csv", ".xlsx") if error_file_path else None
        if err_excel_path and os.path.exists(err_excel_path):
            with open(err_excel_path, "rb") as f:
                st.download_button(
                    "Download Error Log (Excel)",
                    f, file_name="validation_errors.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", use_container_width=True,
                )
        elif error_file_path and os.path.exists(error_file_path):
            with open(error_file_path, "rb") as f:
                st.download_button(
                    "Download Error Log (CSV)",
                    f, file_name="validation_errors.csv",
                    mime="text/csv", use_container_width=True,
                )
        else:
            st.caption("File not generated.")

    with d3:
        st.markdown("""
<div class="card" style="text-align:center; min-height:200px;">
<div style="font-size:2.5rem; margin-bottom:12px; color:#A5B4FC; display:flex; justify-content:center;"><span class="mi" style="font-size:2.5rem;">description</span></div>
<div style="font-weight:700; color:#A5B4FC; font-size:1.05rem; margin-bottom:8px;">Summary Report</div>
<div style="color:#64748B; font-size:0.82rem; margin-bottom:20px; line-height:1.5;">
                Full PDF report with quality score, error breakdown, and AI-generated recommendations.
</div>
</div>
        """, unsafe_allow_html=True)
        if report_file_path and os.path.exists(report_file_path):
            with open(report_file_path, "rb") as f:
                st.download_button(
                    "Download Summary PDF",
                    f, file_name="summary_report.pdf",
                    mime="application/pdf", use_container_width=True,
                )
        else:
            st.caption("File not generated.")

    # Previous Uploads
    st.markdown('<hr class="divider">', unsafe_allow_html=True)
    st.markdown("### Previous Uploads")
    all_uploads = db.query(Upload).filter(
        Upload.processing_status == ProcessingStatus.COMPLETED,
        Upload.id != upload_id
    ).order_by(Upload.created_at.desc()).limit(5).all()

    if all_uploads:
        for u in all_uploads:
            if st.button(f"Load: {u.file_name}  ({u.created_at.strftime('%b %d, %H:%M')})  —  Score: {u.quality_score:.0f}/100", key=f"load_{u.id}"):
                st.session_state["current_upload_id"] = u.id
                st.rerun()
    else:
        st.caption("No other completed uploads found.")

finally:
    db.close()
