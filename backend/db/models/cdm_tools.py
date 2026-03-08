"""
CDM Methodological Tools - Database Models
Tables for tool catalog, execution audit log, and methodology-tool dependencies.
"""

from sqlalchemy import (
    Column, String, Integer, DateTime, Text, Boolean, JSON,
    UniqueConstraint, Index, ForeignKey
)
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
import uuid

from db.base import Base


class CDMTool(Base):
    """Master catalog of 43 CDM methodological tools."""
    __tablename__ = "cdm_tool"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    code = Column(String(20), nullable=False, unique=True, index=True,
                  comment="Tool code (e.g. TOOL01, AR-TOOL14)")
    name = Column(String(255), nullable=False,
                  comment="Full tool name")
    short_name = Column(String(100), nullable=True,
                        comment="Abbreviated name")
    category = Column(String(50), nullable=False, index=True,
                      comment="ADDITIONALITY, EMISSION_CALCULATION, GRID, etc.")
    description = Column(Text, nullable=True,
                         comment="Detailed tool description")
    version = Column(String(20), nullable=True,
                     comment="Latest version number")
    unfccc_reference = Column(String(200), nullable=True,
                              comment="UNFCCC CDM reference URL or document ID")
    applicable_scopes = Column(JSON, default=list,
                               comment="List of applicable project scopes (1-15)")
    input_schema = Column(JSON, default=dict,
                          comment="JSON schema describing required inputs")
    output_schema = Column(JSON, default=dict,
                           comment="JSON schema describing outputs")
    default_parameters = Column(JSON, default=dict,
                                comment="Default parameter values")
    status = Column(String(20), default="active",
                    comment="active | deprecated | superseded")
    created_at = Column(DateTime(timezone=True),
                        default=lambda: datetime.now(timezone.utc))

    executions = relationship("CDMToolExecution", back_populates="tool",
                              cascade="all, delete-orphan")
    dependencies = relationship("MethodologyToolDependency", back_populates="tool",
                                cascade="all, delete-orphan")


class CDMToolExecution(Base):
    """Audit log for CDM tool calculation runs."""
    __tablename__ = "cdm_tool_execution"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    tool_code = Column(String(20), ForeignKey("cdm_tool.code", ondelete="CASCADE"),
                       nullable=False, index=True)
    methodology_code = Column(String(50), nullable=True, index=True,
                              comment="Methodology that triggered this tool run")
    portfolio_id = Column(String, nullable=True, index=True,
                          comment="Optional link to carbon portfolio")
    project_id = Column(String, nullable=True,
                        comment="Optional link to carbon project")

    inputs = Column(JSON, default=dict,
                    comment="Input parameters used")
    outputs = Column(JSON, default=dict,
                     comment="Calculated output values")
    execution_time_ms = Column(Integer, nullable=True,
                               comment="Execution duration in milliseconds")
    status = Column(String(20), default="completed",
                    comment="completed | failed | timeout")
    error_message = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True),
                        default=lambda: datetime.now(timezone.utc))

    tool = relationship("CDMTool", back_populates="executions")


class MethodologyToolDependency(Base):
    """Maps which CDM tools are required by each methodology."""
    __tablename__ = "methodology_tool_dependency"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    methodology_code = Column(String(50), nullable=False, index=True,
                              comment="Methodology code (ACM0002, VM0048, etc.)")
    tool_code = Column(String(20), ForeignKey("cdm_tool.code", ondelete="CASCADE"),
                       nullable=False, index=True)
    usage_context = Column(String(100), nullable=True,
                           comment="baseline | project_emissions | additionality | leakage | monitoring")
    is_mandatory = Column(Boolean, default=True,
                          comment="Whether the tool is mandatory for the methodology")
    notes = Column(Text, nullable=True,
                   comment="Additional context on how the tool is used")

    created_at = Column(DateTime(timezone=True),
                        default=lambda: datetime.now(timezone.utc))

    tool = relationship("CDMTool", back_populates="dependencies")

    __table_args__ = (
        UniqueConstraint("methodology_code", "tool_code",
                         name="uq_methodology_tool"),
        Index("ix_mtd_meth_tool", "methodology_code", "tool_code"),
    )
