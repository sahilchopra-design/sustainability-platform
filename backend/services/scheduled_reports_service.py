"""
Scheduled Report Export Service
Handles automated report generation and scheduling
"""

from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any
from uuid import uuid4
import json
import os

from sqlalchemy import create_engine, text
from sqlalchemy.pool import NullPool
from pydantic import BaseModel, EmailStr
from enum import Enum

# Database connection
_db_engine = None

def _get_db_engine():
    """Get or create database engine."""
    global _db_engine
    if _db_engine is None:
        DATABASE_URL = os.environ.get("DATABASE_URL")
        if DATABASE_URL:
            try:
                _db_engine = create_engine(DATABASE_URL, poolclass=NullPool)
                with _db_engine.connect() as conn:
                    conn.execute(text("SELECT 1"))
            except Exception as e:
                print(f"Warning: Could not connect to PostgreSQL for scheduled reports: {e}")
                _db_engine = None
    return _db_engine


class ReportFrequency(str, Enum):
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"


class ReportType(str, Enum):
    PORTFOLIO_ANALYTICS = "portfolio_analytics"
    CARBON_CREDITS = "carbon_credits"
    STRANDED_ASSETS = "stranded_assets"
    NATURE_RISK = "nature_risk"
    SUSTAINABILITY = "sustainability"
    VALUATION = "valuation"
    SCENARIO_ANALYSIS = "scenario_analysis"


class ScheduledReport(BaseModel):
    id: Optional[str] = None
    name: str
    report_type: ReportType
    frequency: ReportFrequency
    recipients: List[str]  # Email addresses
    format: str = "pdf"  # pdf or excel
    parameters: Dict[str, Any] = {}
    is_active: bool = True
    next_run: Optional[datetime] = None
    last_run: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


def create_scheduled_report_table():
    """Create scheduled reports table if not exists."""
    engine = _get_db_engine()
    if not engine:
        return
    
    try:
        with engine.connect() as conn:
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS scheduled_reports (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    name VARCHAR(255) NOT NULL,
                    report_type VARCHAR(50) NOT NULL,
                    frequency VARCHAR(20) NOT NULL,
                    recipients JSONB NOT NULL DEFAULT '[]',
                    format VARCHAR(10) DEFAULT 'pdf',
                    parameters JSONB DEFAULT '{}',
                    is_active BOOLEAN DEFAULT true,
                    next_run TIMESTAMP WITH TIME ZONE,
                    last_run TIMESTAMP WITH TIME ZONE,
                    user_id UUID,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
                )
            """))
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_scheduled_reports_next_run 
                ON scheduled_reports (next_run) WHERE is_active = true
            """))
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_scheduled_reports_user 
                ON scheduled_reports (user_id)
            """))
            conn.commit()
            print("[OK] Scheduled reports table ready")
    except Exception as e:
        print(f"Error creating scheduled reports table: {e}")


def calculate_next_run(frequency: ReportFrequency, from_date: datetime = None) -> datetime:
    """Calculate next run time based on frequency."""
    base = from_date or datetime.now(timezone.utc)
    
    if frequency == ReportFrequency.DAILY:
        # Next day at 6 AM UTC
        next_run = base.replace(hour=6, minute=0, second=0, microsecond=0) + timedelta(days=1)
    elif frequency == ReportFrequency.WEEKLY:
        # Next Monday at 6 AM UTC
        days_until_monday = (7 - base.weekday()) % 7 or 7
        next_run = base.replace(hour=6, minute=0, second=0, microsecond=0) + timedelta(days=days_until_monday)
    elif frequency == ReportFrequency.MONTHLY:
        # First day of next month at 6 AM UTC
        if base.month == 12:
            next_run = base.replace(year=base.year + 1, month=1, day=1, hour=6, minute=0, second=0, microsecond=0)
        else:
            next_run = base.replace(month=base.month + 1, day=1, hour=6, minute=0, second=0, microsecond=0)
    elif frequency == ReportFrequency.QUARTERLY:
        # First day of next quarter
        quarter_starts = [1, 4, 7, 10]
        current_quarter_start = max([m for m in quarter_starts if m <= base.month])
        next_quarter_idx = (quarter_starts.index(current_quarter_start) + 1) % 4
        next_month = quarter_starts[next_quarter_idx]
        next_year = base.year if next_quarter_idx > 0 else base.year + 1
        next_run = base.replace(year=next_year, month=next_month, day=1, hour=6, minute=0, second=0, microsecond=0)
    else:
        next_run = base + timedelta(days=7)
    
    return next_run


def create_scheduled_report(report: ScheduledReport, user_id: str = None) -> Optional[str]:
    """Create a new scheduled report."""
    engine = _get_db_engine()
    if not engine:
        return None
    
    try:
        report_id = str(uuid4())
        next_run = calculate_next_run(report.frequency)
        
        with engine.connect() as conn:
            conn.execute(text("""
                INSERT INTO scheduled_reports (
                    id, name, report_type, frequency, recipients, format, 
                    parameters, is_active, next_run, user_id, created_at, updated_at
                ) VALUES (
                    :id, :name, :report_type, :frequency, :recipients, :format,
                    :parameters, :is_active, :next_run, :user_id, :created_at, :updated_at
                )
            """), {
                "id": report_id,
                "name": report.name,
                "report_type": report.report_type.value,
                "frequency": report.frequency.value,
                "recipients": json.dumps(report.recipients),
                "format": report.format,
                "parameters": json.dumps(report.parameters),
                "is_active": report.is_active,
                "next_run": next_run,
                "user_id": user_id,
                "created_at": datetime.now(timezone.utc),
                "updated_at": datetime.now(timezone.utc),
            })
            conn.commit()
        return report_id
    except Exception as e:
        print(f"Error creating scheduled report: {e}")
    return None


def get_scheduled_report(report_id: str) -> Optional[ScheduledReport]:
    """Get scheduled report by ID."""
    engine = _get_db_engine()
    if not engine:
        return None
    
    try:
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT id, name, report_type, frequency, recipients, format,
                    parameters, is_active, next_run, last_run, created_at, updated_at
                FROM scheduled_reports WHERE id = :id
            """), {"id": report_id})
            row = result.fetchone()
            
            if row:
                return ScheduledReport(
                    id=str(row[0]),
                    name=row[1],
                    report_type=ReportType(row[2]),
                    frequency=ReportFrequency(row[3]),
                    recipients=row[4] if isinstance(row[4], list) else json.loads(row[4]) if row[4] else [],
                    format=row[5] or "pdf",
                    parameters=row[6] if isinstance(row[6], dict) else json.loads(row[6]) if row[6] else {},
                    is_active=row[7],
                    next_run=row[8],
                    last_run=row[9],
                    created_at=row[10],
                    updated_at=row[11],
                )
    except Exception as e:
        print(f"Error getting scheduled report: {e}")
    return None


def list_scheduled_reports(user_id: str = None, active_only: bool = False) -> List[ScheduledReport]:
    """List all scheduled reports."""
    engine = _get_db_engine()
    if not engine:
        return []
    
    try:
        with engine.connect() as conn:
            query = """
                SELECT id, name, report_type, frequency, recipients, format,
                    parameters, is_active, next_run, last_run, created_at, updated_at
                FROM scheduled_reports
                WHERE 1=1
            """
            params = {}
            
            if user_id:
                query += " AND user_id = :user_id"
                params["user_id"] = user_id
            
            if active_only:
                query += " AND is_active = true"
            
            query += " ORDER BY next_run ASC"
            
            result = conn.execute(text(query), params)
            
            reports = []
            for row in result:
                reports.append(ScheduledReport(
                    id=str(row[0]),
                    name=row[1],
                    report_type=ReportType(row[2]),
                    frequency=ReportFrequency(row[3]),
                    recipients=row[4] if isinstance(row[4], list) else json.loads(row[4]) if row[4] else [],
                    format=row[5] or "pdf",
                    parameters=row[6] if isinstance(row[6], dict) else json.loads(row[6]) if row[6] else {},
                    is_active=row[7],
                    next_run=row[8],
                    last_run=row[9],
                    created_at=row[10],
                    updated_at=row[11],
                ))
            return reports
    except Exception as e:
        print(f"Error listing scheduled reports: {e}")
    return []


def update_scheduled_report(report_id: str, updates: Dict[str, Any]) -> bool:
    """Update a scheduled report."""
    engine = _get_db_engine()
    if not engine:
        return False
    
    try:
        with engine.connect() as conn:
            set_clauses = []
            params = {"id": report_id}
            
            for key, value in updates.items():
                if key in ["name", "report_type", "frequency", "format", "is_active"]:
                    set_clauses.append(f"{key} = :{key}")
                    params[key] = value.value if hasattr(value, 'value') else value
                elif key == "recipients":
                    set_clauses.append("recipients = :recipients")
                    params["recipients"] = json.dumps(value)
                elif key == "parameters":
                    set_clauses.append("parameters = :parameters")
                    params["parameters"] = json.dumps(value)
            
            if "frequency" in updates:
                new_next_run = calculate_next_run(ReportFrequency(updates["frequency"]))
                set_clauses.append("next_run = :next_run")
                params["next_run"] = new_next_run
            
            set_clauses.append("updated_at = :updated_at")
            params["updated_at"] = datetime.now(timezone.utc)
            
            query = f"UPDATE scheduled_reports SET {', '.join(set_clauses)} WHERE id = :id"
            result = conn.execute(text(query), params)
            conn.commit()
            return result.rowcount > 0
    except Exception as e:
        print(f"Error updating scheduled report: {e}")
    return False


def delete_scheduled_report(report_id: str) -> bool:
    """Delete a scheduled report."""
    engine = _get_db_engine()
    if not engine:
        return False
    
    try:
        with engine.connect() as conn:
            result = conn.execute(text("DELETE FROM scheduled_reports WHERE id = :id"), {"id": report_id})
            conn.commit()
            return result.rowcount > 0
    except Exception as e:
        print(f"Error deleting scheduled report: {e}")
    return False


def get_due_reports() -> List[ScheduledReport]:
    """Get reports that are due to run."""
    engine = _get_db_engine()
    if not engine:
        return []
    
    try:
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT id, name, report_type, frequency, recipients, format,
                    parameters, is_active, next_run, last_run, created_at, updated_at
                FROM scheduled_reports
                WHERE is_active = true AND next_run <= :now
                ORDER BY next_run ASC
            """), {"now": datetime.now(timezone.utc)})
            
            reports = []
            for row in result:
                reports.append(ScheduledReport(
                    id=str(row[0]),
                    name=row[1],
                    report_type=ReportType(row[2]),
                    frequency=ReportFrequency(row[3]),
                    recipients=row[4] if isinstance(row[4], list) else json.loads(row[4]) if row[4] else [],
                    format=row[5] or "pdf",
                    parameters=row[6] if isinstance(row[6], dict) else json.loads(row[6]) if row[6] else {},
                    is_active=row[7],
                    next_run=row[8],
                    last_run=row[9],
                    created_at=row[10],
                    updated_at=row[11],
                ))
            return reports
    except Exception as e:
        print(f"Error getting due reports: {e}")
    return []


def mark_report_executed(report_id: str) -> bool:
    """Mark a report as executed and calculate next run."""
    engine = _get_db_engine()
    if not engine:
        return False
    
    try:
        report = get_scheduled_report(report_id)
        if not report:
            return False
        
        next_run = calculate_next_run(report.frequency)
        
        with engine.connect() as conn:
            conn.execute(text("""
                UPDATE scheduled_reports
                SET last_run = :last_run, next_run = :next_run, updated_at = :updated_at
                WHERE id = :id
            """), {
                "id": report_id,
                "last_run": datetime.now(timezone.utc),
                "next_run": next_run,
                "updated_at": datetime.now(timezone.utc),
            })
            conn.commit()
            return True
    except Exception as e:
        print(f"Error marking report executed: {e}")
    return False


# Initialize table on module load
create_scheduled_report_table()
