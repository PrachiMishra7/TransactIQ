import streamlit as st
import requests
import pandas as pd
import os
from dotenv import load_dotenv

load_dotenv()
API_URL = os.getenv("API_URL", "http://localhost:8000/api")

st.set_page_config(page_title="Validation Rules", page_icon="⚙️", layout="wide")

st.title("⚙️ Validation Rules")
st.markdown("Manage the rules used to validate transaction data.")

# Add new rule
with st.expander("➕ Add New Rule"):
    with st.form("new_rule_form"):
        col1, col2 = st.columns(2)
        country_name = col1.text_input("Country Name (e.g., India, Global)")
        country_code = col2.text_input("Country Code (e.g., +91)")
        field_name = col1.text_input("Field Name (e.g., phone, email)")
        validation_type = col2.selectbox("Validation Type", ["phone_length", "email_format", "enum", "regex", "custom"])
        rule_value = st.text_input("Rule Value (e.g., 10, standard, UPI,Card)")
        
        submitted = st.form_submit_button("Add Rule")
        if submitted:
            if not country_name or not field_name or not rule_value:
                st.error("Please fill in required fields.")
            else:
                try:
                    payload = {
                        "country_name": country_name,
                        "country_code": country_code,
                        "field_name": field_name,
                        "validation_type": validation_type,
                        "rule_value": rule_value,
                        "is_active": True
                    }
                    res = requests.post(f"{API_URL}/rules", json=payload)
                    res.raise_for_status()
                    st.success("Rule added successfully!")
                except Exception as e:
                    st.error(f"Failed to add rule: {e}")

st.markdown("---")
st.subheader("Current Rules")

try:
    res = requests.get(f"{API_URL}/rules")
    res.raise_for_status()
    rules = res.json()
    
    if rules:
        df = pd.DataFrame(rules)
        df = df[["country_name", "country_code", "field_name", "validation_type", "rule_value", "is_active", "version"]]
        st.dataframe(df, use_container_width=True)
    else:
        st.info("No rules found.")
except Exception as e:
    st.error(f"Failed to load rules: {e}")
