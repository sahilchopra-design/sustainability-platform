"""
API Routes: Regulatory Report Compiler
========================================
POST /api/v1/regulatory-reports/compile/tcfd           — TCFD 11-rec structured disclosure
POST /api/v1/regulatory-reports/compile/sfdr            — SFDR periodic disclosure (Art.8/9)
POST /api/v1/regulatory-reports/compile/gri305          — GRI 305 emissions report
POST /api/v1/regulatory-reports/compile/sec-climate     — SEC climate disclosure (Reg S-K 1500)
POST /api/v1/regulatory-reports/compile/issb            — ISSB S1/S2 disclosure
POST /api/v1/regulatory-reports/compile/apra-cpg229     — APRA CPG 229 assessment
POST /api/v1/regulatory-reports/compile/brsr            — SEBI BRSR + BRSR Core (GRI/ESRS mapped)
GET  /api/v1/regulatory-reports/frameworks              — Supported frameworks
GET  /api/v1/regulatory-reports/ref/tcfd-structure      — TCFD 11-rec template
GET  /api/v1/regulatory-reports/ref/sfdr-pai            — SFDR PAI template
GET  /api/v1/regulatory-reports/ref/gri305              — GRI 305 template
GET  /api/v1/regulatory-reports/ref/sec-climate         — SEC climate items
GET  /api/v1/regulatory-reports/ref/brsr-framework      — BRSR / BRSR Core structure with mappings
"""
from __future__ import annotations

from fastapi import APIRouter, HTTPException
from fastapi.responses import HTMLResponse, Response
from pydantic import BaseModel, Field
from typing import Optional

from services.regulatory_report_compiler import RegulatoryReportCompiler

router = APIRouter(prefix="/api/v1/regulatory-reports", tags=["Regulatory Reports"])


# ---------------------------------------------------------------------------
# Request Models
# ---------------------------------------------------------------------------

class CompileRequest(BaseModel):
    entity_data: dict = Field(default_factory=dict)
    period_start: str = "2025-01-01"
    period_end: str = "2025-12-31"


class SFDRCompileRequest(BaseModel):
    fund_data: dict = Field(default_factory=dict)
    period_start: str = "2025-01-01"
    period_end: str = "2025-12-31"


# ---------------------------------------------------------------------------
# Compile Endpoints
# ---------------------------------------------------------------------------

@router.post("/compile/tcfd")
def compile_tcfd(req: CompileRequest):
    """Compile TCFD 11-recommendation structured disclosure."""
    compiler = RegulatoryReportCompiler()
    r = compiler.compile_tcfd(req.entity_data, req.period_start, req.period_end)
    return _report_to_dict(r)


@router.post("/compile/sfdr")
def compile_sfdr(req: SFDRCompileRequest):
    """Compile SFDR periodic disclosure (Annex III/IV)."""
    compiler = RegulatoryReportCompiler()
    r = compiler.compile_sfdr_periodic(req.fund_data, req.period_start, req.period_end)
    return _report_to_dict(r)


@router.post("/compile/gri305")
def compile_gri305(req: CompileRequest):
    """Compile GRI 305 emissions disclosure."""
    compiler = RegulatoryReportCompiler()
    r = compiler.compile_gri305(req.entity_data, req.period_start, req.period_end)
    return _report_to_dict(r)


@router.post("/compile/sec-climate")
def compile_sec_climate(req: CompileRequest):
    """Compile SEC Climate-Related Disclosures (Reg S-K Subpart 1500)."""
    compiler = RegulatoryReportCompiler()
    r = compiler.compile_sec_climate(req.entity_data, req.period_start, req.period_end)
    return _report_to_dict(r)


@router.post("/compile/issb")
def compile_issb(req: CompileRequest):
    """Compile ISSB IFRS S1/S2 disclosure."""
    compiler = RegulatoryReportCompiler()
    r = compiler.compile_issb(req.entity_data, req.period_start, req.period_end)
    return _report_to_dict(r)


@router.post("/compile/apra-cpg229")
def compile_apra_cpg229(req: CompileRequest):
    """Compile APRA CPG 229 climate risk assessment."""
    compiler = RegulatoryReportCompiler()
    r = compiler.compile_apra_cpg229(req.entity_data, req.period_start, req.period_end)
    return _report_to_dict(r)


@router.post("/compile/brsr")
def compile_brsr(req: CompileRequest):
    """Compile SEBI BRSR + BRSR Core with GRI and ESRS cross-reference."""
    compiler = RegulatoryReportCompiler()
    r = compiler.compile_brsr(req.entity_data, req.period_start, req.period_end)
    return _report_to_dict(r)


# ---------------------------------------------------------------------------
# Reference Endpoints
# ---------------------------------------------------------------------------

@router.get("/frameworks")
def list_frameworks():
    """List all supported regulatory frameworks."""
    return {"frameworks": RegulatoryReportCompiler.get_supported_frameworks()}


@router.get("/ref/tcfd-structure")
def ref_tcfd():
    """TCFD 11 recommended disclosures structure."""
    return {"tcfd_structure": RegulatoryReportCompiler.get_tcfd_structure()}


@router.get("/ref/sfdr-pai")
def ref_sfdr_pai():
    """SFDR 14 mandatory PAI indicators template."""
    return {"sfdr_pai_template": RegulatoryReportCompiler.get_sfdr_pai_template()}


@router.get("/ref/gri305")
def ref_gri305():
    """GRI 305 emissions disclosure template."""
    return {"gri305_template": RegulatoryReportCompiler.get_gri305_template()}


@router.get("/ref/sec-climate")
def ref_sec_climate():
    """SEC climate disclosure items template."""
    return {"sec_climate_template": RegulatoryReportCompiler.get_sec_climate_template()}


@router.get("/ref/brsr-framework")
def ref_brsr_framework():
    """BRSR / BRSR Core structure with GRI + ESRS mappings."""
    return {"brsr_framework": RegulatoryReportCompiler.get_brsr_framework()}


# ---------------------------------------------------------------------------
# Rendered output endpoints (P1-3 / E4)
# ---------------------------------------------------------------------------

class RenderRequest(BaseModel):
    """Request body for HTML/PDF render endpoints."""
    framework: str = Field(
        ..., description="Framework code: TCFD | SFDR | GRI305 | SEC_CLIMATE | ISSB | APRA_CPG229 | BRSR"
    )
    entity_data: dict = Field(default_factory=dict)
    fund_data: dict = Field(default_factory=dict,
        description="Required for SFDR — pass fund-level data here")
    period_start: str = "2025-01-01"
    period_end: str = "2025-12-31"


def _compile_by_framework(req: RenderRequest):
    """Internal: compile the right framework and return a CompiledReport."""
    compiler = RegulatoryReportCompiler()
    fw = req.framework.upper().replace("-", "_")
    if fw == "TCFD":
        return compiler.compile_tcfd(req.entity_data, req.period_start, req.period_end)
    if fw in ("SFDR", "SFDR_PERIODIC"):
        return compiler.compile_sfdr_periodic(req.fund_data or req.entity_data, req.period_start, req.period_end)
    if fw in ("GRI305", "GRI_305"):
        return compiler.compile_gri305(req.entity_data, req.period_start, req.period_end)
    if fw in ("SEC_CLIMATE", "SEC"):
        return compiler.compile_sec_climate(req.entity_data, req.period_start, req.period_end)
    if fw in ("ISSB", "IFRS_S1_S2"):
        return compiler.compile_issb(req.entity_data, req.period_start, req.period_end)
    if fw in ("APRA_CPG229", "APRA"):
        return compiler.compile_apra_cpg229(req.entity_data, req.period_start, req.period_end)
    if fw == "BRSR":
        return compiler.compile_brsr(req.entity_data, req.period_start, req.period_end)
    raise HTTPException(
        status_code=422,
        detail=f"Unknown framework '{req.framework}'. "
               "Valid values: TCFD, SFDR, GRI305, SEC_CLIMATE, ISSB, APRA_CPG229, BRSR"
    )


@router.post(
    "/render/html",
    response_class=HTMLResponse,
    summary="Compile + render a regulatory report as HTML",
    description=(
        "Compiles the requested framework report and returns a self-contained HTML document "
        "suitable for browser display or as the input to the /render/pdf endpoint."
    ),
)
def render_html(req: RenderRequest):
    """Compile a regulatory report and return it as submission-ready HTML."""
    report = _compile_by_framework(req)
    html_str = RegulatoryReportCompiler.render_html(report)
    return HTMLResponse(content=html_str, status_code=200)


@router.post(
    "/render/pdf",
    summary="Compile + render a regulatory report as PDF",
    description=(
        "Compiles the requested framework report and returns a PDF binary via WeasyPrint. "
        "Requires `weasyprint` to be installed on the server (pip install weasyprint). "
        "Returns 501 if WeasyPrint is not available."
    ),
    responses={
        200: {"content": {"application/pdf": {}}, "description": "PDF report bytes"},
        501: {"description": "WeasyPrint not installed on server"},
    },
)
def render_pdf(req: RenderRequest):
    """Compile a regulatory report and return it as a PDF file download."""
    report = _compile_by_framework(req)
    try:
        pdf_bytes = RegulatoryReportCompiler.render_pdf_bytes(report)
    except ImportError as exc:
        raise HTTPException(
            status_code=501,
            detail=f"PDF rendering requires WeasyPrint: {exc}"
        )
    filename = f"{report.framework.replace(' ', '_')}_{report.entity_name.replace(' ', '_')}_{report.reporting_period_end[:4]}.pdf"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _report_to_dict(report) -> dict:
    """Convert CompiledReport dataclass to JSON-safe dict."""
    return {
        "report_id": report.report_id,
        "framework": report.framework,
        "entity_name": report.entity_name,
        "reporting_period_start": report.reporting_period_start,
        "reporting_period_end": report.reporting_period_end,
        "compilation_date": report.compilation_date,
        "overall_completeness_pct": report.overall_completeness_pct,
        "overall_status": report.overall_status,
        "sections": [
            {
                "section_id": s.section_id,
                "title": s.title,
                "framework": s.framework,
                "status": s.status,
                "completeness_pct": s.completeness_pct,
                "disclosures": s.disclosures,
                "narrative": s.narrative,
                "data_points": s.data_points,
                "gaps": s.gaps,
                "sources": s.sources,
            }
            for s in report.sections
        ],
        "summary": report.summary,
        "gaps_summary": report.gaps_summary,
        "recommendations": report.recommendations,
        "metadata": report.metadata,
    }
