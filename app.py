import os
import streamlit as st

st.set_page_config(page_title="TransactIQ - Global Transaction Validation", page_icon="⚡", layout="wide")

# Load CSS
css_path = os.path.join(os.path.dirname(__file__), "assets", "style.css")
with open(css_path) as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# Hero Section
st.markdown("""
<div class="hero-section">
    <div class="hero-title">Global Transaction Validation Platform</div>
    <div class="hero-subtitle">
        Validate, clean, process and export transaction datasets with enterprise-grade validation. 
        Designed for scale, powered by smart schema mapping and AI insights.
    </div>
    <div class="hero-features">
        <div class="hero-feature-badge">✓ Phone Validation</div>
        <div class="hero-feature-badge">✓ Date Validation</div>
        <div class="hero-feature-badge">✓ Data Quality Checks</div>
        <div class="hero-feature-badge">✓ CSV Chunking</div>
        <div class="hero-feature-badge">✓ AI Insights</div>
    </div>
</div>
""", unsafe_allow_html=True)

st.markdown("### Welcome to TransactIQ")
st.write("Use the sidebar to navigate through the platform features.")
st.write("""
- **Dashboard**: View high-level metrics and dataset health.
- **Upload Dataset**: Drag-and-drop file upload with schema detection and chunk processing.
- **Validation Results**: Dive into specific row-level errors.
- **Analytics**: Interactive Plotly charts showing error distribution.
- **AI Insights**: Automated dataset scoring and natural language error explanations.
- **Downloads**: Download validated datasets and reports.
- **Settings**: Manage validation rules (e.g. Country codes, Phone lengths).
""")

# Initialize DB tables just once here or centrally
from database import engine, Base
import models
Base.metadata.create_all(bind=engine)
models.Base.metadata.create_all(bind=engine)
