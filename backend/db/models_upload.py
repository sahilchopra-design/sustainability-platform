"""Upload-related database models"""
from datetime import datetime
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Text, JSON, Float
from sqlalchemy.orm import relationship
from db.postgres import Base


class FileUpload(Base):
    """File upload tracking"""
    __tablename__ = "file_uploads"
    
    id = Column(String, primary_key=True)
    portfolio_id = Column(String, ForeignKey("portfolios.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # File information
    filename = Column(String, nullable=False)
    file_size = Column(Integer, nullable=False)
    file_format = Column(String, nullable=False)  # csv, xlsx, json
    file_path = Column(String, nullable=True)  # Path to stored file
    
    # Processing status
    status = Column(String, default="uploaded", nullable=False, index=True)
    # Status values: uploaded, validating, mapping, processing, completed, failed
    
    # Metadata
    total_rows = Column(Integer, default=0)
    valid_rows = Column(Integer, default=0)
    invalid_rows = Column(Integer, default=0)
    processed_rows = Column(Integer, default=0)
    
    # Configuration
    mapping_config = Column(JSON, nullable=True)  # Column mapping
    validation_results = Column(JSON, nullable=True)  # Summary of validation
    processing_results = Column(JSON, nullable=True)  # Summary of processing
    
    # Error tracking
    error_message = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    
    # Relationships
    portfolio = relationship("Portfolio", back_populates="file_uploads")
    validation_errors = relationship("ValidationError", back_populates="upload", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<FileUpload(id={self.id}, filename={self.filename}, status={self.status})>"


class ValidationError(Base):
    """Validation error for uploaded data"""
    __tablename__ = "validation_errors"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    upload_id = Column(String, ForeignKey("file_uploads.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Error location
    row_number = Column(Integer, nullable=False, index=True)
    column_name = Column(String, nullable=True)
    
    # Error details
    error_type = Column(String, nullable=False, index=True)
    # Types: missing_required, invalid_format, invalid_value, duplicate, constraint_violation
    error_message = Column(Text, nullable=False)
    severity = Column(String, default="error")  # error, warning, info
    
    # Original value
    original_value = Column(String, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    upload = relationship("FileUpload", back_populates="validation_errors")
    
    def __repr__(self):
        return f"<ValidationError(row={self.row_number}, type={self.error_type})>"


class MappingTemplate(Base):
    """Saved column mapping templates"""
    __tablename__ = "mapping_templates"
    
    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    
    # Template configuration
    mapping_config = Column(JSON, nullable=False)
    file_format = Column(String, nullable=False)  # csv, xlsx, json
    
    # Usage tracking
    usage_count = Column(Integer, default=0)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<MappingTemplate(id={self.id}, name={self.name})>"
