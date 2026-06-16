import streamlit as st
import pandas as pd
import plotly.express as px
import time
import os
import uuid
import asyncio
from datetime import datetime, timedelta
from dotenv import load_dotenv

from database import SessionLocal, engine, Base
from models import Upload, ValidationError, ValidationRule, Report, ProcessingStatus
from sqlalchemy import func, cast, Date

from services.processor import process_upload
from config import settings

load_dotenv()

# Initialize DB tables
Base.metadata.create_all(bind=engine)

st.set_page_config(page_title="TransactIQ", page_icon="📊", layout="wide")

page = st.sidebar.radio("Navigation", ["Dashboard", "Upload Data", "Validation Rules", "Upload History"])

db = SessionLocal()

try:
    if page == "Dashboard":
        st.title("📊 TransactIQ Dashboard")
        st.markdown("Overview of your transaction data quality.")

        try:
            total_files = db.query(Upload).filter(Upload.processing_status == ProcessingStatus.COMPLETED).count()
            total_records = db.query(func.coalesce(func.sum(Upload.total_rows), 0)).scalar()
            avg_score = db.query(func.coalesce(func.avg(Upload.quality_score), 0)).filter(
                Upload.processing_status == ProcessingStatus.COMPLETED
            ).scalar()
            active_rules = db.query(ValidationRule).filter(ValidationRule.is_active == True).count()
            
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Total Files Processed", total_files)
            col2.metric("Total Records Validated", int(total_records))
            col3.metric("Avg Quality Score", f"{round(float(avg_score), 1)} / 100")
            col4.metric("Active Rules", active_rules)
        except Exception as e:
            st.error(f"Failed to fetch stats: {e}")

        st.markdown("---")

        col_left, col_right = st.columns(2)

        with col_left:
            st.subheader("Errors by Type")
            try:
                results = (
                    db.query(ValidationError.error_type, func.count(ValidationError.id))
                    .group_by(ValidationError.error_type)
                    .order_by(func.count(ValidationError.id).desc())
                    .limit(10)
                    .all()
                )
                if results:
                    df = pd.DataFrame([{"type": r[0].replace("_", " ").title(), "count": r[1]} for r in results])
                    fig = px.bar(df, x="type", y="count", color="type")
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("No error data available yet.")
            except Exception as e:
                st.error(f"Could not load chart data: {e}")

            st.subheader("Quality Trend")
            try:
                uploads = (
                    db.query(Upload)
                    .filter(Upload.processing_status == ProcessingStatus.COMPLETED)
                    .order_by(Upload.created_at.desc())
                    .limit(20)
                    .all()
                )
                if uploads:
                    uploads.reverse()
                    df = pd.DataFrame([{"date": u.created_at.strftime("%Y-%m-%d"), "score": u.quality_score, "file_name": u.file_name} for u in uploads])
                    fig = px.line(df, x="date", y="score", hover_data=["file_name"], markers=True)
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("No trend data available yet.")
            except Exception:
                st.error("Could not load chart data.")

        with col_right:
            st.subheader("Files Processed per Day")
            try:
                thirty_days_ago = datetime.utcnow() - timedelta(days=30)
                results = (
                    db.query(cast(Upload.created_at, Date).label("date"), func.count(Upload.id))
                    .filter(Upload.created_at >= thirty_days_ago)
                    .group_by(cast(Upload.created_at, Date))
                    .order_by(cast(Upload.created_at, Date))
                    .all()
                )
                if results:
                    df = pd.DataFrame([{"date": r[0].isoformat(), "count": r[1]} for r in results])
                    fig = px.bar(df, x="date", y="count")
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("No daily data available yet.")
            except Exception:
                st.error("Could not load chart data.")

            st.subheader("Errors by Country")
            try:
                errors = db.query(ValidationError.error_message).all()
                india = sum(1 for e in errors if "india" in e[0].lower() or "+91" in e[0])
                singapore = sum(1 for e in errors if "singapore" in e[0].lower() or "+65" in e[0])
                other = len(errors) - india - singapore
                if errors:
                    df = pd.DataFrame([
                        {"country": "India", "count": india},
                        {"country": "Singapore", "count": singapore},
                        {"country": "Other", "count": max(0, other)},
                    ])
                    fig = px.pie(df, names="country", values="count", hole=0.4)
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("No country error data available yet.")
            except Exception:
                st.error("Could not load chart data.")

    elif page == "Upload Data":
        st.title("📤 Upload Data")
        st.markdown("Upload a CSV or XLSX file for validation and cleaning.")

        uploaded_file = st.file_uploader("Choose a file", type=["csv", "xlsx", "xls"])

        if uploaded_file is not None:
            if st.button("Upload and Process"):
                with st.spinner("Uploading and Processing... this may take a moment."):
                    ext = os.path.splitext(uploaded_file.name)[1].lower()
                    upload_id = str(uuid.uuid4())
                    
                    os.makedirs(settings.upload_dir, exist_ok=True)
                    file_path = os.path.join(settings.upload_dir, f"{upload_id}{ext}")
                    
                    with open(file_path, "wb") as f:
                        f.write(uploaded_file.getvalue())

                    upload = Upload(
                        id=upload_id,
                        file_name=uploaded_file.name,
                        file_size=len(uploaded_file.getvalue()),
                        processing_status=ProcessingStatus.UPLOADING,
                    )
                    db.add(upload)
                    db.commit()

                    # Process synchronously
                    asyncio.run(process_upload(db, upload_id, file_path))
                    
                    st.session_state["current_upload_id"] = upload_id
                    st.success("Processing completed!")

        if "current_upload_id" in st.session_state:
            upload_id = st.session_state["current_upload_id"]
            
            upload = db.query(Upload).filter(Upload.id == upload_id).first()
            if upload and upload.processing_status == ProcessingStatus.COMPLETED:
                st.markdown("### 📋 Results Summary")
                
                def _score_label(score: float) -> str:
                    if score >= 90: return "Excellent"
                    if score >= 75: return "Good"
                    if score >= 60: return "Fair"
                    if score >= 40: return "Poor"
                    return "Critical"
                
                col1, col2, col3, col4 = st.columns(4)
                col1.metric("Quality Score", f"{upload.quality_score} / 100", _score_label(upload.quality_score))
                col2.metric("Total Records", upload.total_rows)
                col3.metric("Valid Records", upload.valid_rows)
                col4.metric("Invalid Records", upload.invalid_rows)
                
                report = db.query(Report).filter(Report.upload_id == upload_id).order_by(Report.generated_at.desc()).first()
                if report and report.summary:
                    st.markdown("#### AI Insights")
                    st.write(report.summary)
                
                st.markdown("### 📥 Downloads")
                st.info(f"Cleaned Data: {upload.cleaned_file_path}")
                st.info(f"Errors Data: {upload.error_file_path}")
                st.info(f"PDF Report: {upload.report_file_path}")
                
                st.markdown("### ⚠️ Errors")
                errors = db.query(ValidationError).filter(ValidationError.upload_id == upload_id).limit(100).all()
                if errors:
                    df_err = pd.DataFrame([{
                        "row_number": e.row_number,
                        "column_name": e.column_name,
                        "error_type": e.error_type,
                        "error_message": e.error_message,
                        "severity": e.severity.value,
                    } for e in errors])
                    st.dataframe(df_err, use_container_width=True)
                else:
                    st.success("No errors found in this file!")

    elif page == "Validation Rules":
        st.title("⚙️ Validation Rules")
        st.markdown("Manage the rules used to validate transaction data.")

        with st.expander("➕ Add New Rule"):
            with st.form("new_rule_form"):
                col1, col2 = st.columns(2)
                country_name = col1.text_input("Country Name (e.g., India, Global)")
                country_code = col2.text_input("Country Code (e.g., +91)")
                field_name = col1.text_input("Field Name (e.g., phone, email)")
                validation_type = col2.selectbox("Validation Type", ["phone_length", "email_format", "enum", "regex", "custom"])
                rule_value = st.text_input("Rule Value (e.g., 10, standard, UPI,Card)")
                
                submitted = st.form_submit_button("Add Rule")
                if submitted:
                    if not country_name or not field_name or not rule_value:
                        st.error("Please fill in required fields.")
                    else:
                        try:
                            r = ValidationRule(
                                id=str(uuid.uuid4()),
                                country_name=country_name,
                                country_code=country_code,
                                field_name=field_name,
                                validation_type=validation_type,
                                rule_value=rule_value,
                                is_active=True,
                            )
                            db.add(r)
                            db.commit()
                            st.success("Rule added successfully!")
                        except Exception as e:
                            st.error(f"Failed to add rule: {e}")

        st.markdown("---")
        st.subheader("Current Rules")

        rules = db.query(ValidationRule).order_by(ValidationRule.created_at.desc()).all()
        if rules:
            df = pd.DataFrame([{
                "country_name": r.country_name,
                "country_code": r.country_code,
                "field_name": r.field_name,
                "validation_type": r.validation_type,
                "rule_value": r.rule_value,
                "is_active": r.is_active,
                "version": r.version
            } for r in rules])
            st.dataframe(df, use_container_width=True)
        else:
            st.info("No rules found.")

    elif page == "Upload History":
        st.title("🕒 Upload History")
        st.markdown("View past uploads and download their reports.")

        uploads = db.query(Upload).order_by(Upload.created_at.desc()).limit(50).all()
        
        if uploads:
            for u in uploads:
                with st.expander(f"{u.file_name} - Score: {u.quality_score} - {u.processing_status.value}"):
                    col1, col2, col3 = st.columns(3)
                    col1.metric("Date", u.created_at.isoformat()[:10])
                    col2.metric("Total Rows", u.total_rows)
                    col3.metric("Invalid", u.invalid_rows)
                    
                    if u.processing_status == ProcessingStatus.COMPLETED:
                        st.info(f"Cleaned Data: {u.cleaned_file_path}")
                        st.info(f"Errors Data: {u.error_file_path}")
                        st.info(f"PDF Report: {u.report_file_path}")
        else:
            st.info("No uploads found.")
finally:
    db.close()
