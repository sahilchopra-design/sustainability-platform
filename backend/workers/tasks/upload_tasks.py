"""Upload task processor"""
import time
from typing import Dict, Any
from sqlalchemy.orm import Session

from db.postgres import SessionLocal
from db.models_upload import FileUpload, ValidationError
from db.models_sql import Asset
from services.upload_service import UploadService
from services.validation_service import ValidationService
from services.enrichment_service import EnrichmentService
from api.v1.repositories import PortfolioRepository


def process_upload_task(upload_id: str, skip_invalid: bool = False, auto_enrich: bool = True):
    """
    Background task to process uploaded file.
    
    This task:
    1. Loads the file
    2. Applies column mapping
    3. Validates all rows
    4. Enriches data (if auto_enrich=True)
    5. Creates portfolio holdings
    6. Updates upload status
    
    Args:
        upload_id: Upload ID
        skip_invalid: Whether to skip invalid rows
        auto_enrich: Whether to auto-enrich missing fields
    """
    db = SessionLocal()
    start_time = time.time()
    
    try:
        # Get upload record
        upload = db.query(FileUpload).filter(FileUpload.id == upload_id).first()
        if not upload:
            return
        
        # Update status to processing
        upload.status = "processing"
        upload.started_at = time.time()
        db.commit()
        
        # Initialize services
        upload_service = UploadService()
        validation_service = ValidationService()
        enrichment_service = EnrichmentService(db)
        portfolio_repo = PortfolioRepository(db)
        
        # Parse file
        df, metadata = upload_service.parse_file(upload.file_path, upload.file_format)
        
        # Apply mapping
        if upload.mapping_config:
            df = upload_service.apply_mapping(df, upload.mapping_config)
        
        # Validate data
        validation_errors, validation_summary = validation_service.validate_dataframe(df)
        
        # Save validation errors to database
        for error in validation_errors:
            val_error = ValidationError(**error, upload_id=upload_id)
            db.add(val_error)
        
        db.commit()
        
        # Update upload with validation results
        upload.validation_results = validation_summary
        upload.valid_rows = len(df) - validation_summary["affected_rows"]
        upload.invalid_rows = validation_summary["affected_rows"]
        db.commit()
        
        # Check if we should proceed
        if not validation_summary["is_valid"] and not skip_invalid:
            upload.status = "validation_failed"
            upload.error_message = f"Validation failed with {validation_summary['total_errors']} errors"
            upload.completed_at = time.time()
            db.commit()
            return
        
        # Filter out invalid rows if skip_invalid is True
        if skip_invalid and validation_summary["total_errors"] > 0:
            # Get row numbers with errors
            error_rows = set(e["row_number"] for e in validation_errors if e["severity"] == "error" and "row_number" in e)
            # Filter DataFrame
            df = df[~df.index.isin([r - 1 for r in error_rows])]
        
        # Enrich data
        if auto_enrich:
            df = enrichment_service.enrich_dataframe(df)
        
        # Convert to holdings
        holdings_data = upload_service.convert_to_holdings(df)
        
        # Create holdings in database
        holdings_created = 0
        for holding_data in holdings_data:
            try:
                holding = portfolio_repo.add_holding(upload.portfolio_id, holding_data)
                holdings_created += 1
            except Exception as e:
                # Log error but continue
                print(f"Failed to create holding: {e}")
        
        # Update upload record
        upload.status = "completed"
        upload.processed_rows = holdings_created
        upload.completed_at = time.time()
        upload.processing_results = {
            "holdings_created": holdings_created,
            "processing_time_seconds": time.time() - start_time,
            "enrichment_applied": auto_enrich,
            "rows_skipped": len(holdings_data) - holdings_created
        }
        
        db.commit()
        
    except Exception as e:
        # Handle errors
        upload = db.query(FileUpload).filter(FileUpload.id == upload_id).first()
        if upload:
            upload.status = "failed"
            upload.error_message = str(e)
            upload.completed_at = time.time()
            db.commit()
    
    finally:
        db.close()
