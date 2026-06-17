import os
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from sqlalchemy import func

from database import SessionLocal
from models import Upload, ProcessingStatus, ValidationError

st.set_page_config(page_title="Analytics | Xeno", layout="wide")

css_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets", "style.css")
with open(css_path) as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

st.markdown("""
<div class="section-header">
    <div class="section-icon">&#9166;</div>
    <h2>Enterprise Analytics</h2>
</div>
<p style="color:#64748B; margin-bottom:1.5rem; font-size:1.05rem;">
    Explore advanced error patterns, hierarchical anomaly distributions, and historical data quality trends.
</p>
""", unsafe_allow_html=True)

CHART_THEME = dict(
    paper_bgcolor='rgba(0,0,0,0)',
    plot_bgcolor='rgba(0,0,0,0)',
    font_color='#475569',
    font_family='Inter',
)

db = SessionLocal()
try:
    upload_id = st.session_state.get("current_upload_id")
    upload = db.query(Upload).filter(Upload.id == upload_id).first() if upload_id else None

    if not upload:
        st.warning("⚠️ No active dataset selected. Showing layout template. Please upload and process a dataset on the 'Upload Dataset' page to view live analytics.")
        total_records = 0
        valid_records = 0
        invalid_records = 0
        file_name = "No Active File"
    else:
        total_records = upload.total_rows
        valid_records = upload.valid_rows
        invalid_records = upload.invalid_rows
        file_name = upload.file_name
        
        st.markdown(f"""
        <div style="background:#F8FAFC; padding:12px 20px; border-radius:8px; margin-bottom:20px; border:1px solid #E2E8F0; display:flex; justify-content:space-between; align-items:center;">
            <div><span style="color:#64748B; font-size:0.9rem;">Analyzing Dataset:</span> <span style="font-weight:600; color:#334155;">{file_name}</span></div>
            <div style="background:#E0E7FF; color:#4338CA; padding:4px 10px; border-radius:6px; font-size:0.8rem; font-weight:600;">Dynamic View</div>
        </div>
        """, unsafe_allow_html=True)

    # --- Row 1: Funnel + Error Treemap ---
    r1_left, r1_right = st.columns([1, 1.5])

    with r1_left:
        st.markdown('<div class="card"><div class="card-title">Data Survival Funnel</div>', unsafe_allow_html=True)
        if total_records > 0:
            funnel_data = dict(
                number=[total_records, total_records - invalid_records, valid_records],
                stage=["Total Ingested", "Processed Data", "Fully Validated"]
            )
            fig_funnel = go.Figure(go.Funnel(
                y=funnel_data["stage"],
                x=funnel_data["number"],
                textposition="inside",
                textinfo="value+percent initial",
                opacity=0.85,
                marker={"color": ["#4F46E5", "#6366F1", "#10B981"],
                        "line": {"width": [0, 0, 0]}}
            ))
            fig_funnel.update_layout(**CHART_THEME, height=350, margin=dict(t=20,b=10,l=20,r=20))
            st.plotly_chart(fig_funnel, use_container_width=True)
        else:
            st.info("No data available for funnel.")
        st.markdown('</div>', unsafe_allow_html=True)

    with r1_right:
        st.markdown('<div class="card"><div class="card-title">Hierarchical Error Distribution</div>', unsafe_allow_html=True)
        
        err_query = db.query(
            ValidationError.severity, ValidationError.error_type, func.count(ValidationError.id)
        )
        if upload_id:
            err_query = err_query.filter(ValidationError.upload_id == upload_id)
            
        err_results = err_query.group_by(ValidationError.severity, ValidationError.error_type).all()

        if err_results:
            df_e = pd.DataFrame([{"Severity": r[0].value.capitalize(), "Type": r[1].replace("_"," ").title(), "Count": r[2]} for r in err_results])
            df_e["Platform"] = "All Errors" # Root node
            
            fig_tree = px.treemap(df_e, path=['Platform', 'Severity', 'Type'], values='Count',
                                  color='Count', color_continuous_scale='Sunsetdark')
            fig_tree.update_layout(**CHART_THEME, height=350, margin=dict(t=10,b=10,l=10,r=10))
            fig_tree.update_traces(root_color="lightgrey")
            st.plotly_chart(fig_tree, use_container_width=True)
        else:
            st.info("No error data available.")
        st.markdown('</div>', unsafe_allow_html=True)

    # --- Row 2: Column Failures + Error Severity ---
    r2_left, r2_right = st.columns([1.5, 1])

    with r2_left:
        st.markdown('<div class="card"><div class="card-title">Errors by Severity</div>', unsafe_allow_html=True)
        
        sev_query = db.query(ValidationError.severity, func.count(ValidationError.id))
        if upload_id:
            sev_query = sev_query.filter(ValidationError.upload_id == upload_id)
            
        sev_results = sev_query.group_by(ValidationError.severity).all()

        if sev_results:
            df_sev = pd.DataFrame([{"Severity": r[0].value.capitalize(), "Count": r[1]} for r in sev_results])
            # define a color map for severities
            color_map = {"Critical": "#EF4444", "High": "#F97316", "Medium": "#F59E0B", "Low": "#10B981"}
            fig_sev = px.bar(df_sev, x="Severity", y="Count", color="Severity", 
                             color_discrete_map=color_map, text="Count")
            fig_sev.update_traces(textposition='outside')
            fig_sev.update_layout(**CHART_THEME, height=350, margin=dict(t=10,b=30,l=10,r=10),
                yaxis=dict(gridcolor='#F1F5F9'), xaxis=dict(gridcolor='rgba(0,0,0,0)', showgrid=False),
                showlegend=False)
            st.plotly_chart(fig_sev, use_container_width=True)
        else:
            st.info("No errors recorded for this dataset.")
        st.markdown('</div>', unsafe_allow_html=True)

    with r2_right:
        st.markdown('<div class="card"><div class="card-title">Top Failing Columns</div>', unsafe_allow_html=True)
        col_query = db.query(
            ValidationError.column_name, func.count(ValidationError.id)
        )
        if upload_id:
            col_query = col_query.filter(ValidationError.upload_id == upload_id)
            
        col_results = col_query.group_by(ValidationError.column_name)\
         .order_by(func.count(ValidationError.id).desc()).limit(8).all()

        if col_results:
            df_c = pd.DataFrame([{"Column": r[0], "Errors": r[1]} for r in col_results])
            df_c = df_c.sort_values('Errors', ascending=True) # Plotly draws bottom-up
            fig_col = go.Figure(go.Bar(
                x=df_c["Errors"],
                y=df_c["Column"],
                orientation='h',
                marker=dict(
                    color=df_c["Errors"],
                    colorscale='Sunsetdark',
                    line=dict(width=0)
                )
            ))
            fig_col.update_layout(**CHART_THEME, height=350, margin=dict(t=10,b=10,l=10,r=10),
                                  xaxis=dict(showgrid=True, gridcolor='#F1F5F9'), yaxis=dict(showgrid=False))
            st.plotly_chart(fig_col, use_container_width=True)
        else:
            st.info("No column data available.")
        st.markdown('</div>', unsafe_allow_html=True)

finally:
    db.close()
