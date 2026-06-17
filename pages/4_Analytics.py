import os
import streamlit as st
import pandas as pd
import plotly.express as px
from sqlalchemy import func

from database import SessionLocal
from models import Upload, ValidationError, ProcessingStatus

st.set_page_config(page_title="Analytics | TransactIQ", layout="wide")

css_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets", "style.css")
with open(css_path) as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

st.title("Analytics")

db = SessionLocal()
try:
    st.markdown("### Global Validation Analytics")
    
    col_left, col_right = st.columns(2)

    with col_left:
        st.markdown('<div class="saas-card">', unsafe_allow_html=True)
        st.subheader("Top Validation Failures")
        results = (db.query(ValidationError.error_type, func.count(ValidationError.id))
                   .group_by(ValidationError.error_type)
                   .order_by(func.count(ValidationError.id).desc())
                   .limit(10).all())
        if results:
            df = pd.DataFrame([{"type": r[0].replace("_", " ").title(), "count": r[1]} for r in results])
            fig = px.bar(df, x="type", y="count", color="type", template="plotly_dark")
            fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No error data available yet.")
        st.markdown('</div>', unsafe_allow_html=True)

    with col_right:
        st.markdown('<div class="saas-card">', unsafe_allow_html=True)
        st.subheader("Validation Success Rate (Global)")
        total_records = db.query(func.coalesce(func.sum(Upload.total_rows), 0)).scalar()
        valid_records = db.query(func.coalesce(func.sum(Upload.valid_rows), 0)).scalar()
        invalid_records = db.query(func.coalesce(func.sum(Upload.invalid_rows), 0)).scalar()
        
        if total_records > 0:
            df_pie = pd.DataFrame([
                {"Category": "Valid", "Count": valid_records},
                {"Category": "Invalid", "Count": invalid_records}
            ])
            fig2 = px.pie(df_pie, names="Category", values="Count", hole=0.4, 
                          color="Category", color_discrete_map={"Valid":"#10B981", "Invalid":"#EF4444"},
                          template="plotly_dark")
            fig2.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
            st.plotly_chart(fig2, use_container_width=True)
        else:
            st.info("No data available.")
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown('<div class="saas-card">', unsafe_allow_html=True)
    st.subheader("Recent Dataset Quality Trend")
    uploads = (db.query(Upload)
               .filter(Upload.processing_status == ProcessingStatus.COMPLETED)
               .order_by(Upload.created_at.desc()).limit(15).all())
    if uploads:
        uploads.reverse()
        df_trend = pd.DataFrame([{
            "date": u.created_at.strftime("%Y-%m-%d %H:%M"),
            "score": u.quality_score,
            "file_name": u.file_name
        } for u in uploads])
        fig3 = px.line(df_trend, x="date", y="score", hover_data=["file_name"], markers=True, template="plotly_dark")
        fig3.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig3, use_container_width=True)
    else:
        st.info("No trend data available.")
    st.markdown('</div>', unsafe_allow_html=True)

finally:
    db.close()
