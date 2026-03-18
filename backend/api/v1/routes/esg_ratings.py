"""
E57: ESG Ratings Reform & Divergence — API Routes

Router prefix: /api/v1/esg-ratings
Tags: ["ESG Ratings"]
"""

from fastapi import APIRouter
from pydantic import BaseModel, ConfigDict
from typing import Optional, List, Dict, Any

from services.esg_ratings_engine import (
    assess_esra_compliance,
    analyse_rating_divergence,
    detect_rating_bias,
    compute_composite_rating,
    assess_e_pillar_divergence,
    benchmark_against_peers,
    generate_divergence_report,
)

router = APIRouter(prefix="/api/v1/esg-ratings", tags=["ESG Ratings"])


# ---------------------------------------------------------------------------
# Pydantic request models
# ---------------------------------------------------------------------------

class ESRAComplianceRequest(BaseModel):
    model_config = ConfigDict(extra="allow")
    entity_id: str
    provider_name: str = "Provider"
    methodology_published: bool = False
    conflict_mgmt: bool = False
    regulatory_supervised: bool = False


class ProviderRating(BaseModel):
    model_config = ConfigDict(extra="allow")
    score: float = 50.0
    rating: Optional[str] = None
    category: Optional[str] = None


class DivergenceAnalysisRequest(BaseModel):
    model_config = ConfigDict(extra="allow")
    entity_id: str
    ratings: Dict[str, ProviderRating] = {}


class BiasDetectionRequest(BaseModel):
    model_config = ConfigDict(extra="allow")
    entity_id: str
    scores: Dict[str, float] = {}
    entity_size: str = "large"
    region: str = "western_europe"
    sector: str = "other"


class CompositeRatingRequest(BaseModel):
    model_config = ConfigDict(extra="allow")
    entity_id: str
    provider_scores: Dict[str, float] = {}
    methodology: str = "equal_weight"


class EPillarDivergenceRequest(BaseModel):
    model_config = ConfigDict(extra="allow")
    entity_id: str
    scores_by_pillar: Dict[str, Dict[str, float]] = {}


class PeerBenchmarkRequest(BaseModel):
    model_config = ConfigDict(extra="allow")
    entity_id: str
    sector: str = "other"
    composite_score: float = 50.0
    n_peers: int = 20


class DivergenceReportRequest(BaseModel):
    model_config = ConfigDict(extra="allow")
    entity_id: str
    entity_name: str = "Entity"
    sector: str = "other"
    ratings: Dict[str, ProviderRating] = {}


# ---------------------------------------------------------------------------
# POST Endpoints
# ---------------------------------------------------------------------------

@router.post("/esra-compliance")
def esra_compliance_endpoint(req: ESRAComplianceRequest) -> dict:
    """
    Assess ESG rating provider compliance with EU ESRA Regulation 2024/3005.

    Evaluates 8 key requirements: governance, methodology, data sources,
    conflict of interest, complaint handling, transparency, authorisation, reporting.
    """
    return assess_esra_compliance(
        entity_id=req.entity_id,
        provider_name=req.provider_name,
        methodology_published=req.methodology_published,
        conflict_mgmt=req.conflict_mgmt,
        regulatory_supervised=req.regulatory_supervised,
    )


@router.post("/divergence-analysis")
def divergence_analysis_endpoint(req: DivergenceAnalysisRequest) -> dict:
    """
    Analyse ESG rating divergence across providers.

    Normalises scores to 0-100 scale and decomposes divergence into Berg et al.
    sources: scope (56%), weight (23%), measurement (21%).
    Outputs correlation matrix and consensus rating with confidence interval.
    """
    ratings_dict = {k: v.model_dump() for k, v in req.ratings.items()}
    return analyse_rating_divergence(
        entity_id=req.entity_id,
        ratings=ratings_dict,
    )


@router.post("/bias-detection")
def bias_detection_endpoint(req: BiasDetectionRequest) -> dict:
    """
    Detect and correct for systematic biases in ESG ratings.

    Adjusts for size bias (large companies score higher), geography bias
    (Western firms benefit from disclosure standards), sector bias
    (services vs manufacturing asymmetry), and reporting bias.
    """
    return detect_rating_bias(
        entity_id=req.entity_id,
        scores=req.scores,
        entity_size=req.entity_size,
        region=req.region,
        sector=req.sector,
    )


@router.post("/composite-rating")
def composite_rating_endpoint(req: CompositeRatingRequest) -> dict:
    """
    Compute composite ESG rating from multiple provider scores.

    Supported methodologies: equal_weight, market_cap_weight,
    specialisation_weight (MSCI for governance, Sustainalytics for risk).
    Returns composite score, AAA-CCC rating, provider weights, and sensitivity analysis.
    """
    return compute_composite_rating(
        entity_id=req.entity_id,
        provider_scores=req.provider_scores,
        methodology=req.methodology,
    )


@router.post("/e-pillar-divergence")
def e_pillar_divergence_endpoint(req: EPillarDivergenceRequest) -> dict:
    """
    Assess provider disagreement across E pillar sub-pillars.

    Sub-pillars: carbon (E1), water (E2), biodiversity (E3), waste (E4), energy (E5).
    Identifies most and least divergent sub-pillars and improvement priorities.
    """
    return assess_e_pillar_divergence(
        entity_id=req.entity_id,
        scores_by_pillar=req.scores_by_pillar,
    )


@router.post("/peer-benchmark")
def peer_benchmark_endpoint(req: PeerBenchmarkRequest) -> dict:
    """
    Benchmark entity composite ESG score against sector peers.

    Generates synthetic sector peer distribution (seeded deterministic).
    Returns percentile rank, gap to median/leader, and improvement roadmap.
    """
    return benchmark_against_peers(
        entity_id=req.entity_id,
        sector=req.sector,
        composite_score=req.composite_score,
        n_peers=req.n_peers,
    )


@router.post("/divergence-report")
def divergence_report_endpoint(req: DivergenceReportRequest) -> dict:
    """
    Generate full ESG rating divergence report combining all analyses.

    Includes divergence decomposition, bias adjustment, composite rating,
    peer benchmark, ESRA regulatory implications, and action items.
    """
    ratings_dict = {k: v.model_dump() for k, v in req.ratings.items()}
    return generate_divergence_report(
        entity_id=req.entity_id,
        entity_name=req.entity_name,
        sector=req.sector,
        ratings=ratings_dict,
    )


# ---------------------------------------------------------------------------
# GET Reference Endpoints
# ---------------------------------------------------------------------------

@router.get("/ref/esra-requirements")
def get_esra_requirements() -> dict:
    """
    EU ESG Ratings Regulation 2024/3005 (ESRA) — 8 key requirements for providers.
    """
    return {
        "regulation": "EU ESG Ratings Regulation 2024/3005 (ESRA)",
        "regulator": "ESMA (European Securities and Markets Authority)",
        "entry_into_force": "2024-07-02",
        "authorisation_deadline": "2025-07-02",
        "scope": "All ESG rating providers operating in the EU",
        "requirements": [
            {
                "id": "R01",
                "category": "Ancillary Services",
                "requirement": "Separation of ESG ratings from ancillary services (consulting, data)",
                "article": "Art. 11",
                "weight_in_scoring": "15%",
            },
            {
                "id": "R02",
                "category": "Methodology",
                "requirement": "Publication of rating methodologies, models and key assumptions",
                "article": "Art. 23",
                "weight_in_scoring": "15%",
            },
            {
                "id": "R03",
                "category": "Data Sources",
                "requirement": "Disclosure of primary data sources and their quality",
                "article": "Art. 23(2)",
                "weight_in_scoring": "10%",
            },
            {
                "id": "R04",
                "category": "Conflict of Interest",
                "requirement": "Written conflict of interest management policy",
                "article": "Art. 12",
                "weight_in_scoring": "15%",
            },
            {
                "id": "R05",
                "category": "Complaint Handling",
                "requirement": "Formal complaint handling and appeals procedure",
                "article": "Art. 19",
                "weight_in_scoring": "10%",
            },
            {
                "id": "R06",
                "category": "Transparency",
                "requirement": "Periodic transparency and disclosure reports to ESMA",
                "article": "Art. 24",
                "weight_in_scoring": "15%",
            },
            {
                "id": "R07",
                "category": "Regulatory Authorisation",
                "requirement": "ESMA registration/authorisation before operating in EU",
                "article": "Art. 5",
                "weight_in_scoring": "15%",
            },
            {
                "id": "R08",
                "category": "Reporting",
                "requirement": "Annual reporting on rated entities and methodologies",
                "article": "Art. 25",
                "weight_in_scoring": "5%",
            },
        ],
    }


@router.get("/ref/provider-methodologies")
def get_provider_methodologies() -> dict:
    """
    Summary of major ESG rating provider methodologies.
    """
    return {
        "source": "IOSCO ESG Ratings and Data Products Providers Report (2021)",
        "providers": [
            {
                "name": "MSCI ESG Ratings",
                "scale": "CCC to AAA (7 categories)",
                "scope": "ESG risk exposure and risk management",
                "data_sources": "Company disclosures + MSCI proprietary data + media",
                "sectors_covered": 158,
                "key_strength": "Governance analysis, controversy screening",
                "known_bias": "Disclosure quality inflates scores; size bias observed",
            },
            {
                "name": "Sustainalytics ESG Risk",
                "scale": "0-50 (risk score, lower = better)",
                "scope": "Unmanaged ESG risk in absolute terms",
                "data_sources": "Company disclosures + controversies + government data",
                "sectors_covered": 138,
                "key_strength": "Industry-specific materiality mapping",
                "known_bias": "Geography bias for non-OECD reporters",
            },
            {
                "name": "S&P Global ESG",
                "scale": "0-100",
                "scope": "ESG performance (DJSI methodology)",
                "data_sources": "Annual Corporate Sustainability Assessment (CSA)",
                "sectors_covered": 61,
                "key_strength": "Deep questionnaire-based assessment",
                "known_bias": "Voluntary participation bias; high-scoring companies over-report",
            },
            {
                "name": "Refinitiv ESG",
                "scale": "0-100 (percentile within sector)",
                "scope": "Relative ESG performance",
                "data_sources": "Public disclosures, annual reports, CSR reports",
                "sectors_covered": 76,
                "key_strength": "Breadth of company coverage (11,000+)",
                "known_bias": "Disclosure volume bias; more disclosure = higher score",
            },
            {
                "name": "Bloomberg ESG",
                "scale": "0-100 (disclosure score)",
                "scope": "ESG data disclosure completeness",
                "data_sources": "Primarily company disclosures",
                "sectors_covered": 84,
                "key_strength": "Transparency on data sourcing",
                "known_bias": "Measures disclosure, not performance",
            },
        ],
    }


@router.get("/ref/divergence-research")
def get_divergence_research() -> dict:
    """
    Berg, Kolbel & Rigobon divergence taxonomy and key research findings.
    """
    return {
        "primary_study": "Berg, Kolbel & Rigobon (2022) — Aggregate Confusion: The Divergence of ESG Ratings, Review of Finance",
        "key_finding": "Average pairwise correlation among major ESG providers: 0.54 (vs 0.99 for credit ratings)",
        "divergence_sources": {
            "scope_56pct": {
                "description": "Different attributes measured (e.g., one provider rates lobbying, another does not)",
                "example": "Carbon emissions vs. climate lobbying vs. stranded assets",
                "implication": "Entity may score differently depending on which ESG topics are included",
            },
            "weight_23pct": {
                "description": "Same attributes, different importance weights across E/S/G",
                "example": "One provider weights E at 40%, another at 25%",
                "implication": "Capital-intensive sectors with high E impact diverge most",
            },
            "measurement_21pct": {
                "description": "Same attributes, different measurement approaches",
                "example": "Carbon intensity: absolute vs. revenue-normalised vs. peer-relative",
                "implication": "Fast-growing companies penalised differently across providers",
            },
        },
        "esra_impact": {
            "expected_convergence": "15-25% reduction in divergence by 2027 per ESMA projections",
            "mechanism": "Mandatory methodology publication (Art. 23) + ESMA supervisory convergence",
            "remaining_divergence": "Fundamental scope divergence will persist due to conceptual differences",
        },
        "additional_studies": [
            "Dimson, Marsh & Staunton (2020) — Divergent ESG Ratings",
            "Kotsantonis & Serafeim (2019) — Four Things No One Will Tell You About ESG Data, JOIM",
            "IOSCO (2021) — ESG Ratings and Data Products Providers Consultation Report",
            "ESMA (2022) — Supervisory Convergence Work Programme on ESG",
        ],
    }
