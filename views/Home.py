import os
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from sqlalchemy import func

from database import engine, Base, SessionLocal
from models import Upload, ProcessingStatus, ValidationError, ValidationRule
import models

# Init DB
Base.metadata.create_all(bind=engine)
models.Base.metadata.create_all(bind=engine)

css_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets", "style.css")
with open(css_path) as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# HERO
# ─────────────────────────────────────────────
st.markdown("""
<div class="hero-section">
    <div class="hero-title">Global Transaction Validation Platform</div>
    <div class="hero-subtitle">
        Validate, clean, process and export transaction datasets with enterprise-grade intelligence.
        Handles 1M+ rows, flags bad phone numbers, dates, SKUs, payments and more — automatically.
    </div>
    <div class="hero-badges">
        <span class="badge">✓ Phone Validation</span>
        <span class="badge">✓ Date Validation</span>
        <span class="badge">✓ SKU & Product Checks</span>
        <span class="badge">✓ Payment Mode Validation</span>
        <span class="badge">✓ CSV Chunking (50k/batch)</span>
        <span class="badge">✓ AI Chat Insights</span>
        <span class="badge">✓ PDF & CSV Exports</span>
    </div>
</div>
""", unsafe_allow_html=True)

db = SessionLocal()
try:
    # ─────────────────────────────────────────────
    # SECTION 1 — LIVE PLATFORM METRICS
    # ─────────────────────────────────────────────
    st.markdown("""
    <div class="section-header">
        <div class="section-icon">&#9632;</div>
        <h2>Live Platform Metrics</h2>
    </div>
    """, unsafe_allow_html=True)

    total_records   = db.query(func.coalesce(func.sum(Upload.total_rows), 0)).scalar()
    valid_records   = db.query(func.coalesce(func.sum(Upload.valid_rows), 0)).scalar()
    invalid_records = db.query(func.coalesce(func.sum(Upload.invalid_rows), 0)).scalar()
    total_files     = db.query(Upload).filter(Upload.processing_status == ProcessingStatus.COMPLETED).count()
    avg_score       = db.query(func.coalesce(func.avg(Upload.quality_score), 0)).filter(
                          Upload.processing_status == ProcessingStatus.COMPLETED).scalar()
    success_rate    = (valid_records / total_records * 100) if total_records > 0 else 0

    m1, m2, m3, m4, m5 = st.columns(5)
    m1.markdown(f"""<div class="kpi-card kpi-purple">
        <div class="kpi-label">Files Processed</div>
        <div class="kpi-value">{total_files}</div>
        <div class="kpi-sub">completed uploads</div>
    </div>""", unsafe_allow_html=True)
    m2.markdown(f"""<div class="kpi-card kpi-purple">
        <div class="kpi-label">Total Records</div>
        <div class="kpi-value">{int(total_records):,}</div>
        <div class="kpi-sub">rows ingested</div>
    </div>""", unsafe_allow_html=True)
    m3.markdown(f"""<div class="kpi-card kpi-green">
        <div class="kpi-label">Valid Records</div>
        <div class="kpi-value">{int(valid_records):,}</div>
        <div class="kpi-sub">{success_rate:.1f}% pass rate</div>
    </div>""", unsafe_allow_html=True)
    m4.markdown(f"""<div class="kpi-card kpi-red">
        <div class="kpi-label">Invalid Records</div>
        <div class="kpi-value">{int(invalid_records):,}</div>
        <div class="kpi-sub">{100-success_rate:.1f}% fail rate</div>
    </div>""", unsafe_allow_html=True)
    m5.markdown(f"""<div class="kpi-card kpi-yellow">
        <div class="kpi-label">Avg Quality Score</div>
        <div class="kpi-value">{avg_score:.0f}</div>
        <div class="kpi-sub">out of 100</div>
    </div>""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ─────────────────────────────────────────────
    # SECTION 2 — VALIDATION RULES ENGINE (always visible)
    # ─────────────────────────────────────────────
    st.markdown('<hr class="divider">', unsafe_allow_html=True)
    st.markdown("""
    <div class="section-header">
        <div class="section-icon">&#9998;</div>
        <h2>Validation Rules Engine</h2>
    </div>
    <p style="color:#64748B; font-size:0.88rem; margin-bottom:1.5rem;">
        These are the active rules applied to datasets dynamically.
    </p>
    """, unsafe_allow_html=True)

    r1, r2, r3 = st.columns(3)

    # Phone Rules from DB
    with r1:
        phone_rules = db.query(ValidationRule).filter(
            ValidationRule.is_active == True,
            ValidationRule.field_name == "phone"
        ).all()

        if phone_rules:
            rows = [{"Country": r.country_name, "Code": r.country_code, "Digits Required": r.rule_value} for r in phone_rules]
        else:
            # If no rules exist in the DB, show a message instead of hardcoding
            rows = [{"Info": "No active phone rules configured in Settings."}]

        st.markdown("""<div class="card">
            <div class="card-title">&#9742; Phone Number Rules</div>
            <p style="color:#64748B; font-size:0.8rem; margin-bottom:12px;">
                Configured phone validation rules from the database.
            </p>""", unsafe_allow_html=True)
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
        st.markdown('</div>', unsafe_allow_html=True)

    # Date Rules from code
    with r2:
        st.markdown("""<div class="card">
            <div class="card-title">&#128197; Date Validation Rules</div>
            <p style="color:#64748B; font-size:0.8rem; margin-bottom:12px;">
                Accepted date formats loaded directly from the validation engine.
            </p>""", unsafe_allow_html=True)
        
        from services.validators import DATE_FORMATS
        date_df = pd.DataFrame([{"Accepted Formats": fmt} for fmt in DATE_FORMATS[:5]])
        st.dataframe(date_df, use_container_width=True, hide_index=True)
        st.markdown('</div>', unsafe_allow_html=True)

    # Payment Rules from code
    with r3:
        st.markdown("""<div class="card">
            <div class="card-title">&#128179; Payment Modes</div>
            <p style="color:#64748B; font-size:0.8rem; margin-bottom:12px;">
                Allowed payment methods loaded directly from the validation engine.
            </p>""", unsafe_allow_html=True)
        
        from services.validators import VALID_PAYMENT_METHODS
        pm_df = pd.DataFrame([{"Payment Modes (Allowed)": pm.title()} for pm in VALID_PAYMENT_METHODS])
        st.dataframe(pm_df, use_container_width=True, hide_index=True)
        st.markdown('</div>', unsafe_allow_html=True)

    # ─────────────────────────────────────────────
    # SECTION 5 — LARGE FILE / CHUNKING
    # ─────────────────────────────────────────────
    st.markdown('<hr class="divider">', unsafe_allow_html=True)
    st.markdown("""
    <div class="section-header">
        <div class="section-icon">&#9889;</div>
        <h2>Large File Handling</h2>
    </div>
    """, unsafe_allow_html=True)

    ch1, ch2, ch3 = st.columns(3)
    ch1.markdown("""<div class="kpi-card kpi-green">
        <div class="kpi-label">Chunk Size</div>
        <div class="kpi-value" style="font-size:1.6rem;">50,000</div>
        <div class="kpi-sub">rows per processing batch</div>
    </div>""", unsafe_allow_html=True)
    ch2.markdown("""<div class="kpi-card kpi-purple">
        <div class="kpi-label">Max Supported Rows</div>
        <div class="kpi-value" style="font-size:1.6rem;">1M+</div>
        <div class="kpi-sub">no memory crashes</div>
    </div>""", unsafe_allow_html=True)
    ch3.markdown("""<div class="kpi-card kpi-yellow">
        <div class="kpi-label">Formats Supported</div>
        <div class="kpi-value" style="font-size:1.6rem;">CSV / XLS</div>
        <div class="kpi-sub">Excel and comma-separated</div>
    </div>""", unsafe_allow_html=True)

    # ─────────────────────────────────────────────
    # SECTION 6 — HOW TO USE (always visible)
    # ─────────────────────────────────────────────
    st.markdown('<hr class="divider">', unsafe_allow_html=True)
    st.markdown("""
    <div class="section-header">
        <div class="section-icon">&#9654;</div>
        <h2>How to Use</h2>
    </div>
    """, unsafe_allow_html=True)

    steps_html = """
    <div style="display:grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap:1rem; margin-bottom:1rem;">
        <div class="feature-card">
            <div class="feature-icon" style="background:linear-gradient(135deg,#6366F1,#4F46E5);">1</div>
            <div class="feature-title">Upload Dataset</div>
            <div class="feature-desc">Go to <strong>Upload Dataset</strong> in the sidebar. Drag & drop your CSV or Excel file. Map columns if needed.</div>
        </div>
        <div class="feature-card">
            <div class="feature-icon" style="background:linear-gradient(135deg,#10B981,#059669);">2</div>
            <div class="feature-title">Process & Validate</div>
            <div class="feature-desc">Click <strong>Process & Validate Dataset</strong>. The engine validates phones, dates, SKUs, payments automatically.</div>
        </div>
        <div class="feature-card">
            <div class="feature-icon" style="background:linear-gradient(135deg,#F59E0B,#D97706);">3</div>
            <div class="feature-title">Review Errors</div>
            <div class="feature-desc">Head to <strong>Validation Results</strong> to filter errors by column, severity (Critical/High/Medium/Low), and type.</div>
        </div>
        <div class="feature-card">
            <div class="feature-icon" style="background:linear-gradient(135deg,#8B5CF6,#7C3AED);">4</div>
            <div class="feature-title">Explore Analytics</div>
            <div class="feature-desc">Go to <strong>Analytics</strong> for 5 interactive Plotly charts — error breakdown, trends, column failures.</div>
        </div>
        <div class="feature-card">
            <div class="feature-icon" style="background:linear-gradient(135deg,#EC4899,#BE185D);">5</div>
            <div class="feature-title">Ask AI</div>
            <div class="feature-desc">Use <strong>AI Insights</strong> to chat with your data. Ask "Why did phones fail?" or "Summarize errors".</div>
        </div>
        <div class="feature-card">
            <div class="feature-icon" style="background:linear-gradient(135deg,#14B8A6,#0D9488);">6</div>
            <div class="feature-title">Export Reports</div>
            <div class="feature-desc">Go to <strong>Downloads</strong> to get your cleaned CSV, error log, and PDF validation summary report.</div>
        </div>
    </div>
    """
    st.markdown(steps_html, unsafe_allow_html=True)

    # ─────────────────────────────────────────────
    # SECTION 7 — RECENT ACTIVITY (if any)
    # ─────────────────────────────────────────────
    if total_files > 0:
        st.markdown('<hr class="divider">', unsafe_allow_html=True)
        st.markdown("""
        <div class="section-header">
            <div class="section-icon">&#128198;</div>
            <h2>Recent Activity</h2>
        </div>
        """, unsafe_allow_html=True)

        st.markdown('<div class="card">', unsafe_allow_html=True)
        uploads = db.query(Upload).order_by(Upload.created_at.desc()).limit(8).all()
        df = pd.DataFrame([{
            "Date": u.created_at.strftime("%Y-%m-%d %H:%M"),
            "File Name": u.file_name,
            "Total Rows": f"{u.total_rows:,}",
            "Valid": f"{u.valid_rows:,}",
            "Invalid": f"{u.invalid_rows:,}",
            "Quality Score": f"{u.quality_score:.0f}/100",
            "Status": u.processing_status.value,
        } for u in uploads])
        st.dataframe(df, use_container_width=True, hide_index=True)
        st.markdown('</div>', unsafe_allow_html=True)

finally:
    db.close()
