import os
import uuid
import asyncio
from typing import Optional

from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, BackgroundTasks, Query
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from sqlalchemy import func, cast, Date
import pandas as pd

from app.database import get_db
from app.models import Upload, ValidationError, ValidationRule, Report, ProcessingStatus
from app.config import settings
from app.services.processor import process_upload
from app.services.chunking import chunk_csv
from app.services.ai_summary import get_validation_insights
from app.services.column_mapper import map_columns

router = APIRouter(prefix="/api/uploads", tags=["uploads"])


@router.post("")
async def upload_file(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    if not file.filename:
        raise HTTPException(400, "No file provided")

    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in (".csv", ".xlsx", ".xls"):
        raise HTTPException(400, "Only CSV and XLSX files are supported")

    upload_id = str(uuid.uuid4())
    os.makedirs(settings.upload_dir, exist_ok=True)
    file_path = os.path.join(settings.upload_dir, f"{upload_id}{ext}")

    content = await file.read()
    with open(file_path, "wb") as f:
        f.write(content)

    upload = Upload(
        id=upload_id,
        file_name=file.filename,
        file_size=len(content),
        processing_status=ProcessingStatus.UPLOADING,
    )
    db.add(upload)
    db.commit()

    background_tasks.add_task(_run_processing, upload_id, file_path)

    return {"upload_id": upload_id, "file_name": file.filename, "status": "processing"}


async def _run_processing(upload_id: str, file_path: str):
    from app.database import SessionLocal
    db = SessionLocal()
    try:
        await process_upload(db, upload_id, file_path)
    finally:
        db.close()


@router.get("/{upload_id}/status")
def get_status(upload_id: str, db: Session = Depends(get_db)):
    upload = db.query(Upload).filter(Upload.id == upload_id).first()
    if not upload:
        raise HTTPException(404, "Upload not found")

    status_order = [
        ProcessingStatus.UPLOADING, ProcessingStatus.PARSING, ProcessingStatus.VALIDATING,
        ProcessingStatus.CLEANING, ProcessingStatus.GENERATING_REPORTS, ProcessingStatus.COMPLETED,
    ]
    progress = 0
    if upload.processing_status == ProcessingStatus.FAILED:
        progress = 0
    elif upload.processing_status == ProcessingStatus.COMPLETED:
        progress = 100
    elif upload.processing_status in status_order:
        progress = int((status_order.index(upload.processing_status) + 1) / len(status_order) * 100)

    return {
        "upload_id": upload_id,
        "status": upload.processing_status.value,
        "progress": progress,
        "file_name": upload.file_name,
    }


@router.get("/{upload_id}/preview")
def get_preview(upload_id: str, db: Session = Depends(get_db)):
    upload = db.query(Upload).filter(Upload.id == upload_id).first()
    if not upload:
        raise HTTPException(404, "Upload not found")

    for ext in (".csv", ".xlsx", ".xls"):
        path = os.path.join(settings.upload_dir, f"{upload_id}{ext}")
        if os.path.exists(path):
            if ext == ".csv":
                df = pd.read_csv(path, nrows=20)
            else:
                df = pd.read_excel(path, nrows=20)
            mapping = map_columns(list(df.columns))
            return {
                "columns": list(df.columns),
                "column_mapping": mapping,
                "rows": df.fillna("").astype(str).to_dict(orient="records"),
                "total_preview_rows": len(df),
            }
    raise HTTPException(404, "File not found")


@router.get("/{upload_id}/results")
def get_results(upload_id: str, db: Session = Depends(get_db)):
    upload = db.query(Upload).filter(Upload.id == upload_id).first()
    if not upload:
        raise HTTPException(404, "Upload not found")

    report = db.query(Report).filter(Report.upload_id == upload_id).order_by(Report.generated_at.desc()).first()
    insights = get_validation_insights(
        [{"error": e.error_message, "column": e.column_name, "error_type": e.error_type, "severity": e.severity.value.lower(), "row": e.row_number}
         for e in upload.validation_errors],
        upload.total_rows,
    )

    return {
        "upload_id": upload_id,
        "file_name": upload.file_name,
        "status": upload.processing_status.value,
        "total_records": upload.total_rows,
        "valid_records": upload.valid_rows,
        "invalid_records": upload.invalid_rows,
        "warnings": upload.warning_rows,
        "quality_score": upload.quality_score,
        "quality_label": _score_label(upload.quality_score),
        "summary": report.summary if report else "",
        "insights": insights,
        "rule_version_id": upload.rule_version_id,
        "created_at": upload.created_at.isoformat(),
    }


def _score_label(score: float) -> str:
    if score >= 90: return "Excellent"
    if score >= 75: return "Good"
    if score >= 60: return "Fair"
    if score >= 40: return "Poor"
    return "Critical"


@router.get("/{upload_id}/errors")
def get_errors(
    upload_id: str,
    search: Optional[str] = None,
    severity: Optional[str] = None,
    error_type: Optional[str] = None,
    sort_by: str = "row_number",
    sort_order: str = "asc",
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=500),
    db: Session = Depends(get_db),
):
    query = db.query(ValidationError).filter(ValidationError.upload_id == upload_id)
    if search:
        query = query.filter(
            ValidationError.error_message.ilike(f"%{search}%") |
            ValidationError.column_name.ilike(f"%{search}%")
        )
    if severity:
        query = query.filter(ValidationError.severity == severity.upper())
    if error_type:
        query = query.filter(ValidationError.error_type == error_type)

    sort_col = getattr(ValidationError, sort_by, ValidationError.row_number)
    query = query.order_by(sort_col.desc() if sort_order == "desc" else sort_col.asc())

    total = query.count()
    errors = query.offset((page - 1) * page_size).limit(page_size).all()

    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "errors": [
            {
                "id": e.id,
                "row_number": e.row_number,
                "column_name": e.column_name,
                "error_type": e.error_type,
                "error_message": e.error_message,
                "severity": e.severity.value,
            }
            for e in errors
        ],
    }


@router.get("/{upload_id}/download/{file_type}")
def download_file(upload_id: str, file_type: str, db: Session = Depends(get_db)):
    upload = db.query(Upload).filter(Upload.id == upload_id).first()
    if not upload:
        raise HTTPException(404, "Upload not found")

    paths = {
        "cleaned": upload.cleaned_file_path,
        "errors": upload.error_file_path,
        "report": upload.report_file_path,
    }
    path = paths.get(file_type)
    if not path or not os.path.exists(path):
        raise HTTPException(404, f"{file_type} file not available")

    media = {"cleaned": "text/csv", "errors": "text/csv", "report": "application/pdf"}
    filename = {"cleaned": "cleaned.csv", "errors": "errors.csv", "report": "validation_report.pdf"}
    return FileResponse(path, media_type=media[file_type], filename=filename[file_type])


@router.get("")
def list_uploads(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    total = db.query(Upload).count()
    uploads = db.query(Upload).order_by(Upload.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()
    return {
        "total": total,
        "uploads": [
            {
                "id": u.id,
                "file_name": u.file_name,
                "file_size": u.file_size,
                "total_rows": u.total_rows,
                "valid_rows": u.valid_rows,
                "invalid_rows": u.invalid_rows,
                "quality_score": u.quality_score,
                "status": u.processing_status.value,
                "created_at": u.created_at.isoformat(),
            }
            for u in uploads
        ],
    }


@router.post("/chunk")
async def chunk_file(
    file: UploadFile = File(...),
    chunk_by: str = Query("row_count", pattern="^(row_count|file_size)$"),
    chunk_size: int = Query(1000, ge=100),
):
    if not file.filename:
        raise HTTPException(400, "No file provided")

    chunk_id = str(uuid.uuid4())
    os.makedirs(os.path.join(settings.output_dir, "chunks", chunk_id), exist_ok=True)
    file_path = os.path.join(settings.output_dir, "chunks", chunk_id, file.filename)
    content = await file.read()
    with open(file_path, "wb") as f:
        f.write(content)

    output_dir = os.path.join(settings.output_dir, "chunks", chunk_id, "output")
    chunks = chunk_csv(file_path, output_dir, chunk_by, chunk_size)

    return {"chunk_id": chunk_id, "total_chunks": len(chunks), "chunks": chunks}
