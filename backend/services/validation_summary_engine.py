"""
Validation Summary Engine
===========================
Cross-cutting per-calculation audit envelope that wraps every engine output
with full traceability: inputs captured, methodology reference, parameters
applied, data sources, quality flags, and confidence scoring.

Implements BCBS 239 Principle 6 (accuracy), EBA GL/2020/06 §4.4 (data quality),
and PCAF DQS (Data Quality Score 1-5) propagation.

Usage — any engine endpoint can wrap its result:

    from services.validation_summary_engine import ValidationSummaryEngine, CalcMeta

    meta = CalcMeta(
        engine_name="re_clvar_engine",
        engine_version="2.1.0",
        methodology_reference="MSCI CLVaR 2024 / NGFS Phase V",
        inputs_captured={"property_type": "office", "floor_area_m2": 5000},
        parameters_applied={"discount_rate": 0.065, "carbon_price_2030": 130},
        data_sources=["CRREM v2.3 pathways", "IEA Grid EF 2024"],
        data_quality_flags=["EPC rating interpolated"],
    )
    envelope = ValidationSummaryEngine.wrap(result_dict, meta, user_id="uid-123")
"""
from __future__ import annotations

import hashlib
import json
import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Optional

logger = logging.getLogger("platform.validation_summary")


# ---------------------------------------------------------------------------
# DQS → Confidence Mapping  (PCAF Data Quality Score framework)
# ---------------------------------------------------------------------------

DQS_CONFIDENCE: dict[int, float] = {
    1: 1.00,  # Verified/audited
    2: 0.90,  # Reported
    3: 0.70,  # Physical activity-based estimates
    4: 0.50,  # Economic activity-based estimates
    5: 0.30,  # Estimated (proxy/revenue)
}


# ---------------------------------------------------------------------------
# Methodology Registry  — canonical references for each engine
# ---------------------------------------------------------------------------

METHODOLOGY_REGISTRY: dict[str, dict] = {
    "carbon_calculator": {
        "reference": "GHG Protocol Corporate Standard (2004, revised 2015)",
        "version": "2.0",
        "standards": ["GHG Protocol", "ISO 14064-1:2018"],
    },
    "carbon_calculator_v2": {
        "reference": "GHG Protocol Corporate Standard + Scope 3 Standard (2011)",
        "version": "2.0",
        "standards": ["GHG Protocol", "ISO 14064-1:2018", "DEFRA Conversion Factors 2024"],
    },
    "cbam_calculator": {
        "reference": "EU CBAM Regulation 2023/956, Implementing Regulation 2023/1773",
        "version": "1.0",
        "standards": ["EU CBAM Art. 7/21/31", "CN8 Nomenclature"],
    },
    "ecl_climate_engine": {
        "reference": "IFRS 9 B5.5.1–B5.5.55, EBA GL/2020/06, ECB Guide on C&E Risks",
        "version": "1.0",
        "standards": ["IFRS 9", "CRR2 Art. 178", "EBA GL/2020/06"],
    },
    "re_clvar_engine": {
        "reference": "MSCI CLVaR 2024, NGFS Phase V Physical Risk, ECB Climate Stress Test 2024",
        "version": "2.1",
        "standards": ["TCFD", "NGFS", "ECB/SSM"],
    },
    "crrem_stranding_engine": {
        "reference": "CRREM v2.3 Decarbonisation Pathways, IEA NZE 2050",
        "version": "2.0",
        "standards": ["CRREM", "RICS VPS 4", "IVS 2024"],
    },
    "epc_transition_engine": {
        "reference": "EU EPBD Recast 2024/1275, UK MEES Regulations 2015",
        "version": "1.0",
        "standards": ["EPBD", "MEES", "EPC Directive"],
    },
    "green_premium_engine": {
        "reference": "JLL Green Building Premium Research 2024, MSCI IPD Green Index",
        "version": "1.0",
        "standards": ["Hedonic Regression", "RICS VPGA 12"],
    },
    "real_estate_valuation_engine": {
        "reference": "RICS Red Book 2022 (PS 1/2, VPS 1-5), IVSC IVS 104/400",
        "version": "1.0",
        "standards": ["RICS Red Book", "IVSC IVS", "AICPA SSVS"],
    },
    "nature_risk_calculator": {
        "reference": "TNFD LEAP v1.1 (2024), ENCORE, SBTN v1",
        "version": "1.0",
        "standards": ["TNFD LEAP", "CBD-GBF Target 15", "ENCORE"],
    },
    "stranded_asset_calculator": {
        "reference": "Carbon Tracker CTI 2023, IEA WEO 2024 NZE",
        "version": "1.0",
        "standards": ["IFRS IAS 36 Impairment", "Carbon Tracker"],
    },
    "pd_calculator": {
        "reference": "CRR2 Art. 178/179, EBA GL/2017/16 PD Estimation",
        "version": "1.0",
        "standards": ["Basel III/IV", "EBA GL/2017/16", "CRR2"],
    },
    "monte_carlo_engine": {
        "reference": "BCBS 239, EBA GL/2018/04 Stress Testing, Glasserman (2003)",
        "version": "1.0",
        "standards": ["BCBS 239", "EBA GL/2018/04"],
    },
    "pe_deal_engine": {
        "reference": "ILPA ESG Assessment Framework 2024, UNPRI DDQ v4",
        "version": "1.0",
        "standards": ["ILPA", "UNPRI", "SFDR Art. 8/9"],
    },
    "pe_portfolio_monitor": {
        "reference": "ILPA Reporting Template v3 (2024), EDCI v3",
        "version": "1.0",
        "standards": ["ILPA", "EDCI", "SFDR PAI"],
    },
    "technology_risk_engine": {
        "reference": "EU EED Recast 2023/1791 Art. 12, ISO 30134 (PUE/WUE/CUE/REF/ERF), GSF SCI v1",
        "version": "1.0",
        "standards": ["EU EED", "ISO 30134", "GSF SCI", "GHG Protocol ICT Guidance"],
    },
    "insurance_risk_engine": {
        "reference": "Solvency II Delegated Reg. 2015/35, EIOPA Opinion on C&E Risks (2023)",
        "version": "1.0",
        "standards": ["Solvency II", "EIOPA", "IFRS 17"],
    },
    "banking_risk_engine": {
        "reference": "CRR2/CRD V, EBA GL/2020/06, ECB Guide on C&E Risks (2024 update)",
        "version": "1.0",
        "standards": ["CRR2", "EBA GL/2020/06", "ECB/SSM"],
    },
    "agriculture_risk_calculator": {
        "reference": "EUDR Regulation 2023/1115, IPCC AR6 WG III Ch. 7, FAO GLEAM",
        "version": "1.0",
        "standards": ["EUDR", "IPCC Tier 1/2", "FAO"],
    },
    "mining_risk_engine": {
        "reference": "GISTM (2020), ICMM Closure Standard, IFC PS 6",
        "version": "1.0",
        "standards": ["GISTM", "ICMM", "IFC PS 6"],
    },
    "facilitated_emissions_engine": {
        "reference": "PCAF Standard Part C (2024), GHG Protocol Scope 3 Cat 15",
        "version": "1.0",
        "standards": ["PCAF Part C", "GHG Protocol"],
    },
    "factor_overlay_engine": {
        "reference": "Internal Factor Model v1, ESG/Geo/Tech 31-factor registry",
        "version": "1.0",
        "standards": ["Fama-French", "BCBS 239"],
    },
}


# ---------------------------------------------------------------------------
# Confidence Scoring Model
# ---------------------------------------------------------------------------

def compute_confidence(
    data_quality_flags: list[str],
    dqs_scores: list[int] | None = None,
    input_completeness_pct: float = 100.0,
    methodology_maturity: str = "established",  # established | evolving | experimental
) -> float:
    """
    Compute 0-1 confidence score based on:
      - PCAF DQS scores (if provided)
      - Number of data quality flags (penalties)
      - Input completeness
      - Methodology maturity
    """
    base = 1.0

    # DQS-weighted (PCAF framework)
    if dqs_scores:
        avg_confidence = sum(DQS_CONFIDENCE.get(d, 0.3) for d in dqs_scores) / len(dqs_scores)
        base = min(base, avg_confidence)

    # Quality flag penalties (each flag reduces confidence by 5%)
    flag_penalty = len(data_quality_flags) * 0.05
    base -= flag_penalty

    # Input completeness scaling
    base *= (input_completeness_pct / 100.0)

    # Methodology maturity discount
    maturity_mult = {"established": 1.0, "evolving": 0.9, "experimental": 0.75}
    base *= maturity_mult.get(methodology_maturity, 0.85)

    return round(max(0.0, min(1.0, base)), 3)


# ---------------------------------------------------------------------------
# Data Classes
# ---------------------------------------------------------------------------

@dataclass
class CalcMeta:
    """Metadata that each engine endpoint provides when wrapping results."""
    engine_name: str
    engine_version: str = ""
    methodology_reference: str = ""
    inputs_captured: dict[str, Any] = field(default_factory=dict)
    parameters_applied: dict[str, Any] = field(default_factory=dict)
    data_sources: list[str] = field(default_factory=list)
    data_quality_flags: list[str] = field(default_factory=list)
    dqs_scores: list[int] = field(default_factory=list)
    input_completeness_pct: float = 100.0
    methodology_maturity: str = "established"


@dataclass
class ValidationSummary:
    """The per-calculation audit envelope."""
    calculation_id: str
    engine_name: str
    engine_version: str
    methodology_reference: str
    standards: list[str]
    inputs_captured: dict[str, Any]
    parameters_applied: dict[str, Any]
    data_sources: list[str]
    data_quality_flags: list[str]
    outputs_hash: str          # SHA-256 of JSON-serialised outputs (non-repudiation)
    confidence_score: float
    confidence_band: str       # high (>0.7) | medium (0.4-0.7) | low (<0.4)
    timestamp: str             # ISO 8601 UTC
    computed_by: str | None


# ---------------------------------------------------------------------------
# Engine
# ---------------------------------------------------------------------------

class ValidationSummaryEngine:
    """
    Cross-cutting wrapper that produces a BCBS 239-compliant validation
    summary envelope for any engine calculation result.
    """

    @staticmethod
    def wrap(
        result: dict[str, Any],
        meta: CalcMeta,
        user_id: str | None = None,
    ) -> dict[str, Any]:
        """
        Wrap a raw engine result dict with a validation_summary envelope.

        Returns the original result dict augmented with a top-level
        "validation_summary" key.
        """
        # Look up methodology registry for canonical references
        registry_entry = METHODOLOGY_REGISTRY.get(meta.engine_name, {})
        meth_ref = meta.methodology_reference or registry_entry.get("reference", "")
        version = meta.engine_version or registry_entry.get("version", "")
        standards = registry_entry.get("standards", [])

        # Compute confidence
        confidence = compute_confidence(
            data_quality_flags=meta.data_quality_flags,
            dqs_scores=meta.dqs_scores if meta.dqs_scores else None,
            input_completeness_pct=meta.input_completeness_pct,
            methodology_maturity=meta.methodology_maturity,
        )

        if confidence >= 0.7:
            band = "high"
        elif confidence >= 0.4:
            band = "medium"
        else:
            band = "low"

        # Non-repudiation hash of outputs
        try:
            outputs_json = json.dumps(result, sort_keys=True, default=str)
            outputs_hash = hashlib.sha256(outputs_json.encode("utf-8")).hexdigest()
        except Exception:
            outputs_hash = "hash_computation_failed"

        calc_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()

        summary = ValidationSummary(
            calculation_id=calc_id,
            engine_name=meta.engine_name,
            engine_version=version,
            methodology_reference=meth_ref,
            standards=standards,
            inputs_captured=meta.inputs_captured,
            parameters_applied=meta.parameters_applied,
            data_sources=meta.data_sources,
            data_quality_flags=meta.data_quality_flags,
            outputs_hash=outputs_hash,
            confidence_score=confidence,
            confidence_band=band,
            timestamp=now,
            computed_by=user_id,
        )

        envelope = {
            "calculation_id": summary.calculation_id,
            "engine_name": summary.engine_name,
            "engine_version": summary.engine_version,
            "methodology_reference": summary.methodology_reference,
            "standards": summary.standards,
            "inputs_captured": summary.inputs_captured,
            "parameters_applied": summary.parameters_applied,
            "data_sources": summary.data_sources,
            "data_quality_flags": summary.data_quality_flags,
            "outputs_hash": summary.outputs_hash,
            "confidence_score": summary.confidence_score,
            "confidence_band": summary.confidence_band,
            "timestamp": summary.timestamp,
            "computed_by": summary.computed_by,
        }

        # Return augmented result
        wrapped = dict(result)
        wrapped["validation_summary"] = envelope
        return wrapped

    @staticmethod
    def get_methodology_registry() -> dict[str, dict]:
        """Return the full methodology registry for documentation/UI display."""
        return dict(METHODOLOGY_REGISTRY)

    @staticmethod
    def get_dqs_confidence_map() -> dict[int, float]:
        """Return PCAF DQS → confidence mapping."""
        return dict(DQS_CONFIDENCE)

    @staticmethod
    def batch_wrap(
        results: list[dict[str, Any]],
        metas: list[CalcMeta],
        user_id: str | None = None,
    ) -> list[dict[str, Any]]:
        """Wrap multiple results in a single batch (e.g., portfolio-level)."""
        if len(results) != len(metas):
            raise ValueError("results and metas must have the same length")
        return [
            ValidationSummaryEngine.wrap(r, m, user_id)
            for r, m in zip(results, metas)
        ]


# ---------------------------------------------------------------------------
# Convenience: Quick-wrap for engines that don't supply full CalcMeta
# ---------------------------------------------------------------------------

def quick_wrap(
    engine_name: str,
    result: dict[str, Any],
    inputs: dict[str, Any] | None = None,
    params: dict[str, Any] | None = None,
    flags: list[str] | None = None,
    user_id: str | None = None,
) -> dict[str, Any]:
    """
    Shortcut for engines that want minimal integration effort.

    Example:
        from services.validation_summary_engine import quick_wrap
        result = engine.calculate(...)
        return quick_wrap("re_clvar_engine", result, inputs={"area": 5000})
    """
    meta = CalcMeta(
        engine_name=engine_name,
        inputs_captured=inputs or {},
        parameters_applied=params or {},
        data_quality_flags=flags or [],
    )
    return ValidationSummaryEngine.wrap(result, meta, user_id)
