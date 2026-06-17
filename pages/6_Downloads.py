import os
import streamlit as st

from database import SessionLocal
from models import Upload, ProcessingStatus

st.set_page_config(page_title="Download Center | TransactIQ", layout="wide")

css_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets", "style.css")
with open(css_path) as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

st.title("Download Center")

db = SessionLocal()
try:
    if "current_upload_id" not in st.session_state:
        st.info("Please upload a dataset first to download reports.")
        st.stop()

    upload_id = st.session_state["current_upload_id"]
    upload = db.query(Upload).filter(Upload.id == upload_id).first()
    
    if upload and upload.processing_status == ProcessingStatus.COMPLETED:
        st.markdown(f"### Downloads for `{upload.file_name}`")
        st.markdown("<br>", unsafe_allow_html=True)
        
        c1, c2, c3 = st.columns(3)
        
        with c1:
            st.markdown('<div class="saas-card" style="text-align: center;">', unsafe_allow_html=True)
            st.subheader("Cleaned Data")
            st.write("Contains only valid rows.")
            if upload.cleaned_file_path and os.path.exists(upload.cleaned_file_path):
                with open(upload.cleaned_file_path, "rb") as f:
                    st.download_button("Download CSV", f, file_name="validated_transactions.csv", mime="text/csv", use_container_width=True, type="primary")
            st.markdown('</div>', unsafe_allow_html=True)

        with c2:
            st.markdown('<div class="saas-card" style="text-align: center;">', unsafe_allow_html=True)
            st.subheader("Error Report")
            st.write("Contains invalid rows and reasons.")
            if upload.error_file_path and os.path.exists(upload.error_file_path):
                with open(upload.error_file_path, "rb") as f:
                    st.download_button("Download CSV", f, file_name="validation_errors.csv", mime="text/csv", use_container_width=True, type="primary")
            st.markdown('</div>', unsafe_allow_html=True)

        with c3:
            st.markdown('<div class="saas-card" style="text-align: center;">', unsafe_allow_html=True)
            st.subheader("Summary Report")
            st.write("PDF summary of validation.")
            if upload.report_file_path and os.path.exists(upload.report_file_path):
                with open(upload.report_file_path, "rb") as f:
                    st.download_button("Download PDF", f, file_name="validation_report.pdf", mime="application/pdf", use_container_width=True, type="primary")
            st.markdown('</div>', unsafe_allow_html=True)
    else:
        st.warning("Processing is not yet complete or failed.")
finally:
    db.close()
