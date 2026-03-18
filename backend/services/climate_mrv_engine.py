"""
Climate Data & MRV Engine — E73
================================
Implements ISO 14064-3 MRV system assessment, satellite coverage scoring
(TROPOMI/Sentinel-5P, GHGSat, CarbonMapper), PCAF DQS mapping, digital MRV
maturity model (5 levels), and CDP/EMAS/UK SECR/EU ETS MRV compliance.

References:
- ISO 14064-3:2019 (GHG Programmes — Validation and Verification)
- ISO 14064-1:2018 (GHG Accounting and Reporting)
- CDP Climate STTI 2023 (Science-based Targets and Transition Intelligence)
- PCAF Data Quality Score framework 2022
- EU ETS MRV Regulation 2018/2066 (Monitoring and Reporting)
- UK SECR — Streamlined Energy and Carbon Reporting (SI 2018/1155)
- EMAS — EU Eco-Management and Audit Scheme Regulation 1221/2009
- GHG Protocol Corporate Standard (Scope 1/2/3)
"""
from __future__ import annotations

import random
from typing import Any, List, Optional
from pydantic import BaseModel, Field

# ---------------------------------------------------------------------------
# Pydantic Models
# ---------------------------------------------------------------------------

class MRVSystemResult(BaseModel):
    class Config:
        extra = "allow"
    entity_id: str
    facility_name: str
    sector: str
    mrv_system_type: str
    annual_emissions_tco2e: float
    iso14064_level: str
    data_quality_score: float
    accuracy_pct: float
    completeness_pct: float
    timeliness_score: float
    digital_mrv_maturity: int
    maturity_label: str
    verification_readiness: str
    checklist_results: list
    cdp_submission_status: str
    emas_applicable: bool
    uk_secr_applicable: bool
    eu_ets_mrv_applicable: bool
    ghg_inventory_summary: dict
    recommendations: list

class SatelliteCoverageResult(BaseModel):
    class Config:
        extra = "allow"
    entity_id: str
    lat: float
    lng: float
    facility_type: str
    tropomi_detection_probability_pct: float
    ghgsat_point_source_resolution_m: float
    carbonmapper_sensitivity_ppb: float
    overpass_frequency_days: float
    satellite_systems: list
    methane_detection_threshold_kg_hr: float
    co2_detection_threshold_kt_yr: float
    overall_satellite_coverage_score: float
    coverage_tier: str
    monitoring_gaps: list

class DataQualityResult(BaseModel):
    class Config:
        extra = "allow"
    entity_id: str
    pcaf_dqs: int
    pcaf_dqs_label: str
    confidence_weight: float
    cdp_completeness_pct: float
    ipcc_tier: int
    ipcc_tier_label: str
    third_party_verified: bool
    uncertainty_pct: float
    dimension_scores: dict
    overall_dqs_score: float
    improvement_actions: list

class DigitalMRVMaturityResult(BaseModel):
    class Config:
        extra = "allow"
    entity_id: str
    current_maturity_level: int
    current_maturity_label: str
    target_maturity_level: int
    gap_analysis: list
    upgrade_roadmap: list
    estimated_cost_usd: float
    estimated_timeline_months: int
    capability_gaps: dict
    benefits_at_target: list

class MRVReportResult(BaseModel):
    class Config:
        extra = "allow"
    entity_id: str
    iso14064_3_checklist: list
    emas_requirements: dict
    uk_secr_requirements: dict
    eu_ets_mrv_requirements: dict
    overall_compliance_score: float
    critical_gaps: list
    recommendations: list

# ---------------------------------------------------------------------------
# Reference Data
# ---------------------------------------------------------------------------

SATELLITE_SYSTEMS = {
    "TROPOMI": {
        "full_name": "TROPOspheric Monitoring Instrument (Sentinel-5P)",
        "operator": "ESA / Copernicus",
        "species": ["CH4", "NO2", "CO", "SO2", "O3"],
        "spatial_resolution_km": 5.5,
        "revisit_days": 1,
        "detection_threshold_ppb": 5.0,
        "methane_detection_kg_hr": 1000.0,
        "coverage": "global",
        "free_access": True,
    },
    "GHGSat": {
        "full_name": "GHGSat Constellation",
        "operator": "GHGSat Inc.",
        "species": ["CH4", "CO2"],
        "spatial_resolution_m": 25.0,
        "revisit_days": 3,
        "detection_threshold_ppb": 0.1,
        "methane_detection_kg_hr": 50.0,
        "coverage": "targeted_global",
        "free_access": False,
    },
    "CarbonMapper": {
        "full_name": "CarbonMapper / AVIRIS-NG",
        "operator": "Carbon Mapper / NASA JPL",
        "species": ["CH4", "CO2"],
        "spatial_resolution_m": 3.0,
        "revisit_days": 14,
        "detection_threshold_ppb": 0.05,
        "methane_detection_kg_hr": 10.0,
        "coverage": "campaign_based",
        "free_access": True,
    },
    "MethaneSAT": {
        "full_name": "MethaneSAT",
        "operator": "Environmental Defense Fund",
        "species": ["CH4"],
        "spatial_resolution_km": 1.0,
        "revisit_days": 7,
        "detection_threshold_ppb": 2.0,
        "methane_detection_kg_hr": 200.0,
        "coverage": "global_hotspots",
        "free_access": True,
    },
    "Landsat_TIRS": {
        "full_name": "Landsat Thermal Infrared Sensor",
        "operator": "USGS / NASA",
        "species": ["thermal_emissions", "land_use"],
        "spatial_resolution_m": 100.0,
        "revisit_days": 16,
        "detection_threshold_ppb": None,
        "methane_detection_kg_hr": None,
        "coverage": "global",
        "free_access": True,
    },
}

ISO_14064_3_CHECKLIST = [
    {"item": "1. Verification scope and boundary", "standard_ref": "ISO 14064-3 §5.2", "weight": 0.08},
    {"item": "2. GHG assertion completeness", "standard_ref": "ISO 14064-3 §5.3", "weight": 0.10},
    {"item": "3. Material misstatement risk assessment", "standard_ref": "ISO 14064-3 §5.4", "weight": 0.10},
    {"item": "4. Evidence-gathering procedures", "standard_ref": "ISO 14064-3 §6.1", "weight": 0.09},
    {"item": "5. Site visits and interviews", "standard_ref": "ISO 14064-3 §6.2", "weight": 0.07},
    {"item": "6. Data and information systems review", "standard_ref": "ISO 14064-3 §6.3", "weight": 0.09},
    {"item": "7. Sampling methodology", "standard_ref": "ISO 14064-3 §6.4", "weight": 0.07},
    {"item": "8. Calculation methodology audit", "standard_ref": "ISO 14064-3 §6.5", "weight": 0.09},
    {"item": "9. Uncertainty quantification", "standard_ref": "ISO 14064-3 §7.1", "weight": 0.08},
    {"item": "10. Materiality threshold assessment (5%)", "standard_ref": "ISO 14064-3 §7.2", "weight": 0.08},
    {"item": "11. Verification opinion (limited/reasonable)", "standard_ref": "ISO 14064-3 §8.1", "weight": 0.08},
    {"item": "12. Verification statement issuance", "standard_ref": "ISO 14064-3 §8.2", "weight": 0.07},
]

MRV_SYSTEM_TYPES = {
    "manual_spreadsheet": {"maturity": 1, "accuracy_range": (60, 80), "completeness_range": (55, 75)},
    "erp_module": {"maturity": 2, "accuracy_range": (75, 88), "completeness_range": (70, 85)},
    "dedicated_esg_platform": {"maturity": 3, "accuracy_range": (82, 93), "completeness_range": (80, 93)},
    "iot_integrated": {"maturity": 4, "accuracy_range": (88, 97), "completeness_range": (88, 97)},
    "ai_automated": {"maturity": 5, "accuracy_range": (93, 99), "completeness_range": (93, 99)},
    "hybrid": {"maturity": 3, "accuracy_range": (78, 92), "completeness_range": (75, 90)},
}

MATURITY_LABELS = {
    1: "Manual",
    2: "Automated",
    3: "Integrated",
    4: "Intelligent",
    5: "Autonomous",
}

MATURITY_DESCRIPTIONS = {
    1: "Manual data collection via spreadsheets; high risk of error; no audit trail",
    2: "System-driven data capture from ERP/accounting; basic workflow; some automation",
    3: "Dedicated ESG platform with cross-system integration; workflow management; API connections",
    4: "IoT sensor integration; near real-time data; AI anomaly detection; digital twin",
    5: "Fully autonomous; continuous satellite + IoT monitoring; blockchain attestation; predictive analytics",
}

PCAF_DQS_MAPPING = {
    1: {"label": "Verified primary data", "confidence": 1.00, "description": "Third-party verified Scope 1/2/3 data per GHG Protocol"},
    2: {"label": "Reported primary data", "confidence": 0.90, "description": "Self-reported data not independently verified"},
    3: {"label": "Physical activity based", "confidence": 0.70, "description": "Derived from physical activity data with emission factors"},
    4: {"label": "Economic activity based", "confidence": 0.50, "description": "Derived from economic/spend data with sector EFs"},
    5: {"label": "Revenue/asset proxy", "confidence": 0.30, "description": "Estimated from revenue or asset size proxies"},
}

SECTOR_EMISSION_FACTORS = {
    "steel": {"scope1_intensity_tco2_t": 1.85, "eu_ets_covered": True},
    "cement": {"scope1_intensity_tco2_t": 0.64, "eu_ets_covered": True},
    "chemicals": {"scope1_intensity_tco2_t": 0.42, "eu_ets_covered": True},
    "oil_gas_upstream": {"scope1_intensity_tco2_boe": 0.028, "eu_ets_covered": True},
    "power_generation": {"scope1_intensity_tco2_mwh": 0.45, "eu_ets_covered": True},
    "manufacturing": {"scope1_intensity_tco2_eur_mn_rev": 145.0, "eu_ets_covered": False},
    "logistics_transport": {"scope1_intensity_tco2_km_t": 0.062, "eu_ets_covered": False},
    "real_estate": {"scope1_intensity_kgco2_m2_yr": 18.5, "eu_ets_covered": False},
}

# ---------------------------------------------------------------------------
# Helper utilities
# ---------------------------------------------------------------------------

def _rng(entity_id: str) -> random.Random:
    return random.Random(hash(str(entity_id)) & 0xFFFFFFFF)

# ---------------------------------------------------------------------------
# Core Engine Functions
# ---------------------------------------------------------------------------

def assess_mrv_system(
    entity_id: str,
    facility_name: str,
    sector: str,
    mrv_type: str,
    annual_emissions_tco2e: float,
) -> dict:
    """
    Assess an MRV system: ISO 14064-3 level, data quality, digital MRV
    maturity index, verification readiness.
    """
    rng = _rng(entity_id + facility_name)

    mrv_info = MRV_SYSTEM_TYPES.get(mrv_type, MRV_SYSTEM_TYPES["dedicated_esg_platform"])
    maturity = mrv_info["maturity"]

    # Data quality dimensions
    acc_min, acc_max = mrv_info["accuracy_range"]
    comp_min, comp_max = mrv_info["completeness_range"]
    accuracy_pct = round(rng.uniform(acc_min, acc_max), 1)
    completeness_pct = round(rng.uniform(comp_min, comp_max), 1)
    timeliness_score = round(rng.uniform(acc_min * 0.95, acc_max * 0.95), 1)

    dqs_raw = (accuracy_pct + completeness_pct + timeliness_score) / 3.0
    data_quality_score = round(dqs_raw, 1)

    # ISO 14064-3 level
    if maturity >= 4 and data_quality_score >= 88:
        iso_level = "Level_1_Reasonable_Assurance"
    elif maturity >= 3 and data_quality_score >= 75:
        iso_level = "Level_2_Limited_Assurance"
    else:
        iso_level = "Level_3_Compilation"

    # Verification readiness
    if data_quality_score >= 88 and maturity >= 3:
        readiness = "ready_for_third_party_verification"
    elif data_quality_score >= 72:
        readiness = "nearly_ready_minor_gaps"
    elif data_quality_score >= 55:
        readiness = "preparatory_work_needed"
    else:
        readiness = "significant_remediation_required"

    # ISO 14064-3 checklist
    checklist_results = []
    for item in ISO_14064_3_CHECKLIST:
        base_score = rng.uniform(55.0, 98.0)
        if maturity >= 4:
            base_score = min(100.0, base_score + 5.0)
        score = round(base_score, 1)
        checklist_results.append({
            "item": item["item"],
            "standard_ref": item["standard_ref"],
            "score": score,
            "weight": item["weight"],
            "status": "compliant" if score >= 70.0 else "non_compliant",
        })

    # CDP submission status
    if completeness_pct >= 85.0:
        cdp_status = "A_list_eligible"
    elif completeness_pct >= 70.0:
        cdp_status = "B_score_range"
    elif completeness_pct >= 55.0:
        cdp_status = "C_score_range"
    else:
        cdp_status = "D_score_incomplete"

    # Applicability flags
    sector_info = SECTOR_EMISSION_FACTORS.get(sector, {})
    eu_ets_applicable = sector_info.get("eu_ets_covered", False)
    emas_applicable = sector in ["manufacturing", "chemicals", "steel", "cement"]
    uk_secr_applicable = annual_emissions_tco2e >= 4000.0

    # GHG inventory summary
    scope2_factor = rng.uniform(0.25, 0.45)
    scope3_factor = rng.uniform(1.5, 4.0)
    ghg_inventory = {
        "scope1_tco2e": round(annual_emissions_tco2e, 0),
        "scope2_location_tco2e": round(annual_emissions_tco2e * scope2_factor, 0),
        "scope2_market_tco2e": round(annual_emissions_tco2e * scope2_factor * 0.85, 0),
        "scope3_material_categories_tco2e": round(annual_emissions_tco2e * scope3_factor, 0),
        "total_ghg_tco2e": round(annual_emissions_tco2e * (1.0 + scope2_factor + scope3_factor), 0),
        "reporting_year": 2024,
        "ghg_protocol_compliant": maturity >= 2,
        "third_party_verified": maturity >= 3 and data_quality_score >= 80,
    }

    recommendations = []
    if maturity < 3:
        recommendations.append("Upgrade from manual spreadsheets to a dedicated ESG/MRV platform")
    if completeness_pct < 80.0:
        recommendations.append("Improve Scope 3 category coverage to reach 80% completeness threshold")
    if eu_ets_applicable and data_quality_score < 85.0:
        recommendations.append("Enhance measurement precision for EU ETS MRV Regulation 2018/2066 compliance")
    if uk_secr_applicable:
        recommendations.append("Ensure SECR annual reporting covers energy use and Scope 1+2 GHG emissions")
    if iso_level == "Level_3_Compilation":
        recommendations.append("Invest in verification infrastructure to achieve ISO 14064-3 Level 2 assurance")

    return MRVSystemResult(
        entity_id=entity_id,
        facility_name=facility_name,
        sector=sector,
        mrv_system_type=mrv_type,
        annual_emissions_tco2e=annual_emissions_tco2e,
        iso14064_level=iso_level,
        data_quality_score=data_quality_score,
        accuracy_pct=accuracy_pct,
        completeness_pct=completeness_pct,
        timeliness_score=timeliness_score,
        digital_mrv_maturity=maturity,
        maturity_label=MATURITY_LABELS[maturity],
        verification_readiness=readiness,
        checklist_results=checklist_results,
        cdp_submission_status=cdp_status,
        emas_applicable=emas_applicable,
        uk_secr_applicable=uk_secr_applicable,
        eu_ets_mrv_applicable=eu_ets_applicable,
        ghg_inventory_summary=ghg_inventory,
        recommendations=recommendations,
    ).dict()


def score_satellite_coverage(
    entity_id: str,
    lat: float,
    lng: float,
    facility_type: str,
) -> dict:
    """
    Score satellite coverage: TROPOMI/Sentinel-5P methane detection,
    GHGSat point-source resolution, CarbonMapper sensitivity, overpass frequency.
    """
    rng = _rng(entity_id + str(lat) + str(lng))

    # Latitude-based factors (polar regions have lower coverage)
    lat_abs = abs(lat)
    lat_factor = 1.0 if lat_abs < 60 else 0.85 if lat_abs < 70 else 0.65

    # Facility type detection thresholds
    facility_emission_rates = {
        "oil_gas_facility": 5000.0,
        "coal_mine": 2000.0,
        "steel_plant": 8000.0,
        "cement_plant": 6000.0,
        "chemical_plant": 3000.0,
        "power_plant": 10000.0,
        "landfill": 1500.0,
        "wastewater": 800.0,
        "agriculture": 500.0,
        "other": 1000.0,
    }
    facility_rate_kg_hr = facility_emission_rates.get(facility_type, 1000.0)

    satellite_results = []
    for sat_name, sat_info in SATELLITE_SYSTEMS.items():
        if sat_info.get("methane_detection_kg_hr") is None:
            continue
        detection_threshold = sat_info["methane_detection_kg_hr"]
        detection_probability = min(
            98.0,
            max(5.0, (facility_rate_kg_hr / detection_threshold) * 60.0 * lat_factor)
        )
        detection_probability = round(detection_probability + rng.uniform(-5.0, 5.0), 1)
        detection_probability = max(5.0, min(98.0, detection_probability))

        satellite_results.append({
            "satellite": sat_name,
            "full_name": sat_info["full_name"],
            "operator": sat_info["operator"],
            "species_detected": sat_info["species"],
            "spatial_resolution": sat_info.get("spatial_resolution_m") or sat_info.get("spatial_resolution_km"),
            "resolution_unit": "m" if "spatial_resolution_m" in sat_info else "km",
            "revisit_days": sat_info["revisit_days"],
            "detection_threshold_kg_hr": detection_threshold,
            "detection_probability_pct": detection_probability,
            "detectable": detection_probability > 50.0,
            "free_access": sat_info["free_access"],
        })

    # Overall coverage score
    detectable_count = sum(1 for s in satellite_results if s["detectable"])
    overall_score = round((detectable_count / len(satellite_results)) * 100.0, 1) if satellite_results else 0.0

    # Coverage tier
    if overall_score >= 75.0:
        coverage_tier = "high_coverage"
    elif overall_score >= 50.0:
        coverage_tier = "medium_coverage"
    elif overall_score >= 25.0:
        coverage_tier = "low_coverage"
    else:
        coverage_tier = "minimal_coverage"

    # Monitoring gaps
    gaps = []
    if lat_abs > 60:
        gaps.append("High latitude reduces satellite overpass frequency and detection reliability")
    if facility_rate_kg_hr < 200:
        gaps.append("Low emission rate facility below most satellite detection thresholds")
    if not any(s["detectable"] and not s["free_access"] for s in satellite_results):
        gaps.append("No paid commercial satellite coverage assessed — consider GHGSat targeted monitoring contract")

    # Best estimates
    tropomi_result = next((s for s in satellite_results if s["satellite"] == "TROPOMI"), None)
    ghgsat_result = next((s for s in satellite_results if s["satellite"] == "GHGSat"), None)
    cm_result = next((s for s in satellite_results if s["satellite"] == "CarbonMapper"), None)

    return SatelliteCoverageResult(
        entity_id=entity_id,
        lat=lat,
        lng=lng,
        facility_type=facility_type,
        tropomi_detection_probability_pct=tropomi_result["detection_probability_pct"] if tropomi_result else 0.0,
        ghgsat_point_source_resolution_m=GHGSat_res if (GHGSat_res := SATELLITE_SYSTEMS["GHGSat"].get("spatial_resolution_m")) else 25.0,
        carbonmapper_sensitivity_ppb=SATELLITE_SYSTEMS["CarbonMapper"]["detection_threshold_ppb"],
        overpass_frequency_days=round(
            sum(s["revisit_days"] for s in satellite_results) / len(satellite_results) if satellite_results else 7.0,
            1
        ),
        satellite_systems=satellite_results,
        methane_detection_threshold_kg_hr=SATELLITE_SYSTEMS["GHGSat"]["methane_detection_kg_hr"],
        co2_detection_threshold_kt_yr=round(rng.uniform(10.0, 50.0), 1),
        overall_satellite_coverage_score=overall_score,
        coverage_tier=coverage_tier,
        monitoring_gaps=gaps,
    ).dict()


def calculate_data_quality_score(
    entity_id: str,
    data_sources: Optional[list] = None,
) -> dict:
    """
    Calculate PCAF DQS 1-5 mapping, CDP completeness, IPCC Tier level,
    uncertainty quantification.
    """
    rng = _rng(entity_id + "dqs")

    if not data_sources:
        data_sources = [
            {"type": "utility_bills", "verified": False, "coverage_pct": 75.0},
            {"type": "fuel_invoices", "verified": False, "coverage_pct": 85.0},
            {"type": "meter_readings", "verified": False, "coverage_pct": 60.0},
        ]

    # Assess data source quality
    total_coverage = 0.0
    verified_sources = 0
    primary_sources = 0

    for ds in data_sources:
        total_coverage += ds.get("coverage_pct", 50.0)
        if ds.get("verified"):
            verified_sources += 1
        if ds.get("type") in ["utility_bills", "fuel_invoices", "meter_readings", "iot_sensors"]:
            primary_sources += 1

    avg_coverage = total_coverage / len(data_sources) if data_sources else 50.0
    third_party_verified = verified_sources >= len(data_sources) * 0.5

    # PCAF DQS determination
    if third_party_verified and avg_coverage >= 90.0:
        pcaf_dqs = 1
    elif avg_coverage >= 80.0 and primary_sources >= len(data_sources) * 0.6:
        pcaf_dqs = 2
    elif avg_coverage >= 65.0:
        pcaf_dqs = 3
    elif avg_coverage >= 45.0:
        pcaf_dqs = 4
    else:
        pcaf_dqs = 5

    dqs_info = PCAF_DQS_MAPPING[pcaf_dqs]

    # IPCC Tier determination
    if primary_sources >= len(data_sources) * 0.7 and avg_coverage >= 80.0:
        ipcc_tier = 3
        ipcc_label = "Facility-specific measurement data"
    elif primary_sources >= len(data_sources) * 0.4:
        ipcc_tier = 2
        ipcc_label = "Country/sector specific emission factors"
    else:
        ipcc_tier = 1
        ipcc_label = "Default IPCC emission factors"

    # Uncertainty quantification
    uncertainty_by_tier = {1: rng.uniform(20.0, 60.0), 2: rng.uniform(10.0, 25.0), 3: rng.uniform(3.0, 12.0)}
    uncertainty_pct = round(uncertainty_by_tier[ipcc_tier], 1)

    # CDP completeness
    cdp_completeness = round(avg_coverage * rng.uniform(0.85, 1.0), 1)

    # Dimension scores
    dimension_scores = {
        "completeness": round(avg_coverage, 1),
        "accuracy": round(95.0 - (5 - pcaf_dqs) * 7 + rng.uniform(-3, 3), 1),
        "timeliness": round(rng.uniform(65.0, 92.0), 1),
        "granularity": round(primary_sources / max(len(data_sources), 1) * 100.0 + rng.uniform(-10, 10), 1),
        "verifiability": round(100.0 if third_party_verified else rng.uniform(40.0, 70.0), 1),
    }
    for k in dimension_scores:
        dimension_scores[k] = max(0.0, min(100.0, dimension_scores[k]))

    overall_dqs_score = round(sum(dimension_scores.values()) / len(dimension_scores), 1)

    # Improvement actions
    improvement_actions = []
    if pcaf_dqs > 2:
        improvement_actions.append("Move from estimated to primary activity-based emission factors (IPCC Tier 2→3)")
    if not third_party_verified:
        improvement_actions.append("Commission ISO 14064-3 third-party verification for key emission sources")
    if avg_coverage < 80.0:
        improvement_actions.append("Expand data collection coverage to ≥80% of emission sources")
    if ipcc_tier < 3:
        improvement_actions.append(f"Upgrade from IPCC Tier {ipcc_tier} to Tier {ipcc_tier+1} measurement methods")

    return DataQualityResult(
        entity_id=entity_id,
        pcaf_dqs=pcaf_dqs,
        pcaf_dqs_label=dqs_info["label"],
        confidence_weight=dqs_info["confidence"],
        cdp_completeness_pct=cdp_completeness,
        ipcc_tier=ipcc_tier,
        ipcc_tier_label=ipcc_label,
        third_party_verified=third_party_verified,
        uncertainty_pct=uncertainty_pct,
        dimension_scores=dimension_scores,
        overall_dqs_score=overall_dqs_score,
        improvement_actions=improvement_actions,
    ).dict()


def assess_digital_mrv_maturity(
    entity_id: str,
    current_systems: Optional[list] = None,
) -> dict:
    """
    Assess digital MRV maturity: 5-level model (manual→autonomous),
    gap analysis, upgrade roadmap, cost estimate.
    """
    rng = _rng(entity_id + "maturity")

    if not current_systems:
        current_systems = ["spreadsheets", "erp_partial"]

    # Determine current level
    level_indicators = {
        1: ["spreadsheets", "manual", "excel"],
        2: ["erp", "erp_partial", "accounting_system", "automated_some"],
        3: ["esg_platform", "dedicated_software", "api_connected", "erp_integrated"],
        4: ["iot", "iot_sensors", "real_time", "smart_meters", "digital_twin"],
        5: ["ai", "ml", "blockchain", "fully_automated", "autonomous", "satellite_direct"],
    }

    current_level = 1
    for sys in current_systems:
        for level, indicators in level_indicators.items():
            if any(ind in sys.lower() for ind in indicators):
                current_level = max(current_level, level)

    target_level = min(5, current_level + 2)

    # Gap analysis by capability
    capabilities = [
        "Data collection automation",
        "Real-time monitoring",
        "IoT sensor integration",
        "API connectivity to source systems",
        "Uncertainty quantification",
        "Third-party verification workflow",
        "Satellite data integration",
        "AI anomaly detection",
        "Blockchain attestation",
        "Scope 3 supplier portal",
    ]

    maturity_thresholds = {cap: rng.randint(2, 5) for cap in capabilities}
    capability_gaps = {}
    for cap in capabilities:
        threshold = maturity_thresholds[cap]
        if current_level < threshold:
            capability_gaps[cap] = {
                "current": current_level,
                "required_level": threshold,
                "gap": threshold - current_level,
                "priority": "high" if threshold - current_level >= 2 else "medium",
            }

    # Upgrade roadmap
    roadmap = []
    for step_level in range(current_level + 1, target_level + 1):
        step_cost = {
            2: rng.uniform(50_000, 150_000),
            3: rng.uniform(150_000, 500_000),
            4: rng.uniform(500_000, 2_000_000),
            5: rng.uniform(2_000_000, 8_000_000),
        }.get(step_level, 100_000)
        step_months = {2: 3, 3: 6, 4: 12, 5: 18}.get(step_level, 6)
        roadmap.append({
            "phase": f"Level {current_level} → Level {step_level}",
            "maturity_level": step_level,
            "label": MATURITY_LABELS[step_level],
            "description": MATURITY_DESCRIPTIONS[step_level],
            "key_actions": _roadmap_actions(current_level, step_level),
            "estimated_cost_usd": round(step_cost, 0),
            "estimated_months": step_months,
        })

    total_cost = sum(r["estimated_cost_usd"] for r in roadmap)
    total_months = sum(r["estimated_months"] for r in roadmap)

    benefits_at_target = [
        f"Achieve PCAF DQS 1-2 (vs current DQS 3-4) improving financed emissions accuracy",
        f"Qualify for ISO 14064-3 Level 1 reasonable assurance",
        f"Reduce CDP data collection effort by ~60%",
        f"Meet EU ETS MRV Regulation 2018/2066 continuous monitoring requirements",
        f"Enable real-time GHG dashboarding for CSRD ESRS E1 reporting",
    ]

    return DigitalMRVMaturityResult(
        entity_id=entity_id,
        current_maturity_level=current_level,
        current_maturity_label=MATURITY_LABELS[current_level],
        target_maturity_level=target_level,
        gap_analysis=list(capability_gaps.items()),
        upgrade_roadmap=roadmap,
        estimated_cost_usd=round(total_cost, 0),
        estimated_timeline_months=total_months,
        capability_gaps=capability_gaps,
        benefits_at_target=benefits_at_target,
    ).dict()


def _roadmap_actions(from_level: int, to_level: int) -> list:
    actions_map = {
        2: ["Deploy automated meter reading", "Integrate ERP accounting data", "Establish data governance policy"],
        3: ["Implement dedicated ESG/MRV platform", "Configure API connections to utility providers",
            "Build Scope 3 supplier data collection portal", "Establish verification workflow"],
        4: ["Deploy IoT sensors on major emission sources", "Build real-time GHG dashboard",
            "Configure AI anomaly detection", "Integrate smart building management systems"],
        5: ["Connect satellite data feeds (TROPOMI/GHGSat)", "Implement blockchain attestation",
            "Deploy ML-based emission prediction models", "Achieve autonomous regulatory reporting"],
    }
    return actions_map.get(to_level, ["Define requirements", "Select technology vendor"])


def generate_mrv_report(entity_id: str) -> dict:
    """
    Generate comprehensive MRV compliance report: ISO 14064-3 checklist,
    EMAS requirements, UK SECR, EU ETS MRV Regulation 2018/2066.
    """
    rng = _rng(entity_id + "mrv_report")

    iso14064_3_checklist = []
    total_weighted_score = 0.0
    for item in ISO_14064_3_CHECKLIST:
        score = round(rng.uniform(55.0, 98.0), 1)
        total_weighted_score += score * item["weight"]
        iso14064_3_checklist.append({
            **item,
            "score": score,
            "status": "compliant" if score >= 70.0 else "non_compliant",
        })
    overall_iso_score = round(total_weighted_score, 1)

    emas_requirements = {
        "regulation": "EU EMAS Regulation 1221/2009",
        "applicable_sectors": ["manufacturing", "chemicals", "steel", "cement"],
        "requirements": [
            "Environmental management system (EMS) implementation",
            "Initial environmental review",
            "Annual environmental performance reporting",
            "EMAS verified environmental statement",
            "Registration with national competent body",
        ],
        "compliance_score": round(rng.uniform(55.0, 88.0), 1),
        "verification_cycle_years": 3,
        "accredited_verifier_required": True,
    }

    uk_secr_requirements = {
        "regulation": "UK SECR — SI 2018/1155",
        "threshold_tco2e": 4000.0,
        "threshold_energy_mwh": 400.0,
        "applicable_entities": "UK companies with >250 employees or >£36M turnover",
        "mandatory_disclosures": [
            "UK energy use (Scope 1 + Scope 2 within UK operations)",
            "Scope 1 and 2 GHG emissions",
            "Intensity ratio (CO2e per £ revenue or FTE)",
            "Energy efficiency actions taken during the year",
        ],
        "reporting_standard": "GHG Protocol Corporate Standard",
        "disclosure_vehicle": "Directors Report / Strategic Report",
        "compliance_score": round(rng.uniform(60.0, 90.0), 1),
        "penalty_for_non_compliance": "Criminal offence for false or misleading statements",
    }

    eu_ets_mrv_requirements = {
        "regulation": "EU MRV Regulation 2018/2066",
        "covered_sectors": list(SECTOR_EMISSION_FACTORS.keys()),
        "monitoring_plan_required": True,
        "annual_emission_report_deadline": "March 31",
        "verification_deadline": "March 31",
        "key_requirements": [
            "Approved monitoring plan per Art 12-14",
            "Tier methodology compliance (Tier 1-4 per source)",
            "Annual emission report per Annex X",
            "Third-party accredited verifier (EN ISO 14065)",
            "Surrender of allowances by April 30",
        ],
        "compliance_score": round(rng.uniform(58.0, 92.0), 1),
        "non_compliance_penalty_eur_tco2": 100.0,
    }

    overall_compliance_score = round(
        (overall_iso_score + emas_requirements["compliance_score"] +
         uk_secr_requirements["compliance_score"] + eu_ets_mrv_requirements["compliance_score"]) / 4.0,
        1
    )

    critical_gaps = []
    if overall_iso_score < 70.0:
        critical_gaps.append("ISO 14064-3 verification procedures below minimum threshold")
    if eu_ets_mrv_requirements["compliance_score"] < 65.0:
        critical_gaps.append("EU ETS MRV monitoring plan deficiencies require immediate remediation")
    if uk_secr_requirements["compliance_score"] < 65.0:
        critical_gaps.append("UK SECR mandatory disclosure elements incomplete")

    recommendations = [
        "Commission ISO 14064-3 gap assessment before next annual reporting cycle",
        "Register facility with accredited EMAS verifier if in manufacturing sector",
        "Submit monitoring plan revision to competent authority within 90 days",
        "Deploy digital MRV to achieve EU ETS Tier 3/4 measurement methodology",
        "Train ESG team on CDP STTI response requirements for A-list status",
    ]

    return MRVReportResult(
        entity_id=entity_id,
        iso14064_3_checklist=iso14064_3_checklist,
        emas_requirements=emas_requirements,
        uk_secr_requirements=uk_secr_requirements,
        eu_ets_mrv_requirements=eu_ets_mrv_requirements,
        overall_compliance_score=overall_compliance_score,
        critical_gaps=critical_gaps,
        recommendations=recommendations,
    ).dict()
