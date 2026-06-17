import streamlit as st

st.set_page_config(
    page_title="Xeno Data Quality Platform",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Initialize database
from database import engine
from models import Base
Base.metadata.create_all(bind=engine)

# Define pages using the new st.navigation API (Streamlit 1.36+)
home       = st.Page("views/Home.py", title="Home", icon=":material/home:", default=True)
dashboard  = st.Page("views/1_Dashboard.py", title="Dashboard", icon=":material/dashboard:")
upload     = st.Page("views/2_Upload_Dataset.py", title="Upload Dataset", icon=":material/upload_file:")
results    = st.Page("views/3_Validation_Results.py", title="Validation Results", icon=":material/fact_check:")
analytics  = st.Page("views/4_Analytics.py", title="Analytics", icon=":material/analytics:")
ai         = st.Page("views/5_AI_Insights.py", title="AI Insights", icon=":material/lightbulb:")
downloads  = st.Page("views/6_Downloads.py", title="Downloads", icon=":material/download:")
settings   = st.Page("views/7_Settings.py", title="Settings", icon=":material/settings:")

from database import SessionLocal
from models import Upload, ProcessingStatus

# Custom sidebar content
with st.sidebar:
    st.markdown("""
    <div style="padding: 1rem 0; margin-bottom: 1rem; border-bottom: 1px solid rgba(255,255,255,0.1);">
        <h2 style="color: white; margin: 0; font-size: 1.8rem; letter-spacing: -0.5px; font-weight:800;">Xeno</h2>
        <div style="color: #64748B; font-size: 0.8rem; margin-top: 4px;">Data Quality & Intelligence</div>
    </div>
    """, unsafe_allow_html=True)
    
    # Global Active Dataset Selector
    db = SessionLocal()
    try:
        uploads = db.query(Upload).filter(Upload.processing_status == ProcessingStatus.COMPLETED).order_by(Upload.created_at.desc()).all()
        if uploads:
            options = {u.id: f"{u.file_name} ({u.created_at.strftime('%b %d, %H:%M')})" for u in uploads}
            
            # Default to the most recent upload if none is selected
            if "current_upload_id" not in st.session_state:
                st.session_state["current_upload_id"] = uploads[0].id
                
            current_val = st.session_state.get("current_upload_id")
            if current_val not in options:
                current_val = uploads[0].id
                
            selected = st.selectbox(
                "Active Dataset",
                options=list(options.keys()),
                format_func=lambda x: options[x],
                index=list(options.keys()).index(current_val)
            )
            
            if selected != st.session_state.get("current_upload_id"):
                st.session_state["current_upload_id"] = selected
                st.rerun()
    finally:
        db.close()

# Navigation routing
pg = st.navigation({
    "Platform": [home, dashboard, upload, results, analytics],
    "Tools": [ai, downloads, settings]
})

pg.run()
