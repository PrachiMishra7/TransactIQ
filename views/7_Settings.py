import os
import streamlit as st
import pandas as pd
import json

from database import SessionLocal
from models import ValidationRule


css_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets", "style.css")
with open(css_path) as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

st.markdown("""
<div class="section-header">
    <div class="section-icon"><span class="mi">settings</span></div>
    <h2>Platform Settings</h2>
</div>
<p style="color:#64748B; margin-bottom:1.5rem; font-size:1.05rem;">
    Configure Xeno validation engine rules, strictness levels, and export configurations.
</p>
""", unsafe_allow_html=True)

db = SessionLocal()
try:
    tab1, tab2, tab3 = st.tabs(["Engine Rules", "System Toggles", "Export Config"])

    with tab1:
        st.markdown('<div class="card"><div class="card-title">Validation Strictness Rules</div>', unsafe_allow_html=True)
        st.markdown("<p style='color:#64748B; font-size:0.9rem;'>Manage how strict the AI engine is when evaluating country-specific rules.</p>", unsafe_allow_html=True)
        
        # Active rules table
        rules = db.query(ValidationRule).filter(ValidationRule.is_active == True)\
                   .order_by(ValidationRule.country_name).all()

        if rules:
            df = pd.DataFrame([{
                "Country": r.country_name,
                "Country Code": r.country_code,
                "Field": r.field_name,
                "Rule Type": r.validation_type,
                "Required Format/Length": r.rule_value,
            } for r in rules])
            st.dataframe(df, use_container_width=True, hide_index=True)
        else:
            st.info("No validation rules configured yet.")
        st.markdown('</div>', unsafe_allow_html=True)

        # Add new rule
        st.markdown('<div class="card"><div class="card-title">Add / Update Rule</div>', unsafe_allow_html=True)

        col1, col2, col3 = st.columns(3)
        with col1:
            new_country = st.text_input("Country Name", placeholder="e.g. United Kingdom")
            new_code    = st.text_input("Country Code", placeholder="e.g. +44")
        with col2:
            new_field   = st.selectbox("Field", ["phone", "date", "payment_method", "sku", "email"])
            new_type    = st.selectbox("Rule Type", ["length", "format", "allowlist", "pattern"])
        with col3:
            new_val     = st.text_input("Expected Value", placeholder="e.g. 10 (for phone length)")
            
            st.markdown("<div style='height: 28px;'></div>", unsafe_allow_html=True)
            if st.button("Save Rule Engine Configuration", type="primary", use_container_width=True):
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

    with tab2:
        st.markdown('<div class="card"><div class="card-title">System & AI Toggles</div>', unsafe_allow_html=True)
        st.markdown("<p style='color:#64748B; font-size:0.9rem; margin-bottom:1rem;'>Configure pipeline automation and error logging verbosity.</p>", unsafe_allow_html=True)
        
        st.toggle("Auto-Fix Formatting", value=True, help="AI will attempt to automatically correct whitespace and padding issues.")
        st.toggle("Flag Disposable Emails", value=True, help="Automatically flag temp/disposable email domains as Warnings.")
        st.toggle("Enable Deep Schema Mapping", value=True, help="Use NLP to map unknown CSV column headers to the canonical system.")
        st.toggle("Strict Date Parsing", value=False, help="Fail records if the date format isn't strictly YYYY-MM-DD (overrides smart parsing).")
        
        st.markdown("<hr class='divider'>", unsafe_allow_html=True)
        st.markdown('#### Global Rate Limits')
        st.slider("Concurrent Processing Chunks", min_value=1, max_value=10, value=4, help="Number of 50k row chunks to process in parallel.")
        st.markdown('</div>', unsafe_allow_html=True)

    with tab3:
        st.markdown('<div class="card"><div class="card-title">Export Validation Configuration</div>', unsafe_allow_html=True)
        st.markdown("<p style='color:#64748B; font-size:0.9rem;'>Download your current Rule Engine setup as a JSON file to backup or share with other workspaces.</p>", unsafe_allow_html=True)
        
        if rules:
            export_data = [{
                "country_name": r.country_name,
                "country_code": r.country_code,
                "field_name": r.field_name,
                "validation_type": r.validation_type,
                "rule_value": r.rule_value,
                "is_active": r.is_active,
                "version": r.version
            } for r in rules]
            
            json_str = json.dumps(export_data, indent=4)
            st.download_button(
                label="📥 Download Config (JSON)",
                data=json_str,
                file_name="xeno_rules_config.json",
                mime="application/json",
                type="primary"
            )
            
            st.markdown("### Config Preview")
            st.json(export_data)
        else:
            st.info("No active rules to export.")
        st.markdown('</div>', unsafe_allow_html=True)

finally:
    db.close()
