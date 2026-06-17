import os
import streamlit as st

from database import SessionLocal
from models import Upload, ProcessingStatus


css_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets", "style.css")
with open(css_path) as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

st.markdown("""
<div class="section-header">
<div class="section-icon">&#8615;</div>
    <h2>Export Center</h2>
</div>
<p style="color:#64748B; margin-bottom:1.5rem; font-size:0.9rem;">
    Download the outputs generated for your processed dataset — cleaned file, error log, and summary report.
</p>
""", unsafe_allow_html=True)

db = SessionLocal()
try:
    if "current_upload_id" not in st.session_state:
        st.markdown("""
<div class="info-callout">
            No dataset selected. Please upload and process a file first to generate downloadable outputs.
</div>
        """, unsafe_allow_html=True)
        st.stop()

    upload_id = st.session_state["current_upload_id"]
    upload = db.query(Upload).filter(Upload.id == upload_id).first()

    if not upload or upload.processing_status != ProcessingStatus.COMPLETED:
        st.warning("Dataset processing is not complete. Please wait for it to finish.")
        st.stop()

    # Summary Bar
    st.markdown(f"""
<div class="card" style="margin-bottom:1.5rem;">
<div class="card-title">Current Dataset</div>
<div style="display:flex; align-items:center; gap:1.5rem; flex-wrap:wrap;">
<div>
<div class="kpi-label">File Name</div>
<div style="color:#1E293B; font-weight:600; font-size:0.95rem;">{upload.file_name}</div>
</div>
<div>
<div class="kpi-label">Total Records</div>
<div style="color:#4F46E5; font-weight:700; font-size:1.1rem;">{upload.total_rows:,}</div>
</div>
<div>
<div class="kpi-label">Valid Records</div>
<div style="color:#059669; font-weight:700; font-size:1.1rem;">{upload.valid_rows:,}</div>
</div>
<div>
<div class="kpi-label">Quality Score</div>
<div style="color:#D97706; font-weight:700; font-size:1.1rem;">{upload.quality_score:.0f}/100</div>
</div>
</div>
</div>
    """, unsafe_allow_html=True)

    # Visual File Chunking Module
    import math
    chunks = math.ceil(upload.total_rows / 50000) if upload.total_rows > 0 else 1
    file_size_display = f"{upload.file_size/1024:.1f} KB" if upload.file_size < 1024*1024 else f"{upload.file_size/1024/1024:.2f} MB"
    
    st.markdown(f"""
<div class="card" style="margin-bottom:1.5rem; display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:1rem;">
<div style="text-align:center;">
<div style="font-size:3rem;">📄</div>
<div style="font-weight:700;">Original File</div>
<div style="color:#4F46E5;">{file_size_display}</div>
</div>
<div style="font-size:2rem; color:#64748B;">&rarr; Split &rarr;</div>
<div style="text-align:center; background:rgba(79,70,229,0.05); border:1px solid rgba(79,70,229,0.15); border-radius:12px; padding:16px;">
<div style="font-size:1.5rem; margin-bottom:8px;">📦 Chunked Output</div>
<div style="display:flex; flex-direction:column; gap:4px; font-family:monospace; color:#4F46E5; font-size:0.9rem;">
{'<br>'.join([f"Chunk_{i+1}.csv" for i in range(min(chunks, 4))])}
{f"<br>... and {chunks-4} more" if chunks > 4 else ""}
</div>
</div>
<div style="text-align:center;">
<div class="kpi-label">Rows per chunk:</div>
<div style="font-size:1.5rem; font-weight:800; color:#34D399;">50,000</div>
</div>
</div>
    """, unsafe_allow_html=True)

    # Download Cards
    d1, d2, d3 = st.columns(3)

    with d1:
        st.markdown("""
<div class="card" style="text-align:center; min-height:200px;">
<div style="font-size:2.5rem; margin-bottom:12px;">&#9989;</div>
<div style="font-weight:700; color:#34D399; font-size:1.05rem; margin-bottom:8px;">Cleaned Dataset</div>
<div style="color:#64748B; font-size:0.82rem; margin-bottom:20px; line-height:1.5;">
                All validated and cleaned records. Invalid rows removed, data normalized.
</div>
</div>
        """, unsafe_allow_html=True)
        if upload.cleaned_file_path and os.path.exists(upload.cleaned_file_path):
            with open(upload.cleaned_file_path, "rb") as f:
                st.download_button(
                    "Download Cleaned CSV",
                    f, file_name="validated_transactions.csv",
                    mime="text/csv", use_container_width=True,
                )
        else:
            st.caption("File not generated.")

    with d2:
        st.markdown("""
<div class="card" style="text-align:center; min-height:200px;">
<div style="font-size:2.5rem; margin-bottom:12px;">&#128221;</div>
<div style="font-weight:700; color:#F87171; font-size:1.05rem; margin-bottom:8px;">Validation Errors Log</div>
<div style="color:#64748B; font-size:0.82rem; margin-bottom:20px; line-height:1.5;">
                All rows that failed validation with row number, column, and error message.
</div>
</div>
        """, unsafe_allow_html=True)
        if upload.error_file_path and os.path.exists(upload.error_file_path):
            with open(upload.error_file_path, "rb") as f:
                st.download_button(
                    "Download Error Log CSV",
                    f, file_name="validation_errors.csv",
                    mime="text/csv", use_container_width=True,
                )
        else:
            st.caption("File not generated.")

    with d3:
        st.markdown("""
<div class="card" style="text-align:center; min-height:200px;">
<div style="font-size:2.5rem; margin-bottom:12px;">&#128196;</div>
<div style="font-weight:700; color:#A5B4FC; font-size:1.05rem; margin-bottom:8px;">Summary Report</div>
<div style="color:#64748B; font-size:0.82rem; margin-bottom:20px; line-height:1.5;">
                Full PDF report with quality score, error breakdown, and AI-generated recommendations.
</div>
</div>
        """, unsafe_allow_html=True)
        if upload.report_file_path and os.path.exists(upload.report_file_path):
            with open(upload.report_file_path, "rb") as f:
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
