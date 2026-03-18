"""
E59: Health-Climate Nexus & Social Risk — API Routes

Router prefix: /api/v1/health-climate
Tags: ["Health-Climate Nexus"]
"""

from fastapi import APIRouter
from pydantic import BaseModel, ConfigDict
from typing import Optional, List, Dict, Any

from services.health_climate_engine import (
    assess_heat_stress_risk,
    assess_air_quality_risk,
    assess_vector_disease_risk,
    model_food_security_health,
    calculate_health_financial_impact,
    assess_who_climate_health,
    compute_health_climate_composite,
    WHO_AQG_PM25, WHO_AQG_NO2, WHO_AQG_O3,
    EU_AQD_PM25, EU_AQD_NO2,
    WBGT_MODERATE, WBGT_SEVERE,
)

router = APIRouter(prefix="/api/v1/health-climate", tags=["Health-Climate Nexus"])


# ---------------------------------------------------------------------------
# Pydantic request models
# ---------------------------------------------------------------------------

class HeatStressRequest(BaseModel):
    model_config = ConfigDict(extra="allow")
    entity_id: str
    country_code: str = "IN"
    outdoor_worker_pct: float = 30.0
    sector: str = "construction"


class AirQualityRequest(BaseModel):
    model_config = ConfigDict(extra="allow")
    entity_id: str
    country_code: str = "CN"
    sector: str = "manufacturing"
    annual_production: float = 1_000_000.0


class VectorDiseaseRequest(BaseModel):
    model_config = ConfigDict(extra="allow")
    entity_id: str
    country_code: str = "NG"
    rcp_scenario: str = "rcp45"


class FoodSecurityHealthRequest(BaseModel):
    model_config = ConfigDict(extra="allow")
    entity_id: str
    country_code: str = "ET"
    supply_chain_exposure: List[str] = ["maize", "wheat", "soy"]


class HealthFinancialImpactRequest(BaseModel):
    model_config = ConfigDict(extra="allow")
    entity_id: str
    country_code: str = "IN"
    employee_count: int = 1000
    outdoor_pct: float = 40.0
    sector: str = "construction"


class WHOClimateHealthRequest(BaseModel):
    model_config = ConfigDict(extra="allow")
    entity_id: str
    country_code: str = "BD"


class HealthClimateCompositeRequest(BaseModel):
    model_config = ConfigDict(extra="allow")
    entity_id: str
    entity_name: str = "Entity"
    country_code: str = "IN"
    sector: str = "manufacturing"
    employee_count: int = 5000


# ---------------------------------------------------------------------------
# POST Endpoints
# ---------------------------------------------------------------------------

@router.post("/heat-stress")
def heat_stress_endpoint(req: HeatStressRequest) -> dict:
    """
    Assess occupational heat stress risk and workforce productivity impact.

    Based on ILO/WHO WBGT model. Productivity loss: 10% per degree above 26°C WBGT
    for outdoor workers. Includes OSHA heat standard compliance assessment
    and Lancet Countdown RCP 4.5/8.5 mortality projections.
    """
    return assess_heat_stress_risk(
        entity_id=req.entity_id,
        country_code=req.country_code,
        outdoor_worker_pct=req.outdoor_worker_pct,
        sector=req.sector,
    )


@router.post("/air-quality")
def air_quality_endpoint(req: AirQualityRequest) -> dict:
    """
    Assess climate-air quality nexus risk and health liability exposure.

    WHO AQG 2021: PM2.5=5μg/m3, NO2=10μg/m3. EU AQD 2024 revision: PM2.5=10μg/m3.
    Quantifies climate-amplified PM2.5 fraction (wildfire, dust storms, ozone formation)
    and compliance cost to reach EU directive threshold.
    """
    return assess_air_quality_risk(
        entity_id=req.entity_id,
        country_code=req.country_code,
        sector=req.sector,
        annual_production=req.annual_production,
    )


@router.post("/vector-disease")
def vector_disease_endpoint(req: VectorDiseaseRequest) -> dict:
    """
    Model climate-driven vector-borne disease risk change.

    Covers malaria, dengue, Lyme, Zika, West Nile under RCP 4.5 and 8.5.
    Dengue doubling risk by 2050 under RCP 4.5. Malaria geographic range
    expands 2-7% per degree of warming (IPCC AR6).
    """
    return assess_vector_disease_risk(
        entity_id=req.entity_id,
        country_code=req.country_code,
        rcp_scenario=req.rcp_scenario,
    )


@router.post("/food-security-health")
def food_security_health_endpoint(req: FoodSecurityHealthRequest) -> dict:
    """
    Model food security and nutritional health impacts of climate change.

    IPCC AR6: 2-3% per decade global crop yield decline. Malnutrition-driven
    stunting creates long-term workforce productivity losses.
    Supply chain climate exposure assessed per commodity.
    """
    return model_food_security_health(
        entity_id=req.entity_id,
        country_code=req.country_code,
        supply_chain_exposure=req.supply_chain_exposure,
    )


@router.post("/financial-impact")
def financial_impact_endpoint(req: HealthFinancialImpactRequest) -> dict:
    """
    Calculate financial impact of health-climate risks on workforce costs.

    Quantifies: healthcare cost uplift (climate-attributed sick days),
    productivity loss (heat-adjusted working hours), insurance premium uplift (5-20%),
    and litigation exposure (employer duty of care). Returns ROI on adaptation investment.
    """
    return calculate_health_financial_impact(
        entity_id=req.entity_id,
        country_code=req.country_code,
        employee_count=req.employee_count,
        outdoor_pct=req.outdoor_pct,
        sector=req.sector,
    )


@router.post("/who-climate-health")
def who_climate_health_endpoint(req: WHOClimateHealthRequest) -> dict:
    """
    Assess WHO Climate Change and Health country profile for entity jurisdiction.

    Based on WHO Climate and Health Country Profiles 2023.
    Returns CCS score, adaptation finance gap, NCCHAP status, and peer comparison.
    """
    return assess_who_climate_health(
        entity_id=req.entity_id,
        country_code=req.country_code,
    )


@router.post("/composite")
def composite_endpoint(req: HealthClimateCompositeRequest) -> dict:
    """
    Compute overall health-climate composite risk score and rating.

    Aggregates: heat_stress (25%) + air_quality (25%) + vector_disease (15%)
    + food_security (15%) + financial_impact (20%).
    Returns risk rating (Critical/High/Medium/Low), priority hazards,
    key interventions, and SDG 3 alignment score.
    """
    return compute_health_climate_composite(
        entity_id=req.entity_id,
        entity_name=req.entity_name,
        country_code=req.country_code,
        sector=req.sector,
        employee_count=req.employee_count,
    )


# ---------------------------------------------------------------------------
# GET Reference Endpoints
# ---------------------------------------------------------------------------

@router.get("/ref/who-guidelines")
def get_who_guidelines() -> dict:
    """
    WHO Air Quality Guidelines 2021 thresholds and EU Air Quality Directive 2024 comparison.
    """
    return {
        "source": "WHO Global Air Quality Guidelines 2021",
        "publication_date": "2021-09-22",
        "eu_directive": "EU Air Quality Directive 2024/2881 (revised 2024)",
        "pollutants": [
            {
                "pollutant": "PM2.5",
                "who_annual_guideline_ugm3": WHO_AQG_PM25,
                "eu_annual_limit_ugm3": EU_AQD_PM25,
                "previous_who_guideline_ugm3": 10.0,
                "health_impact": "Cardiovascular and respiratory disease; premature mortality",
                "climate_nexus": "Wildfire smoke, dust storms amplify PM2.5 under climate change",
            },
            {
                "pollutant": "NO2",
                "who_annual_guideline_ugm3": WHO_AQG_NO2,
                "eu_annual_limit_ugm3": EU_AQD_NO2,
                "previous_who_guideline_ugm3": 40.0,
                "health_impact": "Respiratory inflammation; exacerbates asthma",
                "climate_nexus": "Higher temperatures increase ground-level NO2 formation",
            },
            {
                "pollutant": "O3",
                "who_peak_season_guideline_ugm3": WHO_AQG_O3,
                "eu_target_ugm3": 120.0,
                "health_impact": "Respiratory and cardiovascular effects; reduced lung function",
                "climate_nexus": "Higher temperatures significantly increase ozone formation",
            },
            {
                "pollutant": "PM10",
                "who_annual_guideline_ugm3": 15.0,
                "eu_annual_limit_ugm3": 20.0,
                "health_impact": "Respiratory disease",
                "climate_nexus": "Desertification and dust storms increase PM10 under RCP 4.5/8.5",
            },
        ],
        "notes": [
            "WHO 2021 guidelines are 2x stricter than 2005 guidelines for PM2.5",
            "EU 2024 revision aligns more closely with WHO (PM2.5 10 vs 5 μg/m3 by 2030)",
            "97% of world population lives in areas exceeding WHO AQG PM2.5 threshold",
        ],
    }


@router.get("/ref/lancet-indicators")
def get_lancet_indicators() -> dict:
    """
    Lancet Countdown 2023 health-climate indicators tracked annually.
    """
    return {
        "source": "Lancet Countdown on Health and Climate Change — 2023 Report",
        "publication": "The Lancet, November 2023",
        "indicator_domains": [
            {
                "domain": "1. Climate Change Impacts, Exposures and Vulnerabilities",
                "indicators": [
                    {"id": "1.1", "name": "Heat exposure of vulnerable populations", "trend": "Worsening — record heat exposure in 2022"},
                    {"id": "1.2", "name": "Change in labour capacity from heat", "trend": "9.4% of global working hours lost in 2021"},
                    {"id": "1.3", "name": "Change in epidemic potential of key diseases", "trend": "Dengue epidemic potential up 12% vs 1951-1960 baseline"},
                    {"id": "1.4", "name": "Climate suitability for Vibrio cholerae transmission", "trend": "Coastal water temps conducive to cholera rising"},
                    {"id": "1.5", "name": "Food security and undernutrition", "trend": "Crop yield stability declining in 60% of assessed countries"},
                ],
            },
            {
                "domain": "2. Adaptation, Planning and Resilience",
                "indicators": [
                    {"id": "2.1", "name": "Health adaptation in National Adaptation Plans", "trend": "Only 40% of NAPs include health-specific actions"},
                    {"id": "2.2", "name": "Healthcare facility climate resilience", "trend": "Less than 10% of health facilities in LMICs climate-resilient"},
                    {"id": "2.3", "name": "Urban heat island management", "trend": "Growing adoption of cool roofs and urban greening"},
                ],
            },
            {
                "domain": "4. Economics and Finance",
                "indicators": [
                    {"id": "4.1", "name": "Economic costs of heat-related mortality", "trend": "$863B estimated cost in 2021"},
                    {"id": "4.4", "name": "Health insurance exposure to climate risk", "trend": "Premium loading 5-20% in high-risk jurisdictions"},
                ],
            },
        ],
    }


@router.get("/ref/country-profiles")
def get_country_profiles() -> dict:
    """
    Country health-climate vulnerability profiles with WHO CCS scores and resilience ratings.
    """
    return {
        "source": "WHO Climate Change and Health Country Profiles 2023; Lancet Countdown 2023",
        "note": "CCS = Climate-Sensitive disease burden Score (0-100, higher = more burden); health_resilience (0-100, higher = more resilient)",
        "profiles": [
            {
                "country_code": "IN",
                "country": "India",
                "who_ccs_score": 72.0,
                "health_resilience": 38.0,
                "heat_mortality_per_100k": 3.5,
                "pm25_ugm3": 58.0,
                "ncchap": True,
                "health_in_ndc": True,
                "priority_diseases": ["heat stroke", "vector-borne", "air pollution"],
            },
            {
                "country_code": "NG",
                "country": "Nigeria",
                "who_ccs_score": 82.0,
                "health_resilience": 25.0,
                "heat_mortality_per_100k": 5.1,
                "pm25_ugm3": 68.0,
                "ncchap": False,
                "health_in_ndc": False,
                "priority_diseases": ["malaria", "cholera", "heat stress"],
            },
            {
                "country_code": "BD",
                "country": "Bangladesh",
                "who_ccs_score": 78.0,
                "health_resilience": 30.0,
                "heat_mortality_per_100k": 4.2,
                "pm25_ugm3": 62.0,
                "ncchap": True,
                "health_in_ndc": True,
                "priority_diseases": ["flood-related disease", "dengue", "diarrhoeal disease"],
            },
            {
                "country_code": "US",
                "country": "United States",
                "who_ccs_score": 28.0,
                "health_resilience": 78.0,
                "heat_mortality_per_100k": 0.7,
                "pm25_ugm3": 8.5,
                "ncchap": True,
                "health_in_ndc": True,
                "priority_diseases": ["wildfire smoke", "extreme heat", "Lyme disease"],
            },
            {
                "country_code": "DE",
                "country": "Germany",
                "who_ccs_score": 22.0,
                "health_resilience": 85.0,
                "heat_mortality_per_100k": 0.6,
                "pm25_ugm3": 11.0,
                "ncchap": True,
                "health_in_ndc": True,
                "priority_diseases": ["heat waves (elderly)", "tick-borne encephalitis", "pollen allergy"],
            },
            {
                "country_code": "CN",
                "country": "China",
                "who_ccs_score": 55.0,
                "health_resilience": 55.0,
                "heat_mortality_per_100k": 2.1,
                "pm25_ugm3": 32.0,
                "ncchap": True,
                "health_in_ndc": True,
                "priority_diseases": ["air pollution", "heat stress", "vector-borne"],
            },
        ],
        "wbgt_thresholds": {
            "moderate_work_restriction_c": WBGT_MODERATE,
            "work_stoppage_c": WBGT_SEVERE,
            "productivity_loss_onset_c": 26.0,
            "source": "ILO Working on a Warmer Planet (2019); ISO 7933",
        },
    }
