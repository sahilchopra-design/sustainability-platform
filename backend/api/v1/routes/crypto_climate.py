"""
E76 — Digital Assets & Crypto Climate Risk Routes
==================================================
Prefix: /api/v1/crypto-climate
Tags:   E76 Crypto Climate
"""

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from services.crypto_climate_engine import (
    CONSENSUS_GHG_INTENSITY,
    MICA_REQUIREMENTS,
    MINING_COUNTRY_PROFILES,
    CryptoAssetInput,
    CryptoClimateEngine,
    CryptoPortfolioInput,
    MiningGeographyInput,
)

router = APIRouter(prefix="/api/v1/crypto-climate", tags=["E76 Crypto Climate"])
_engine = CryptoClimateEngine()


# ---------------------------------------------------------------------------
# Request models
# ---------------------------------------------------------------------------

class CryptoAssetRequest(BaseModel):
    asset_symbol: str = Field(..., example="BTC")
    consensus_mechanism: str = Field(..., example="PoW", description="PoW | PoS | DPoS | PoA | PoH")
    annual_transaction_count: Optional[float] = Field(None, example=300_000_000)
    network_energy_twh_yr: Optional[float] = Field(None, example=120.0)
    mining_country_distribution: Optional[Dict[str, float]] = Field(
        None, example={"US": 38, "KZ": 13, "RU": 9, "CA": 6.5, "other": 33.5}
    )
    market_cap_usd: Optional[float] = Field(None, example=1_200_000_000_000)
    outstanding_value_usd: Optional[float] = Field(None, example=5_000_000)
    issuer_incorporated_eu: bool = False
    has_white_paper: bool = False
    discloses_energy_consumption: bool = False
    discloses_renewable_pct: bool = False
    discloses_ghg_emissions: bool = False
    is_tokenised_green_asset: bool = False
    underlying_asset_type: Optional[str] = Field(None, example="green_bond")
    underlying_face_value_usd: Optional[float] = None
    on_chain_verification: bool = False
    certification_standard: Optional[str] = Field(None, example="EU_GBS")


class MiningGeographyRequest(BaseModel):
    hashrate_eh_s: float = Field(..., example=500.0, description="Network hashrate in Exahash/second")
    country_distribution: Dict[str, float] = Field(
        ..., example={"US": 38, "KZ": 13, "RU": 9, "CA": 6.5, "other": 33.5}
    )
    hardware_efficiency_j_th: float = Field(40.0, example=40.0, description="Joules per TeraHash")
    assessment_year: int = Field(2024, example=2024)


class MiCAComplianceRequest(BaseModel):
    asset_symbol: str = Field(..., example="BTC")
    consensus_mechanism: str = Field(..., example="PoW")
    market_cap_usd: Optional[float] = Field(None, example=1_200_000_000_000)
    issuer_incorporated_eu: bool = False
    has_white_paper: bool = False
    discloses_energy_consumption: bool = False
    discloses_renewable_pct: bool = False
    discloses_ghg_emissions: bool = False


class TokenisedGreenAssetRequest(BaseModel):
    asset_symbol: str = Field(..., example="GreenBond_ETH")
    consensus_mechanism: str = Field("PoS", example="PoS")
    is_tokenised_green_asset: bool = True
    underlying_asset_type: str = Field(..., example="green_bond", description="green_bond | carbon_credit | green_certificate")
    underlying_face_value_usd: Optional[float] = Field(None, example=10_000_000)
    on_chain_verification: bool = False
    certification_standard: Optional[str] = Field(None, example="EU_GBS")
    market_cap_usd: Optional[float] = None


class FundedEmissionsRequest(BaseModel):
    portfolio_id: str = Field(..., example="CRYPTO_PORT_001")
    holdings: List[Dict[str, Any]] = Field(
        ...,
        example=[
            {
                "symbol": "BTC",
                "consensus_mechanism": "PoW",
                "value_usd": 5_000_000,
                "market_cap_usd": 1_200_000_000_000,
                "mining_country_distribution": {"US": 38, "KZ": 13, "other": 49},
            },
            {
                "symbol": "ETH",
                "consensus_mechanism": "PoS",
                "value_usd": 2_000_000,
                "market_cap_usd": 400_000_000_000,
            },
        ],
    )
    total_portfolio_value_usd: float = Field(..., example=7_000_000)
    investor_name: Optional[str] = Field(None, example="GreenFund I")
    reporting_period: str = Field("2024", example="2024")


class PortfolioRequest(BaseModel):
    portfolio_id: str = Field(..., example="CRYPTO_PORT_001")
    holdings: List[Dict[str, Any]] = Field(...)
    total_portfolio_value_usd: float = Field(..., example=10_000_000)
    investor_name: Optional[str] = None
    reporting_period: str = "2024"
    include_defi_protocols: bool = False
    defi_tvl_usd: Optional[float] = None


# ---------------------------------------------------------------------------
# POST endpoints
# ---------------------------------------------------------------------------

@router.post(
    "/assess",
    summary="Single crypto asset climate assessment",
    response_model=Dict[str, Any],
)
def assess_crypto_asset(request: CryptoAssetRequest) -> Dict[str, Any]:
    """
    Full climate risk assessment for a single crypto asset.

    Combines Cambridge CBECI energy estimation, consensus GHG intensity,
    geography-adjusted grid carbon factor, EU MiCA Art 66 compliance check,
    and optional PCAF financed emissions calculation.

    Returns energy bounds (low/central/high), gCO2e/tx, annual tCO2e,
    MiCA compliance level/score/gaps, and overall climate risk tier.
    """
    try:
        asset = CryptoAssetInput(
            asset_symbol=request.asset_symbol,
            consensus_mechanism=request.consensus_mechanism,
            annual_transaction_count=request.annual_transaction_count,
            network_energy_twh_yr=request.network_energy_twh_yr,
            mining_country_distribution=request.mining_country_distribution,
            market_cap_usd=request.market_cap_usd,
            outstanding_value_usd=request.outstanding_value_usd,
            issuer_incorporated_eu=request.issuer_incorporated_eu,
            has_white_paper=request.has_white_paper,
            discloses_energy_consumption=request.discloses_energy_consumption,
            discloses_renewable_pct=request.discloses_renewable_pct,
            discloses_ghg_emissions=request.discloses_ghg_emissions,
            is_tokenised_green_asset=request.is_tokenised_green_asset,
            underlying_asset_type=request.underlying_asset_type,
            underlying_face_value_usd=request.underlying_face_value_usd,
            on_chain_verification=request.on_chain_verification,
            certification_standard=request.certification_standard,
        )
        result = _engine.assess_crypto_asset(asset)
        # Convert dataclass to dict
        return {
            "asset_symbol": result.asset_symbol,
            "consensus_mechanism": result.consensus_mechanism,
            "energy": {
                "network_energy_twh_yr_low": result.network_energy_twh_yr_low,
                "network_energy_twh_yr_central": result.network_energy_twh_yr_central,
                "network_energy_twh_yr_high": result.network_energy_twh_yr_high,
                "energy_per_tx_kwh": result.energy_per_tx_kwh,
            },
            "emissions": {
                "gco2e_per_tx_low": result.gco2e_per_tx_low,
                "gco2e_per_tx_central": result.gco2e_per_tx_central,
                "gco2e_per_tx_high": result.gco2e_per_tx_high,
                "annual_network_tco2e": result.annual_network_tco2e,
            },
            "geography": {
                "effective_renewable_pct": result.effective_renewable_pct,
                "effective_grid_carbon_gco2_kwh": result.effective_grid_carbon_gco2_kwh,
            },
            "mica_compliance": {
                "level": result.mica_compliance_level,
                "score": result.mica_score,
                "gaps": result.mica_gaps,
            },
            "tokenised_green_asset": {
                "tokenisation_premium_bps": result.tokenisation_premium_bps,
                "green_asset_verified": result.green_asset_verified,
            },
            "pcaf": {
                "financed_emissions_tco2e": result.financed_emissions_tco2e,
                "dqs": result.pcaf_dqs,
            },
            "climate_risk_tier": result.climate_risk_tier,
            "summary": result.summary,
        }
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.post(
    "/mining-geography",
    summary="Mining location carbon footprint (CBECI methodology)",
    response_model=Dict[str, Any],
)
def assess_mining_geography(request: MiningGeographyRequest) -> Dict[str, Any]:
    """
    Calculate the carbon footprint of a Bitcoin mining operation based on
    hashrate and geographic distribution.

    Uses Cambridge CBECI methodology: hashrate × hardware efficiency → annual energy,
    then applies country-level grid carbon intensity for total tCO2e/yr.
    Returns per-country breakdown and a renewable energy counterfactual.
    """
    try:
        geo = MiningGeographyInput(
            hashrate_eh_s=request.hashrate_eh_s,
            country_distribution=request.country_distribution,
            hardware_efficiency_j_th=request.hardware_efficiency_j_th,
            assessment_year=request.assessment_year,
        )
        return _engine.assess_mining_geography(geo)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.post(
    "/mica-compliance",
    summary="EU MiCA Art 66 sustainability compliance check",
    response_model=Dict[str, Any],
)
def check_mica_compliance(request: MiCAComplianceRequest) -> Dict[str, Any]:
    """
    Evaluate a crypto-asset issuer's compliance with EU MiCA Regulation
    (EU) 2023/1114 Article 66 sustainability indicator requirements.

    Determines required disclosure level (basic/enhanced/full) based on
    market capitalisation and scores the issuer's current disclosures.
    Returns compliance level, score (0-100), and identified gaps.
    """
    try:
        asset = CryptoAssetInput(
            asset_symbol=request.asset_symbol,
            consensus_mechanism=request.consensus_mechanism,
            market_cap_usd=request.market_cap_usd,
            issuer_incorporated_eu=request.issuer_incorporated_eu,
            has_white_paper=request.has_white_paper,
            discloses_energy_consumption=request.discloses_energy_consumption,
            discloses_renewable_pct=request.discloses_renewable_pct,
            discloses_ghg_emissions=request.discloses_ghg_emissions,
        )
        return _engine.check_mica_compliance(asset)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.post(
    "/tokenised-green-assets",
    summary="Tokenised green asset (RWA) assessment",
    response_model=Dict[str, Any],
)
def assess_tokenised_green_assets(request: TokenisedGreenAssetRequest) -> Dict[str, Any]:
    """
    Assess a tokenised green asset (Real World Asset on-chain).

    Covers green bond tokenisation, carbon credit tokenisation (Art 6 ITMOs),
    and on-chain green certificate verification. Returns tokenisation premium
    in basis points, verification status, and framework alignment.
    """
    try:
        asset = CryptoAssetInput(
            asset_symbol=request.asset_symbol,
            consensus_mechanism=request.consensus_mechanism,
            is_tokenised_green_asset=True,
            underlying_asset_type=request.underlying_asset_type,
            underlying_face_value_usd=request.underlying_face_value_usd,
            on_chain_verification=request.on_chain_verification,
            certification_standard=request.certification_standard,
            market_cap_usd=request.market_cap_usd,
        )
        return _engine.assess_tokenised_green_asset(asset)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.post(
    "/financed-emissions",
    summary="PCAF crypto portfolio financed emissions",
    response_model=Dict[str, Any],
)
def calculate_financed_emissions(request: FundedEmissionsRequest) -> Dict[str, Any]:
    """
    Calculate PCAF-aligned financed emissions for a crypto portfolio.

    Uses PCAF Emerging Methodology (Part D analogy):
      Financed emissions = (outstanding_value / market_cap) × network_energy × grid_factor

    Assigns DQS 3-4 based on data availability. Returns per-holding breakdown
    and portfolio-level intensity metric (tCO2e/M USD invested).
    """
    try:
        port = CryptoPortfolioInput(
            portfolio_id=request.portfolio_id,
            holdings=request.holdings,
            total_portfolio_value_usd=request.total_portfolio_value_usd,
            investor_name=request.investor_name,
            reporting_period=request.reporting_period,
        )
        return _engine.calculate_financed_emissions(port)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.post(
    "/portfolio",
    summary="Full crypto portfolio climate aggregation",
    response_model=Dict[str, Any],
)
def aggregate_portfolio(request: PortfolioRequest) -> Dict[str, Any]:
    """
    Aggregate climate metrics across a multi-asset crypto portfolio.

    Returns portfolio-level weighted average gCO2e/tx, total MWh/yr,
    total tCO2e/yr, MiCA compliance scores, climate risk tier distribution,
    and per-holding breakdown. Optionally includes DeFi protocol overlay
    assessment (TVL-weighted Ethereum PoS emissions).
    """
    try:
        port = CryptoPortfolioInput(
            portfolio_id=request.portfolio_id,
            holdings=request.holdings,
            total_portfolio_value_usd=request.total_portfolio_value_usd,
            investor_name=request.investor_name,
            reporting_period=request.reporting_period,
            include_defi_protocols=request.include_defi_protocols,
            defi_tvl_usd=request.defi_tvl_usd,
        )
        return _engine.aggregate_portfolio(port)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))


# ---------------------------------------------------------------------------
# GET reference endpoints
# ---------------------------------------------------------------------------

@router.get(
    "/ref/consensus-mechanisms",
    summary="Reference: GHG intensity by consensus mechanism",
    response_model=Dict[str, Any],
)
def get_consensus_mechanisms() -> Dict[str, Any]:
    """
    Return GHG intensity profiles for all supported consensus mechanisms.

    Includes low/central/high gCO2e/tx ranges, representative assets,
    energy per transaction (kWh), and source citations.
    """
    return {
        "consensus_mechanisms": CONSENSUS_GHG_INTENSITY,
        "methodology_notes": (
            "PoW values derived from Cambridge CBECI annualised energy "
            "consumption divided by annual transaction count. "
            "PoS values based on Ethereum Foundation post-Merge energy report (Sept 2022). "
            "DPoS/PoA/PoH from academic literature and network operator disclosures."
        ),
        "last_updated": "2024-Q1",
    }


@router.get(
    "/ref/country-energy-profiles",
    summary="Reference: Mining country grid carbon intensity profiles",
    response_model=Dict[str, Any],
)
def get_country_energy_profiles() -> Dict[str, Any]:
    """
    Return grid energy profiles for the 15 country mining regions.

    Includes renewable energy percentage, grid carbon intensity (gCO2e/kWh),
    estimated hashrate share, and primary energy sources.
    Sources: IEA 2023, Ember Climate 2024, Cambridge Centre for Alternative Finance.
    """
    return {
        "country_profiles": MINING_COUNTRY_PROFILES,
        "total_countries": len(MINING_COUNTRY_PROFILES),
        "sources": ["IEA 2023", "Ember Climate 2024", "CCAF 2024", "National grid operators"],
    }


@router.get(
    "/ref/mica-requirements",
    summary="Reference: EU MiCA Art 66 sustainability requirements",
    response_model=Dict[str, Any],
)
def get_mica_requirements() -> Dict[str, Any]:
    """
    Return EU MiCA Regulation (EU) 2023/1114 Article 66 sustainability
    indicator requirements by compliance level (basic/enhanced/full).

    Includes market cap thresholds, required disclosures, frequency,
    reporting format, and cross-framework references (CSRD, EU Taxonomy, SFDR).
    """
    return MICA_REQUIREMENTS


@router.get(
    "/ref/rwa-frameworks",
    summary="Reference: Tokenised green asset (RWA) frameworks",
    response_model=Dict[str, Any],
)
def get_rwa_frameworks() -> Dict[str, Any]:
    """
    Return reference data for tokenised green asset frameworks and standards.

    Covers green bond (ICMA GBP, EU GBS), carbon credit (VCS, Gold Standard,
    Art 6 ITMOs, CDM), and green certificate tokenisation standards.
    Includes tokenisation premium estimates and on-chain verification methods.
    """
    return {
        "frameworks": {
            "ICMA_GBP": {
                "name": "ICMA Green Bond Principles 2021",
                "asset_type": "green_bond",
                "tokenisation_premium_bps_base": 5.0,
                "certification_quality_pct": 100,
                "key_requirements": ["Use of Proceeds", "Project Evaluation", "Management of Proceeds", "Reporting"],
                "on_chain_use_case": "Immutable use-of-proceeds tracking, automated reporting",
            },
            "EU_GBS": {
                "name": "EU Green Bond Standard (EU) 2023/2631",
                "asset_type": "green_bond",
                "tokenisation_premium_bps_base": 6.0,
                "certification_quality_pct": 120,
                "key_requirements": ["EU Taxonomy alignment", "DNSH", "Min safeguards", "ESAP registration"],
                "on_chain_use_case": "Taxonomy alignment attestation, automated KPI reporting to ESAP",
                "effective_date": "2024-12-21",
            },
            "VCS": {
                "name": "Verified Carbon Standard (Verra) v4",
                "asset_type": "carbon_credit",
                "tokenisation_premium_bps_base": 18.0,
                "certification_quality_pct": 90,
                "key_requirements": ["Additionality", "Permanence", "MRV", "Registry issuance"],
                "on_chain_use_case": "Retirement tracking, double-counting prevention, fractionalization",
            },
            "Gold_Standard": {
                "name": "Gold Standard for the Global Goals v4.3",
                "asset_type": "carbon_credit",
                "tokenisation_premium_bps_base": 20.0,
                "certification_quality_pct": 100,
                "key_requirements": ["SDG co-benefits", "Safeguards", "Additionality", "Community validation"],
                "on_chain_use_case": "SDG impact tracking, community benefit distribution via smart contract",
            },
            "Art6_ITMO": {
                "name": "UNFCCC Article 6 Internationally Transferred Mitigation Outcomes",
                "asset_type": "carbon_credit",
                "tokenisation_premium_bps_base": 26.0,
                "certification_quality_pct": 130,
                "key_requirements": ["Corresponding adjustment", "UNFCCC registry", "NDC alignment", "Sustainable development"],
                "on_chain_use_case": "Cross-border transfer tracking, corresponding adjustment automation",
                "notes": "Highest quality carbon credit; Paris Agreement linkage; CORSIA eligible",
            },
            "CDM": {
                "name": "Clean Development Mechanism (UNFCCC)",
                "asset_type": "carbon_credit",
                "tokenisation_premium_bps_base": 12.0,
                "certification_quality_pct": 60,
                "key_requirements": ["Host country LoA", "CDM registry CER issuance", "Additionality"],
                "on_chain_use_case": "Legacy CER bridge to modern carbon markets",
                "notes": "Legacy standard; transitioning to Art 6. Discount applied.",
            },
        },
        "tokenisation_benefits": [
            "Enhanced liquidity via fractional ownership",
            "Reduced settlement friction (T+0 vs T+2/T+3)",
            "Immutable audit trail for use-of-proceeds",
            "Automated covenant monitoring via smart contracts",
            "Global investor access without custodian intermediaries",
            "Real-time impact reporting",
        ],
        "risks": [
            "Smart contract vulnerability",
            "Regulatory uncertainty in many jurisdictions",
            "Oracle risk for off-chain data feeds",
            "Double-counting if off-chain registry not bridged",
        ],
        "key_regulation": "EU MiCA (EU) 2023/1114 — ART tokens for asset-referenced tokens",
    }
