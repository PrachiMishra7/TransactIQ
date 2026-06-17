import re
from datetime import datetime

import pandas as pd

from services.column_mapper import map_columns
from services.validators import (
    validate_email, validate_phone, validate_date, validate_time,
    validate_payment, validate_product, validate_order, ValidationResult, parse_date
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


def run_validation(df: pd.DataFrame, phone_rules: list[dict], user_mapping: dict | None = None, validation_settings: dict | None = None) -> tuple[list[dict], pd.DataFrame]:
    """Validate dataframe and return errors + cleaned dataframe."""
    errors: list[dict] = []
    seen_order_ids: set[str] = set()
    seen_txn_ids: set[str] = set()

    if validation_settings is None:
        validation_settings = {"phone": True, "date": True, "duplicate": True, "payment": True}

    if user_mapping:
        mapping = {k: v for k, v in user_mapping.items() if v and v != "(Ignore)"}
    else:
        mapping = map_columns(list(df.columns))
    df = df.rename(columns=mapping)

    for idx, row in df.iterrows():
        row_num = int(idx) + 2  # 1-indexed + header

        # Validate order columns if they exist in the dataframe
        if "order_id" in df.columns:
            oid = get_cell(row, "order_id")
            if not oid or str(oid).strip() == "" or str(oid).lower() == "nan":
                errors.append(ValidationResult(row_num, "order_id", "critical", "Missing order ID", "missing_value").to_dict())
            else:
                oid_str = str(oid).strip()
                if oid_str in seen_order_ids:
                    errors.append(ValidationResult(row_num, "order_id", "high", f"Duplicate order ID: {oid_str}", "duplicate").to_dict())
                else:
                    seen_order_ids.add(oid_str)
                    
        if "customer_name" in df.columns:
            name = get_cell(row, "customer_name")
            if not name or str(name).strip() == "" or str(name).lower() == "nan":
                errors.append(ValidationResult(row_num, "customer_name", "medium", "Missing customer name", "missing_value").to_dict())
                
        if "order_date" in df.columns and "delivery_date" in df.columns:
            od = parse_date(str(get_cell(row, "order_date")))
            dd = parse_date(str(get_cell(row, "delivery_date")))
            if od and dd and dd < od:
                errors.append(ValidationResult(row_num, "delivery_date", "high", "Delivery date is before order date", "relationship_error").to_dict())

        if "email" in df.columns:
            email_errors = validate_email(get_cell(row, "email"), row_num)
            errors.extend([e.to_dict() for e in email_errors])

        if "phone" in df.columns and validation_settings.get("phone", True):
            phone_errors = validate_phone(
                get_cell(row, "phone"), row_num, phone_rules,
                country=str(get_cell(row, "country")) if "country" in df.columns else "",
            )
            errors.extend([e.to_dict() for e in phone_errors])

        if validation_settings.get("date", True):
            for date_col in ["order_date", "delivery_date"]:
                if date_col in df.columns:
                    date_errors = validate_date(get_cell(row, date_col), row_num, date_col, allow_future=(date_col == "delivery_date"))
                    errors.extend([e.to_dict() for e in date_errors])

        if "time" in df.columns:
            time_errors = validate_time(get_cell(row, "time"), row_num)
            errors.extend([e.to_dict() for e in time_errors])

        if validation_settings.get("payment", True):
            if "payment_method" in df.columns or "transaction_id" in df.columns:
                method = get_cell(row, "payment_method") if "payment_method" in df.columns else "cash"
                txn_id = get_cell(row, "transaction_id") if "transaction_id" in df.columns else ""
                payment_errors = validate_payment(method, txn_id, row_num)
                # Filter errors to only check columns that are in df.columns
                payment_errors = [
                    e for e in payment_errors
                    if (e.column == "payment_method" and "payment_method" in df.columns) or
                       (e.column == "transaction_id" and "transaction_id" in df.columns)
                ]
                errors.extend([e.to_dict() for e in payment_errors])

        if "transaction_id" in df.columns and validation_settings.get("duplicate", True):
            txn = str(get_cell(row, "transaction_id")).strip()
            if txn and txn.lower() != "nan":
                if txn in seen_txn_ids:
                    errors.append(ValidationResult(row_num, "transaction_id", "high", f"Duplicate transaction ID: {txn}", "duplicate").to_dict())
                else:
                    seen_txn_ids.add(txn)

        if any(c in df.columns for c in ["sku", "quantity", "unit_price", "total_price", "product_name"]):
            product_errors = validate_product(
                get_cell(row, "product_name") if "product_name" in df.columns else "dummy",
                get_cell(row, "sku") if "sku" in df.columns else "SKU-000",
                get_cell(row, "quantity") if "quantity" in df.columns else 1,
                get_cell(row, "unit_price") if "unit_price" in df.columns else 0.0,
                get_cell(row, "total_price") if "total_price" in df.columns else 0.0,
                row_num,
            )
            # Filter errors to only check columns that are in df.columns
            product_errors = [e for e in product_errors if e.column in df.columns]
            errors.extend([e.to_dict() for e in product_errors])

    cleaned_df = apply_cleaning(df)
    return errors, cleaned_df


def compute_quality_score(total_rows: int, errors: list[dict], duplicate_count: int = 0) -> dict:
    if total_rows == 0:
        return {"score": 0, "completeness": 0, "accuracy": 0, "duplicates": 0, "formatting": 0, "label": "Poor"}

    # Count UNIQUE rows that have specific types of errors, rather than total raw errors,
    # because a single row could have 5 errors and disproportionately tank the score.
    rows_with_any_error = len(set(e["row"] for e in errors))
    
    high_error_rows = len(set(e["row"] for e in errors if e.get("severity") in ("high", "critical")))
    format_error_rows = len(set(e["row"] for e in errors if e.get("error_type") in ("format_error", "invalid_chars", "length_error")))
    missing_value_rows = len(set(e["row"] for e in errors if e.get("error_type") == "missing_value"))

    completeness = max(0, 100 - (missing_value_rows / max(total_rows, 1)) * 100)
    accuracy = max(0, 100 - (high_error_rows / max(total_rows, 1)) * 100)
    
    dup_penalty = (duplicate_count / max(total_rows, 1)) * 100
    duplicates = max(0, 100 - dup_penalty * 1.5)  # 1.5x penalty for duplicates
    
    formatting = max(0, 100 - (format_error_rows / max(total_rows, 1)) * 100)

    # Re-weight: Completeness and Accuracy are most important
    score = round(completeness * 0.35 + accuracy * 0.40 + duplicates * 0.15 + formatting * 0.10, 1)

    # For a premium SaaS feel, we apply a smoothing curve to the score so it feels realistic but forgiving.
    # A score of 50 gets bumped to ~75. A score of 90 stays around 90.
    adjusted_score = min(100.0, score + (100 - score) * 0.4)

    if adjusted_score >= 90:
        label = "Excellent"
    elif adjusted_score >= 80:
        label = "Good"
    elif adjusted_score >= 65:
        label = "Fair"
    elif adjusted_score >= 50:
        label = "Poor"
    else:
        label = "Critical"

    return {
        "score": round(adjusted_score, 1),
        "completeness": round(completeness, 1),
        "accuracy": round(accuracy, 1),
        "duplicates": round(duplicates, 1),
        "formatting": round(formatting, 1),
        "label": label,
        "rows_with_errors": rows_with_any_error,
    }
