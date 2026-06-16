import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import ValidationRule

router = APIRouter(prefix="/api/rules", tags=["rules"])


class RuleCreate(BaseModel):
    country_name: str
    country_code: str
    field_name: str
    validation_type: str
    rule_value: str
    is_active: bool = True


class RuleUpdate(BaseModel):
    country_name: Optional[str] = None
    country_code: Optional[str] = None
    field_name: Optional[str] = None
    validation_type: Optional[str] = None
    rule_value: Optional[str] = None
    is_active: Optional[bool] = None


@router.get("")
def list_rules(db: Session = Depends(get_db)):
    rules = db.query(ValidationRule).order_by(ValidationRule.created_at.desc()).all()
    return [
        {
            "id": r.id,
            "country_name": r.country_name,
            "country_code": r.country_code,
            "field_name": r.field_name,
            "validation_type": r.validation_type,
            "rule_value": r.rule_value,
            "is_active": r.is_active,
            "version": r.version,
            "created_at": r.created_at.isoformat(),
        }
        for r in rules
    ]


@router.post("")
def create_rule(rule: RuleCreate, db: Session = Depends(get_db)):
    r = ValidationRule(
        id=str(uuid.uuid4()),
        country_name=rule.country_name,
        country_code=rule.country_code,
        field_name=rule.field_name,
        validation_type=rule.validation_type,
        rule_value=rule.rule_value,
        is_active=rule.is_active,
    )
    db.add(r)
    db.commit()
    return {"id": r.id, "message": "Rule created successfully"}


@router.put("/{rule_id}")
def update_rule(rule_id: str, rule: RuleUpdate, db: Session = Depends(get_db)):
    r = db.query(ValidationRule).filter(ValidationRule.id == rule_id).first()
    if not r:
        raise HTTPException(404, "Rule not found")
    for field, value in rule.model_dump(exclude_unset=True).items():
        setattr(r, field, value)
    r.version += 1
    db.commit()
    return {"message": "Rule updated successfully"}


@router.delete("/{rule_id}")
def delete_rule(rule_id: str, db: Session = Depends(get_db)):
    r = db.query(ValidationRule).filter(ValidationRule.id == rule_id).first()
    if not r:
        raise HTTPException(404, "Rule not found")
    r.is_active = False
    db.commit()
    return {"message": "Rule disabled successfully"}


@router.post("/seed")
def seed_default_rules(db: Session = Depends(get_db)):
    if db.query(ValidationRule).count() > 0:
        return {"message": "Rules already exist"}
    defaults = [
        ValidationRule(id=str(uuid.uuid4()), country_name="India", country_code="+91", field_name="phone", validation_type="phone_length", rule_value="10"),
        ValidationRule(id=str(uuid.uuid4()), country_name="Singapore", country_code="+65", field_name="phone", validation_type="phone_length", rule_value="8"),
        ValidationRule(id=str(uuid.uuid4()), country_name="Global", country_code="", field_name="email", validation_type="email_format", rule_value="standard"),
        ValidationRule(id=str(uuid.uuid4()), country_name="Global", country_code="", field_name="payment_method", validation_type="enum", rule_value="UPI,Card,Wallet,Net Banking,Cash"),
    ]
    for r in defaults:
        db.add(r)
    db.commit()
    return {"message": f"Seeded {len(defaults)} default rules"}
