import os
import streamlit as st
import pandas as pd

from database import SessionLocal
from models import Upload, Report, ValidationError, ProcessingStatus

st.set_page_config(page_title="AI Insights | TransactIQ", page_icon="🤖", layout="wide")

css_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets", "style.css")
with open(css_path) as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

st.title("🤖 AI Insights")

db = SessionLocal()
try:
    if "current_upload_id" not in st.session_state:
        st.info("Please upload a dataset first to see AI Insights.")
        st.stop()

    upload_id = st.session_state["current_upload_id"]
    upload = db.query(Upload).filter(Upload.id == upload_id).first()
    
    if upload and upload.processing_status == ProcessingStatus.COMPLETED:
        report = (db.query(Report).filter(Report.upload_id == upload_id)
                  .order_by(Report.generated_at.desc()).first())
        
        st.markdown(f"""
        <div class="saas-card" style="margin-bottom: 2rem;">
            <h3>Dataset Quality Score</h3>
            <div class="metric-value" style="font-size: 3rem;">{upload.quality_score}/100</div>
        </div>
        """, unsafe_allow_html=True)
        
        if report and report.summary:
            st.markdown('<div class="saas-card">', unsafe_allow_html=True)
            st.markdown("### 📝 AI Summary")
            st.write(report.summary)
            st.markdown('</div>', unsafe_allow_html=True)
            
        st.markdown("<br>### 🔍 Error Explanation Engine", unsafe_allow_html=True)
        errors = db.query(ValidationError).filter(ValidationError.upload_id == upload_id).limit(10).all()
        if errors:
            selected_error = st.selectbox(
                "Select an error to explain:",
                [f"[{e.column_name}] {e.error_message}" for e in errors]
            )
            if selected_error:
                st.markdown('<div class="saas-card">', unsafe_allow_html=True)
                st.markdown("#### Explanation")
                st.info(f"**Insight:** This error typically means the data in the column does not conform to the expected format or constraints. For example, phone numbers must strictly match the country's required digit count (e.g., 10 digits for India), and SKUs must follow the format `SKU-12345`.")
                st.markdown('</div>', unsafe_allow_html=True)
        else:
            st.success("No errors to explain!")
finally:
    db.close()
