import os
import streamlit as st
import pandas as pd
from sqlalchemy import func
import plotly.express as px

from database import SessionLocal
from models import Upload, ProcessingStatus, ValidationRule

st.set_page_config(page_title="Dashboard | TransactIQ", page_icon="📊", layout="wide")

css_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets", "style.css")
with open(css_path) as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

st.title("📊 Dashboard")
st.markdown("Overview of your transaction data quality.")

db = SessionLocal()

try:
    total_files = db.query(Upload).filter(Upload.processing_status == ProcessingStatus.COMPLETED).count()
    total_records = db.query(func.coalesce(func.sum(Upload.total_rows), 0)).scalar()
    valid_records = db.query(func.coalesce(func.sum(Upload.valid_rows), 0)).scalar()
    invalid_records = db.query(func.coalesce(func.sum(Upload.invalid_rows), 0)).scalar()
    avg_score = db.query(func.coalesce(func.avg(Upload.quality_score), 0)).filter(
        Upload.processing_status == ProcessingStatus.COMPLETED).scalar()
    
    success_rate = (valid_records / total_records * 100) if total_records > 0 else 0

    col1, col2, col3, col4 = st.columns(4)
    
    col1.markdown(f"""
    <div class="saas-card">
        <div class="metric-label">Total Records</div>
        <div class="metric-value">{int(total_records):,}</div>
    </div>
    """, unsafe_allow_html=True)
    
    col2.markdown(f"""
    <div class="saas-card">
        <div class="metric-label">Valid Records</div>
        <div class="metric-value" style="color: #10B981;">{int(valid_records):,}</div>
    </div>
    """, unsafe_allow_html=True)
    
    col3.markdown(f"""
    <div class="saas-card">
        <div class="metric-label">Invalid Records</div>
        <div class="metric-value" style="color: #EF4444;">{int(invalid_records):,}</div>
    </div>
    """, unsafe_allow_html=True)
    
    col4.markdown(f"""
    <div class="saas-card">
        <div class="metric-label">Success Rate</div>
        <div class="metric-value">{success_rate:.1f}%</div>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("<br><br>", unsafe_allow_html=True)
    st.subheader("Recent Processing Activity")
    
    uploads = db.query(Upload).order_by(Upload.created_at.desc()).limit(5).all()
    if uploads:
        df = pd.DataFrame([{
            "Date": u.created_at.strftime("%Y-%m-%d %H:%M"),
            "File Name": u.file_name,
            "Records": u.total_rows,
            "Valid": u.valid_rows,
            "Invalid": u.invalid_rows,
            "Score": f"{u.quality_score}/100",
            "Status": u.processing_status.value
        } for u in uploads])
        st.dataframe(df, use_container_width=True)
    else:
        st.info("No processing activity yet.")

finally:
    db.close()
