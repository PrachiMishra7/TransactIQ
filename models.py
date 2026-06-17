import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, Text, Enum as SAEnum, ForeignKey, JSON
from sqlalchemy.orm import relationship
import enum

from database import Base


class ProcessingStatus(str, enum.Enum):
    PENDING = "PENDING"
    UPLOADING = "UPLOADING"
    PARSING = "PARSING"
    VALIDATING = "VALIDATING"
    CLEANING = "CLEANING"
    GENERATING_REPORTS = "GENERATING_REPORTS"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class Severity(str, enum.Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class Upload(Base):
    __tablename__ = "uploads"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    file_name = Column(String, nullable=False)
    file_size = Column(Integer, nullable=False)
    total_rows = Column(Integer, default=0)
    valid_rows = Column(Integer, default=0)
    invalid_rows = Column(Integer, default=0)
    warning_rows = Column(Integer, default=0)
    quality_score = Column(Float, default=0.0)
    processing_status = Column(SAEnum(ProcessingStatus), default=ProcessingStatus.PENDING)
    rule_version_id = Column(String, nullable=True)
    validation_settings = Column(JSON, nullable=True)
    cleaned_file_path = Column(String, nullable=True)
    error_file_path = Column(String, nullable=True)
    report_file_path = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships are defined at the bottom of the file to prevent Streamlit hot-reload registry errors
class ValidationError(Base):
    __tablename__ = "validation_errors"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    upload_id = Column(String, ForeignKey("uploads.id", ondelete="CASCADE"), nullable=False)
    row_number = Column(Integer, nullable=False)
    column_name = Column(String, nullable=False)
    error_type = Column(String, nullable=False)
    error_message = Column(String, nullable=False)
    severity = Column(SAEnum(Severity), default=Severity.MEDIUM)
    created_at = Column(DateTime, default=datetime.utcnow)

    upload = relationship(Upload, back_populates="validation_errors")


class ValidationRule(Base):
    __tablename__ = "validation_rules"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    country_name = Column(String, nullable=False)
    country_code = Column(String, nullable=False)
    field_name = Column(String, nullable=False)
    validation_type = Column(String, nullable=False)
    rule_value = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    version = Column(Integer, default=1)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class RuleVersion(Base):
    __tablename__ = "rule_versions"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    version = Column(Integer, nullable=False)
    description = Column(String, nullable=True)
    rule_snapshot = Column(JSON, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class Report(Base):
    __tablename__ = "reports"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    upload_id = Column(String, ForeignKey("uploads.id", ondelete="CASCADE"), nullable=False)
    summary = Column(Text, nullable=False)
    quality_score = Column(Float, nullable=False)
    generated_at = Column(DateTime, default=datetime.utcnow)

    upload = relationship(Upload, back_populates="reports")

# Define relationships using direct class references to avoid SQLAlchemy string lookup registry issues during Streamlit hot-reloads
Upload.validation_errors = relationship(ValidationError, back_populates="upload", cascade="all, delete-orphan")
Upload.reports = relationship(Report, back_populates="upload", cascade="all, delete-orphan")
