"""Upload-related Pydantic schemas"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class FileUploadResponse(BaseModel):
    upload_id: str
    portfolio_id: str
    filename: str
    file_size: int
    file_format: str
    status: str
    total_rows: int = 0
    created_at: datetime
    
    class Config:
        from_attributes = True


class FileUploadStatus(BaseModel):
    upload_id: str
    status: str
    total_rows: int
    valid_rows: int
    invalid_rows: int
    processed_rows: int
    mapping_config: Optional[Dict[str, Any]] = None
    validation_results: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


class ColumnMapping(BaseModel):
    standard_field: str
    uploaded_column: str


class MappingUpdate(BaseModel):
    mapping: Dict[str, str] = Field(..., description="Dict mapping standard fields to uploaded columns")


class ValidationErrorResponse(BaseModel):
    row_number: Optional[int]
    column_name: Optional[str]
    error_type: str
    error_message: str
    severity: str
    original_value: Optional[str] = None
    
    class Config:
        from_attributes = True


class PreviewRow(BaseModel):
    row_number: int
    data: Dict[str, Any]
    errors: List[ValidationErrorResponse] = []


class UploadPreview(BaseModel):
    upload_id: str
    filename: str
    total_rows: int
    preview_rows: List[Dict[str, Any]]
    columns: List[str]
    mapping: Optional[Dict[str, str]] = None
    statistics: Optional[Dict[str, Any]] = None


class ProcessRequest(BaseModel):
    skip_invalid: bool = Field(default=False, description="Skip invalid rows and process valid ones")
    auto_enrich: bool = Field(default=True, description="Automatically enrich missing fields")


class ProcessingResult(BaseModel):
    upload_id: str
    status: str
    holdings_created: int
    rows_skipped: int
    processing_time_seconds: float
    errors: List[ValidationErrorResponse] = []


class MappingTemplateCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    mapping_config: Dict[str, str]
    file_format: str


class MappingTemplateResponse(BaseModel):
    id: str
    name: str
    description: Optional[str]
    mapping_config: Dict[str, str]
    file_format: str
    usage_count: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class UploadStatistics(BaseModel):
    total_exposure: float
    currency_distribution: Dict[str, float]
    sector_distribution: Dict[str, int]
    rating_distribution: Dict[str, int]
    avg_pd: float
    avg_lgd: float
