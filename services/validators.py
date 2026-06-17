import re
from datetime import datetime, date
from typing import Any

DISPOSABLE_DOMAINS = {
    "mailinator.com", "tempmail.com", "throwaway.email", "guerrillamail.com",
    "10minutemail.com", "yopmail.com", "trashmail.com", "fakeinbox.com",
}

VALID_PAYMENT_METHODS = {"upi", "card", "wallet", "net banking", "net_banking", "cash", "credit card", "debit card"}

EMAIL_REGEX = re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")

DATE_FORMATS = [
    "%Y-%m-%d", "%d-%m-%Y", "%d/%m/%Y", "%m/%d/%Y",
    "%Y/%m/%d", "%d.%m.%Y", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H:%M:%S.%f",
    "%Y-%m-%dT%H:%M:%SZ",
]

TIME_FORMATS = ["%H:%M:%S", "%H:%M", "%I:%M %p", "%I:%M:%S %p"]


class ValidationResult:
    def __init__(self, row: int, column: str, severity: str, error: str, error_type: str = "validation"):
        self.row = row
        self.column = column
        self.severity = severity
        self.error = error
        self.error_type = error_type

    def to_dict(self) -> dict[str, Any]:
        return {
            "row": self.row,
            "column": self.column,
            "severity": self.severity,
            "error": self.error,
            "error_type": self.error_type,
        }


def validate_email(value: str, row: int, column: str = "email") -> list[ValidationResult]:
    errors: list[ValidationResult] = []
    if not value or str(value).strip() == "" or str(value).lower() == "nan":
        return [ValidationResult(row, column, "high", "Missing email address", "missing_value")]
    val = str(value).strip()
    if not EMAIL_REGEX.match(val):
        errors.append(ValidationResult(row, column, "high", "Invalid email format", "format_error"))
    if ".." in val or val.startswith(".") or val.endswith("."):
        errors.append(ValidationResult(row, column, "medium", "Invalid characters in email", "invalid_chars"))
    domain = val.split("@")[-1].lower() if "@" in val else ""
    if domain in DISPOSABLE_DOMAINS:
        errors.append(ValidationResult(row, column, "medium", f"Disposable email domain: {domain}", "disposable_email"))
    return errors


def validate_phone(value: str, row: int, country_rules: list[dict], country: str = "", column: str = "phone") -> list[ValidationResult]:
    errors: list[ValidationResult] = []
    if not value or str(value).strip() == "" or str(value).lower() == "nan":
        return [ValidationResult(row, column, "high", "Missing phone number", "missing_value")]

    cleaned = re.sub(r"[\s\-().+]", "", str(value).strip())
    if cleaned.startswith("91") and len(cleaned) > 10:
        cleaned = cleaned[2:]
    elif cleaned.startswith("65") and len(cleaned) > 8:
        cleaned = cleaned[2:]

    if not cleaned.isdigit():
        errors.append(ValidationResult(row, column, "high", "Phone number must be numeric only", "format_error"))
        return errors

    rule = None
    country_lower = str(country).strip().lower() if country and str(country).lower() != "nan" else ""
    for r in country_rules:
        if r.get("country_name", "").lower() == country_lower or r.get("country_code", "") in str(value):
            rule = r
            break

    if not rule and country_rules:
        rule = country_rules[0]

    if rule:
        expected_len = int(rule.get("phone_length", rule.get("rule_value", "10")))
        code = rule.get("country_code", rule.get("code", ""))
        if len(cleaned) != expected_len:
            errors.append(ValidationResult(
                row, column, "high",
                f"Invalid phone number length: expected {expected_len} digits for {rule.get('country_name', 'country')}",
                "length_error",
            ))
        raw = str(value).strip()
        if code and code.replace("+", "") not in raw.replace("+", "").replace("-", "").replace(" ", "") and country_lower:
            if not any(raw.startswith(c) for c in [code, code.replace("+", ""), f"+{code.replace('+','')}"]):
                pass  # lenient if digits match after strip
    elif len(cleaned) < 8 or len(cleaned) > 15:
        errors.append(ValidationResult(row, column, "medium", "Phone number length out of range (8-15 digits)", "length_error"))

    return errors


def parse_date(value: str) -> date | None:
    if not value or str(value).strip() == "" or str(value).lower() == "nan":
        return None
    val = str(value).strip()
    for fmt in DATE_FORMATS:
        try:
            return datetime.strptime(val[:26], fmt).date()
        except ValueError:
            continue
    try:
        return datetime.fromisoformat(val.replace("Z", "+00:00")).date()
    except ValueError:
        return None


def validate_date(value: str, row: int, column: str = "order_date", allow_future: bool = False) -> list[ValidationResult]:
    errors: list[ValidationResult] = []
    if not value or str(value).strip() == "" or str(value).lower() == "nan":
        return [ValidationResult(row, column, "high", "Missing date value", "missing_value")]
    parsed = parse_date(str(value))
    if parsed is None:
        errors.append(ValidationResult(row, column, "high", f"Malformed or unsupported date format: {value}", "format_error"))
    elif not allow_future and parsed > date.today():
        errors.append(ValidationResult(row, column, "medium", "Future date detected", "future_date"))
    return errors


def validate_time(value: str, row: int, column: str = "time") -> list[ValidationResult]:
    errors: list[ValidationResult] = []
    if not value or str(value).strip() == "" or str(value).lower() == "nan":
        return []
    val = str(value).strip()
    for fmt in TIME_FORMATS:
        try:
            datetime.strptime(val, fmt)
            return errors
        except ValueError:
            continue
    errors.append(ValidationResult(row, column, "medium", f"Invalid time format: {value}", "format_error"))
    return errors


def validate_payment(method: str, txn_id: str, row: int) -> list[ValidationResult]:
    errors: list[ValidationResult] = []
    if not method or str(method).strip() == "" or str(method).lower() == "nan":
        errors.append(ValidationResult(row, "payment_method", "high", "Missing payment method", "missing_value"))
    elif str(method).strip().lower() not in VALID_PAYMENT_METHODS:
        errors.append(ValidationResult(row, "payment_method", "high", f"Unsupported payment method: {method}", "unsupported_method"))
    if not txn_id or str(txn_id).strip() == "" or str(txn_id).lower() == "nan":
        if method and str(method).strip().lower() not in ("cash",):
            errors.append(ValidationResult(row, "transaction_id", "high", "Missing transaction ID", "missing_value"))
    return errors


def validate_product(product_name: str, sku: str, qty: Any, unit_price: Any, total_price: Any, row: int) -> list[ValidationResult]:
    errors: list[ValidationResult] = []
    q: float | None = None
    up: float | None = None
    if not product_name or str(product_name).strip() == "" or str(product_name).lower() == "nan":
        errors.append(ValidationResult(row, "product_name", "medium", "Missing product name", "missing_value"))
    if not sku or str(sku).strip() == "" or str(sku).lower() == "nan":
        errors.append(ValidationResult(row, "sku", "high", "Missing SKU", "missing_value"))
    else:
        if not re.match(r"^SKU-\d+$", str(sku).strip(), re.IGNORECASE):
            errors.append(ValidationResult(row, "sku", "medium", f"Invalid SKU format: {sku}", "format_error"))
    try:
        q = float(qty)
        if q <= 0:
            errors.append(ValidationResult(row, "quantity", "high", "Quantity must be greater than 0", "range_error"))
    except (TypeError, ValueError):
        errors.append(ValidationResult(row, "quantity", "high", f"Invalid quantity: {qty}", "format_error"))
    try:
        up = float(unit_price)
        if up < 0:
            errors.append(ValidationResult(row, "unit_price", "high", "Unit price cannot be negative", "range_error"))
    except (TypeError, ValueError):
        errors.append(ValidationResult(row, "unit_price", "medium", f"Invalid unit price: {unit_price}", "format_error"))
    try:
        tp = float(total_price)
        if tp < 0:
            errors.append(ValidationResult(row, "total_price", "high", "Total price cannot be negative", "range_error"))
        if up is not None and q is not None:
            expected = round(q * up, 2)
            if abs(tp - expected) > 0.02:
                errors.append(ValidationResult(
                    row, "total_price", "high",
                    f"Total price mismatch: expected {expected}, got {tp} (qty × unit_price)",
                    "calculation_error",
                ))
    except (TypeError, ValueError):
        errors.append(ValidationResult(row, "total_price", "medium", f"Invalid total price: {total_price}", "format_error"))
    return errors


def validate_order(
    order_id: str, customer_name: str, order_date: str, delivery_date: str,
    row: int, seen_order_ids: set[str],
) -> list[ValidationResult]:
    errors: list[ValidationResult] = []
    if not order_id or str(order_id).strip() == "" or str(order_id).lower() == "nan":
        errors.append(ValidationResult(row, "order_id", "critical", "Missing order ID", "missing_value"))
    else:
        oid = str(order_id).strip()
        if oid in seen_order_ids:
            errors.append(ValidationResult(row, "order_id", "high", f"Duplicate order ID: {oid}", "duplicate"))
        else:
            seen_order_ids.add(oid)
    if not customer_name or str(customer_name).strip() == "" or str(customer_name).lower() == "nan":
        errors.append(ValidationResult(row, "customer_name", "medium", "Missing customer name", "missing_value"))
    od = parse_date(str(order_date)) if order_date and str(order_date).lower() != "nan" else None
    dd = parse_date(str(delivery_date)) if delivery_date and str(delivery_date).lower() != "nan" else None
    if od and dd and dd < od:
        errors.append(ValidationResult(
            row, "delivery_date", "high",
            "Delivery date is before order date",
            "relationship_error",
        ))
    return errors
