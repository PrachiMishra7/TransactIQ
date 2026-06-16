import uuid
from typing import Optional
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import func, cast, Date

from app.database import get_db
from app.models import Upload, ValidationError, ValidationRule, Report, ProcessingStatus

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


@router.get("/stats")
def get_dashboard_stats(db: Session = Depends(get_db)):
    total_files = db.query(Upload).filter(Upload.processing_status == ProcessingStatus.COMPLETED).count()
    total_records = db.query(func.coalesce(func.sum(Upload.total_rows), 0)).scalar()
    avg_score = db.query(func.coalesce(func.avg(Upload.quality_score), 0)).filter(
        Upload.processing_status == ProcessingStatus.COMPLETED
    ).scalar()
    active_rules = db.query(ValidationRule).filter(ValidationRule.is_active == True).count()

    return {
        "total_files_processed": total_files,
        "total_records_validated": int(total_records or 0),
        "average_quality_score": round(float(avg_score or 0), 1),
        "active_validation_rules": active_rules,
    }


@router.get("/charts/errors-by-type")
def errors_by_type(db: Session = Depends(get_db)):
    results = (
        db.query(ValidationError.error_type, func.count(ValidationError.id))
        .group_by(ValidationError.error_type)
        .order_by(func.count(ValidationError.id).desc())
        .limit(10)
        .all()
    )
    return [{"type": r[0].replace("_", " ").title(), "count": r[1]} for r in results]


@router.get("/charts/files-per-day")
def files_per_day(db: Session = Depends(get_db)):
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    results = (
        db.query(cast(Upload.created_at, Date).label("date"), func.count(Upload.id))
        .filter(Upload.created_at >= thirty_days_ago)
        .group_by(cast(Upload.created_at, Date))
        .order_by(cast(Upload.created_at, Date))
        .all()
    )
    return [{"date": r[0].isoformat(), "count": r[1]} for r in results]


@router.get("/charts/quality-trend")
def quality_trend(db: Session = Depends(get_db)):
    uploads = (
        db.query(Upload)
        .filter(Upload.processing_status == ProcessingStatus.COMPLETED)
        .order_by(Upload.created_at.desc())
        .limit(20)
        .all()
    )
    uploads.reverse()
    return [
        {"date": u.created_at.strftime("%Y-%m-%d"), "score": u.quality_score, "file_name": u.file_name}
        for u in uploads
    ]


@router.get("/charts/country-errors")
def country_errors(db: Session = Depends(get_db)):
    errors = db.query(ValidationError.error_message).all()
    india = sum(1 for e in errors if "india" in e[0].lower() or "+91" in e[0])
    singapore = sum(1 for e in errors if "singapore" in e[0].lower() or "+65" in e[0])
    other = len(errors) - india - singapore
    return [
        {"country": "India", "count": india},
        {"country": "Singapore", "count": singapore},
        {"country": "Other", "count": max(0, other)},
    ]
