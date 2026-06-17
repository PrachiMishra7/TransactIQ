import os
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from sqlalchemy import func

from database import SessionLocal
from models import Upload, ProcessingStatus, ValidationError

st.set_page_config(page_title="Analytics | TransactIQ", layout="wide")

css_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets", "style.css")
with open(css_path) as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

st.markdown("""
<div class="section-header">
    <div class="section-icon">&#9166;</div>
    <h2>Analytics</h2>
</div>
<p style="color:#64748B; margin-bottom:1.5rem; font-size:0.9rem;">
    Interactive charts powered by Plotly — explore error patterns, trends, and data quality across all processed files.
</p>
""", unsafe_allow_html=True)

CHART_THEME = dict(
    paper_bgcolor='rgba(0,0,0,0)',
    plot_bgcolor='rgba(0,0,0,0)',
    font_color='#CBD5E1',
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

    # --- Row 1: Pie + Error Distribution ---
    r1_left, r1_right = st.columns(2)

    with r1_left:
        st.markdown('<div class="card"><div class="card-title">Validation Success Rate</div>', unsafe_allow_html=True)
        success_rate = (valid_records / total_records * 100) if total_records > 0 else 0
        fig_pie = go.Figure(go.Pie(
            labels=["Valid", "Invalid"],
            values=[int(valid_records), int(invalid_records)],
            hole=0.62,
            marker=dict(colors=["#10B981", "#EF4444"], line=dict(color='#0F172A', width=2)),
            textfont_size=14,
        ))
        fig_pie.update_layout(
            **CHART_THEME, height=320, margin=dict(t=10,b=10,l=10,r=10),
            legend=dict(font_color='#94A3B8', bgcolor='rgba(0,0,0,0)', orientation='h', y=-0.1),
            annotations=[dict(text=f"<b>{success_rate:.0f}%</b><br>Valid", x=0.5, y=0.5,
                font_size=18, font_color='#818CF8', showarrow=False)]
        )
        st.plotly_chart(fig_pie, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

    with r1_right:
        st.markdown('<div class="card"><div class="card-title">Error Distribution by Type</div>', unsafe_allow_html=True)
        err_results = db.query(
            ValidationError.error_type, func.count(ValidationError.id)
        ).group_by(ValidationError.error_type)\
         .order_by(func.count(ValidationError.id).desc()).limit(10).all()

        if err_results:
            df_e = pd.DataFrame([{"Type": r[0].replace("_"," ").title(), "Count": r[1]} for r in err_results])
            fig_bar = px.bar(df_e, x="Type", y="Count",
                color="Count", color_continuous_scale=["#6366F1", "#EC4899"],
                template="plotly_dark")
            fig_bar.update_layout(**CHART_THEME, height=320, margin=dict(t=10,b=60,l=10,r=10),
                coloraxis_showscale=False)
            fig_bar.update_traces(marker_line_width=0)
            st.plotly_chart(fig_bar, use_container_width=True)
        else:
            st.info("No error data available.")
        st.markdown('</div>', unsafe_allow_html=True)

    # --- Row 2: Column Failures + File Score Trend ---
    r2_left, r2_right = st.columns(2)

    with r2_left:
        st.markdown('<div class="card"><div class="card-title">Top Failing Columns</div>', unsafe_allow_html=True)
        col_results = db.query(
            ValidationError.column_name, func.count(ValidationError.id)
        ).group_by(ValidationError.column_name)\
         .order_by(func.count(ValidationError.id).desc()).limit(8).all()

        if col_results:
            df_c = pd.DataFrame([{"Column": r[0], "Errors": r[1]} for r in col_results])
            fig_col = px.bar(df_c, y="Column", x="Errors", orientation="h",
                color="Errors", color_continuous_scale=["#6366F1", "#F59E0B"],
                template="plotly_dark")
            fig_col.update_layout(**CHART_THEME, height=300, margin=dict(t=10,b=10,l=10,r=10),
                coloraxis_showscale=False)
            fig_col.update_traces(marker_line_width=0)
            st.plotly_chart(fig_col, use_container_width=True)
        else:
            st.info("No column data available.")
        st.markdown('</div>', unsafe_allow_html=True)

    with r2_right:
        st.markdown('<div class="card"><div class="card-title">Quality Score Trend (per Upload)</div>', unsafe_allow_html=True)
        uploads = db.query(Upload).filter(
            Upload.processing_status == ProcessingStatus.COMPLETED
        ).order_by(Upload.created_at.asc()).limit(20).all()

        if uploads and len(uploads) > 0:
            df_trend = pd.DataFrame([{
                "Date": u.created_at.strftime("%b %d"),
                "Score": u.quality_score,
                "File": u.file_name,
            } for u in uploads])
            fig_trend = px.line(df_trend, x="Date", y="Score", markers=True,
                hover_name="File", template="plotly_dark",
                color_discrete_sequence=["#818CF8"])
            fig_trend.update_layout(**CHART_THEME, height=300, margin=dict(t=10,b=30,l=10,r=10),
                yaxis=dict(range=[0,105], ticksuffix=" pts", gridcolor='rgba(255,255,255,0.05)'),
                xaxis=dict(gridcolor='rgba(255,255,255,0.05)'))
            fig_trend.update_traces(line_width=2.5, marker_size=8, marker_color='#6366F1',
                fill='tozeroy', fillcolor='rgba(99,102,241,0.08)')
            st.plotly_chart(fig_trend, use_container_width=True)
        else:
            st.info("Process more files to see trend data.")
        st.markdown('</div>', unsafe_allow_html=True)

    # --- Row 3: All uploads bar chart ---
    st.markdown('<div class="card"><div class="card-title">Records per Upload (Valid vs Invalid)</div>', unsafe_allow_html=True)
    uploads_all = db.query(Upload).filter(
        Upload.processing_status == ProcessingStatus.COMPLETED
    ).order_by(Upload.created_at.desc()).limit(12).all()

    if uploads_all:
        data = []
        for u in uploads_all:
            nm = u.file_name[:18]+"…" if len(u.file_name)>18 else u.file_name
            data.append({"File": nm, "Count": u.valid_rows,   "Type": "Valid"})
            data.append({"File": nm, "Count": u.invalid_rows, "Type": "Invalid"})
        df_all = pd.DataFrame(data)
        fig_all = px.bar(df_all, x="File", y="Count", color="Type",
            color_discrete_map={"Valid":"#10B981","Invalid":"#EF4444"},
            barmode="group", template="plotly_dark")
        fig_all.update_layout(**CHART_THEME, height=340, margin=dict(t=10,b=60,l=10,r=10),
            legend=dict(font_color='#94A3B8', bgcolor='rgba(0,0,0,0)'),
            xaxis=dict(tickangle=-30))
        fig_all.update_traces(marker_line_width=0)
        st.plotly_chart(fig_all, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

finally:
    db.close()
