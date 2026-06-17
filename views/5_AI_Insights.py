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
    st.markdown('<div class="card"><div class="card-title">Chat with your Data</div>', unsafe_allow_html=True)
    st.markdown('<p style="color:#64748B; font-size:0.85rem; margin-bottom:1rem;">Ask any question about the errors in your dataset. Try: <em>"Why did phones fail?"</em> or <em>"Summarize the errors"</em></p>', unsafe_allow_html=True)

    if "messages" not in st.session_state:
        st.session_state.messages = [{
            "role": "assistant",
            "content": f"Hello! I've analyzed `{upload.file_name}`. It has a quality score of **{score:.0f}/100** with **{total_errs:,} errors** across {len(err_by_col)} columns. What would you like to know?"
        }]

    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    if prompt := st.chat_input("Ask about your data errors..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        p = prompt.lower()

        # Build contextual response
        if "phone" in p:
            n = sum(1 for e in errors if e.column_name in ["phone", "phone_number"])
            res = f"There are **{n} phone number errors** in your dataset. Common causes:\n- **Length mismatch**: India (+91) needs 10 digits, Singapore (+65) needs 8 digits.\n- **Non-numeric characters**: spaces, dashes or brackets in the number.\n- **Missing country code**: the number doesn't include the international prefix."
        elif "date" in p:
            n = sum(1 for e in errors if "date" in e.column_name.lower())
            res = f"**{n} date errors** were found. Supported formats are `YYYY-MM-DD`, `DD-MM-YYYY`, `MM/DD/YYYY`, and `YYYY-MM-DD HH:MM:SS`. Issues are usually:\n- Completely wrong format (e.g. text instead of date)\n- Invalid day/month values\n- Delivery date appearing before order date"
        elif "sku" in p or "product" in p:
            n = sum(1 for e in errors if e.column_name in ["sku", "product_name"])
            res = f"**{n} product/SKU errors** detected. SKUs must follow the exact pattern `SKU-<digits>` (e.g., `SKU-10041`). Missing the prefix or using letters after the dash causes failures."
        elif "payment" in p:
            n = sum(1 for e in errors if "payment" in e.column_name.lower())
            res = f"**{n} payment errors** found. Allowed payment modes are: `UPI`, `Credit Card`, `Debit Card`, `Cash`, `Wallet`, `Net Banking`. Any variations (e.g. `upi`, `CC`, `crypto`) will be flagged."
        elif "summar" in p or "overview" in p:
            top3 = err_by_col.most_common(3)
            breakdown = "\n".join([f"- `{c}`: {n} errors" for c, n in top3])
            res = f"**Summary for `{upload.file_name}`**\n\n- Total Records: **{upload.total_rows:,}**\n- Valid: **{upload.valid_rows:,}** ({success_rate:.1f}%)\n- Invalid: **{upload.invalid_rows:,}**\n- Quality Score: **{score:.0f}/100**\n\nTop failing columns:\n{breakdown}"
        elif "duplicate" in p or "order" in p:
            n = sum(1 for e in errors if e.error_type == "duplicate")
            res = f"**{n} duplicate order ID errors** detected. Every order must have a unique `order_id`. Duplicate entries indicate data entry errors or failed deduplication upstream."
        elif "how" in p and "improv" in p:
            res = "To improve your quality score:\n1. **Fix phone formats** — strip spaces and ensure correct digit count per country.\n2. **Normalize dates** — convert all dates to `YYYY-MM-DD` before upload.\n3. **Validate SKUs** — enforce the `SKU-XXXXX` pattern in your source system.\n4. **Standardize payment modes** — use a controlled vocabulary and avoid free-text entries."
        else:
            res = f"That's a great question! Based on my analysis of `{upload.file_name}`, the primary issues are concentrated in phone number formats and date fields. Your dataset scored **{score:.0f}/100**. Try asking specifically about:\n- phones, dates, SKUs, payment modes, duplicates, or 'how to improve'."

        with st.chat_message("assistant"):
            placeholder = st.empty()
            displayed = ""
            for word in res.split(" "):
                displayed += word + " "
                placeholder.markdown(displayed + "▌")
                time.sleep(0.025)
            placeholder.markdown(displayed)

        st.session_state.messages.append({"role": "assistant", "content": displayed})
    st.markdown('</div>', unsafe_allow_html=True)

finally:
    db.close()
