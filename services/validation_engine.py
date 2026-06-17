import re
from datetime import datetime

import pandas as pd

from services.column_mapper import map_columns
from services.validators import (
    validate_email, validate_phone, validate_date, validate_time,
    validate_payment, validate_product, validate_order, ValidationResult,
)


def clean_whitespace(value) -> str:
    if pd.isna(value):
        return value
    return " ".join(str(value).split())


def clean_phone(value) -> str:
    if pd.isna(value) or str(value).strip() == "":
        return value
    cleaned = re.sub(r"[\s\-().]", "", str(value).strip())
    if cleaned.startswith("+91"):
        cleaned = cleaned[3:]
    elif cleaned.startswith("91") and len(cleaned) > 10:
        cleaned = cleaned[2:]
    elif cleaned.startswith("+65"):
        cleaned = cleaned[3:]
    elif cleaned.startswith("65") and len(cleaned) > 8:
        cleaned = cleaned[2:]
    return cleaned


def clean_email(value) -> str:
    if pd.isna(value):
        return value
    return str(value).strip().lower()


def clean_name(value) -> str:
    if pd.isna(value):
        return value
    return " ".join(str(value).split()).title()


def normalize_date(value) -> str:
    if pd.isna(value) or str(value).strip() == "":
        return value
    from services.validators import parse_date
    parsed = parse_date(str(value))
    if parsed:
        return parsed.strftime("%Y-%m-%d")
    return value


def apply_cleaning(df: pd.DataFrame) -> pd.DataFrame:
    cleaned = df.copy()
    col_map = {c: c for c in cleaned.columns}

    for col in cleaned.columns:
        canonical = col
        if col in ("phone", "mobile", "phone_no", "contact_number"):
            cleaned[col] = cleaned[col].apply(clean_phone)
        elif col in ("email", "email_address", "customer_email"):
            cleaned[col] = cleaned[col].apply(clean_email)
        elif col in ("customer_name", "name", "buyer_name"):
            cleaned[col] = cleaned[col].apply(clean_name)
        elif "date" in col.lower():
            cleaned[col] = cleaned[col].apply(normalize_date)
        elif col in ("customer_name",):
            cleaned[col] = cleaned[col].apply(clean_whitespace)

    for col in cleaned.select_dtypes(include=["object"]).columns:
        cleaned[col] = cleaned[col].apply(lambda x: clean_whitespace(x) if isinstance(x, str) else x)

    return cleaned


def get_cell(row: pd.Series, *names: str):
    for n in names:
        if n in row.index and not pd.isna(row[n]):
            return row[n]
    return ""


def run_validation(df: pd.DataFrame, phone_rules: list[dict], user_mapping: dict | None = None) -> tuple[list[dict], pd.DataFrame]:
    """Validate dataframe and return errors + cleaned dataframe."""
    errors: list[dict] = []
    seen_order_ids: set[str] = set()
    seen_txn_ids: set[str] = set()

    if user_mapping:
        mapping = {k: v for k, v in user_mapping.items() if v and v != "(Ignore)"}
    else:
        mapping = map_columns(list(df.columns))
    df = df.rename(columns=mapping)

    for idx, row in df.iterrows():
        row_num = int(idx) + 2  # 1-indexed + header

        order_errors = validate_order(
            get_cell(row, "order_id"),
            get_cell(row, "customer_name"),
            get_cell(row, "order_date"),
            get_cell(row, "delivery_date"),
            row_num, seen_order_ids,
        )
        errors.extend([e.to_dict() for e in order_errors])

        email_errors = validate_email(get_cell(row, "email"), row_num)
        errors.extend([e.to_dict() for e in email_errors])

        phone_errors = validate_phone(
            get_cell(row, "phone"), row_num, phone_rules,
            country=str(get_cell(row, "country")),
        )
        errors.extend([e.to_dict() for e in phone_errors])

        for date_col in ["order_date", "delivery_date"]:
            if date_col in df.columns:
                date_errors = validate_date(get_cell(row, date_col), row_num, date_col, allow_future=(date_col == "delivery_date"))
                errors.extend([e.to_dict() for e in date_errors])

        if "time" in df.columns:
            time_errors = validate_time(get_cell(row, "time"), row_num)
            errors.extend([e.to_dict() for e in time_errors])

        payment_errors = validate_payment(get_cell(row, "payment_method"), get_cell(row, "transaction_id"), row_num)
        errors.extend([e.to_dict() for e in payment_errors])

        txn = str(get_cell(row, "transaction_id")).strip()
        if txn and txn.lower() != "nan":
            if txn in seen_txn_ids:
                errors.append(ValidationResult(row_num, "transaction_id", "high", f"Duplicate transaction ID: {txn}", "duplicate").to_dict())
            else:
                seen_txn_ids.add(txn)

        if any(c in df.columns for c in ["sku", "quantity", "unit_price", "total_price", "product_name"]):
            product_errors = validate_product(
                get_cell(row, "product_name"), get_cell(row, "sku"), get_cell(row, "quantity"),
                get_cell(row, "unit_price"), get_cell(row, "total_price"), row_num,
            )
            errors.extend([e.to_dict() for e in product_errors])

    cleaned_df = apply_cleaning(df)
    return errors, cleaned_df


def compute_quality_score(total_rows: int, errors: list[dict], duplicate_count: int = 0) -> dict:
    if total_rows == 0:
        return {"score": 0, "completeness": 0, "accuracy": 0, "duplicates": 0, "formatting": 0, "label": "Poor"}

    rows_with_errors = len(set(e["row"] for e in errors))
    high_errors = [e for e in errors if e.get("severity") in ("high", "critical")]
    format_errors = [e for e in errors if e.get("error_type") in ("format_error", "invalid_chars")]

    completeness = max(0, 100 - (len([e for e in errors if e.get("error_type") == "missing_value"]) / max(total_rows, 1)) * 100)
    accuracy = max(0, 100 - (len(high_errors) / max(total_rows, 1)) * 100)
    dup_penalty = min(100, (duplicate_count / max(total_rows, 1)) * 100)
    duplicates = max(0, 100 - dup_penalty * 10)
    formatting = max(0, 100 - (len(format_errors) / max(total_rows, 1)) * 100)

    score = round(completeness * 0.4 + accuracy * 0.4 + duplicates * 0.1 + formatting * 0.1, 1)

    if score >= 90:
        label = "Excellent"
    elif score >= 75:
        label = "Good"
    elif score >= 60:
        label = "Fair"
    elif score >= 40:
        label = "Poor"
    else:
        label = "Critical"

    return {
        "score": score,
        "completeness": round(completeness, 1),
        "accuracy": round(accuracy, 1),
        "duplicates": round(duplicates, 1),
        "formatting": round(formatting, 1),
        "label": label,
        "rows_with_errors": rows_with_errors,
    }
