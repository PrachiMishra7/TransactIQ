import os
import uuid
import streamlit as st
import pandas as pd

from database import SessionLocal
from models import ValidationRule

st.set_page_config(page_title="Settings | TransactIQ", page_icon="⚙️", layout="wide")

css_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets", "style.css")
with open(css_path) as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

st.title("⚙️ Validation Settings")

db = SessionLocal()
try:
    st.markdown('<div class="saas-card" style="margin-bottom: 2rem;">', unsafe_allow_html=True)
    st.subheader("➕ Add New Rule")
    with st.form("new_rule_form"):
        c1, c2 = st.columns(2)
        country_name    = c1.text_input("Country Name (e.g., India, Global)")
        country_code    = c2.text_input("Country Code (e.g., +91)")
        field_name      = c1.text_input("Field Name (e.g., phone, email)")
        validation_type = c2.selectbox("Validation Type", ["phone_length", "email_format", "enum", "regex", "custom"])
        rule_value = st.text_input("Rule Value (e.g., 10 for length)")

        if st.form_submit_button("Add Rule"):
            if not country_name or not field_name or not rule_value:
                st.error("Please fill in required fields.")
            else:
                db.add(ValidationRule(
                    id=str(uuid.uuid4()),
                    country_name=country_name,
                    country_code=country_code,
                    field_name=field_name,
                    validation_type=validation_type,
                    rule_value=rule_value,
                    is_active=True,
                ))
                db.commit()
                st.success("Rule added!")
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("### Active Rules")
    rules = db.query(ValidationRule).order_by(ValidationRule.created_at.desc()).all()
    if rules:
        df = pd.DataFrame([{
            "Country Name": r.country_name, "Country Code": r.country_code,
            "Field Name": r.field_name, "Validation Type": r.validation_type,
            "Rule Value": r.rule_value, "Active": r.is_active
        } for r in rules])
        st.dataframe(df, use_container_width=True)
    else:
        st.info("No rules found.")
finally:
    db.close()
