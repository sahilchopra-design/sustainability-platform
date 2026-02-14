"""Upload routes for portfolio file import"""
import uuid
import os
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, BackgroundTasks, Query
from sqlalchemy.orm import Session

from api.v1.deps import get_db
from api.v1.repositories import PortfolioRepository
from api.v1.schemas_upload import (
    FileUploadResponse, FileUploadStatus, UploadPreview,
    MappingUpdate, ProcessRequest, ProcessingResult,
    ValidationErrorResponse, MappingTemplateCreate, MappingTemplateResponse
)
from db.models_upload import FileUpload, ValidationError, MappingTemplate
from services.upload_service import UploadService
from services.validation_service import ValidationService
from workers.tasks.upload_tasks import process_upload_task

router = APIRouter(prefix="/uploads", tags=["uploads"])

# Constants
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB
ALLOWED_EXTENSIONS = [".csv", ".xlsx", ".xls", ".json"]


def get_file_extension(filename: str) -> str:
    """Get file extension"""
    return os.path.splitext(filename)[1].lower()


def get_file_format(filename: str) -> str:
    """Get file format from filename"""
    ext = get_file_extension(filename)
    if ext == ".csv":
        return "csv"
    elif ext in [".xlsx", ".xls"]:
        return "xlsx"
    elif ext == ".json":
        return "json"
    else:
        raise ValueError(f"Unsupported file format: {ext}")


@router.post("", response_model=FileUploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_file(
    portfolio_id: str = Query(..., description="Portfolio ID"),
    file: UploadFile = File(..., description="File to upload"),
    background_tasks: BackgroundTasks = None,
    db: Session = Depends(get_db)
):
    """
    Upload a portfolio file (CSV, Excel, JSON).
    
    This endpoint:
    1. Validates file format and size
    2. Saves file to disk
    3. Parses file and detects columns
    4. Auto-maps columns using fuzzy matching
    5. Returns upload ID for further processing
    
    Max file size: 50MB
    Supported formats: .csv, .xlsx, .xls, .json
    """
    # Verify portfolio exists
    portfolio_repo = PortfolioRepository(db)
    portfolio = portfolio_repo.get_by_id(portfolio_id)
    
    if not portfolio:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Portfolio {portfolio_id} not found"
        )
    
    # Validate file extension
    file_ext = get_file_extension(file.filename)
    if file_ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file format. Allowed: {', '.join(ALLOWED_EXTENSIONS)}"
        )
    
    # Read file content
    file_content = await file.read()
    file_size = len(file_content)
    
    # Validate file size
    if file_size > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File too large. Max size: {MAX_FILE_SIZE / (1024*1024):.0f}MB"
        )
    
    # Generate upload ID
    upload_id = str(uuid.uuid4())
    
    # Initialize upload service
    upload_service = UploadService()
    
    # Save file
    try:
        file_format = get_file_format(file.filename)
        file_path = upload_service.save_file(file_content, file.filename, upload_id)
        
        # Parse file to get metadata
        df, metadata = upload_service.parse_file(file_path, file_format)
        
        # Auto-map columns
        auto_mapping = upload_service.auto_map_columns(metadata["columns"])
        
        # Create upload record
        upload = FileUpload(
            id=upload_id,
            portfolio_id=portfolio_id,
            filename=file.filename,
            file_size=file_size,
            file_format=file_format,
            file_path=file_path,
            status="uploaded",
            total_rows=metadata["total_rows"],
            mapping_config=auto_mapping
        )
        
        db.add(upload)
        db.commit()
        db.refresh(upload)
        
        return FileUploadResponse(
            upload_id=upload.id,
            portfolio_id=upload.portfolio_id,
            filename=upload.filename,
            file_size=upload.file_size,
            file_format=upload.file_format,
            status=upload.status,
            total_rows=upload.total_rows,
            created_at=upload.created_at
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process upload: {str(e)}"
        )


@router.get("/{upload_id}", response_model=FileUploadStatus)
def get_upload_status(
    upload_id: str,
    db: Session = Depends(get_db)
):
    """
    Get upload status and processing information.
    
    Returns current status, validation results, and processing progress.
    """
    upload = db.query(FileUpload).filter(FileUpload.id == upload_id).first()
    
    if not upload:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Upload {upload_id} not found"
        )
    
    return FileUploadStatus(
        upload_id=upload.id,
        status=upload.status,
        total_rows=upload.total_rows,
        valid_rows=upload.valid_rows,
        invalid_rows=upload.invalid_rows,
        processed_rows=upload.processed_rows,
        mapping_config=upload.mapping_config,
        validation_results=upload.validation_results,
        error_message=upload.error_message,
        created_at=upload.created_at,
        started_at=upload.started_at,
        completed_at=upload.completed_at
    )


@router.get("/{upload_id}/preview", response_model=UploadPreview)
def get_upload_preview(
    upload_id: str,
    max_rows: int = Query(100, ge=1, le=1000, description="Max rows to preview"),
    db: Session = Depends(get_db)
):
    """
    Get preview of uploaded data.
    
    Returns:
    - First N rows of data
    - Column names
    - Current mapping configuration
    - Basic statistics
    
    Use this to review data before processing.
    """
    upload = db.query(FileUpload).filter(FileUpload.id == upload_id).first()
    
    if not upload:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Upload {upload_id} not found"
        )
    
    # Parse file
    upload_service = UploadService()
    
    try:
        df, metadata = upload_service.parse_file(upload.file_path, upload.file_format)
        
        # Apply mapping if exists
        if upload.mapping_config:
            df = upload_service.apply_mapping(df, upload.mapping_config)
        
        # Get preview rows
        preview_rows = upload_service.get_preview(df, max_rows)
        
        # Calculate statistics
        statistics = upload_service.calculate_statistics(df)
        
        return UploadPreview(
            upload_id=upload.id,
            filename=upload.filename,
            total_rows=upload.total_rows,
            preview_rows=preview_rows,
            columns=list(df.columns),
            mapping=upload.mapping_config,
            statistics=statistics
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate preview: {str(e)}"
        )


@router.patch("/{upload_id}/mapping", response_model=FileUploadStatus)
def update_mapping(
    upload_id: str,
    mapping_update: MappingUpdate,
    db: Session = Depends(get_db)
):
    """
    Update column mapping configuration.
    
    Provide a dict mapping standard field names to uploaded column names.
    
    Example:
    ```json
    {
      "mapping": {
        "counterparty_name": "Company Name",
        "exposure_amount": "Total Exposure",
        "currency": "CCY"
      }
    }
    ```
    """
    upload = db.query(FileUpload).filter(FileUpload.id == upload_id).first()
    
    if not upload:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Upload {upload_id} not found"
        )
    
    # Update mapping
    upload.mapping_config = mapping_update.mapping
    db.commit()
    db.refresh(upload)
    
    return FileUploadStatus(
        upload_id=upload.id,
        status=upload.status,
        total_rows=upload.total_rows,
        valid_rows=upload.valid_rows,
        invalid_rows=upload.invalid_rows,
        processed_rows=upload.processed_rows,
        mapping_config=upload.mapping_config,
        validation_results=upload.validation_results,
        error_message=upload.error_message,
        created_at=upload.created_at,
        started_at=upload.started_at,
        completed_at=upload.completed_at
    )


@router.post("/{upload_id}/process", response_model=FileUploadStatus, status_code=status.HTTP_202_ACCEPTED)
def process_upload(
    upload_id: str,
    process_request: ProcessRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Process uploaded file and create portfolio holdings.
    
    This endpoint:
    1. Validates all rows
    2. Enriches missing fields (if auto_enrich=True)
    3. Creates portfolio holdings
    4. Returns immediately with status
    
    Use GET /uploads/{upload_id} to check processing status.
    
    Parameters:
    - skip_invalid: Skip invalid rows and process only valid ones
    - auto_enrich: Automatically fill in missing fields with defaults
    """
    upload = db.query(FileUpload).filter(FileUpload.id == upload_id).first()
    
    if not upload:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Upload {upload_id} not found"
        )
    
    if upload.status not in ["uploaded", "validation_failed"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Upload is already {upload.status}"
        )
    
    # Update status
    upload.status = "processing"
    db.commit()
    
    # Add background task
    background_tasks.add_task(
        process_upload_task,
        upload_id,
        process_request.skip_invalid,
        process_request.auto_enrich
    )
    
    return FileUploadStatus(
        upload_id=upload.id,
        status=upload.status,
        total_rows=upload.total_rows,
        valid_rows=upload.valid_rows,
        invalid_rows=upload.invalid_rows,
        processed_rows=upload.processed_rows,
        mapping_config=upload.mapping_config,
        validation_results=upload.validation_results,
        error_message=upload.error_message,
        created_at=upload.created_at,
        started_at=upload.started_at,
        completed_at=upload.completed_at
    )


@router.get("/{upload_id}/errors", response_model=List[ValidationErrorResponse])
def get_validation_errors(
    upload_id: str,
    error_type: Optional[str] = Query(None, description="Filter by error type"),
    severity: Optional[str] = Query(None, description="Filter by severity"),
    db: Session = Depends(get_db)
):
    """
    Get validation errors for an upload.
    
    Returns detailed list of all validation errors with row numbers,
    column names, and error messages.
    
    Filters:
    - error_type: missing_required, invalid_format, invalid_value, duplicate, etc.
    - severity: error, warning, info
    """
    # Verify upload exists
    upload = db.query(FileUpload).filter(FileUpload.id == upload_id).first()
    if not upload:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Upload {upload_id} not found"
        )
    
    # Query validation errors
    query = db.query(ValidationError).filter(ValidationError.upload_id == upload_id)
    
    if error_type:
        query = query.filter(ValidationError.error_type == error_type)
    
    if severity:
        query = query.filter(ValidationError.severity == severity)
    
    errors = query.order_by(ValidationError.row_number).all()
    
    return [
        ValidationErrorResponse(
            row_number=e.row_number,
            column_name=e.column_name,
            error_type=e.error_type,
            error_message=e.error_message,
            severity=e.severity,
            original_value=e.original_value
        )
        for e in errors
    ]


# Mapping Templates
@router.get("/templates", response_model=List[MappingTemplateResponse])
def list_mapping_templates(
    db: Session = Depends(get_db)
):
    """
    Get list of saved mapping templates.
    
    Mapping templates allow you to save and reuse column mappings
    for files with consistent structure.
    """
    templates = db.query(MappingTemplate).order_by(MappingTemplate.usage_count.desc()).all()
    
    return [
        MappingTemplateResponse(
            id=t.id,
            name=t.name,
            description=t.description,
            mapping_config=t.mapping_config,
            file_format=t.file_format,
            usage_count=t.usage_count,
            created_at=t.created_at,
            updated_at=t.updated_at
        )
        for t in templates
    ]


@router.post("/templates", response_model=MappingTemplateResponse, status_code=status.HTTP_201_CREATED)
def create_mapping_template(
    template_data: MappingTemplateCreate,
    db: Session = Depends(get_db)
):
    """
    Create a new mapping template.
    
    Save a column mapping configuration for reuse.
    """
    template = MappingTemplate(
        id=str(uuid.uuid4()),
        name=template_data.name,
        description=template_data.description,
        mapping_config=template_data.mapping_config,
        file_format=template_data.file_format,
        usage_count=0
    )
    
    db.add(template)
    db.commit()
    db.refresh(template)
    
    return MappingTemplateResponse(
        id=template.id,
        name=template.name,
        description=template.description,
        mapping_config=template.mapping_config,
        file_format=template.file_format,
        usage_count=template.usage_count,
        created_at=template.created_at,
        updated_at=template.updated_at
    )
