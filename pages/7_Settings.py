import os
import streamlit as st
import pandas as pd

from database import SessionLocal
from models import ValidationRule

st.set_page_config(page_title="Settings | TransactIQ", layout="wide")

css_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets", "style.css")
with open(css_path) as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

st.markdown("""
<div class="section-header">
    <div class="section-icon">&#9881;</div>
    <h2>Settings & Validation Rules</h2>
</div>
<p style="color:#64748B; margin-bottom:1.5rem; font-size:0.9rem;">
    Manage country-specific phone validation rules and other configurable validation parameters.
</p>
""", unsafe_allow_html=True)

db = SessionLocal()
try:
    # Active rules table
    rules = db.query(ValidationRule).filter(ValidationRule.is_active == True)\
               .order_by(ValidationRule.country_name).all()

    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown('<div class="card-title">Active Phone Validation Rules</div>', unsafe_allow_html=True)

    if rules:
        df = pd.DataFrame([{
            "Country": r.country_name,
            "Country Code": r.country_code,
            "Field": r.field_name,
            "Rule Type": r.validation_type,
            "Expected Length / Value": r.rule_value,
            "Version": r.version,
        } for r in rules])
        st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.info("No validation rules configured yet.")

    st.markdown('</div>', unsafe_allow_html=True)

    # Add new rule
    st.markdown('<hr class="divider">', unsafe_allow_html=True)
    st.markdown('<div class="card"><div class="card-title">Add / Update Validation Rule</div>', unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)
    with col1:
        new_country = st.text_input("Country Name", placeholder="e.g. India")
        new_code    = st.text_input("Country Code", placeholder="e.g. +91")
    with col2:
        new_field   = st.selectbox("Field", ["phone", "date", "payment_method", "sku", "email"])
        new_type    = st.selectbox("Rule Type", ["length", "format", "allowlist", "pattern"])
    with col3:
        new_val     = st.text_input("Rule Value", placeholder="e.g. 10  (for phone length)")

    if st.button("Add Rule", type="primary"):
        if new_country and new_code and new_val:
            existing = db.query(ValidationRule).filter(
                ValidationRule.country_name == new_country,
                ValidationRule.field_name   == new_field,
            ).first()
            if existing:
                existing.rule_value      = new_val
                existing.country_code    = new_code
                existing.validation_type = new_type
                existing.version         = existing.version + 1
                db.commit()
                st.success(f"Updated rule for {new_country} — {new_field}.")
            else:
                db.add(ValidationRule(
                    country_name=new_country, country_code=new_code,
                    field_name=new_field, validation_type=new_type, rule_value=new_val,
                ))
                db.commit()
                st.success(f"Added rule: {new_country} / {new_field} = {new_val}")
            st.rerun()
        else:
            st.warning("Please fill in all required fields.")
    st.markdown('</div>', unsafe_allow_html=True)

    # Payment Mode Reference
    st.markdown('<hr class="divider">', unsafe_allow_html=True)
    st.markdown('<div class="card"><div class="card-title">Payment Mode Allow-List</div>', unsafe_allow_html=True)
    pm = ["UPI", "Credit Card", "Debit Card", "Cash", "Wallet", "Net Banking"]
    cols = st.columns(len(pm))
    for i, mode in enumerate(pm):
        cols[i].markdown(f'<span class="status-badge status-info">{mode}</span>', unsafe_allow_html=True)
    st.markdown('<p style="color:#475569; font-size:0.82rem; margin-top:12px;">Any value outside this list will be flagged as an invalid payment method.</p>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    # Date Format Reference
    st.markdown('<div class="card"><div class="card-title">Accepted Date Formats</div>', unsafe_allow_html=True)
    fmts = ["`YYYY-MM-DD`", "`DD-MM-YYYY`", "`MM/DD/YYYY`", "`YYYY-MM-DD HH:MM:SS`"]
    st.markdown("  |  ".join(fmts))
    st.markdown('</div>', unsafe_allow_html=True)

finally:
    db.close()
