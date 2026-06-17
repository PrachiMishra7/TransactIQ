import streamlit as st

st.set_page_config(
    page_title="TransactIQ — Global Transaction Validation",
    layout="wide",
    initial_sidebar_state="expanded",
)

# CSS loaded by individual pages

# Define pages using the new st.navigation API (Streamlit 1.36+)
home       = st.Page("views/Home.py", title="Home", icon=":material/home:")
dashboard  = st.Page("views/1_Dashboard.py", title="Dashboard", icon=":material/dashboard:")
upload     = st.Page("views/2_Upload_Dataset.py", title="Upload Dataset", icon=":material/upload_file:")
results    = st.Page("views/3_Validation_Results.py", title="Validation Results", icon=":material/fact_check:")
analytics  = st.Page("views/4_Analytics.py", title="Analytics", icon=":material/monitoring:")
ai         = st.Page("views/5_AI_Insights.py", title="AI Insights", icon=":material/smart_toy:")
downloads  = st.Page("views/6_Downloads.py", title="Downloads", icon=":material/download:")
settings   = st.Page("views/7_Settings.py", title="Settings", icon=":material/settings:")

# Custom sidebar content
with st.sidebar:
    st.markdown("""
    <div style="padding: 1rem 0; margin-bottom: 1rem; border-bottom: 1px solid rgba(255,255,255,0.1);">
        <h2 style="color: white; margin: 0; font-size: 1.5rem; letter-spacing: -0.5px;">Transact<span style="color:#6366F1;">IQ</span></h2>
        <div style="color: #64748B; font-size: 0.8rem; margin-top: 4px;">Data Validation Platform</div>
    </div>
    """, unsafe_allow_html=True)

# Navigation routing
pg = st.navigation({
    "Platform": [home, dashboard, upload, results, analytics],
    "Tools": [ai, downloads, settings]
})

pg.run()
