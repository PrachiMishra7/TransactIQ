import os
import streamlit as st
import pandas as pd
from sqlalchemy import func

from database import engine, Base, SessionLocal
from models import Upload, ProcessingStatus, ValidationRule
import models

# Init DB
Base.metadata.create_all(bind=engine)
models.Base.metadata.create_all(bind=engine)

css_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets", "style.css")
with open(css_path) as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# HERO SECTION (Compact)
# ─────────────────────────────────────────────
st.markdown("""
<div class="hero-section" style="padding: 32px 40px; margin-bottom: 1.5rem; background: linear-gradient(135deg, #FFFFFF 0%, #EEF2FF 100%); position: relative; overflow: hidden; border: 1px solid #E2E8F0; box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.05); border-radius: 20px;">
<div style="position:absolute; top:-50%; left:-10%; width:50%; height:200%; background:radial-gradient(ellipse at center, rgba(99, 102, 241, 0.1) 0%, transparent 70%); transform:rotate(-45deg);"></div>
<div style="position:absolute; bottom:-50%; right:-10%; width:50%; height:200%; background:radial-gradient(ellipse at center, rgba(16, 185, 129, 0.05) 0%, transparent 70%); transform:rotate(-45deg);"></div>
<div style="position:relative; z-index:1;">
<div class="hero-title" style="font-size:2.2rem; font-weight:800; background: -webkit-linear-gradient(45deg, #1E293B, #4F46E5); -webkit-background-clip: text; -webkit-text-fill-color: transparent; margin-bottom:0.5rem;">Xeno Data Quality & Transaction Intelligence Platform</div>
<div class="hero-subtitle" style="font-size:1.05rem; color:#475569; max-width:800px; margin: 0 0 1.2rem 0;">
Validate, Clean, Analyze and Process Global Transaction Data
</div>
</div>
</div>
""", unsafe_allow_html=True)

h_col1, h_col2, _ = st.columns([1, 1, 3])
with h_col1:
    st.page_link("views/2_Upload_Dataset.py", label="**Upload Dataset**", icon=":material/upload:", use_container_width=True)
with h_col2:
    st.page_link("views/6_Downloads.py", label="**View Sample Dataset**", icon=":material/description:", use_container_width=True)

st.markdown("<br>", unsafe_allow_html=True)

db = SessionLocal()
try:
    # ─────────────────────────────────────────────
    # SECTION 2 — PLATFORM HEALTH DASHBOARD
    # ─────────────────────────────────────────────
    total_records   = db.query(func.coalesce(func.sum(Upload.total_rows), 0)).scalar()
    valid_records   = db.query(func.coalesce(func.sum(Upload.valid_rows), 0)).scalar()
    invalid_records = db.query(func.coalesce(func.sum(Upload.invalid_rows), 0)).scalar()
    avg_score       = db.query(func.coalesce(func.avg(Upload.quality_score), 0)).filter(
                          Upload.processing_status == ProcessingStatus.COMPLETED).scalar()
    
    m1, m2, m3, m4 = st.columns(4)
    m1.markdown(f"""<div class="kpi-card kpi-purple">
<div class="kpi-label">Total Records</div>
<div class="kpi-value">{int(total_records):,}</div>
</div>""", unsafe_allow_html=True)
    m2.markdown(f"""<div class="kpi-card kpi-green">
<div class="kpi-label">Valid Records</div>
<div class="kpi-value">{int(valid_records):,}</div>
</div>""", unsafe_allow_html=True)
    m3.markdown(f"""<div class="kpi-card kpi-red">
<div class="kpi-label">Invalid Records</div>
<div class="kpi-value">{int(invalid_records):,}</div>
</div>""", unsafe_allow_html=True)
    m4.markdown(f"""<div class="kpi-card kpi-yellow">
<div class="kpi-label">Data Quality Score</div>
<div class="kpi-value">{avg_score:.0f}</div>
</div>""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ─────────────────────────────────────────────
    # SECTION 3 — VALIDATION RULES ENGINE
    # ─────────────────────────────────────────────
    st.markdown("""
<div class="section-header">
<div class="section-icon"><span class="mi">rule</span></div>
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
            rows = [{"Info": "No active phone rules configured in Settings."}]

        c1 = st.container(border=True)
        with c1:
            st.markdown('#### :material/call: Phone Number Rules')
            st.markdown("""<p style="color:#64748B; font-size:0.8rem; margin-bottom:12px;">
                Configured phone validation rules from the database.
            </p>""", unsafe_allow_html=True)
            st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

    # Date Rules from code
    with r2:
        c2 = st.container(border=True)
        with c2:
            st.markdown('#### :material/calendar_month: Date Validation Rules')
            st.markdown("""<p style="color:#64748B; font-size:0.8rem; margin-bottom:12px;">
                Accepted date formats loaded directly from the validation engine.
            </p>""", unsafe_allow_html=True)
            
            from services.validators import DATE_FORMATS
            date_mapping = {
                "%Y-%m-%d": "YYYY-MM-DD (e.g. 2024-01-31)",
                "%d-%m-%Y": "DD-MM-YYYY (e.g. 31-01-2024)",
                "%d/%m/%Y": "DD/MM/YYYY (e.g. 31/01/2024)",
                "%m/%d/%Y": "MM/DD/YYYY (e.g. 01/31/2024)",
                "%Y/%m/%d": "YYYY/MM/DD (e.g. 2024/01/31)"
            }
            formatted_dates = [{"Accepted Formats": date_mapping.get(fmt, fmt)} for fmt in DATE_FORMATS[:5]]
            st.dataframe(pd.DataFrame(formatted_dates), use_container_width=True, hide_index=True)

    # Payment Rules from code
    with r3:
        c3 = st.container(border=True)
        with c3:
            st.markdown('#### :material/credit_card: Payment Modes')
            st.markdown("""<p style="color:#64748B; font-size:0.8rem; margin-bottom:12px;">
                Allowed payment methods loaded directly from the validation engine.
            </p>""", unsafe_allow_html=True)
            
            clean_payments = ["UPI", "Credit Card", "Debit Card", "Net Banking", "Wallet", "Cash"]
            pm_df = pd.DataFrame([{"Payment Modes (Allowed)": pm} for pm in clean_payments])
            st.dataframe(pm_df, use_container_width=True, hide_index=True)

    # ─────────────────────────────────────────────
    # SECTION 4 — QUICK ACTIONS
    # ─────────────────────────────────────────────
    st.markdown("""
<div class="section-header">
<div class="section-icon">&#9654;</div>
    <h2>Quick Actions</h2>
</div>
    """, unsafe_allow_html=True)

    actions_html = """
<div style="display:grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap:1rem;">
<a href="/Upload_Dataset" target="_self" style="text-decoration:none; color:inherit;">
<div class="feature-card" style="padding:20px; cursor:pointer;">
<div class="feature-icon" style="background:#EEF2FF; color:#4F46E5; width:40px; height:40px; font-size:1.2rem; margin-bottom:12px; display:flex; align-items:center; justify-content:center;"><span class="mi">upload</span></div>
<div class="feature-title" style="margin-bottom:4px;">Upload Dataset</div>
<div class="feature-desc" style="font-size:0.8rem;">Upload & validate new data</div>
</div>
</a>
<a href="/Validation_Results" target="_self" style="text-decoration:none; color:inherit;">
<div class="feature-card" style="padding:20px; cursor:pointer;">
<div class="feature-icon" style="background:#FEF2F2; color:#DC2626; width:40px; height:40px; font-size:1.2rem; margin-bottom:12px; display:flex; align-items:center; justify-content:center;"><span class="mi">report_problem</span></div>
<div class="feature-title" style="margin-bottom:4px;">Review Errors</div>
<div class="feature-desc" style="font-size:0.8rem;">Fix validation issues</div>
</div>
</a>
<a href="/Analytics" target="_self" style="text-decoration:none; color:inherit;">
<div class="feature-card" style="padding:20px; cursor:pointer;">
<div class="feature-icon" style="background:#F0FDF4; color:#16A34A; width:40px; height:40px; font-size:1.2rem; margin-bottom:12px; display:flex; align-items:center; justify-content:center;"><span class="mi">dashboard</span></div>
<div class="feature-title" style="margin-bottom:4px;">Open Analytics</div>
<div class="feature-desc" style="font-size:0.8rem;">Executive dashboards</div>
</div>
</a>
<a href="/AI_Insights" target="_self" style="text-decoration:none; color:inherit;">
<div class="feature-card" style="padding:20px; cursor:pointer;">
<div class="feature-icon" style="background:#FFFBEB; color:#D97706; width:40px; height:40px; font-size:1.2rem; margin-bottom:12px; display:flex; align-items:center; justify-content:center;"><span class="mi">chat</span></div>
<div class="feature-title" style="margin-bottom:4px;">Chat With AI</div>
<div class="feature-desc" style="font-size:0.8rem;">Ask about your data</div>
</div>
</a>
</div>
    """
    st.markdown(actions_html, unsafe_allow_html=True)

    # ─────────────────────────────────────────────
    # SECTION 5 — RECENT ACTIVITY
    # ─────────────────────────────────────────────
    st.markdown('<hr class="divider">', unsafe_allow_html=True)
    st.markdown("""
<div class="section-header">
<div class="section-icon">&#128198;</div>
    <h2>Recent Activity</h2>
</div>
    """, unsafe_allow_html=True)

    uploads = db.query(Upload).order_by(Upload.created_at.desc()).limit(5).all()
    if uploads:
        feed_items = ""
        for u in uploads:
            time_str = u.created_at.strftime("%I:%M %p • %b %d, %Y")
            if u.processing_status == ProcessingStatus.COMPLETED:
                icon_cls = "success"
                icon_sym = "✓"
                title = f"{u.file_name} validation completed"
            elif u.processing_status == ProcessingStatus.FAILED:
                icon_cls = "error"
                icon_sym = "✗"
                title = f"{u.file_name} processing failed"
            else:
                icon_cls = "upload"
                icon_sym = "↑"
                title = f"{u.file_name} uploaded"

            feed_items += f"""
<div class="feed-item">
<div class="feed-icon {icon_cls}">{icon_sym}</div>
<div class="feed-content">
<div class="feed-title">{title}</div>
<div class="feed-time">{time_str}</div>
</div>
</div>
            """
            
            if u.processing_status == ProcessingStatus.COMPLETED:
                feed_items += f"""
<div class="feed-item">
<div class="feed-icon info">ℹ</div>
<div class="feed-content">
<div class="feed-title">Error report generated for {u.file_name}</div>
<div class="feed-time">{time_str}</div>
</div>
</div>
                """

        st.markdown(f"""
<div class="feed-container">
{feed_items}
</div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
<div class="feed-container">
<div class="feed-item">
<div class="feed-icon info">ℹ</div>
<div class="feed-content">
<div class="feed-title">No recent activity</div>
<div class="feed-time">Upload a dataset to get started.</div>
</div>
</div>
</div>
        """, unsafe_allow_html=True)

finally:
    db.close()
