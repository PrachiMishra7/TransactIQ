from collections import Counter
from typing import Any


def generate_ai_summary(
    total_rows: int,
    valid_rows: int,
    errors: list[dict],
    quality_score: float,
    file_name: str,
) -> str:
    """Generate intelligent validation summary (template-based with optional LLM hook)."""
    if total_rows == 0:
        return "No records were processed."

    pass_rate = round((valid_rows / total_rows) * 100, 1)
    error_types = Counter(e.get("error_type", "unknown") for e in errors)
    columns = Counter(e.get("column", "unknown") for e in errors)
    messages = Counter(e.get("error", "unknown") for e in errors)

    top_issue = messages.most_common(1)[0] if messages else ("None", 0)
    second_issue = messages.most_common(2)[1] if len(messages) > 1 else ("None", 0)
    top_field = columns.most_common(1)[0][0] if columns else "N/A"
    top_error_type = error_types.most_common(1)[0][0] if error_types else "N/A"

    country_errors: Counter = Counter()
    for e in errors:
        msg = e.get("error", "").lower()
        if "india" in msg or "+91" in msg:
            country_errors["India"] += 1
        elif "singapore" in msg or "+65" in msg:
            country_errors["Singapore"] += 1

    top_country = country_errors.most_common(1)[0][0] if country_errors else "N/A"

    severity_high = len([e for e in errors if e.get("severity") in ("high", "critical")])

    summary_parts = [
        f"Processed {total_rows:,} records from '{file_name}'.",
        f"{pass_rate}% of records passed validation ({valid_rows:,} valid, {total_rows - valid_rows:,} with issues).",
        f"Overall data quality score: {quality_score}/100.",
        "",
        "Key Insights:",
        f"• Most common issue: {top_issue[0]} ({top_issue[1]} occurrences)",
        f"• Second most common issue: {second_issue[0]} ({second_issue[1]} occurrences)",
        f"• Most problematic field: {top_field}",
        f"• Primary error category: {top_error_type.replace('_', ' ').title()}",
    ]

    if top_country != "N/A":
        summary_parts.append(f"• Country with highest error rate: {top_country}")

    summary_parts.extend([
        "",
        "Severity Breakdown:",
        f"• High/Critical severity errors: {severity_high}",
        f"• Total validation findings: {len(errors)}",
        "",
        "Recommended Actions:",
    ])

    recommendations = _get_recommendations(errors, top_field, top_issue[0])
    summary_parts.extend(f"• {r}" for r in recommendations)

    return "\n".join(summary_parts)


def _get_recommendations(errors: list[dict], top_field: str, top_issue: str) -> list[str]:
    recs: list[str] = []
    error_types = {e.get("error_type") for e in errors}

    if "phone" in top_field or "length_error" in error_types:
        recs.append("Verify mobile number formatting before upload — ensure country code and digit count match configured rules.")
    if "missing_value" in error_types:
        recs.append("Review source system exports for null/missing mandatory fields (order ID, email, transaction ID).")
    if "duplicate" in error_types:
        recs.append("Implement deduplication checks at the source before exporting transaction data.")
    if "calculation_error" in error_types:
        recs.append("Validate that quantity × unit price equals total price in the source ERP system.")
    if "disposable_email" in error_types:
        recs.append("Filter disposable email domains at registration to improve customer data quality.")
    if "format_error" in error_types:
        recs.append("Standardize date formats to YYYY-MM-DD across all data sources.")
    if not recs:
        recs.append("Data quality is good. Continue monitoring upload metrics via the dashboard.")
    return recs[:4]


def get_validation_insights(errors: list[dict], total_rows: int) -> dict[str, Any]:
    if not errors:
        return {
            "topError": "None",
            "mostProblematicField": "None",
            "countryWithHighestErrorRate": "None",
            "errorRateByType": {},
        }

    messages = Counter(e.get("error", "unknown") for e in errors)
    columns = Counter(e.get("column", "unknown") for e in errors)
    types = Counter(e.get("error_type", "unknown") for e in errors)

    country_errors: Counter = Counter()
    for e in errors:
        msg = e.get("error", "").lower()
        if "india" in msg:
            country_errors["India"] += 1
        elif "singapore" in msg:
            country_errors["Singapore"] += 1

    return {
        "topError": messages.most_common(1)[0][0],
        "topErrorCount": messages.most_common(1)[0][1],
        "mostProblematicField": columns.most_common(1)[0][0],
        "fieldErrorCount": columns.most_common(1)[0][1],
        "countryWithHighestErrorRate": country_errors.most_common(1)[0][0] if country_errors else "N/A",
        "errorRateByType": dict(types),
        "totalErrors": len(errors),
        "affectedRows": len(set(e["row"] for e in errors)),
        "errorRate": round(len(set(e["row"] for e in errors)) / max(total_rows, 1) * 100, 1),
    }
