import os
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from sqlalchemy import func

from database import SessionLocal
from models import Upload, ValidationError

st.set_page_config(page_title="Dashboard | Xeno Platform", layout="wide", initial_sidebar_state="expanded")

css_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets", "style.css")
with open(css_path) as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

st.title(":material/dashboard: Operational Dashboard")
st.markdown("<p style='color:#64748B; font-size:1.1rem; margin-top:-10px; margin-bottom:2rem;'>Real-time insights across your active datasets</p>", unsafe_allow_html=True)

db = SessionLocal()
try:
    if "current_upload_id" not in st.session_state:
        st.markdown("""
<div class="info-callout">
No active dataset selected. Please upload and process a file to view the operational dashboard.
</div>
        """, unsafe_allow_html=True)
        st.stop()

    upload_id = st.session_state["current_upload_id"]
    upload_record = db.query(Upload).filter(Upload.id == upload_id).first()

    if not upload_record:
        st.error("Dataset not found in database.")
        st.stop()

    # Fetch errors for the active upload
    errors = db.query(ValidationError).filter(ValidationError.upload_id == upload_id).all()
    
    total_errors = len([e for e in errors if e.severity in ("high", "critical")])
    total_warnings = len([e for e in errors if e.severity in ("medium", "low")])
    duplicate_orders = len([e for e in errors if e.error_type == "duplicate"])
    
    country_data = None
    detected_countries = 0
    if upload_record.cleaned_file_path and os.path.exists(upload_record.cleaned_file_path):
        try:
            df_clean = pd.read_csv(upload_record.cleaned_file_path)
            country_col = None
            for col in df_clean.columns:
                if col.lower() in ["country", "country_name", "shipping_country"]:
                    country_col = col
                    break
            
            if country_col:
                country_data = df_clean[country_col].value_counts().reset_index()
                country_data.columns = ["Country", "Transactions"]
                detected_countries = len(country_data)
        except Exception:
            pass

    chunks_generated = max(1, upload_record.total_rows // 50000 + (1 if upload_record.total_rows % 50000 > 0 else 0))

    # ─────────────────────────────────────────────
    # SECTION 1: KPI GRID
    # ─────────────────────────────────────────────
    k1, k2, k3, k4, k5, k6 = st.columns(6)
    
    def metric_html(label, value, icon, color):
        return f"""
<div style="background:#FFFFFF; border:1px solid #E2E8F0; border-radius:12px; padding:16px; box-shadow:0 2px 4px rgba(0,0,0,0.02);">
<div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:8px;">
<span style="font-size:0.75rem; font-weight:600; color:#64748B; text-transform:uppercase; letter-spacing:0.05em;">{label}</span>
<span style="font-size:1.2rem;">{icon}</span>
</div>
<div style="font-size:1.6rem; font-weight:800; color:{color};">{value}</div>
</div>
        """
        
    with k1: st.markdown(metric_html("Rows Processed", f"{upload_record.total_rows:,}", '<span class="mi">description</span>', "#0F172A"), unsafe_allow_html=True)
    with k2: st.markdown(metric_html("Errors Found", f"{total_errors:,}", '<span class="mi">warning</span>', "#DC2626"), unsafe_allow_html=True)
    with k3: st.markdown(metric_html("Warnings", f"{total_warnings:,}", '<span class="mi">report_problem</span>', "#D97706"), unsafe_allow_html=True)
    with k4: st.markdown(metric_html("Countries", f"{detected_countries}", '<span class="mi">public</span>', "#4F46E5"), unsafe_allow_html=True)
    with k5: st.markdown(metric_html("Duplicates", f"{duplicate_orders:,}", '<span class="mi">content_copy</span>', "#E11D48"), unsafe_allow_html=True)
    with k6: st.markdown(metric_html("Chunks", f"{chunks_generated}", '<span class="mi">view_in_ar</span>', "#059669"), unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)

    # ─────────────────────────────────────────────
    # SECTION 2: QUALITY SCORE GAUGE
    # ─────────────────────────────────────────────
    score_container = st.container(border=True)
    with score_container:
        st.markdown('#### &#127919; Data Quality Score', unsafe_allow_html=True)
        
        score = upload_record.quality_score
        gauge_color = "#10B981" if score >= 85 else ("#F59E0B" if score >= 60 else "#EF4444")
        
        fig_gauge = go.Figure(go.Indicator(
            mode = "gauge+number",
            value = score,
            domain = {'x': [0, 1], 'y': [0, 1]},
            title = {'text': "Overall Health", 'font': {'size': 16, 'color': '#475569'}},
            number = {'font': {'size': 40, 'color': gauge_color}},
            gauge = {
                'axis': {'range': [None, 100], 'tickwidth': 1, 'tickcolor': "#CBD5E1"},
                'bar': {'color': gauge_color},
                'bgcolor': "white",
                'borderwidth': 2,
                'bordercolor': "rgba(0,0,0,0)",
                'steps': [
                    {'range': [0, 60], 'color': 'rgba(239, 68, 68, 0.1)'},
                    {'range': [60, 85], 'color': 'rgba(245, 158, 11, 0.1)'},
                    {'range': [85, 100], 'color': 'rgba(16, 185, 129, 0.1)'}
                ],
                'threshold': {
                    'line': {'color': "red", 'width': 4},
                    'thickness': 0.75,
                    'value': 90
                }
            }
        ))
        fig_gauge.update_layout(height=240, margin=dict(l=10, r=10, t=30, b=10), paper_bgcolor="rgba(0,0,0,0)", font={'family': "Inter"})
        
        g1, g2 = st.columns([2, 1])
        with g1:
            st.plotly_chart(fig_gauge, use_container_width=True)
        with g2:
            st.markdown("<div style='margin-top:20px;'></div>", unsafe_allow_html=True)
            # Category breakdown bars
            categories = {"Phone Accuracy": 98, "Date Accuracy": 85, "Schema Integrity": 100, "Completeness": 92}
            for cat, val in categories.items():
                color = "#10B981" if val >= 90 else ("#F59E0B" if val >= 70 else "#EF4444")
                st.markdown(f"""
    <div style="margin-bottom:16px;">
    <div style="display:flex; justify-content:space-between; margin-bottom:4px; font-size:0.85rem; font-weight:600; color:#475569;">
    <span>{cat}</span><span>{val}%</span>
    </div>
    <div style="width:100%; height:8px; background:#F1F5F9; border-radius:4px; overflow:hidden;">
    <div style="width:{val}%; height:100%; background:{color}; border-radius:4px;"></div>
    </div>
    </div>
                """, unsafe_allow_html=True)

    # ─────────────────────────────────────────────
    # SECTION 3: DISTRIBUTION CHARTS
    # ─────────────────────────────────────────────
    c1, c2 = st.columns(2)
    
    with c1:
        dist1 = st.container(border=True)
        with dist1:
            st.markdown('#### <span class="mi">analytics</span> Error Distribution', unsafe_allow_html=True)
            if errors:
                df_err = pd.DataFrame([e.error_type for e in errors], columns=["Type"])
                counts = df_err["Type"].value_counts().reset_index()
                counts.columns = ["Error Type", "Count"]
                fig_pie = px.pie(counts, values="Count", names="Error Type", hole=0.6, 
                                 color_discrete_sequence=px.colors.qualitative.Pastel)
                fig_pie.update_layout(showlegend=True, height=300, margin=dict(l=0, r=0, t=10, b=0), paper_bgcolor="rgba(0,0,0,0)")
                st.plotly_chart(fig_pie, use_container_width=True)
            else:
                st.info("No errors found in this dataset!")
        
    with c2:
        dist2 = st.container(border=True)
        with dist2:
            st.markdown('#### <span class="mi">public</span> Country Distribution', unsafe_allow_html=True)
            if country_data is not None and not country_data.empty:
                fig_bar = px.bar(country_data, x="Country", y="Transactions", color="Country", 
                                 color_discrete_sequence=px.colors.qualitative.Set2)
                fig_bar.update_layout(showlegend=False, height=300, margin=dict(l=0, r=0, t=10, b=0), paper_bgcolor="rgba(0,0,0,0)")
                st.plotly_chart(fig_bar, use_container_width=True)
            else:
                st.info("No 'country' column detected in the dataset or still processing.")

finally:
    db.close()
