"""
Scheduled Reports API Routes
Endpoints for managing scheduled report exports
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, EmailStr
from typing import List, Optional, Dict, Any
from datetime import datetime

from services.scheduled_reports_service import (
    ScheduledReport, ReportType, ReportFrequency,
    create_scheduled_report, get_scheduled_report, list_scheduled_reports,
    update_scheduled_report, delete_scheduled_report, get_due_reports
)

router = APIRouter(prefix="/api/v1/scheduled-reports", tags=["Scheduled Reports"])


class CreateScheduledReportRequest(BaseModel):
    name: str
    report_type: ReportType
    frequency: ReportFrequency
    recipients: List[str]
    format: str = "pdf"
    parameters: Dict[str, Any] = {}


class UpdateScheduledReportRequest(BaseModel):
    name: Optional[str] = None
    frequency: Optional[ReportFrequency] = None
    recipients: Optional[List[str]] = None
    format: Optional[str] = None
    parameters: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None


class ScheduledReportResponse(BaseModel):
    id: str
    name: str
    report_type: str
    frequency: str
    recipients: List[str]
    format: str
    parameters: Dict[str, Any]
    is_active: bool
    next_run: Optional[str] = None
    last_run: Optional[str] = None
    created_at: Optional[str] = None


class ScheduledReportListResponse(BaseModel):
    items: List[ScheduledReportResponse]
    total: int


def report_to_response(report: ScheduledReport) -> ScheduledReportResponse:
    """Convert ScheduledReport to response model."""
    return ScheduledReportResponse(
        id=report.id,
        name=report.name,
        report_type=report.report_type.value,
        frequency=report.frequency.value,
        recipients=report.recipients,
        format=report.format,
        parameters=report.parameters,
        is_active=report.is_active,
        next_run=report.next_run.isoformat() if report.next_run else None,
        last_run=report.last_run.isoformat() if report.last_run else None,
        created_at=report.created_at.isoformat() if report.created_at else None,
    )


@router.post("", response_model=ScheduledReportResponse)
async def create_report(request: CreateScheduledReportRequest):
    """Create a new scheduled report."""
    report = ScheduledReport(
        name=request.name,
        report_type=request.report_type,
        frequency=request.frequency,
        recipients=request.recipients,
        format=request.format,
        parameters=request.parameters,
    )
    
    report_id = create_scheduled_report(report)
    if not report_id:
        raise HTTPException(status_code=500, detail="Failed to create scheduled report")
    
    created_report = get_scheduled_report(report_id)
    if not created_report:
        raise HTTPException(status_code=500, detail="Failed to retrieve created report")
    
    return report_to_response(created_report)


@router.get("", response_model=ScheduledReportListResponse)
async def list_reports(active_only: bool = False):
    """List all scheduled reports."""
    reports = list_scheduled_reports(active_only=active_only)
    return ScheduledReportListResponse(
        items=[report_to_response(r) for r in reports],
        total=len(reports)
    )


@router.get("/{report_id}", response_model=ScheduledReportResponse)
async def get_report(report_id: str):
    """Get a scheduled report by ID."""
    report = get_scheduled_report(report_id)
    if not report:
        raise HTTPException(status_code=404, detail="Scheduled report not found")
    return report_to_response(report)


@router.patch("/{report_id}", response_model=ScheduledReportResponse)
async def update_report(report_id: str, request: UpdateScheduledReportRequest):
    """Update a scheduled report."""
    updates = request.model_dump(exclude_unset=True)
    
    if not updates:
        raise HTTPException(status_code=400, detail="No updates provided")
    
    success = update_scheduled_report(report_id, updates)
    if not success:
        raise HTTPException(status_code=404, detail="Scheduled report not found or update failed")
    
    updated_report = get_scheduled_report(report_id)
    return report_to_response(updated_report)


@router.delete("/{report_id}")
async def delete_report(report_id: str):
    """Delete a scheduled report."""
    success = delete_scheduled_report(report_id)
    if not success:
        raise HTTPException(status_code=404, detail="Scheduled report not found")
    return {"message": "Scheduled report deleted successfully"}


@router.post("/{report_id}/toggle")
async def toggle_report(report_id: str):
    """Toggle a scheduled report's active status."""
    report = get_scheduled_report(report_id)
    if not report:
        raise HTTPException(status_code=404, detail="Scheduled report not found")
    
    success = update_scheduled_report(report_id, {"is_active": not report.is_active})
    if not success:
        raise HTTPException(status_code=500, detail="Failed to toggle report")
    
    updated_report = get_scheduled_report(report_id)
    return report_to_response(updated_report)


@router.get("/due/list")
async def get_due_reports_list():
    """Get reports that are due to run (for scheduler)."""
    reports = get_due_reports()
    return {
        "items": [report_to_response(r) for r in reports],
        "total": len(reports),
    }


# Available report types and frequencies
@router.get("/options/types")
async def get_report_types():
    """Get available report types."""
    return {
        "types": [
            {"value": rt.value, "label": rt.value.replace("_", " ").title()}
            for rt in ReportType
        ]
    }


@router.get("/options/frequencies")
async def get_frequencies():
    """Get available frequencies."""
    return {
        "frequencies": [
            {"value": rf.value, "label": rf.value.title()}
            for rf in ReportFrequency
        ]
    }
