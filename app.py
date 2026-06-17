import os
import streamlit as st

st.set_page_config(
    page_title="TransactIQ — Global Transaction Validation",
    layout="wide",
    initial_sidebar_state="expanded",
)

css_path = os.path.join(os.path.dirname(__file__), "assets", "style.css")
with open(css_path) as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# Initialize DB tables
from database import engine, Base
import models
Base.metadata.create_all(bind=engine)
models.Base.metadata.create_all(bind=engine)

# Hero Section
st.markdown("""
<div class="hero-section">
    <div class="hero-title">Global Transaction Validation Platform</div>
    <div class="hero-subtitle">
        Validate, clean, process and export transaction datasets with enterprise-grade intelligence.
        Built for scale. Designed for clarity.
    </div>
    <div class="hero-badges">
        <span class="badge">✓ Phone Validation</span>
        <span class="badge">✓ Date Validation</span>
        <span class="badge">✓ Data Quality Checks</span>
        <span class="badge">✓ CSV Chunking</span>
        <span class="badge">✓ AI Insights</span>
        <span class="badge">✓ Export Center</span>
    </div>
</div>
""", unsafe_allow_html=True)

# Platform Capabilities
st.markdown("""
<div class="section-header">
    <div class="section-icon">&#9889;</div>
    <h2>Platform Capabilities</h2>
</div>
<p style="color: #64748B; margin-bottom: 1.5rem; font-size: 0.9rem;">
    Use the sidebar navigation to explore each feature. Here's a quick overview of what TransactIQ can do.
</p>
<div class="feature-grid">
    <div class="feature-card">
        <div class="feature-icon" style="background: linear-gradient(135deg, #6366F1, #4F46E5);">&#8679;</div>
        <div class="feature-title">Intelligent Upload</div>
        <div class="feature-desc">Drag-and-drop CSV or Excel files. Auto-detects your schema and maps columns intelligently before processing.</div>
    </div>
    <div class="feature-card">
        <div class="feature-icon" style="background: linear-gradient(135deg, #10B981, #059669);">&#9889;</div>
        <div class="feature-title">Chunk Processing</div>
        <div class="feature-desc">Handle 1M+ row files with zero crashes. Streaming Pandas chunk processing (50k rows/batch) for peak efficiency.</div>
    </div>
    <div class="feature-card">
        <div class="feature-icon" style="background: linear-gradient(135deg, #F59E0B, #D97706);">&#9998;</div>
        <div class="feature-title">Rules Engine</div>
        <div class="feature-desc">Country-specific phone rules, date format validation, SKU patterns, payment allow-lists, and order integrity checks.</div>
    </div>
    <div class="feature-card">
        <div class="feature-icon" style="background: linear-gradient(135deg, #8B5CF6, #7C3AED);">&#9166;</div>
        <div class="feature-title">Rich Analytics</div>
        <div class="feature-desc">Interactive Plotly charts. Visualize error distribution, validation success rates, country breakdowns, and trends.</div>
    </div>
    <div class="feature-card">
        <div class="feature-icon" style="background: linear-gradient(135deg, #EC4899, #BE185D);">&#9733;</div>
        <div class="feature-title">AI Data Chat</div>
        <div class="feature-desc">A smart AI assistant that analyzes your actual errors and answers questions about data quality conversationally.</div>
    </div>
    <div class="feature-card">
        <div class="feature-icon" style="background: linear-gradient(135deg, #14B8A6, #0D9488);">&#8615;</div>
        <div class="feature-title">Export Center</div>
        <div class="feature-desc">One-click downloads: cleaned CSV, error isolation file, and a full PDF summary report with quality scores.</div>
    </div>
</div>
""", unsafe_allow_html=True)

# Quick Nav
st.markdown('<hr class="divider">', unsafe_allow_html=True)
st.markdown("""
<div class="info-callout">
    <strong>Getting Started:</strong> Go to <em>Upload Dataset</em> in the sidebar to process your first file.
    Results, analytics, and AI insights will appear automatically after processing.
</div>
""", unsafe_allow_html=True)
