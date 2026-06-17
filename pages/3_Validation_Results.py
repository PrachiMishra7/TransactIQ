import os
import streamlit as st
import pandas as pd
from collections import Counter

from database import SessionLocal
from models import Upload, ProcessingStatus, ValidationError, Severity

st.set_page_config(page_title="Validation Results | TransactIQ", layout="wide")

css_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets", "style.css")
with open(css_path) as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

st.markdown("""
<div class="section-header">
    <div class="section-icon">&#9998;</div>
    <h2>Validation Results</h2>
</div>
""", unsafe_allow_html=True)

db = SessionLocal()
try:
    if "current_upload_id" not in st.session_state:
        st.markdown("""
        <div class="info-callout">
            No dataset selected. Please upload a file from the <strong>Upload Dataset</strong> page first.
        </div>
        """, unsafe_allow_html=True)
        st.stop()

    upload_id = st.session_state["current_upload_id"]
    upload = db.query(Upload).filter(Upload.id == upload_id).first()

    if not upload:
        st.error("Upload record not found.")
        st.stop()

    if upload.processing_status != ProcessingStatus.COMPLETED:
        st.warning(f"Processing status: **{upload.processing_status.value}**. Please wait for completion.")
        st.stop()

    # Summary Banner
    success_rate = (upload.valid_rows / upload.total_rows * 100) if upload.total_rows > 0 else 0
    score_color = "#34D399" if upload.quality_score >= 80 else "#FCD34D" if upload.quality_score >= 60 else "#F87171"

    c1, c2, c3, c4 = st.columns(4)
    c1.markdown(f"""<div class="kpi-card kpi-purple">
        <div class="kpi-label">File</div>
        <div style="color:#E2E8F0; font-size:0.95rem; font-weight:700; margin-top:6px;">{upload.file_name[:20]}…</div>
    </div>""", unsafe_allow_html=True)
    c2.markdown(f"""<div class="kpi-card kpi-green">
        <div class="kpi-label">Valid Rows</div>
        <div class="kpi-value">{upload.valid_rows:,}</div>
        <div class="kpi-sub">{success_rate:.1f}% pass rate</div>
    </div>""", unsafe_allow_html=True)
    c3.markdown(f"""<div class="kpi-card kpi-red">
        <div class="kpi-label">Invalid Rows</div>
        <div class="kpi-value">{upload.invalid_rows:,}</div>
        <div class="kpi-sub">{100-success_rate:.1f}% fail rate</div>
    </div>""", unsafe_allow_html=True)
    c4.markdown(f"""<div class="kpi-card" style="background:linear-gradient(145deg,#1E293B,#162032);border:1px solid rgba(255,255,255,0.07);border-radius:18px;padding:24px 20px;">
        <div class="kpi-label">Quality Score</div>
        <div class="kpi-value" style="color:{score_color};">{upload.quality_score:.0f}</div>
        <div class="kpi-sub">out of 100</div>
    </div>""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # Fetch errors
    errors = db.query(ValidationError).filter(ValidationError.upload_id == upload_id).all()

    if not errors:
        st.markdown("""
        <div class="card" style="text-align:center; padding:48px;">
            <div style="font-size:3rem; margin-bottom:16px;">&#10003;</div>
            <div style="font-size:1.2rem; font-weight:700; color:#34D399; margin-bottom:8px;">All Records Passed Validation</div>
            <div style="color:#64748B;">Your dataset is clean. No errors were detected.</div>
        </div>
        """, unsafe_allow_html=True)
    else:
        # Error summary by type
        type_counts = Counter(e.error_type for e in errors)
        col_counts  = Counter(e.column_name for e in errors)
        sev_counts  = Counter(e.severity.value for e in errors)

        # Summary tiles
        st.markdown('<div class="card"><div class="card-title">Error Summary by Severity</div>', unsafe_allow_html=True)
        sc1, sc2, sc3, sc4 = st.columns(4)
        sc1.markdown(f"""<div style="background:rgba(239,68,68,0.1);border:1px solid rgba(239,68,68,0.25);border-radius:12px;padding:16px;text-align:center;">
            <div class="kpi-label" style="color:#F87171;">Critical</div>
            <div style="font-size:1.8rem;font-weight:800;color:#F87171;">{sev_counts.get('CRITICAL',0)}</div>
        </div>""", unsafe_allow_html=True)
        sc2.markdown(f"""<div style="background:rgba(239,68,68,0.08);border:1px solid rgba(239,68,68,0.2);border-radius:12px;padding:16px;text-align:center;">
            <div class="kpi-label" style="color:#F87171;">High</div>
            <div style="font-size:1.8rem;font-weight:800;color:#F87171;">{sev_counts.get('HIGH',0)}</div>
        </div>""", unsafe_allow_html=True)
        sc3.markdown(f"""<div style="background:rgba(245,158,11,0.08);border:1px solid rgba(245,158,11,0.2);border-radius:12px;padding:16px;text-align:center;">
            <div class="kpi-label" style="color:#FCD34D;">Medium</div>
            <div style="font-size:1.8rem;font-weight:800;color:#FCD34D;">{sev_counts.get('MEDIUM',0)}</div>
        </div>""", unsafe_allow_html=True)
        sc4.markdown(f"""<div style="background:rgba(99,102,241,0.08);border:1px solid rgba(99,102,241,0.2);border-radius:12px;padding:16px;text-align:center;">
            <div class="kpi-label" style="color:#818CF8;">Low</div>
            <div style="font-size:1.8rem;font-weight:800;color:#818CF8;">{sev_counts.get('LOW',0)}</div>
        </div>""", unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

        # Filters
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown('<div class="card-title">Error Table</div>', unsafe_allow_html=True)

        f1, f2, f3 = st.columns(3)
        with f1:
            filter_col = st.selectbox("Filter by Column", ["All"] + list(col_counts.keys()))
        with f2:
            filter_type = st.selectbox("Filter by Error Type", ["All"] + list(type_counts.keys()))
        with f3:
            filter_sev = st.selectbox("Filter by Severity", ["All", "CRITICAL", "HIGH", "MEDIUM", "LOW"])

        filtered = errors
        if filter_col != "All":
            filtered = [e for e in filtered if e.column_name == filter_col]
        if filter_type != "All":
            filtered = [e for e in filtered if e.error_type == filter_type]
        if filter_sev != "All":
            filtered = [e for e in filtered if e.severity.value == filter_sev]

        if filtered:
            sev_color = {"CRITICAL": "🔴", "HIGH": "🟠", "MEDIUM": "🟡", "LOW": "🔵"}
            df_err = pd.DataFrame([{
                "Sev": sev_color.get(e.severity.value, "⚪"),
                "Row": e.row_number,
                "Column": e.column_name,
                "Error Type": e.error_type.replace("_", " ").title(),
                "Message": e.error_message,
            } for e in filtered[:500]])
            st.dataframe(df_err, use_container_width=True, hide_index=True)
            if len(filtered) > 500:
                st.caption(f"Showing first 500 of {len(filtered)} errors. Download the full error file from the Downloads page.")
        else:
            st.info("No errors match your filters.")
        st.markdown('</div>', unsafe_allow_html=True)

finally:
    db.close()
