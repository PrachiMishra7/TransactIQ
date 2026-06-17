import os
import streamlit as st

st.set_page_config(page_title="TransactIQ - Global Transaction Validation", layout="wide")

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

st.markdown("### Platform Capabilities")
st.markdown("Use the sidebar to navigate through the platform features.")

st.markdown("""
<div class="feature-grid">
    <div class="saas-card">
        <h3 style="margin-top: 0;">1. Intelligent Upload</h3>
        <p style="color: #94A3B8;">Drag and drop CSV or Excel files. Our system automatically detects your schema and allows manual overrides before processing.</p>
    </div>
    <div class="saas-card">
        <h3 style="margin-top: 0;">2. Chunk Processing</h3>
        <p style="color: #94A3B8;">Built for scale. Files exceeding 100,000+ rows are split into sequential 50k chunks via Pandas to ensure zero memory crashes.</p>
    </div>
    <div class="saas-card">
        <h3 style="margin-top: 0;">3. Rules Engine</h3>
        <p style="color: #94A3B8;">Strict validations for Product SKUs, dynamic Country Phone Codes, Dates, and Payment Allow-lists based on customizable rules.</p>
    </div>
    <div class="saas-card">
        <h3 style="margin-top: 0;">4. Rich Analytics</h3>
        <p style="color: #94A3B8;">Dive deep into interactive Plotly charts. Visualize your validation success rates, common failure reasons, and historical trends.</p>
    </div>
    <div class="saas-card">
        <h3 style="margin-top: 0;">5. Chat with Data</h3>
        <p style="color: #94A3B8;">A fully integrated AI assistant that analyzes your exact database errors to provide instant, conversational explanations.</p>
    </div>
    <div class="saas-card">
        <h3 style="margin-top: 0;">6. Export Center</h3>
        <p style="color: #94A3B8;">One-click generation of Cleaned Datasets, Error Isolation files, and comprehensive PDF Validation Summary Reports.</p>
    </div>
</div>
""", unsafe_allow_html=True)

# Initialize DB tables just once here or centrally
from database import engine, Base
import models
Base.metadata.create_all(bind=engine)
models.Base.metadata.create_all(bind=engine)
