import os
import uuid
import asyncio
from datetime import datetime

import pandas as pd
from sqlalchemy.orm import Session

from config import settings
from models import Upload, ValidationError, ValidationRule, Report, ProcessingStatus, Severity, RuleVersion
from services.validation_engine import run_validation, compute_quality_score
from services.ai_summary import generate_ai_summary, get_validation_insights
from services.report_generator import generate_pdf_report, generate_error_excel, generate_cleaned_excel


async def update_status(db: Session, upload_id: str, status: ProcessingStatus):
    upload = db.query(Upload).filter(Upload.id == upload_id).first()
    if upload:
        upload.processing_status = status
        db.commit()
    await asyncio.sleep(0.3)


def load_phone_rules(db: Session) -> list[dict]:
    rules = db.query(ValidationRule).filter(
        ValidationRule.is_active == True,
        ValidationRule.field_name == "phone",
    ).all()
    result = []
    for r in rules:
        result.append({
            "country_name": r.country_name,
            "country_code": r.country_code,
            "phone_length": int(r.rule_value) if r.rule_value.isdigit() else 10,
            "rule_value": r.rule_value,
        })
    if not result:
        result = [
            {"country_name": "India", "country_code": "+91", "phone_length": 10},
            {"country_name": "Singapore", "country_code": "+65", "phone_length": 8},
        ]
    return result


def snapshot_rules(db: Session) -> tuple[str, int]:
    rules = db.query(ValidationRule).filter(ValidationRule.is_active == True).all()
    snapshot = [
        {
            "id": r.id, "country_name": r.country_name, "country_code": r.country_code,
            "field_name": r.field_name, "validation_type": r.validation_type,
            "rule_value": r.rule_value, "version": r.version,
        }
        for r in rules
    ]
    max_version = db.query(RuleVersion).count() + 1
    rv = RuleVersion(version=max_version, description=f"Auto-snapshot v{max_version}", rule_snapshot=snapshot)
    db.add(rv)
    db.commit()
    return rv.id, max_version


def parse_file(file_path: str) -> pd.DataFrame:
    ext = os.path.splitext(file_path)[1].lower()
    if ext in (".xlsx", ".xls"):
        return pd.read_excel(file_path)
    return pd.read_csv(file_path)


async def process_upload(db: Session, upload_id: str, file_path: str, user_mapping: dict | None = None, validation_settings: dict | None = None):
    upload = db.query(Upload).filter(Upload.id == upload_id).first()
    if not upload:
        return

    try:
        await update_status(db, upload_id, ProcessingStatus.UPLOADING)
        await update_status(db, upload_id, ProcessingStatus.PARSING)

        ext = os.path.splitext(file_path)[1].lower()
        if ext == ".csv":
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                total_rows = sum(1 for _ in f) - 1
        else:
            df_full = parse_file(file_path)
            total_rows = len(df_full)

        upload.total_rows = max(total_rows, 0)
        db.commit()

        rule_version_id, _ = snapshot_rules(db)
        upload.rule_version_id = rule_version_id

        await update_status(db, upload_id, ProcessingStatus.VALIDATING)
        phone_rules = load_phone_rules(db)
        
        errors = []
        cleaned_dfs = []
        actual_total_rows = 0
        
        if ext == ".csv" and total_rows > 0:
            CHUNK_SIZE = 50000
            for chunk in pd.read_csv(file_path, chunksize=CHUNK_SIZE):
                chunk = chunk.dropna(how="all")
                if chunk.empty:
                    continue
                actual_total_rows += len(chunk)
                chunk_errors, chunk_cleaned = run_validation(chunk, phone_rules, user_mapping=user_mapping, validation_settings=validation_settings)
                errors.extend(chunk_errors)
                cleaned_dfs.append(chunk_cleaned)
            cleaned_df = pd.concat(cleaned_dfs, ignore_index=True) if cleaned_dfs else pd.DataFrame()
        else:
            if total_rows > 0:
                df_full = parse_file(file_path)
                df_full = df_full.dropna(how="all")
                actual_total_rows = len(df_full)
                errors, cleaned_df = run_validation(df_full, phone_rules, user_mapping=user_mapping, validation_settings=validation_settings)
            else:
                cleaned_df = pd.DataFrame()

        await update_status(db, upload_id, ProcessingStatus.CLEANING)

        upload.total_rows = actual_total_rows
        db.commit()

        duplicate_count = len([e for e in errors if e.get("error_type") == "duplicate"])
        quality = compute_quality_score(upload.total_rows, errors, duplicate_count)

        rows_with_high = set(
            e["row"] for e in errors if e.get("severity") in ("high", "critical")
        )
        warning_rows = len(set(e["row"] for e in errors if e.get("severity") in ("low", "medium")))
        invalid_rows = len(rows_with_high)
        valid_rows = upload.total_rows - invalid_rows

        upload.valid_rows = valid_rows
        upload.invalid_rows = invalid_rows
        upload.warning_rows = warning_rows
        upload.quality_score = quality["score"]
        db.commit()

        for err in errors:
            sev_map = {"low": Severity.LOW, "medium": Severity.MEDIUM, "high": Severity.HIGH, "critical": Severity.CRITICAL}
            db.add(ValidationError(
                upload_id=upload_id,
                row_number=err["row"],
                column_name=err["column"],
                error_type=err.get("error_type", "validation"),
                error_message=err["error"],
                severity=sev_map.get(err.get("severity", "medium"), Severity.MEDIUM),
            ))
        db.commit()

        await update_status(db, upload_id, ProcessingStatus.GENERATING_REPORTS)

        output_dir = os.path.join(settings.output_dir, upload_id)
        os.makedirs(output_dir, exist_ok=True)

        summary = generate_ai_summary(
            total_rows, valid_rows, errors, quality["score"], upload.file_name,
        )

        cleaned_path = os.path.join(output_dir, "cleaned.xlsx")
        error_path = os.path.join(output_dir, "errors.xlsx")
        report_path = os.path.join(output_dir, "validation_report.pdf")

        generate_cleaned_excel(cleaned_path, cleaned_df)
        generate_error_excel(error_path, errors)
        generate_pdf_report(
            report_path, upload.file_name, total_rows, valid_rows, invalid_rows,
            quality["score"], quality["label"], errors, summary,
        )

        upload.cleaned_file_path = cleaned_path
        upload.error_file_path = error_path
        upload.report_file_path = report_path

        db.add(Report(upload_id=upload_id, summary=summary, quality_score=quality["score"]))
        db.commit()

        await update_status(db, upload_id, ProcessingStatus.COMPLETED)

    except Exception as e:
        upload.processing_status = ProcessingStatus.FAILED
        db.commit()
        raise e
