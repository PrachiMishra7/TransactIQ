"""Smart column mapping - maps variant column names to canonical fields."""

COLUMN_ALIASES: dict[str, list[str]] = {
    "order_id": ["order_id", "orderid", "order_no", "order_number", "order #"],
    "customer_name": ["customer_name", "customer", "name", "buyer_name", "client_name"],
    "phone": ["phone", "mobile", "phone_no", "phone_number", "contact_number", "mobile_no", "cell"],
    "email": ["email", "email_id", "email_address", "e_mail", "customer_email"],
    "address": ["address", "shipping_address", "delivery_address", "addr"],
    "order_date": ["order_date", "date_ordered", "purchase_date", "order_dt"],
    "delivery_date": ["delivery_date", "ship_date", "delivery_dt", "expected_delivery"],
    "sku": ["sku", "product_sku", "item_sku", "product_code", "item_code"],
    "product_name": ["product_name", "item_name", "product", "item"],
    "quantity": ["quantity", "qty", "units", "item_quantity"],
    "unit_price": ["unit_price", "price", "item_price", "unit_cost"],
    "total_price": ["total_price", "total", "line_total", "amount", "subtotal"],
    "payment_method": ["payment_method", "payment_type", "pay_method", "payment_mode"],
    "transaction_id": ["transaction_id", "txn_id", "payment_id", "transaction_ref"],
    "country": ["country", "country_name", "nation"],
}


def normalize_column_name(col: str) -> str:
    col_lower = col.strip().lower().replace(" ", "_")
    for canonical, aliases in COLUMN_ALIASES.items():
        if col_lower in aliases:
            return canonical
    return col_lower


def map_columns(columns: list[str]) -> dict[str, str]:
    """Returns mapping from original column name to canonical name."""
    mapping: dict[str, str] = {}
    used_canonical: set[str] = set()
    for col in columns:
        canonical = normalize_column_name(col)
        if canonical in used_canonical:
            mapping[col] = col.strip().lower().replace(" ", "_")
        else:
            mapping[col] = canonical
            if canonical in COLUMN_ALIASES:
                used_canonical.add(canonical)
    return mapping
