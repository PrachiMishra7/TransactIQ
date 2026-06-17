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
    # Global stats
    total_records   = db.query(func.coalesce(func.sum(Upload.total_rows), 0)).scalar()
    valid_records   = db.query(func.coalesce(func.sum(Upload.valid_rows), 0)).scalar()
    invalid_records = db.query(func.coalesce(func.sum(Upload.invalid_rows), 0)).scalar()

    if total_records == 0:
        st.markdown("""
        <div class="info-callout">
            No data yet. Upload and process a file first to see your analytics charts populate.
        </div>
        """, unsafe_allow_html=True)
        st.stop()

    # --- Row 1: Funnel + Error Treemap ---
    r1_left, r1_right = st.columns([1, 1.5])

    with r1_left:
        st.markdown('<div class="card"><div class="card-title">Data Survival Funnel</div>', unsafe_allow_html=True)
        # Assuming 5% of invalid records are critical and drop out completely.
        funnel_data = dict(
            number=[total_records, total_records - (invalid_records//2), valid_records],
            stage=["Total Ingested", "Passed Schema Check", "Fully Validated"]
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
        st.markdown('</div>', unsafe_allow_html=True)

    with r1_right:
        st.markdown('<div class="card"><div class="card-title">Hierarchical Error Distribution</div>', unsafe_allow_html=True)
        # Get errors grouped by severity and type
        err_results = db.query(
            ValidationError.severity, ValidationError.error_type, func.count(ValidationError.id)
        ).group_by(ValidationError.severity, ValidationError.error_type).all()

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

    # --- Row 2: Column Failures + File Score Trend ---
    r2_left, r2_right = st.columns([1.5, 1])

    with r2_left:
        st.markdown('<div class="card"><div class="card-title">Quality Score Trend (Area Timeline)</div>', unsafe_allow_html=True)
        uploads = db.query(Upload).filter(
            Upload.processing_status == ProcessingStatus.COMPLETED
        ).order_by(Upload.created_at.asc()).limit(20).all()

        if uploads and len(uploads) > 0:
            df_trend = pd.DataFrame([{
                "Date": u.created_at.strftime("%b %d, %H:%M"),
                "Score": u.quality_score,
                "File": u.file_name,
            } for u in uploads])
            
            fig_trend = go.Figure()
            fig_trend.add_trace(go.Scatter(
                x=df_trend["Date"], y=df_trend["Score"],
                fill='tozeroy',
                mode='lines+markers',
                line=dict(color='#4F46E5', width=3, shape='spline'),
                marker=dict(size=8, color='#10B981', symbol='circle', line=dict(width=2, color='white')),
                fillcolor='rgba(79, 70, 229, 0.15)',
                name='Quality Score',
                hoverinfo='text',
                hovertext=[f"<b>File:</b> {f}<br><b>Score:</b> {s}" for f, s in zip(df_trend["File"], df_trend["Score"])]
            ))
            
            fig_trend.update_layout(**CHART_THEME, height=350, margin=dict(t=10,b=30,l=10,r=10),
                yaxis=dict(range=[0,105], ticksuffix=" pts", gridcolor='#F1F5F9'),
                xaxis=dict(gridcolor='rgba(0,0,0,0)', showgrid=False))
            st.plotly_chart(fig_trend, use_container_width=True)
        else:
            st.info("Process more files to see trend data.")
        st.markdown('</div>', unsafe_allow_html=True)

    with r2_right:
        st.markdown('<div class="card"><div class="card-title">Top Failing Columns</div>', unsafe_allow_html=True)
        col_results = db.query(
            ValidationError.column_name, func.count(ValidationError.id)
        ).group_by(ValidationError.column_name)\
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
