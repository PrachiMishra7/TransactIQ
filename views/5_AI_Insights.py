import os
import time
import streamlit as st
from collections import Counter

from database import SessionLocal
from models import Upload, ProcessingStatus, ValidationError, Report


css_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets", "style.css")
with open(css_path) as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

st.markdown("""
<div class="section-header">
    <div class="section-icon">&#9733;</div>
    <h2>AI Insights</h2>
</div>
<p style="color:#64748B; margin-bottom:1.5rem; font-size:0.9rem;">
    Chat with your dataset. The AI assistant analyzes your actual validation errors to answer questions intelligently.
</p>
""", unsafe_allow_html=True)

db = SessionLocal()
try:
    if "current_upload_id" not in st.session_state:
        st.markdown("""
        <div class="info-callout">
            No dataset selected. Please upload and process a file first to unlock AI Insights.
        </div>
        """, unsafe_allow_html=True)
        st.stop()

    upload_id = st.session_state["current_upload_id"]
    upload = db.query(Upload).filter(Upload.id == upload_id).first()

    if not upload or upload.processing_status != ProcessingStatus.COMPLETED:
        st.warning("Dataset processing is not complete yet.")
        st.stop()

    # Fetch all errors for this upload
    errors = db.query(ValidationError).filter(ValidationError.upload_id == upload_id).all()
    err_by_type = Counter(e.error_type for e in errors)
    err_by_col  = Counter(e.column_name for e in errors)
    total_errs  = len(errors)
    success_rate = (upload.valid_rows / upload.total_rows * 100) if upload.total_rows > 0 else 100

    # Quality Score Card
    score = upload.quality_score
    score_color = "#34D399" if score >= 80 else "#FCD34D" if score >= 60 else "#F87171"
    grade = "Excellent" if score >= 90 else "Good" if score >= 80 else "Fair" if score >= 60 else "Poor"

    left_col, right_col = st.columns([1, 2])

    with left_col:
        st.markdown(f"""
        <div class="card" style="text-align:center; padding:40px 24px;">
            <div class="kpi-label" style="margin-bottom:12px;">Dataset Quality Score</div>
            <div style="font-size:5rem; font-weight:900; color:{score_color}; letter-spacing:-0.04em; line-height:1;">{score:.0f}</div>
            <div style="color:#475569; font-size:0.8rem; margin-top:4px;">/ 100 points</div>
            <div style="margin-top:12px;">
                <span class="status-badge {'status-success' if score>=80 else 'status-warning' if score>=60 else 'status-error'}">{grade}</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

    with right_col:
        # Auto-generated summary
        top_issues = err_by_col.most_common(3)
        top_issue_text = ", ".join([f"`{c[0]}`" for c in top_issues]) if top_issues else "none detected"
        top_type_text = err_by_type.most_common(1)[0][0].replace("_"," ") if err_by_type else "none"

        summary = f"""The dataset **{upload.file_name}** contains **{upload.total_rows:,} total records** with a validation pass rate of **{success_rate:.1f}%**.

**{total_errs:,} validation issues** were detected across {len(err_by_col)} columns. The most error-prone columns are {top_issue_text}, and the most common error category is **{top_type_text}**.

**Recommendations:**
- Review phone number formats — ensure country codes are correct and digit counts match country rules.
- Standardize date fields to `YYYY-MM-DD` format before uploading.
- Check SKU values — they must follow the pattern `SKU-12345`.
- Verify payment mode values against the allowed list: UPI, Credit Card, Debit Card, Cash, Wallet, Net Banking.
"""
        st.markdown(f'<div class="card"><div class="card-title">AI Analysis Summary</div>', unsafe_allow_html=True)
        st.markdown(summary)
        st.markdown('</div>', unsafe_allow_html=True)

    # --- Chat Interface ---
    st.markdown('<hr class="divider">', unsafe_allow_html=True)
    st.markdown('<div class="card-title" style="margin-bottom:0.5rem;">Chat with your Data</div>', unsafe_allow_html=True)
    st.markdown('<p style="color:#64748B; font-size:0.85rem; margin-bottom:1rem;">Ask any question about the errors in your dataset, or click a suggestion below.</p>', unsafe_allow_html=True)

    # Suggested Questions Pills
    s1, s2, s3, s4 = st.columns(4)
    suggestion = None
    if s1.button(":material/dashboard: Summarize errors", use_container_width=True): suggestion = "Summarize the errors"
    if s2.button(":material/call: Why did phones fail?", use_container_width=True): suggestion = "Why did phones fail?"
    if s3.button(":material/calendar_month: Date issues?", use_container_width=True): suggestion = "What are the date issues?"
    if s4.button(":material/lightbulb: How to improve?", use_container_width=True): suggestion = "How can I improve?"

    st.markdown("<br>", unsafe_allow_html=True)

    # Chat Container
    chat_container = st.container(height=400)
    
    if "messages" not in st.session_state:
        st.session_state.messages = [{
            "role": "assistant",
            "content": f"Hello! I've analyzed `{upload.file_name}`. It scored **{score:.0f}/100** with **{total_errs:,} errors**. What would you like to know?"
        }]

    with chat_container:
        for msg in st.session_state.messages:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])

    # Input Handling
    prompt = st.chat_input("Ask about your data errors...")
    active_prompt = prompt or suggestion

    if active_prompt:
        st.session_state.messages.append({"role": "user", "content": active_prompt})
        with chat_container:
            with st.chat_message("user"):
                st.markdown(active_prompt)

        p = active_prompt.lower()

        # Build contextual response
        if "phone" in p:
            n = sum(1 for e in errors if e.column_name in ["phone", "phone_number"])
            res = f"There are **{n} phone number errors** in your dataset.\n\n**Common causes:**\n- **Length mismatch**: Incorrect number of digits for the country.\n- **Invalid characters**: Contains letters or symbols.\n- **Country code mismatch**: The number does not match the configured rules."
        elif "date" in p:
            n = sum(1 for e in errors if "date" in e.column_name.lower())
            res = f"**{n} date errors** were found. Supported formats include `YYYY-MM-DD` and `DD-MM-YYYY`. Issues are usually:\n- Completely wrong format\n- Invalid day/month values\n- Delivery date appearing before order date"
        elif "sku" in p or "product" in p:
            n = sum(1 for e in errors if e.column_name in ["sku", "product_name"])
            res = f"**{n} product/SKU errors** detected. SKUs must follow the exact pattern `SKU-<digits>` (e.g., `SKU-10041`)."
        elif "payment" in p:
            n = sum(1 for e in errors if "payment" in e.column_name.lower())
            res = f"**{n} payment errors** found. Values must perfectly match the allow-list configured in Settings."
        elif "summar" in p or "overview" in p:
            top3 = err_by_col.most_common(3)
            breakdown = "\n".join([f"- **{c}**: {n} errors" for c, n in top3])
            res = f"### Summary for `{upload.file_name}`\n\n- **Total Records:** {upload.total_rows:,}\n- **Valid:** {upload.valid_rows:,} ({success_rate:.1f}%)\n- **Invalid:** {upload.invalid_rows:,}\n- **Quality Score:** {score:.0f}/100\n\n**Top failing columns:**\n{breakdown}"
        elif "duplicate" in p or "order" in p:
            n = sum(1 for e in errors if e.error_type == "duplicate")
            res = f"**{n} duplicate order ID errors** detected. Every order must have a unique `order_id`."
        elif "how" in p and "improv" in p:
            res = "### How to Improve\n1. **Fix phone formats** — strip spaces and ensure correct digit count per country.\n2. **Normalize dates** — convert all dates to `YYYY-MM-DD`.\n3. **Validate SKUs** — enforce the `SKU-XXXXX` pattern.\n4. **Standardize payment modes** — use a controlled vocabulary."
        else:
            res = f"Based on my analysis of `{upload.file_name}`, the primary issues are concentrated in phone number formats and date fields. Your dataset scored **{score:.0f}/100**."

        with chat_container:
            with st.chat_message("assistant"):
                placeholder = st.empty()
                displayed = ""
                for word in res.split(" "):
                    displayed += word + " "
                    placeholder.markdown(displayed + "▌")
                    time.sleep(0.02)
                placeholder.markdown(displayed)

        st.session_state.messages.append({"role": "assistant", "content": displayed})
        st.rerun()

finally:
    db.close()
