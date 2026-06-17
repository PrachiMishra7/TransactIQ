import os
import streamlit as st
import pandas as pd

from database import SessionLocal
from models import Upload, ValidationError, ProcessingStatus

st.set_page_config(page_title="Validation Results | TransactIQ", layout="wide")

css_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets", "style.css")
with open(css_path) as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

st.title("Validation Results")

db = SessionLocal()
try:
    if "current_upload_id" not in st.session_state:
        st.info("Please upload a dataset first to see validation results.")
        st.stop()

    upload_id = st.session_state["current_upload_id"]
    upload = db.query(Upload).filter(Upload.id == upload_id).first()
    
    if upload and upload.processing_status == ProcessingStatus.COMPLETED:
        st.markdown(f"### Results for `{upload.file_name}`")
        
        c1, c2, c3 = st.columns(3)
        c1.markdown(f'<div class="saas-card"><div class="metric-label">Total Records</div><div class="metric-value">{upload.total_rows}</div></div>', unsafe_allow_html=True)
        c2.markdown(f'<div class="saas-card"><div class="metric-label">Valid Records</div><div class="metric-value" style="color:#10B981;">{upload.valid_rows}</div></div>', unsafe_allow_html=True)
        c3.markdown(f'<div class="saas-card"><div class="metric-label">Invalid Records</div><div class="metric-value" style="color:#EF4444;">{upload.invalid_rows}</div></div>', unsafe_allow_html=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
        st.subheader("Errors Breakdown")
        errors = db.query(ValidationError).filter(ValidationError.upload_id == upload_id).limit(500).all()
        if errors:
            df_err = pd.DataFrame([{
                "Row Number": e.row_number,
                "Column Name": e.column_name,
                "Error Type": e.error_type,
                "Error Message": e.error_message,
                "Severity": e.severity.value,
            } for e in errors])
            st.dataframe(df_err, use_container_width=True)
        else:
            st.success("No errors found in this dataset!")
    else:
        st.warning("Processing is not yet complete or failed.")
finally:
    db.close()
