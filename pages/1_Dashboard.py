import os
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from sqlalchemy import func

from database import SessionLocal
from models import Upload, ProcessingStatus, ValidationError

st.set_page_config(page_title="Dashboard | TransactIQ", layout="wide")

css_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets", "style.css")
with open(css_path) as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

st.markdown("""
<div class="section-header">
    <div class="section-icon">&#9616;</div>
    <h2>Dashboard</h2>
</div>
<p style="color:#64748B; margin-bottom:1.5rem; font-size:0.9rem;">
    Real-time overview of your transaction data quality across all processed files.
</p>
""", unsafe_allow_html=True)

db = SessionLocal()
try:
    total_records  = db.query(func.coalesce(func.sum(Upload.total_rows), 0)).scalar()
    valid_records  = db.query(func.coalesce(func.sum(Upload.valid_rows), 0)).scalar()
    invalid_records = db.query(func.coalesce(func.sum(Upload.invalid_rows), 0)).scalar()
    avg_score      = db.query(func.coalesce(func.avg(Upload.quality_score), 0)).filter(
        Upload.processing_status == ProcessingStatus.COMPLETED).scalar()
    total_files    = db.query(Upload).filter(Upload.processing_status == ProcessingStatus.COMPLETED).count()
    success_rate   = (valid_records / total_records * 100) if total_records > 0 else 0

    # KPI Cards
    c1, c2, c3, c4 = st.columns(4)

    c1.markdown(f"""
    <div class="kpi-card kpi-purple">
        <div class="kpi-icon">&#9632;</div>
        <div class="kpi-label">Total Records</div>
        <div class="kpi-value">{int(total_records):,}</div>
        <div class="kpi-sub">{total_files} files processed</div>
    </div>""", unsafe_allow_html=True)

    c2.markdown(f"""
    <div class="kpi-card kpi-green">
        <div class="kpi-icon">&#10003;</div>
        <div class="kpi-label">Valid Records</div>
        <div class="kpi-value">{int(valid_records):,}</div>
        <div class="kpi-sub">{success_rate:.1f}% success rate</div>
    </div>""", unsafe_allow_html=True)

    c3.markdown(f"""
    <div class="kpi-card kpi-red">
        <div class="kpi-icon">&#10007;</div>
        <div class="kpi-label">Invalid Records</div>
        <div class="kpi-value">{int(invalid_records):,}</div>
        <div class="kpi-sub">{100-success_rate:.1f}% failure rate</div>
    </div>""", unsafe_allow_html=True)

    c4.markdown(f"""
    <div class="kpi-card kpi-yellow">
        <div class="kpi-icon">&#9733;</div>
        <div class="kpi-label">Avg Quality Score</div>
        <div class="kpi-value">{avg_score:.0f}</div>
        <div class="kpi-sub">out of 100 points</div>
    </div>""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # --- Charts Row ---
    if total_records > 0:
        left, right = st.columns(2)

        with left:
            st.markdown('<div class="card"><div class="card-title">&#9685; Validation Health</div>', unsafe_allow_html=True)
            fig_pie = go.Figure(go.Pie(
                labels=["Valid", "Invalid"],
                values=[int(valid_records), int(invalid_records)],
                hole=0.65,
                marker_colors=["#10B981", "#EF4444"],
                textfont_size=13,
                showlegend=True,
            ))
            fig_pie.update_layout(
                paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                font_color='#CBD5E1', margin=dict(t=10,b=10,l=10,r=10),
                legend=dict(font_color='#94A3B8', bgcolor='rgba(0,0,0,0)'),
                annotations=[dict(text=f'{success_rate:.0f}%', x=0.5, y=0.5,
                    font_size=28, font_color='#818CF8', showarrow=False, font_family='Inter')]
            )
            st.plotly_chart(fig_pie, use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)

        with right:
            st.markdown('<div class="card"><div class="card-title">&#128198; Recent Processing Activity</div>', unsafe_allow_html=True)
            uploads = db.query(Upload).order_by(Upload.created_at.desc()).limit(6).all()
            if uploads:
                df = pd.DataFrame([{
                    "File": u.file_name[:28] + "…" if len(u.file_name) > 28 else u.file_name,
                    "Records": u.total_rows,
                    "Valid": u.valid_rows,
                    "Invalid": u.invalid_rows,
                    "Score": f"{u.quality_score:.0f}",
                    "Status": u.processing_status.value,
                    "Date": u.created_at.strftime("%b %d, %H:%M"),
                } for u in uploads])
                st.dataframe(df, use_container_width=True, hide_index=True)
            else:
                st.info("No uploads yet. Head to Upload Dataset to get started.")
            st.markdown('</div>', unsafe_allow_html=True)

        # Error Type Bar Chart
        st.markdown('<div class="card"><div class="card-title">&#9650; Top Validation Failures</div>', unsafe_allow_html=True)
        err_results = db.query(
            ValidationError.error_type, func.count(ValidationError.id)
        ).group_by(ValidationError.error_type)\
         .order_by(func.count(ValidationError.id).desc()).limit(8).all()

        if err_results:
            df_e = pd.DataFrame([{"Error Type": r[0].replace("_", " ").title(), "Count": r[1]} for r in err_results])
            fig_bar = px.bar(df_e, x="Count", y="Error Type", orientation="h",
                color="Count", color_continuous_scale=["#6366F1", "#EC4899"],
                template="plotly_dark")
            fig_bar.update_layout(
                paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                font_color='#CBD5E1', margin=dict(t=10,b=10,l=10,r=10),
                coloraxis_showscale=False,
            )
            fig_bar.update_traces(marker_line_width=0)
            st.plotly_chart(fig_bar, use_container_width=True)
        else:
            st.info("No error data to display yet.")
        st.markdown('</div>', unsafe_allow_html=True)

    else:
        st.markdown("""
        <div class="info-callout">
            No data processed yet. Upload a CSV or Excel file to see your dashboard populate with live metrics.
        </div>
        """, unsafe_allow_html=True)

finally:
    db.close()
