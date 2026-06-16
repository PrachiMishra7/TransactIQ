import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database import SessionLocal, engine
from app.models import Base, ValidationRule

def main():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        if db.query(ValidationRule).count() == 0:
            db.add_all([
                ValidationRule(country_name="India", country_code="+91", field_name="phone", validation_type="phone_length", rule_value="10"),
                ValidationRule(country_name="Singapore", country_code="+65", field_name="phone", validation_type="phone_length", rule_value="8"),
                ValidationRule(country_name="Global", country_code="", field_name="email", validation_type="email_format", rule_value="standard"),
                ValidationRule(country_name="Global", country_code="", field_name="payment_method", validation_type="enum", rule_value="UPI,Card,Wallet,Net Banking,Cash"),
            ])
            db.commit()
            print("Seeded default validation rules")
        else:
            print("Rules already seeded")
    finally:
        db.close()

if __name__ == "__main__":
    main()
