import os
import streamlit as st
import pandas as pd
from collections import Counter
from st_aggrid import AgGrid, GridOptionsBuilder, ColumnsAutoSizeMode

from database import SessionLocal
from models import Upload, ProcessingStatus, ValidationError, Severity


css_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets", "style.css")
with open(css_path) as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

st.markdown("""
<div class="section-header">
    <div class="section-icon">&#9998;</div>
    <h2>Validation Results</h2>
</div>
""", unsafe_allow_html=True)

db = SessionLocal()
try:
    if "current_upload_id" not in st.session_state:
        st.markdown("""
        <div class="info-callout">
            No dataset selected. Please upload a file from the <strong>Upload Dataset</strong> page first.
        </div>
        """, unsafe_allow_html=True)
        st.stop()

    upload_id = st.session_state["current_upload_id"]
    upload = db.query(Upload).filter(Upload.id == upload_id).first()

    if not upload:
        st.error("Upload record not found.")
        st.stop()

    if upload.processing_status != ProcessingStatus.COMPLETED:
        st.warning(f"Processing status: **{upload.processing_status.value}**. Please wait for completion.")
        st.stop()

    # Summary Banner
    success_rate = (upload.valid_rows / upload.total_rows * 100) if upload.total_rows > 0 else 0
    score_color = "#10B981" if upload.quality_score >= 80 else "#F59E0B" if upload.quality_score >= 60 else "#EF4444"

    c1, c2, c3, c4 = st.columns(4)
    c1.markdown(f"""<div class="kpi-card kpi-purple">
        <div class="kpi-label">File</div>
        <div style="color:#E2E8F0; font-size:0.95rem; font-weight:700; margin-top:6px;">{upload.file_name[:20]}…</div>
    </div>""", unsafe_allow_html=True)
    c2.markdown(f"""<div class="kpi-card kpi-green">
        <div class="kpi-label">Valid Rows</div>
        <div class="kpi-value">{upload.valid_rows:,}</div>
        <div class="kpi-sub">{success_rate:.1f}% pass rate</div>
    </div>""", unsafe_allow_html=True)
    c3.markdown(f"""<div class="kpi-card kpi-red">
        <div class="kpi-label">Invalid Rows</div>
        <div class="kpi-value">{upload.invalid_rows:,}</div>
        <div class="kpi-sub">{100-success_rate:.1f}% fail rate</div>
    </div>""", unsafe_allow_html=True)
    c4.markdown(f"""<div class="kpi-card" style="background:linear-gradient(145deg,#1E293B,#162032);border:1px solid rgba(255,255,255,0.07);border-radius:18px;padding:24px 20px;">
        <div class="kpi-label">Quality Score</div>
        <div class="kpi-value" style="color:{score_color};">{upload.quality_score:.0f}</div>
        <div class="kpi-sub">out of 100</div>
    </div>""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # Fetch errors
    errors = db.query(ValidationError).filter(ValidationError.upload_id == upload_id).all()

    tab1, tab2, tab3, tab4, tab5 = st.tabs(["Overview", "Errors", "Warnings", "Fixed Records", "Recommendations"])

    with tab1:
        st.markdown('<div class="card"><div class="card-title">Data Quality Overview</div>', unsafe_allow_html=True)
        if upload.total_rows > 0:
            import plotly.graph_objects as go
            import plotly.express as px
            
            c1, c2 = st.columns(2)
            with c1:
                # Pie Chart
                fig = go.Figure(data=[go.Pie(
                    labels=['Valid Data', 'Invalid Data'], 
                    values=[upload.valid_rows, upload.invalid_rows],
                    hole=.6,
                    marker_colors=['#10B981', '#EF4444']
                )])
                fig.update_layout(
                    title_text="Data Quality Breakdown",
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)',
                    font_color='#1E293B',
                    margin=dict(t=40, b=0, l=0, r=0)
                )
                st.plotly_chart(fig, use_container_width=True)
            
            with c2:
                # Bar Chart for error columns
                if errors:
                    col_counts = Counter(e.column_name for e in errors)
                    df_cols = pd.DataFrame(list(col_counts.items()), columns=['Column', 'Errors']).sort_values('Errors', ascending=True)
                    fig2 = px.bar(df_cols, x='Errors', y='Column', orientation='h', title='Errors by Column',
                                  color_discrete_sequence=['#4F46E5'])
                    fig2.update_layout(
                        paper_bgcolor='rgba(0,0,0,0)',
                        plot_bgcolor='rgba(0,0,0,0)',
                        font_color='#1E293B',
                        margin=dict(t=40, b=0, l=0, r=0)
                    )
                    st.plotly_chart(fig2, use_container_width=True)
                else:
                    st.info("No errors to display.")
        st.markdown('</div>', unsafe_allow_html=True)

    with tab2:
        st.markdown('### Critical & High Errors', unsafe_allow_html=True)
        err_filtered = [e for e in errors if e.severity.value in ["CRITICAL", "HIGH"]]
        if err_filtered:
            sev_color = {"CRITICAL": "🔴", "HIGH": "🟠"}
            df_err = pd.DataFrame([{
                "Severity": sev_color.get(e.severity.value, "⚪"),
                "Row": e.row_number,
                "Column": e.column_name,
                "Issue": e.error_message,
            } for e in err_filtered[:500]])
            
            gb = GridOptionsBuilder.from_dataframe(df_err)
            gb.configure_default_column(resizable=True, filterable=True, sortable=True)
            gb.configure_column("Issue", wrapText=True, autoHeight=True, width=400)
            gb.configure_selection('single')
            gridOptions = gb.build()
            AgGrid(df_err, gridOptions=gridOptions, height=450, theme="alpine", columns_auto_size_mode=ColumnsAutoSizeMode.FIT_CONTENTS)
        else:
            st.success("No critical or high errors found!")

    with tab3:
        st.markdown('### Warnings (Medium/Low)', unsafe_allow_html=True)
        warn_filtered = [e for e in errors if e.severity.value in ["MEDIUM", "LOW"]]
        if warn_filtered:
            sev_color = {"MEDIUM": "🟡", "LOW": "🔵"}
            df_warn = pd.DataFrame([{
                "Severity": sev_color.get(e.severity.value, "⚪"),
                "Row": e.row_number,
                "Column": e.column_name,
                "Issue": e.error_message,
            } for e in warn_filtered[:500]])
            
            gb = GridOptionsBuilder.from_dataframe(df_warn)
            gb.configure_default_column(resizable=True, filterable=True, sortable=True)
            gb.configure_column("Issue", wrapText=True, autoHeight=True, width=400)
            gb.configure_selection('single')
            gridOptions = gb.build()
            AgGrid(df_warn, gridOptions=gridOptions, height=450, theme="alpine", columns_auto_size_mode=ColumnsAutoSizeMode.FIT_CONTENTS)
        else:
            st.success("No warnings found!")

    with tab4:
        st.markdown('<div class="card"><div class="card-title">AI Auto-Fixed Records</div>', unsafe_allow_html=True)
        st.markdown("<p style='color:#64748B;'>Our AI agent attempted to automatically fix formatting issues (e.g. padding dates, cleaning phone syntax).</p>", unsafe_allow_html=True)
        st.info("Download the Cleaned Data from the Downloads tab to view all AI-applied auto-fixes.")
        st.markdown('</div>', unsafe_allow_html=True)

    with tab5:
        st.markdown('<div class="card"><div class="card-title">Xeno Smart Recommendations</div>', unsafe_allow_html=True)
        
        c1, c2 = st.columns([1, 2])
        with c1:
            st.markdown(f"""
            <div style="text-align:center; padding:2rem 0;">
                <div style="font-size:4rem; font-weight:800; color:{score_color};">{upload.quality_score:.0f}<span style="font-size:2rem; color:#64748B;">/100</span></div>
                <div class="kpi-label">Data Quality Score</div>
            </div>
            """, unsafe_allow_html=True)
        
        with c2:
            st.markdown("### Top Issues Detected")
            if errors:
                type_counts = Counter(e.error_message for e in errors)
                for issue, count in type_counts.most_common(3):
                    st.markdown(f"- **{count}** records with: `{issue}`")
                
                st.markdown("### Xeno AI Recommendation")
                st.success("Clean customer contact fields and standardize date formats before importing to downstream CRM systems. Consider using the 'Download Cleaned' file to bypass these errors automatically.")
            else:
                st.success("Dataset is clean! No recommendations needed.")
                
        st.markdown('</div>', unsafe_allow_html=True)
        
        if errors:
            st.markdown('<div class="card"><div class="card-title">AI Error Explanation Panel</div>', unsafe_allow_html=True)
            st.write("Select a common error from this dataset to understand why it failed and how to fix it.")
            common_errs = [e[0] for e in type_counts.most_common(5)]
            selected_err = st.selectbox("Select Error to Explain:", common_errs)
            
            if selected_err:
                with st.spinner("AI generating explanation..."):
                    import time
                    time.sleep(0.8) # simulate AI thinking
                    
                    st.markdown(f"""
                    <div style="background:rgba(79,70,229,0.05); border-left:4px solid #4F46E5; padding:16px; margin-top:16px; border-radius:4px;">
                        <h4 style="margin-top:0; color:#4F46E5;">Error: {selected_err}</h4>
                        <p><strong>AI Analysis:</strong> This error occurs because the provided value violates the strict validation schema rules or country-specific formats defined in your active Settings for this column.</p>
                        <p><strong>Suggested Fix:</strong> Review the raw source data for formatting discrepancies. You can update the Validation Rules engine to be more lenient for this specific country, or manually correct the source values in your CRM prior to export.</p>
                    </div>
                    """, unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

finally:
    db.close()
