"""
Internal Carbon Pricing & Net-Zero Economics Engine — E84
Standards: IPCC AR6 WG3 carbon price ranges (2022); SBTi Corporate Manual v2 (2023);
SBTI Near-term and Net-Zero standards; EU ETS Phase 4 Directive 2003/87/EC as amended
by 2023/958; ETS2 Directive 2023/959 (buildings, road transport, fuels);
ICVCM CCP 2023; GHG Protocol Corporate Standard (2011, updated 2015 Scope 2).
IEA World Energy Outlook 2023 NZE scenario capex trajectories.
"""

import logging
import math
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Reference Data
# ---------------------------------------------------------------------------

ICP_MECHANISM_TYPES: Dict[str, Dict] = {
    "shadow_price": {
        "description": (
            "Internal shadow carbon price applied to investment appraisals and "
            "capex decisions — does not generate real cash flows but adjusts IRR/NPV."
        ),
        "use_case": "Capital allocation, project screening, R&D prioritisation",
        "sbti_recommended": True,
        "cash_flow_impact": False,
        "typical_icp_eur_t": 50,
        "implementation_effort": "low",
        "regulatory_ref": "SBTi Corporate Manual v2 §5.3; IEA WEO 2023 NZE pathway",
    },
    "internal_fee_dividend": {
        "description": (
            "Real internal levy on business-unit emissions routed back as "
            "sustainability fund or dividend — incentivises reduction behaviours."
        ),
        "use_case": "Behaviour change, BU accountability, green innovation funding",
        "sbti_recommended": True,
        "cash_flow_impact": True,
        "typical_icp_eur_t": 75,
        "implementation_effort": "medium",
        "regulatory_ref": "CDP Internal Carbon Pricing 2021; WBCSD ICP guide 2022",
    },
    "budget_based": {
        "description": (
            "Implicit carbon budget allocated by emissions allowances; excess "
            "triggers purchase of internal permits from a central treasury."
        ),
        "use_case": "SBTi target operationalisation, portfolio net-zero governance",
        "sbti_recommended": True,
        "cash_flow_impact": True,
        "typical_icp_eur_t": 100,
        "implementation_effort": "high",
        "regulatory_ref": "SBTi Net-Zero Standard v1.1 (2021) §4.2; GFANZ 2022 guidance",
    },
    "implicit_price": {
        "description": (
            "Revealed carbon price derived from existing policy costs: fuel duty, "
            "energy efficiency subsidies, compliance spend."
        ),
        "use_case": "Regulatory cost mapping, policy scenario analysis",
        "sbti_recommended": False,
        "cash_flow_impact": True,
        "typical_icp_eur_t": 30,
        "implementation_effort": "low",
        "regulatory_ref": "OECD Effective Carbon Rates 2023; IMF Carbon Price Floor 2021",
    },
    "ets_shadow": {
        "description": (
            "Shadow price tracking the EU ETS or ETS2 futures curve, updated "
            "quarterly — aligns internal hurdle rates to market-observed carbon costs."
        ),
        "use_case": "ETS-regulated sectors, CBAM-exposed exports, financed emissions",
        "sbti_recommended": True,
        "cash_flow_impact": False,
        "typical_icp_eur_t": 65,
        "implementation_effort": "medium",
        "regulatory_ref": (
            "EU ETS Phase 4 Directive 2003/87/EC (as amended 2023/958); "
            "ETS2 Directive 2023/959"
        ),
    },
}

# EU ETS Phase 4 price trajectory (EUR/tCO2) — based on EEX settlement curve,
# ICF/ICIS analyst consensus and IPCC AR6 WG3 carbon price corridors.
EU_ETS_PRICE_TRAJECTORY: Dict[int, float] = {
    2024: 65.0,
    2025: 72.0,
    2026: 82.0,
    2027: 95.0,
    2028: 108.0,
    2029: 120.0,
    2030: 133.0,
    2031: 142.0,
    2032: 151.0,
    2033: 160.0,
    2034: 170.0,
    2035: 180.0,
    2036: 192.0,
    2037: 204.0,
    2038: 215.0,
    2039: 226.0,
    2040: 238.0,
    2041: 244.0,
    2042: 249.0,
    2043: 253.0,
    2044: 256.0,
    2045: 258.0,
    2046: 259.0,
    2047: 259.5,
    2048: 260.0,
    2049: 250.0,  # post-Phase 4 — supply tightening eases slightly
    2050: 250.0,
}

# ETS2 trajectory (EUR/tCO2) — buildings, road transport, small industry
# Directive (EU) 2023/959; start 2027 with €45 price ceiling initially
ETS2_PRICE_TRAJECTORY: Dict[int, float] = {
    2027: 45.0,
    2028: 52.0,
    2029: 60.0,
    2030: 68.0,
    2031: 76.0,
    2032: 84.0,
    2033: 92.0,
    2034: 100.0,
    2035: 108.0,
    2036: 112.0,
    2037: 116.0,
    2038: 120.0,
    2039: 125.0,
    2040: 130.0,
    2041: 132.0,
    2042: 133.0,
    2043: 134.0,
    2044: 135.0,
    2045: 135.0,
    2046: 135.0,
    2047: 135.0,
    2048: 135.0,
    2049: 135.0,
    2050: 135.0,
}

# SBTi ICP minimum recommended prices (EUR/tCO2e)
# Source: IPCC AR6 WG3 Table 3.SM.1 carbon price corridors; SBTi Corporate Manual v2 §5.3
SBTI_ICP_GUIDANCE: Dict[str, Dict] = {
    "1.5C": {
        "temperature_target": "1.5°C (Paris Agreement ambition)",
        "2025": {"min_eur_t": 50, "recommended_eur_t": 100, "source": "IPCC AR6 WG3 C1 pathway"},
        "2030": {"min_eur_t": 135, "recommended_eur_t": 200, "source": "IPCC AR6 WG3 C1 pathway"},
        "2035": {"min_eur_t": 175, "recommended_eur_t": 230, "source": "IPCC AR6 WG3 C1 pathway"},
        "2040": {"min_eur_t": 210, "recommended_eur_t": 260, "source": "IPCC AR6 WG3 C1 pathway"},
        "2050": {"min_eur_t": 250, "recommended_eur_t": 350, "source": "IPCC AR6 WG3 C1 pathway"},
        "sbti_ref": "SBTi Net-Zero Standard v1.1 §4.2; IPCC AR6 WG3 SPM (2022)",
    },
    "2C": {
        "temperature_target": "Well-below 2°C",
        "2025": {"min_eur_t": 25, "recommended_eur_t": 50, "source": "IPCC AR6 WG3 C3 pathway"},
        "2030": {"min_eur_t": 75, "recommended_eur_t": 120, "source": "IPCC AR6 WG3 C3 pathway"},
        "2035": {"min_eur_t": 100, "recommended_eur_t": 160, "source": "IPCC AR6 WG3 C3 pathway"},
        "2040": {"min_eur_t": 130, "recommended_eur_t": 190, "source": "IPCC AR6 WG3 C3 pathway"},
        "2050": {"min_eur_t": 175, "recommended_eur_t": 240, "source": "IPCC AR6 WG3 C3 pathway"},
        "sbti_ref": "SBTi Corporate Manual v2 §5.3 (2023); IPCC AR6 WG3 SPM",
    },
}

# Marginal Abatement Cost benchmarks — 20 measures
# Sources: McKinsey MAC 2023; IEA Technology Perspectives 2023; BloombergNEF LCOE 2024
ABATEMENT_COST_BENCHMARKS: Dict[str, Dict] = {
    "onshore_wind": {
        "cost_eur_tco2e": -12.0,
        "max_reduction_tco2e_yr": 500_000,
        "implementation_years": 3,
        "description": "Onshore wind power replacing coal/gas generation",
        "capex_m_per_100ktco2": 8.5,
    },
    "solar_pv_utility": {
        "cost_eur_tco2e": -8.0,
        "max_reduction_tco2e_yr": 800_000,
        "implementation_years": 2,
        "description": "Utility-scale solar PV replacing fossil generation",
        "capex_m_per_100ktco2": 6.0,
    },
    "energy_efficiency_buildings": {
        "cost_eur_tco2e": 5.0,
        "max_reduction_tco2e_yr": 200_000,
        "implementation_years": 5,
        "description": "Building envelope + HVAC upgrades (EPC B target)",
        "capex_m_per_100ktco2": 12.0,
    },
    "industrial_electrification": {
        "cost_eur_tco2e": 35.0,
        "max_reduction_tco2e_yr": 300_000,
        "implementation_years": 7,
        "description": "Electrification of low-temp industrial heat",
        "capex_m_per_100ktco2": 25.0,
    },
    "green_hydrogen_industrial": {
        "cost_eur_tco2e": 120.0,
        "max_reduction_tco2e_yr": 150_000,
        "implementation_years": 10,
        "description": "Green H2 replacing grey H2 in ammonia/refining",
        "capex_m_per_100ktco2": 80.0,
    },
    "ccs_power": {
        "cost_eur_tco2e": 95.0,
        "max_reduction_tco2e_yr": 1_000_000,
        "implementation_years": 8,
        "description": "Post-combustion CCS on natural gas power plants",
        "capex_m_per_100ktco2": 120.0,
    },
    "methane_leak_reduction": {
        "cost_eur_tco2e": -20.0,
        "max_reduction_tco2e_yr": 400_000,
        "implementation_years": 2,
        "description": "O&G LDAR and compressor upgrades (methane GWP-100)",
        "capex_m_per_100ktco2": 4.0,
    },
    "fleet_ev_transition": {
        "cost_eur_tco2e": 18.0,
        "max_reduction_tco2e_yr": 100_000,
        "implementation_years": 4,
        "description": "Corporate fleet electrification (LCVs + cars)",
        "capex_m_per_100ktco2": 15.0,
    },
    "supply_chain_engagement": {
        "cost_eur_tco2e": 10.0,
        "max_reduction_tco2e_yr": 500_000,
        "implementation_years": 3,
        "description": "Scope 3 Cat 1 supplier decarbonisation programs",
        "capex_m_per_100ktco2": 5.0,
    },
    "reforestation": {
        "cost_eur_tco2e": 15.0,
        "max_reduction_tco2e_yr": 200_000,
        "implementation_years": 5,
        "description": "Native species reforestation (permanence risk adjusted)",
        "capex_m_per_100ktco2": 8.0,
    },
    "soil_carbon_agriculture": {
        "cost_eur_tco2e": 22.0,
        "max_reduction_tco2e_yr": 100_000,
        "implementation_years": 3,
        "description": "Regenerative agriculture / no-till soil carbon",
        "capex_m_per_100ktco2": 10.0,
    },
    "offshore_wind": {
        "cost_eur_tco2e": 2.0,
        "max_reduction_tco2e_yr": 700_000,
        "implementation_years": 5,
        "description": "Offshore wind power (including grid connection costs)",
        "capex_m_per_100ktco2": 18.0,
    },
    "heat_pump_commercial": {
        "cost_eur_tco2e": 28.0,
        "max_reduction_tco2e_yr": 80_000,
        "implementation_years": 3,
        "description": "Air/ground source heat pumps in commercial buildings",
        "capex_m_per_100ktco2": 22.0,
    },
    "blue_hydrogen_ccus": {
        "cost_eur_tco2e": 75.0,
        "max_reduction_tco2e_yr": 200_000,
        "implementation_years": 6,
        "description": "Blue H2 production with 90% CCUS capture rate",
        "capex_m_per_100ktco2": 55.0,
    },
    "smart_grid_demand_response": {
        "cost_eur_tco2e": -5.0,
        "max_reduction_tco2e_yr": 150_000,
        "implementation_years": 2,
        "description": "AI-enabled demand response and smart grid flexibility",
        "capex_m_per_100ktco2": 3.0,
    },
    "direct_air_capture": {
        "cost_eur_tco2e": 300.0,
        "max_reduction_tco2e_yr": 50_000,
        "implementation_years": 5,
        "description": "DAC + permanent geological storage (Climeworks scale)",
        "capex_m_per_100ktco2": 350.0,
    },
    "manure_biogas": {
        "cost_eur_tco2e": 8.0,
        "max_reduction_tco2e_yr": 60_000,
        "implementation_years": 3,
        "description": "Anaerobic digestion of livestock manure for biogas",
        "capex_m_per_100ktco2": 12.0,
    },
    "biomass_ccs": {
        "cost_eur_tco2e": 110.0,
        "max_reduction_tco2e_yr": 120_000,
        "implementation_years": 7,
        "description": "BECCS — bioenergy with carbon capture and storage",
        "capex_m_per_100ktco2": 140.0,
    },
    "process_efficiency_cement": {
        "cost_eur_tco2e": 45.0,
        "max_reduction_tco2e_yr": 80_000,
        "implementation_years": 5,
        "description": "Clinker substitution and kiln efficiency in cement",
        "capex_m_per_100ktco2": 35.0,
    },
    "circular_economy_materials": {
        "cost_eur_tco2e": 12.0,
        "max_reduction_tco2e_yr": 250_000,
        "implementation_years": 4,
        "description": "Circular procurement, recycled content targets, waste heat recovery",
        "capex_m_per_100ktco2": 9.0,
    },
}

# NACE sector carbon intensity (tCO2e per €M revenue, Scope 1+2+3)
# Source: CDP Supply Chain Report 2023; MSCI Carbon Intensity Dataset 2023
SECTOR_CARBON_INTENSITY: Dict[str, Dict] = {
    "C19_petroleum_refining": {
        "nace": "C19",
        "intensity_tco2e_per_m_eur": 4_200,
        "scope1_pct": 55,
        "scope2_pct": 10,
        "scope3_pct": 35,
        "primary_abatement": ["ccs_power", "blue_hydrogen_ccus", "process_efficiency_cement"],
    },
    "D35_electricity_gas": {
        "nace": "D35",
        "intensity_tco2e_per_m_eur": 3_800,
        "scope1_pct": 70,
        "scope2_pct": 5,
        "scope3_pct": 25,
        "primary_abatement": ["onshore_wind", "solar_pv_utility", "offshore_wind"],
    },
    "C24_basic_metals": {
        "nace": "C24",
        "intensity_tco2e_per_m_eur": 2_200,
        "scope1_pct": 60,
        "scope2_pct": 20,
        "scope3_pct": 20,
        "primary_abatement": ["industrial_electrification", "green_hydrogen_industrial"],
    },
    "C23_cement_glass": {
        "nace": "C23",
        "intensity_tco2e_per_m_eur": 1_900,
        "scope1_pct": 65,
        "scope2_pct": 15,
        "scope3_pct": 20,
        "primary_abatement": ["process_efficiency_cement", "ccs_power", "biomass_ccs"],
    },
    "A01_agriculture": {
        "nace": "A01",
        "intensity_tco2e_per_m_eur": 1_600,
        "scope1_pct": 75,
        "scope2_pct": 5,
        "scope3_pct": 20,
        "primary_abatement": ["methane_leak_reduction", "soil_carbon_agriculture", "manure_biogas"],
    },
    "H49_road_transport": {
        "nace": "H49",
        "intensity_tco2e_per_m_eur": 950,
        "scope1_pct": 55,
        "scope2_pct": 5,
        "scope3_pct": 40,
        "primary_abatement": ["fleet_ev_transition", "smart_grid_demand_response"],
    },
    "F41_construction": {
        "nace": "F41",
        "intensity_tco2e_per_m_eur": 600,
        "scope1_pct": 30,
        "scope2_pct": 10,
        "scope3_pct": 60,
        "primary_abatement": ["circular_economy_materials", "energy_efficiency_buildings"],
    },
    "L68_real_estate": {
        "nace": "L68",
        "intensity_tco2e_per_m_eur": 380,
        "scope1_pct": 20,
        "scope2_pct": 40,
        "scope3_pct": 40,
        "primary_abatement": ["energy_efficiency_buildings", "heat_pump_commercial"],
    },
    "C20_chemicals": {
        "nace": "C20",
        "intensity_tco2e_per_m_eur": 1_200,
        "scope1_pct": 50,
        "scope2_pct": 15,
        "scope3_pct": 35,
        "primary_abatement": ["green_hydrogen_industrial", "industrial_electrification", "ccs_power"],
    },
    "H51_air_transport": {
        "nace": "H51",
        "intensity_tco2e_per_m_eur": 2_800,
        "scope1_pct": 85,
        "scope2_pct": 2,
        "scope3_pct": 13,
        "primary_abatement": ["direct_air_capture", "biomass_ccs"],
    },
    "K64_banking_finance": {
        "nace": "K64",
        "intensity_tco2e_per_m_eur": 85,
        "scope1_pct": 5,
        "scope2_pct": 15,
        "scope3_pct": 80,
        "primary_abatement": ["supply_chain_engagement", "energy_efficiency_buildings"],
    },
    "G46_wholesale_trade": {
        "nace": "G46",
        "intensity_tco2e_per_m_eur": 420,
        "scope1_pct": 20,
        "scope2_pct": 10,
        "scope3_pct": 70,
        "primary_abatement": ["supply_chain_engagement", "fleet_ev_transition"],
    },
    "C10_food_beverage": {
        "nace": "C10",
        "intensity_tco2e_per_m_eur": 750,
        "scope1_pct": 25,
        "scope2_pct": 10,
        "scope3_pct": 65,
        "primary_abatement": ["supply_chain_engagement", "soil_carbon_agriculture", "circular_economy_materials"],
    },
    "J62_ict_services": {
        "nace": "J62",
        "intensity_tco2e_per_m_eur": 95,
        "scope1_pct": 5,
        "scope2_pct": 30,
        "scope3_pct": 65,
        "primary_abatement": ["solar_pv_utility", "smart_grid_demand_response"],
    },
    "C29_automotive": {
        "nace": "C29",
        "intensity_tco2e_per_m_eur": 880,
        "scope1_pct": 20,
        "scope2_pct": 15,
        "scope3_pct": 65,
        "primary_abatement": ["supply_chain_engagement", "fleet_ev_transition", "circular_economy_materials"],
    },
}

# NZE investment requirements — annual capex as % of revenue by scenario
# Source: IEA World Energy Outlook 2023 NZE; IPCC AR6 WG3 §16.2; McKinsey NZE 2022
NZE_INVESTMENT_REQUIREMENTS: Dict[str, Dict] = {
    "orderly_transition": {
        "description": "Paris-aligned orderly transition — early, ambitious action",
        "temperature_target": "1.5°C with 50% probability",
        "capex_pct_revenue_2024_2030": 6.5,
        "capex_pct_revenue_2031_2040": 5.0,
        "capex_pct_revenue_2041_2050": 3.5,
        "opex_savings_pct_revenue_2030": 2.5,
        "opex_savings_pct_revenue_2050": 4.5,
        "source": "IEA NZE 2023; NGFS Orderly scenario",
    },
    "delayed_transition": {
        "description": "Delayed policy action — higher physical + transition risk",
        "temperature_target": "~2°C with significant overshoot risk",
        "capex_pct_revenue_2024_2030": 3.0,
        "capex_pct_revenue_2031_2040": 8.0,
        "capex_pct_revenue_2041_2050": 7.0,
        "opex_savings_pct_revenue_2030": 0.5,
        "opex_savings_pct_revenue_2050": 3.5,
        "source": "IEA APS 2023; NGFS Divergent Net Zero",
    },
    "net_zero_2050": {
        "description": "Full net-zero by 2050 — maximum ambition, balanced action",
        "temperature_target": "1.5°C with >66% probability",
        "capex_pct_revenue_2024_2030": 8.0,
        "capex_pct_revenue_2031_2040": 6.0,
        "capex_pct_revenue_2041_2050": 4.0,
        "opex_savings_pct_revenue_2030": 3.0,
        "opex_savings_pct_revenue_2050": 5.5,
        "source": "IEA NZE 2023 §2.4; SBTi Net-Zero Standard v1.1",
    },
}

# SBTi interim reduction rates (% per year from base)
SBTI_ANNUAL_REDUCTION_RATES: Dict[str, float] = {
    "1.5C": 4.2,   # % per year from base — SBTi 1.5°C absolute contraction
    "2C": 2.5,     # % per year from base — SBTi well-below 2°C
    "net_zero": 4.2,  # same slope as 1.5C for near-term
}


# ---------------------------------------------------------------------------
# Engine
# ---------------------------------------------------------------------------

class InternalCarbonPriceEngine:
    """E84 — Internal Carbon Pricing & Net-Zero Economics Engine."""

    # -----------------------------------------------------------------------
    # 1. ICP Mechanism Design
    # -----------------------------------------------------------------------

    def design_icp_mechanism(
        self,
        entity_id: str,
        mechanism_type: str,
        target_year: int,
        sbti_target: str,
        current_icp: Optional[float] = None,
    ) -> Dict[str, Any]:
        """
        Design an internal carbon pricing mechanism and check SBTi alignment.

        Returns recommended shadow price, price trajectory 2024-2050,
        SBTi alignment status, and mechanism design guidance.
        """
        logger.info("design_icp_mechanism: entity=%s mechanism=%s sbti=%s", entity_id, mechanism_type, sbti_target)

        if mechanism_type not in ICP_MECHANISM_TYPES:
            raise ValueError(f"Unknown mechanism_type '{mechanism_type}'. Valid: {list(ICP_MECHANISM_TYPES)}")
        if sbti_target not in SBTI_ICP_GUIDANCE:
            raise ValueError(f"Unknown sbti_target '{sbti_target}'. Valid: {list(SBTI_ICP_GUIDANCE)}")

        mech = ICP_MECHANISM_TYPES[mechanism_type]
        guidance = SBTI_ICP_GUIDANCE[sbti_target]

        # Find guidance milestone just below target_year
        milestone_year = max(
            [int(y) for y in guidance if str(y).isdigit() and int(y) <= target_year],
            default=2025,
        )
        milestone = guidance.get(str(milestone_year), guidance.get(milestone_year, {}))

        recommended_icp = milestone.get("recommended_eur_t", mech["typical_icp_eur_t"])
        minimum_icp = milestone.get("min_eur_t", recommended_icp * 0.7)

        # SBTi alignment check
        if current_icp is not None:
            gap = recommended_icp - current_icp
            aligned = current_icp >= minimum_icp
            alignment_status = "aligned" if aligned else "below_minimum"
        else:
            gap = None
            alignment_status = "not_assessed"

        # Build price trajectory 2024-target_year
        trajectory = {}
        for year in range(2024, min(target_year + 1, 2051)):
            # Linear interpolation between milestones
            milestones = {int(k): v for k, v in guidance.items() if str(k).isdigit()}
            sorted_years = sorted(milestones.keys())
            lower_year = max((y for y in sorted_years if y <= year), default=sorted_years[0])
            upper_year = min((y for y in sorted_years if y >= year), default=sorted_years[-1])
            if lower_year == upper_year:
                icp_t = milestones[lower_year]["recommended_eur_t"]
            else:
                frac = (year - lower_year) / (upper_year - lower_year)
                icp_t = (
                    milestones[lower_year]["recommended_eur_t"] * (1 - frac)
                    + milestones[upper_year]["recommended_eur_t"] * frac
                )
            trajectory[year] = round(icp_t, 1)

        # Design guidance
        design_steps = [
            "Define governance: assign ICP owner (CFO / Sustainability function)",
            "Set price update cadence (annual or semi-annual board review)",
            f"Choose starting ICP: ≥€{minimum_icp}/tCO2e for {sbti_target} alignment",
            "Integrate ICP into NPV/IRR hurdle for all capex >€1M",
            "Commission third-party verification of emissions inventory (ISO 14064-1)",
        ]
        if mech["cash_flow_impact"]:
            design_steps.append("Establish internal carbon fund account and redistribution rules")

        return {
            "entity_id": entity_id,
            "mechanism_type": mechanism_type,
            "mechanism_description": mech["description"],
            "sbti_target": sbti_target,
            "target_year": target_year,
            "recommended_icp_eur_t": recommended_icp,
            "minimum_icp_eur_t": minimum_icp,
            "current_icp_eur_t": current_icp,
            "alignment_gap_eur_t": gap,
            "alignment_status": alignment_status,
            "sbti_recommended_mechanism": mech["sbti_recommended"],
            "cash_flow_impact": mech["cash_flow_impact"],
            "implementation_effort": mech["implementation_effort"],
            "icp_trajectory_2024_to_target": trajectory,
            "regulatory_reference": mech["regulatory_ref"],
            "design_steps": design_steps,
            "sbti_guidance_ref": guidance.get("sbti_ref"),
        }

    # -----------------------------------------------------------------------
    # 2. Scope Cost Allocation
    # -----------------------------------------------------------------------

    def calculate_scope_cost_allocation(
        self,
        entity_id: str,
        scope1_tco2: float,
        scope2_tco2: float,
        scope3_tco2: float,
        icp_eur: float,
        ebitda_m: Optional[float] = None,
        business_units: Optional[List[Dict]] = None,
    ) -> Dict[str, Any]:
        """
        Allocate carbon costs across Scope 1/2/3 at the given ICP.

        Returns cost per scope, total carbon cost, % of EBITDA,
        and business-unit level allocation if provided.
        """
        logger.info("calculate_scope_cost_allocation: entity=%s icp=%s", entity_id, icp_eur)

        scope1_cost = scope1_tco2 * icp_eur
        scope2_cost = scope2_tco2 * icp_eur
        scope3_cost = scope3_tco2 * icp_eur
        total_cost = scope1_cost + scope2_cost + scope3_cost
        total_emissions = scope1_tco2 + scope2_tco2 + scope3_tco2

        ebitda_impact_pct = None
        if ebitda_m and ebitda_m > 0:
            ebitda_impact_pct = round((total_cost / (ebitda_m * 1_000_000)) * 100, 2)

        # Business unit allocation
        bu_allocations = []
        if business_units:
            for bu in business_units:
                bu_emissions = bu.get("emissions_tco2e", 0)
                bu_cost = bu_emissions * icp_eur
                bu_share = (bu_emissions / total_emissions * 100) if total_emissions > 0 else 0
                bu_allocations.append({
                    "business_unit": bu.get("name", "Unknown"),
                    "emissions_tco2e": bu_emissions,
                    "carbon_cost_eur": round(bu_cost, 2),
                    "share_pct": round(bu_share, 1),
                    "cost_materiality": "high" if bu_share >= 30 else "medium" if bu_share >= 10 else "low",
                })

        # Materiality assessment
        def _materiality(cost_eur: float) -> str:
            if cost_eur >= 10_000_000:
                return "very_high"
            if cost_eur >= 1_000_000:
                return "high"
            if cost_eur >= 100_000:
                return "medium"
            return "low"

        return {
            "entity_id": entity_id,
            "icp_eur_per_tco2": icp_eur,
            "scope1": {
                "emissions_tco2e": scope1_tco2,
                "carbon_cost_eur": round(scope1_cost, 2),
                "share_of_total_pct": round(scope1_tco2 / total_emissions * 100, 1) if total_emissions else 0,
                "materiality": _materiality(scope1_cost),
            },
            "scope2": {
                "emissions_tco2e": scope2_tco2,
                "carbon_cost_eur": round(scope2_cost, 2),
                "share_of_total_pct": round(scope2_tco2 / total_emissions * 100, 1) if total_emissions else 0,
                "materiality": _materiality(scope2_cost),
            },
            "scope3": {
                "emissions_tco2e": scope3_tco2,
                "carbon_cost_eur": round(scope3_cost, 2),
                "share_of_total_pct": round(scope3_tco2 / total_emissions * 100, 1) if total_emissions else 0,
                "materiality": _materiality(scope3_cost),
            },
            "total_emissions_tco2e": total_emissions,
            "total_carbon_cost_eur": round(total_cost, 2),
            "total_carbon_cost_m_eur": round(total_cost / 1_000_000, 3),
            "ebitda_impact_pct": ebitda_impact_pct,
            "business_unit_allocations": bu_allocations,
            "ghg_protocol_ref": "GHG Protocol Corporate Standard 2011 (Scope 1/2/3)",
        }

    # -----------------------------------------------------------------------
    # 3. Carbon Budget Tracking
    # -----------------------------------------------------------------------

    def track_carbon_budget(
        self,
        entity_id: str,
        base_year: int,
        base_year_emissions_tco2: float,
        sbti_target: str,
        current_year: int,
        actual_emissions_tco2: float,
    ) -> Dict[str, Any]:
        """
        Track carbon budget against SBTi target trajectory.

        Returns remaining budget, years to exhaustion, annual reduction required,
        on-track status, and cumulative overshoot/undershoot.
        """
        logger.info("track_carbon_budget: entity=%s sbti=%s", entity_id, sbti_target)

        if sbti_target not in SBTI_ANNUAL_REDUCTION_RATES:
            rate = 4.2
        else:
            rate = SBTI_ANNUAL_REDUCTION_RATES[sbti_target]

        years_elapsed = current_year - base_year

        # Target trajectory: annual linear reduction
        target_current_year = base_year_emissions_tco2 * max(
            0, 1 - (rate / 100) * years_elapsed
        )

        # Cumulative budget consumed vs trajectory
        cumulative_actual = 0.0
        cumulative_target = 0.0
        trajectory_by_year: Dict[int, Dict] = {}
        for yr in range(base_year, current_year + 1):
            yrs = yr - base_year
            target_yr = base_year_emissions_tco2 * max(0, 1 - (rate / 100) * yrs)
            # Approximate actual using linear interpolation from base to current
            frac = (yr - base_year) / max(1, years_elapsed)
            approx_actual = base_year_emissions_tco2 + frac * (actual_emissions_tco2 - base_year_emissions_tco2)
            cumulative_target += target_yr
            cumulative_actual += approx_actual
            trajectory_by_year[yr] = {
                "target_tco2e": round(target_yr, 0),
                "actual_tco2e": round(approx_actual, 0),
                "variance_tco2e": round(approx_actual - target_yr, 0),
            }

        overshoot = actual_emissions_tco2 - target_current_year
        on_track = overshoot <= 0

        # Remaining budget to 2050
        remaining_budget = sum(
            base_year_emissions_tco2 * max(0, 1 - (rate / 100) * (yr - base_year))
            for yr in range(current_year + 1, 2051)
        )

        # Annual reduction required from current year
        years_to_2050 = 2050 - current_year
        if years_to_2050 > 0:
            required_annual_reduction = actual_emissions_tco2 / years_to_2050
        else:
            required_annual_reduction = actual_emissions_tco2

        # Years to budget exhaustion if current trend holds
        if actual_emissions_tco2 > 0 and remaining_budget > 0:
            years_to_exhaustion = remaining_budget / actual_emissions_tco2
        else:
            years_to_exhaustion = float("inf")

        return {
            "entity_id": entity_id,
            "base_year": base_year,
            "base_year_emissions_tco2e": base_year_emissions_tco2,
            "sbti_target": sbti_target,
            "annual_reduction_rate_pct": rate,
            "current_year": current_year,
            "actual_emissions_tco2e": actual_emissions_tco2,
            "target_emissions_tco2e": round(target_current_year, 0),
            "overshoot_tco2e": round(overshoot, 0),
            "on_track": on_track,
            "on_track_label": "On Track" if on_track else "Off Track",
            "cumulative_target_tco2e": round(cumulative_target, 0),
            "cumulative_actual_tco2e": round(cumulative_actual, 0),
            "remaining_budget_to_2050_tco2e": round(remaining_budget, 0),
            "years_to_budget_exhaustion": round(years_to_exhaustion, 1) if years_to_exhaustion != float("inf") else None,
            "required_annual_reduction_tco2e": round(required_annual_reduction, 0),
            "reduction_rate_required_pct": round(
                (actual_emissions_tco2 - 0) / max(1, years_to_2050) / actual_emissions_tco2 * 100, 2
            ) if actual_emissions_tco2 > 0 else 0,
            "trajectory_by_year": trajectory_by_year,
            "sbti_ref": "SBTi Corporate Manual v2 (2023); SBTi Net-Zero Standard v1.1",
        }

    # -----------------------------------------------------------------------
    # 4. Abatement Cost Curve
    # -----------------------------------------------------------------------

    def build_abatement_cost_curve(
        self,
        entity_id: str,
        sector: str,
        current_emissions_tco2: float,
        target_reduction_pct: float,
        max_capex_m: Optional[float] = None,
    ) -> Dict[str, Any]:
        """
        Build a marginal abatement cost (MAC) curve for the entity.

        Measures are ordered by cost (cheapest first — McKinsey MAC convention).
        Returns cumulative reduction potential, total investment, payback.
        """
        logger.info("build_abatement_cost_curve: entity=%s sector=%s", entity_id, sector)

        target_tco2 = current_emissions_tco2 * (target_reduction_pct / 100)

        # Prioritise sector-relevant measures
        sector_data = SECTOR_CARBON_INTENSITY.get(sector, {})
        priority_measures = sector_data.get("primary_abatement", [])

        # All measures sorted by cost (negative = revenue/savings)
        all_measures = sorted(
            ABATEMENT_COST_BENCHMARKS.items(),
            key=lambda x: x[1]["cost_eur_tco2e"],
        )

        curve: List[Dict] = []
        cumulative_reduction = 0.0
        total_capex_m = 0.0
        total_opex_savings_m = 0.0

        for measure_key, measure in all_measures:
            if cumulative_reduction >= target_tco2:
                break
            # Scale max reduction to entity size
            scaled_max = min(
                measure["max_reduction_tco2e_yr"],
                current_emissions_tco2 * 0.35,  # cap at 35% per measure
            )
            remaining = target_tco2 - cumulative_reduction
            reduction = min(scaled_max, remaining)

            capex_m = (reduction / 100_000) * measure["capex_m_per_100ktco2"]
            if max_capex_m and total_capex_m + capex_m > max_capex_m:
                affordable_reduction = (max_capex_m - total_capex_m) * 100_000 / measure["capex_m_per_100ktco2"]
                reduction = min(reduction, max(0, affordable_reduction))
                capex_m = (reduction / 100_000) * measure["capex_m_per_100ktco2"]

            annual_saving_m = abs(
                measure["cost_eur_tco2e"] * reduction / 1_000_000
            ) if measure["cost_eur_tco2e"] < 0 else 0.0
            cost_total_eur = measure["cost_eur_tco2e"] * reduction

            payback_years = (capex_m * 1_000_000 / max(1, annual_saving_m * 1_000_000)) if annual_saving_m > 0 else None

            cumulative_reduction += reduction
            total_capex_m += capex_m
            if measure["cost_eur_tco2e"] < 0:
                total_opex_savings_m += annual_saving_m

            curve.append({
                "measure": measure_key,
                "description": measure["description"],
                "cost_eur_tco2e": measure["cost_eur_tco2e"],
                "reduction_tco2e": round(reduction, 0),
                "cumulative_reduction_tco2e": round(cumulative_reduction, 0),
                "capex_required_m_eur": round(capex_m, 2),
                "annual_saving_m_eur": round(annual_saving_m, 2),
                "implementation_years": measure["implementation_years"],
                "payback_years": round(payback_years, 1) if payback_years else None,
                "priority_for_sector": measure_key in priority_measures,
                "cost_category": (
                    "negative_cost" if measure["cost_eur_tco2e"] < 0
                    else "low_cost" if measure["cost_eur_tco2e"] < 50
                    else "medium_cost" if measure["cost_eur_tco2e"] < 150
                    else "high_cost"
                ),
            })

        coverage_pct = (cumulative_reduction / target_tco2 * 100) if target_tco2 > 0 else 0
        avg_mac = (
            sum(m["cost_eur_tco2e"] * m["reduction_tco2e"] for m in curve)
            / max(1, cumulative_reduction)
        )

        return {
            "entity_id": entity_id,
            "sector": sector,
            "current_emissions_tco2e": current_emissions_tco2,
            "target_reduction_pct": target_reduction_pct,
            "target_reduction_tco2e": round(target_tco2, 0),
            "achievable_reduction_tco2e": round(cumulative_reduction, 0),
            "coverage_pct": round(coverage_pct, 1),
            "total_capex_required_m_eur": round(total_capex_m, 2),
            "total_opex_savings_m_eur_annual": round(total_opex_savings_m, 2),
            "weighted_avg_mac_eur_tco2e": round(avg_mac, 1),
            "measures_count": len(curve),
            "abatement_curve": curve,
            "mac_ref": "McKinsey MAC 2023; IEA Technology Perspectives 2023; BloombergNEF LCOE 2024",
        }

    # -----------------------------------------------------------------------
    # 5. Net-Zero Economics
    # -----------------------------------------------------------------------

    def calculate_nze_economics(
        self,
        entity_id: str,
        revenue_m: float,
        sector: str,
        current_emissions_tco2: float,
        nze_year: int,
        discount_rate: float = 0.08,
    ) -> Dict[str, Any]:
        """
        Calculate net-zero economics: NZE capex, opex savings, NPV, IRR, payback.
        Source: IEA WEO 2023 NZE scenario capex trajectories.
        """
        logger.info("calculate_nze_economics: entity=%s sector=%s nze_year=%s", entity_id, sector, nze_year)

        scenario = NZE_INVESTMENT_REQUIREMENTS["net_zero_2050"]
        years_to_nze = max(1, nze_year - 2024)

        # Capex phased by period
        capex_2024_2030 = revenue_m * scenario["capex_pct_revenue_2024_2030"] / 100
        capex_2031_2040 = revenue_m * scenario["capex_pct_revenue_2031_2040"] / 100
        capex_2041_nze = revenue_m * scenario["capex_pct_revenue_2041_2050"] / 100

        # Total NZE capex
        yrs_p1 = min(6, years_to_nze)
        yrs_p2 = min(10, max(0, years_to_nze - 6))
        yrs_p3 = max(0, years_to_nze - 16)
        total_capex_m = (
            capex_2024_2030 * yrs_p1
            + capex_2031_2040 * yrs_p2
            + capex_2041_nze * yrs_p3
        )

        # Annual opex savings (energy, maintenance, carbon cost avoidance)
        opex_savings_2030 = revenue_m * scenario["opex_savings_pct_revenue_2030"] / 100
        opex_savings_2050 = revenue_m * scenario["opex_savings_pct_revenue_2050"] / 100

        # NPV calculation
        npv = 0.0
        annual_cashflows = []
        year_range = range(2024, min(nze_year + 1, 2051))
        for i, yr in enumerate(year_range):
            period = yr - 2024
            # Capex outflow
            if yr <= 2030:
                capex_yr = capex_2024_2030
            elif yr <= 2040:
                capex_yr = capex_2031_2040
            else:
                capex_yr = capex_2041_nze

            # Opex savings increase linearly
            t = period / years_to_nze
            savings_yr = opex_savings_2030 + t * (opex_savings_2050 - opex_savings_2030)

            # Net cash flow
            net_cf = savings_yr - capex_yr
            pv = net_cf / ((1 + discount_rate) ** period)
            npv += pv
            annual_cashflows.append({
                "year": yr,
                "capex_m_eur": round(capex_yr, 2),
                "savings_m_eur": round(savings_yr, 2),
                "net_cf_m_eur": round(net_cf, 2),
                "pv_m_eur": round(pv, 2),
            })

        # Simple payback
        cumulative = 0.0
        payback_years = None
        for cf in annual_cashflows:
            cumulative += cf["net_cf_m_eur"]
            if cumulative >= 0 and payback_years is None:
                payback_years = cf["year"] - 2024

        # Per-tonne abatement cost
        total_abatement = current_emissions_tco2 * years_to_nze * 0.5  # avg 50% reductions
        per_tonne_cost = (total_capex_m * 1_000_000 / max(1, total_abatement))

        # Simplified IRR approximation
        avg_annual_savings = opex_savings_2030
        avg_annual_capex = total_capex_m / max(1, years_to_nze)
        irr_approx = (avg_annual_savings / max(0.01, avg_annual_capex)) - 1

        return {
            "entity_id": entity_id,
            "sector": sector,
            "revenue_m_eur": revenue_m,
            "current_emissions_tco2e": current_emissions_tco2,
            "nze_year": nze_year,
            "years_to_nze": years_to_nze,
            "discount_rate_pct": discount_rate * 100,
            "total_capex_required_m_eur": round(total_capex_m, 2),
            "annual_capex_phase1_2024_2030_m_eur": round(capex_2024_2030, 2),
            "annual_capex_phase2_2031_2040_m_eur": round(capex_2031_2040, 2),
            "annual_capex_phase3_2041_nze_m_eur": round(capex_2041_nze, 2),
            "annual_opex_savings_2030_m_eur": round(opex_savings_2030, 2),
            "annual_opex_savings_2050_m_eur": round(opex_savings_2050, 2),
            "npv_m_eur": round(npv, 2),
            "irr_approx_pct": round(irr_approx * 100, 1),
            "payback_years": payback_years,
            "per_tonne_abatement_eur": round(per_tonne_cost, 1),
            "npv_positive": npv > 0,
            "annual_cashflows": annual_cashflows[:10],  # first 10 years
            "source": "IEA WEO 2023 NZE scenario §2.4; IPCC AR6 WG3 §16.2",
        }

    # -----------------------------------------------------------------------
    # 6. ETS Shadow Exposure
    # -----------------------------------------------------------------------

    def assess_ets_shadow_exposure(
        self,
        entity_id: str,
        eu_ets_verified_tco2: float,
        free_allocation_tco2: float,
        ets2_fuel_consumption_gj: Optional[float] = None,
    ) -> Dict[str, Any]:
        """
        Calculate EU ETS Phase 4 and ETS2 carbon liability trajectories.
        EU ETS: Directive 2003/87/EC as amended by 2023/958.
        ETS2: Directive 2023/959 (buildings, road transport, small industry).
        """
        logger.info("assess_ets_shadow_exposure: entity=%s", entity_id)

        net_ets_tco2 = max(0, eu_ets_verified_tco2 - free_allocation_tco2)

        # ETS2: approx 0.056 tCO2e per GJ (gas/oil mix)
        ets2_emissions_tco2 = (ets2_fuel_consumption_gj or 0) * 0.056

        trajectory: List[Dict] = []
        for year, price in EU_ETS_PRICE_TRAJECTORY.items():
            ets_liability = net_ets_tco2 * price
            ets2_price = ETS2_PRICE_TRAJECTORY.get(year, 0.0)
            ets2_liability = ets2_emissions_tco2 * ets2_price
            total = ets_liability + ets2_liability

            # Free allocation phases out under CBAM: -25%/yr from 2026
            if year >= 2026:
                cbam_phaseout_pct = min(1.0, (year - 2026 + 1) * 0.25)
                free_allocation_adj = free_allocation_tco2 * (1 - cbam_phaseout_pct)
                net_ets_adj = max(0, eu_ets_verified_tco2 - free_allocation_adj)
                ets_liability = net_ets_adj * price
                total = ets_liability + ets2_liability
            else:
                free_allocation_adj = free_allocation_tco2

            trajectory.append({
                "year": year,
                "eu_ets_price_eur_t": price,
                "ets2_price_eur_t": ETS2_PRICE_TRAJECTORY.get(year, 0.0),
                "free_allocation_tco2e": round(free_allocation_adj, 0),
                "net_ets_compliance_tco2e": round(max(0, eu_ets_verified_tco2 - free_allocation_adj), 0),
                "ets_liability_eur_m": round(ets_liability / 1_000_000, 3),
                "ets2_liability_eur_m": round(ets2_liability / 1_000_000, 3),
                "total_carbon_liability_eur_m": round(total / 1_000_000, 3),
            })

        current_liability = net_ets_tco2 * EU_ETS_PRICE_TRAJECTORY.get(2024, 65.0)
        liability_2030 = next((r["total_carbon_liability_eur_m"] for r in trajectory if r["year"] == 2030), None)
        liability_2035 = next((r["total_carbon_liability_eur_m"] for r in trajectory if r["year"] == 2035), None)

        return {
            "entity_id": entity_id,
            "eu_ets_verified_emissions_tco2e": eu_ets_verified_tco2,
            "free_allocation_tco2e": free_allocation_tco2,
            "net_ets_compliance_obligation_tco2e": round(net_ets_tco2, 0),
            "ets2_estimated_emissions_tco2e": round(ets2_emissions_tco2, 0),
            "current_ets_liability_eur": round(current_liability, 2),
            "current_ets_price_eur_t": EU_ETS_PRICE_TRAJECTORY.get(2024, 65.0),
            "liability_2030_m_eur": liability_2030,
            "liability_2035_m_eur": liability_2035,
            "cbam_phaseout_risk": free_allocation_tco2 > 0,
            "cbam_ref": "EU CBAM Regulation 2023/956 (full phase-in 2026)",
            "ets_trajectory": trajectory,
            "regulatory_ref": (
                "EU ETS Phase 4 Directive 2003/87/EC as amended 2023/958; "
                "ETS2 Directive 2023/959"
            ),
        }

    # -----------------------------------------------------------------------
    # 7. Full Assessment
    # -----------------------------------------------------------------------

    def run_full_assessment(
        self,
        entity_id: str,
        request_data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Orchestrate all ICP sub-assessments and compute ICP maturity score.

        Tier: Leader (>=85) / Advanced (>=70) / Developing (>=50) / Early (>=30) / Absent (<30)
        """
        logger.info("run_full_assessment: entity=%s", entity_id)

        results: Dict[str, Any] = {"entity_id": entity_id}

        # Mechanism design
        mechanism_result = self.design_icp_mechanism(
            entity_id=entity_id,
            mechanism_type=request_data.get("mechanism_type", "shadow_price"),
            target_year=request_data.get("target_year", 2030),
            sbti_target=request_data.get("sbti_target", "1.5C"),
            current_icp=request_data.get("current_icp"),
        )
        results["mechanism_design"] = mechanism_result

        # Scope cost allocation
        if all(k in request_data for k in ["scope1_tco2", "scope2_tco2", "scope3_tco2", "icp_eur"]):
            results["scope_cost_allocation"] = self.calculate_scope_cost_allocation(
                entity_id=entity_id,
                scope1_tco2=request_data["scope1_tco2"],
                scope2_tco2=request_data["scope2_tco2"],
                scope3_tco2=request_data["scope3_tco2"],
                icp_eur=request_data["icp_eur"],
                ebitda_m=request_data.get("ebitda_m"),
            )

        # Carbon budget tracking
        if "base_year_emissions_tco2" in request_data:
            results["carbon_budget"] = self.track_carbon_budget(
                entity_id=entity_id,
                base_year=request_data.get("base_year", 2019),
                base_year_emissions_tco2=request_data["base_year_emissions_tco2"],
                sbti_target=request_data.get("sbti_target", "1.5C"),
                current_year=2024,
                actual_emissions_tco2=request_data.get("actual_emissions_tco2", request_data["base_year_emissions_tco2"] * 0.9),
            )

        # Abatement curve
        if "sector" in request_data and "current_emissions_tco2" in request_data:
            results["abatement_curve"] = self.build_abatement_cost_curve(
                entity_id=entity_id,
                sector=request_data["sector"],
                current_emissions_tco2=request_data["current_emissions_tco2"],
                target_reduction_pct=request_data.get("target_reduction_pct", 50),
            )

        # NZE economics
        if "revenue_m" in request_data and "sector" in request_data:
            results["nze_economics"] = self.calculate_nze_economics(
                entity_id=entity_id,
                revenue_m=request_data["revenue_m"],
                sector=request_data["sector"],
                current_emissions_tco2=request_data.get("current_emissions_tco2", 10_000),
                nze_year=request_data.get("nze_year", 2050),
                discount_rate=request_data.get("discount_rate", 0.08),
            )

        # ETS shadow exposure
        if "eu_ets_verified_tco2" in request_data:
            results["ets_exposure"] = self.assess_ets_shadow_exposure(
                entity_id=entity_id,
                eu_ets_verified_tco2=request_data["eu_ets_verified_tco2"],
                free_allocation_tco2=request_data.get("free_allocation_tco2", 0),
                ets2_fuel_consumption_gj=request_data.get("ets2_fuel_consumption_gj"),
            )

        # ICP maturity scoring
        score = 0
        if request_data.get("current_icp"):
            score += 20
            if mechanism_result["alignment_status"] == "aligned":
                score += 20
        if request_data.get("mechanism_type") in ["internal_fee_dividend", "budget_based"]:
            score += 15
        if request_data.get("sbti_target") == "1.5C":
            score += 15
        if "abatement_curve" in results:
            score += 15
        if "nze_economics" in results:
            score += 15

        tier = (
            "Leader" if score >= 85
            else "Advanced" if score >= 70
            else "Developing" if score >= 50
            else "Early" if score >= 30
            else "Absent"
        )

        results["icp_maturity_score"] = score
        results["icp_maturity_tier"] = tier
        results["assessment_standard"] = (
            "IPCC AR6 WG3 (2022); SBTi Corporate Manual v2 (2023); "
            "EU ETS Phase 4 Directive 2023/958; ETS2 Directive 2023/959"
        )

        return results


# ---------------------------------------------------------------------------
# E84 — Required Named Constants (route-layer aliases)
# ---------------------------------------------------------------------------

# SBTi minimum ICP price (EUR/tCO2) by year.
# Source: SBTi ICP Guidance 2023
SBTI_ICP_THRESHOLDS: Dict[int, float] = {
    2023: 135.0,
    2025: 175.0,
    2030: 250.0,
    2035: 350.0,
    2040: 500.0,
}

# EU ETS Phase 4 product benchmarks (tCO2/unit).
# Source: Commission Decision 2021/447 + Decision 2024/903
EU_ETS_PHASE4_BENCHMARKS: Dict[str, float] = {
    "hot_metal":               0.1254,   # tCO2/t — iron & steel
    "clinker":                 0.7666,   # tCO2/t — cement
    "lime":                    0.9540,   # tCO2/t — lime
    "float_glass":             0.4533,   # tCO2/t — flat glass
    "refinery":                0.0295,   # tCO2/GJ — oil refineries
    "steam_cracker":           0.6027,   # tCO2/t — petrochemicals
    "pulp":                    0.1169,   # tCO2/t — Kraft pulp
    "newsprint":               0.2750,   # tCO2/t — newsprint paper
    "coated_paper":            0.4321,   # tCO2/t — coated fine paper
    "heat_district":           0.0575,   # tCO2/GJ — district heating
    "electricity_generation":  0.3394,   # tCO2/MWh — power baseline
    "aluminium_primary":       1.4940,   # tCO2/t — primary aluminium
}

# ETS carbon price trajectory (EUR/t) by scenario and year (2024–2050).
# Source: IEA WEO 2023; IPCC AR6 WG3 carbon price corridors
ETS_PRICE_TRAJECTORY: Dict[str, Dict[int, float]] = {
    "current_policies": {
        2024: 62,  2025: 65,  2026: 68,  2027: 70,  2028: 72,
        2029: 74,  2030: 76,  2031: 78,  2032: 80,  2033: 82,
        2034: 84,  2035: 86,  2036: 88,  2037: 90,  2038: 92,
        2039: 94,  2040: 96,  2041: 98,  2042: 100, 2043: 102,
        2044: 104, 2045: 106, 2046: 108, 2047: 110, 2048: 112,
        2049: 114, 2050: 116,
    },
    "net_zero_2050": {
        2024: 75,  2025: 90,  2026: 110, 2027: 130, 2028: 150,
        2029: 175, 2030: 200, 2031: 225, 2032: 250, 2033: 270,
        2034: 290, 2035: 315, 2036: 340, 2037: 365, 2038: 395,
        2039: 425, 2040: 460, 2041: 490, 2042: 520, 2043: 550,
        2044: 580, 2045: 610, 2046: 640, 2047: 670, 2048: 700,
        2049: 730, 2050: 760,
    },
    "delayed_transition": {
        2024: 62,  2025: 63,  2026: 65,  2027: 68,  2028: 72,
        2029: 78,  2030: 90,  2031: 115, 2032: 145, 2033: 175,
        2034: 210, 2035: 250, 2036: 295, 2037: 340, 2038: 385,
        2039: 430, 2040: 480, 2041: 510, 2042: 540, 2043: 565,
        2044: 585, 2045: 605, 2046: 620, 2047: 635, 2048: 645,
        2049: 655, 2050: 660,
    },
}

# Marginal abatement cost categories (8 macro groups).
# Source: McKinsey Global MAC Curve v4.0; IEA Technology Perspectives 2023
ABATEMENT_COST_CATEGORIES: List[Dict[str, Any]] = [
    {
        "category":              "energy_efficiency",
        "cost_eur_tco2_low":     -50.0,
        "cost_eur_tco2_high":     30.0,
        "potential_mtco2_yr":     8.5,
        "description":           "Building insulation, motor efficiency, industrial heat recovery",
        "readiness":             "commercial",
        "typical_payback_years":  4.0,
    },
    {
        "category":              "renewable_switch",
        "cost_eur_tco2_low":      5.0,
        "cost_eur_tco2_high":    60.0,
        "potential_mtco2_yr":    14.2,
        "description":           "Solar PV, onshore/offshore wind power procurement (PPAs)",
        "readiness":             "commercial",
        "typical_payback_years":  6.0,
    },
    {
        "category":              "fuel_switch",
        "cost_eur_tco2_low":     20.0,
        "cost_eur_tco2_high":   120.0,
        "potential_mtco2_yr":    5.8,
        "description":           "Gas-to-hydrogen, coal-to-gas, biomass co-firing",
        "readiness":             "early_commercial",
        "typical_payback_years":  8.0,
    },
    {
        "category":              "ccus",
        "cost_eur_tco2_low":     60.0,
        "cost_eur_tco2_high":   250.0,
        "potential_mtco2_yr":    3.1,
        "description":           "Carbon capture utilisation and storage — point source + DAC",
        "readiness":             "demonstration",
        "typical_payback_years": 15.0,
    },
    {
        "category":              "electrification",
        "cost_eur_tco2_low":     10.0,
        "cost_eur_tco2_high":    90.0,
        "potential_mtco2_yr":    6.4,
        "description":           "EV fleet transition, electric heat pumps, electric arc furnaces",
        "readiness":             "commercial",
        "typical_payback_years":  7.0,
    },
    {
        "category":              "process_change",
        "cost_eur_tco2_low":     30.0,
        "cost_eur_tco2_high":   180.0,
        "potential_mtco2_yr":    2.9,
        "description":           "Low-carbon cement, green steel (DRI-H2), circular manufacturing",
        "readiness":             "early_commercial",
        "typical_payback_years": 10.0,
    },
    {
        "category":              "nature_based",
        "cost_eur_tco2_low":      5.0,
        "cost_eur_tco2_high":    50.0,
        "potential_mtco2_yr":    4.7,
        "description":           "Reforestation, soil carbon, wetland restoration, agroforestry",
        "readiness":             "commercial",
        "typical_payback_years": 20.0,
    },
    {
        "category":              "offsetting",
        "cost_eur_tco2_low":      3.0,
        "cost_eur_tco2_high":   100.0,
        "potential_mtco2_yr":   12.0,
        "description":           "Voluntary carbon market credits (VCS, Gold Standard, Art 6 ITMOs)",
        "readiness":             "commercial",
        "typical_payback_years":  1.0,
    },
]

# ICP maturity tiers (4 levels, score 0-100).
ICP_MATURITY_TIERS: Dict[str, Dict[str, Any]] = {
    "initial": {
        "description":     "Ad-hoc or no formal ICP; price not used in decision-making",
        "score_range":     [0, 24],
        "characteristics": [
            "No formal ICP policy document",
            "Shadow price considered but not applied",
            "No Scope 3 coverage",
            "Price below SBTi 2023 minimum (€135/t)",
        ],
        "next_steps": [
            "Formalise ICP policy",
            "Apply shadow price to CAPEX gates",
            "Set 2025 price path",
        ],
    },
    "developing": {
        "description":     "Formal ICP policy; applied to some CAPEX; limited scope coverage",
        "score_range":     [25, 49],
        "characteristics": [
            "Written ICP policy approved at board or CFO level",
            "Shadow price ≥ SBTi 2023 minimum (€135/t)",
            "Scope 1 + 2 covered; Scope 3 partial",
            "Annual review cadence established",
        ],
        "next_steps": [
            "Extend to all CAPEX and M&A",
            "Integrate Scope 3 value chain",
            "Publish ICP externally",
        ],
    },
    "advanced": {
        "description":     "ICP embedded in business planning; Scopes 1-3 covered; SBTi-aligned trajectory",
        "score_range":     [50, 74],
        "characteristics": [
            "Fee or shadow price applied consistently across Scopes 1/2/3",
            "Price ≥ SBTi 2030 trajectory (€250/t by 2030)",
            "Revenue recycling or internal fund mechanism",
            "Linked to NZE investment targets and SBTi targets",
        ],
        "next_steps": [
            "Achieve leading tier",
            "Align with 2035 SBTi trajectory",
            "Publish TCFD/IFRS S2 disclosure",
        ],
    },
    "leading": {
        "description":     "Best-in-class ICP; fee-based; full scope coverage; disclosed and verified",
        "score_range":     [75, 100],
        "characteristics": [
            "Fee-based mechanism with internal fund recycled to NZE investments",
            "Price ≥ SBTi 2035+ trajectory (≥€350/t by 2035)",
            "Full Scope 1/2/3 coverage including Category 15",
            "Third-party verified; published in annual sustainability report",
            "Linked to executive compensation KPIs",
        ],
        "next_steps": [
            "Maintain leadership",
            "Explore Art 6 ITMOs for residual emissions",
            "Benchmark peer alignment",
        ],
    },
}


# ---------------------------------------------------------------------------
# E84 — Module-level wrapper functions (thin delegates to class methods)
# ---------------------------------------------------------------------------

_ENGINE = InternalCarbonPriceEngine()

# Internal helpers for module-level functions
def _ets_price_from_trajectory(year: int, trajectory: str) -> float:
    traj = ETS_PRICE_TRAJECTORY.get(trajectory, ETS_PRICE_TRAJECTORY["net_zero_2050"])
    years = sorted(traj.keys())
    if year <= years[0]:
        return traj[years[0]]
    if year >= years[-1]:
        return traj[years[-1]]
    for i in range(len(years) - 1):
        y0, y1 = years[i], years[i + 1]
        if y0 <= year <= y1:
            frac = (year - y0) / (y1 - y0)
            return traj[y0] + frac * (traj[y1] - traj[y0])
    return traj[years[-1]]


def _sbti_threshold_for_year(year: int) -> float:
    """Linear interpolation of SBTi ICP threshold for a given year."""
    items = sorted(SBTI_ICP_THRESHOLDS.items())
    if year <= items[0][0]:
        return items[0][1]
    if year >= items[-1][0]:
        return items[-1][1]
    for i in range(len(items) - 1):
        y0, p0 = items[i]
        y1, p1 = items[i + 1]
        if y0 <= year <= y1:
            frac = (year - y0) / (y1 - y0)
            return p0 + frac * (p1 - p0)
    return items[-1][1]


def _assign_maturity_tier(score: float) -> str:
    for tier, meta in ICP_MATURITY_TIERS.items():
        lo, hi = meta["score_range"]
        if lo <= score <= hi:
            return tier
    return "initial"


def assess_icp_mechanism(entity_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Evaluate ICP mechanism (shadow vs fee), check SBTi minimum price compliance,
    score maturity (0-100), assign tier, compute price coverage across scopes.
    """
    icp_price   = float(entity_data.get("icp_price_eur_t", 0.0))
    mechanism   = entity_data.get("mechanism_type", "none").lower()
    sc1_cov     = bool(entity_data.get("scope1_covered", False))
    sc2_cov     = bool(entity_data.get("scope2_covered", False))
    sc3_cov     = bool(entity_data.get("scope3_covered", False))
    sc3_cats    = entity_data.get("scope3_categories", [])
    capex       = bool(entity_data.get("applied_to_capex", False))
    ma          = bool(entity_data.get("applied_to_ma", False))
    board       = bool(entity_data.get("board_approved", False))
    disclosed   = bool(entity_data.get("external_disclosed", False))
    verified    = bool(entity_data.get("third_party_verified", False))
    recycled    = bool(entity_data.get("revenue_recycled", False))
    exec_comp   = bool(entity_data.get("linked_exec_comp", False))
    annual_rev  = bool(entity_data.get("annual_review", False))

    s1_em = float(entity_data.get("scope1_emissions_tco2", 0.0))
    s2_em = float(entity_data.get("scope2_emissions_tco2", 0.0))
    s3_em = float(entity_data.get("scope3_emissions_tco2", 0.0))

    sbti_2023_met = icp_price >= SBTI_ICP_THRESHOLDS[2023]
    sbti_2025_met = icp_price >= SBTI_ICP_THRESHOLDS[2025]
    sbti_2030_met = icp_price >= SBTI_ICP_THRESHOLDS[2030]
    sbti_2035_met = icp_price >= SBTI_ICP_THRESHOLDS[2035]

    total_em   = s1_em + s2_em + s3_em
    covered_em = (
        (s1_em if sc1_cov else 0.0)
        + (s2_em if sc2_cov else 0.0)
        + (s3_em * (len(sc3_cats) / 15.0) if sc3_cov else 0.0)
    )
    coverage_pct = (covered_em / total_em * 100.0) if total_em > 0 else 0.0

    # Maturity scoring (0-100)
    score = 0.0
    if icp_price > 0:
        score += 5.0
    if sbti_2023_met:
        score += 10.0
    if sbti_2025_met:
        score += 5.0
    if sbti_2030_met:
        score += 10.0
    if sbti_2035_met:
        score += 5.0
    if mechanism == "fee" or mechanism == "internal_fee_dividend":
        score += 15.0
    elif mechanism in ("shadow", "shadow_price", "ets_shadow"):
        score += 8.0
    score += min(10.0, coverage_pct / 10.0)
    if sc1_cov and sc2_cov:
        score += 5.0
    if sc3_cov and len(sc3_cats) >= 10:
        score += 5.0
    if capex:
        score += 7.0
    if ma:
        score += 4.0
    if annual_rev:
        score += 4.0
    if board:
        score += 4.0
    if disclosed:
        score += 4.0
    if verified:
        score += 4.0
    if recycled:
        score += 2.0
    if exec_comp:
        score += 1.0
    score = min(100.0, score)
    tier = _assign_maturity_tier(score)

    gaps: List[str] = []
    if mechanism == "none":
        gaps.append("No ICP mechanism established")
    if not sbti_2023_met:
        gaps.append(
            f"ICP price €{icp_price}/t below SBTi 2023 minimum €{SBTI_ICP_THRESHOLDS[2023]}/t"
        )
    if not sc3_cov:
        gaps.append("Scope 3 not covered — required for SBTi alignment")
    if not capex:
        gaps.append("ICP not applied to CAPEX investment decisions")
    if not board:
        gaps.append("ICP policy not board-approved")
    if not disclosed:
        gaps.append("ICP not externally disclosed (TCFD/IFRS S2 requirement)")

    return {
        "icp_price_eur_t":        icp_price,
        "mechanism_type":         mechanism,
        "sbti_2023_minimum_met":  sbti_2023_met,
        "sbti_2025_minimum_met":  sbti_2025_met,
        "sbti_2030_minimum_met":  sbti_2030_met,
        "sbti_2035_minimum_met":  sbti_2035_met,
        "sbti_icp_guidance_met":  sbti_2023_met,
        "maturity_score":         round(score, 1),
        "maturity_tier":          tier,
        "tier_description":       ICP_MATURITY_TIERS[tier]["description"],
        "emission_coverage_pct":  round(coverage_pct, 1),
        "covered_emissions_tco2": round(covered_em, 0),
        "total_emissions_tco2":   round(total_em, 0),
        "scope_coverage": {
            "scope1": sc1_cov,
            "scope2": sc2_cov,
            "scope3": sc3_cov,
            "scope3_categories_covered": len(sc3_cats),
        },
        "governance": {
            "board_approved":       board,
            "external_disclosed":   disclosed,
            "third_party_verified": verified,
            "revenue_recycled":     recycled,
            "linked_exec_comp":     exec_comp,
            "annual_review":        annual_rev,
        },
        "gaps":               gaps,
        "recommended_price":  _sbti_threshold_for_year(2025),
        "next_sbti_threshold": {
            "year":        2030,
            "price_eur_t": SBTI_ICP_THRESHOLDS[2030],
        },
    }


def compute_scope_carbon_costs(
    entity_data: Dict[str, Any],
    icp_price: float,
    trajectory: str = "net_zero_2050",
) -> Dict[str, Any]:
    """
    Calculate S1/S2/S3 carbon costs at given ICP price, project to
    2030/2035/2040, and compute EBITDA impact %.
    """
    s1     = float(entity_data.get("scope1_emissions_tco2", 0.0))
    s2     = float(entity_data.get("scope2_emissions_tco2", 0.0))
    s3     = float(entity_data.get("scope3_emissions_tco2", 0.0))
    ebitda = float(entity_data.get("ebitda_eur", 1.0)) or 1.0
    rd1    = float(entity_data.get("annual_reduction_pct_s1", 0.05))
    rd2    = float(entity_data.get("annual_reduction_pct_s2", 0.05))
    rd3    = float(entity_data.get("annual_reduction_pct_s3", 0.03))

    base_year = 2024

    def _proj_em(base: float, rd: float, ahead: int) -> float:
        return base * ((1 - rd) ** ahead)

    def _costs_at(yr: int) -> Dict[str, Any]:
        ahead    = yr - base_year
        em_s1    = _proj_em(s1, rd1, ahead)
        em_s2    = _proj_em(s2, rd2, ahead)
        em_s3    = _proj_em(s3, rd3, ahead)
        ets_p    = _ets_price_from_trajectory(yr, trajectory)
        eff_p    = max(icp_price, ets_p)
        c1       = em_s1 * eff_p
        c2       = em_s2 * eff_p
        c3       = em_s3 * eff_p * 0.3
        total    = c1 + c2 + c3
        return {
            "scope1_emissions_tco2":  round(em_s1, 0),
            "scope2_emissions_tco2":  round(em_s2, 0),
            "scope3_emissions_tco2":  round(em_s3, 0),
            "effective_price_eur_t":  round(eff_p, 2),
            "scope1_cost_eur":        round(c1, 0),
            "scope2_cost_eur":        round(c2, 0),
            "scope3_cost_eur":        round(c3, 0),
            "total_cost_eur":         round(total, 0),
            "ebitda_impact_pct":      round(total / ebitda * 100, 2),
        }

    current   = _costs_at(base_year)
    proj_2030 = _costs_at(2030)
    proj_2035 = _costs_at(2035)
    proj_2040 = _costs_at(2040)

    return {
        "icp_price_eur_t":        icp_price,
        "trajectory":             trajectory,
        "base_year":              base_year,
        "current":                current,
        "projection_2030":        proj_2030,
        "projection_2035":        proj_2035,
        "projection_2040":        proj_2040,
        "total_carbon_cost_eur":  current["total_cost_eur"],
        "carbon_cost_pct_ebitda": current["ebitda_impact_pct"],
        "cost_increase_to_2030_pct": round(
            (proj_2030["total_cost_eur"] - current["total_cost_eur"])
            / max(current["total_cost_eur"], 1) * 100,
            1,
        ),
    }


def model_carbon_budget(
    entity_data: Dict[str, Any],
    scenario: str = "net_zero_2050",
) -> Dict[str, Any]:
    """
    Model remaining Paris-aligned 1.5 °C carbon budget, exhaustion year,
    required annual reduction %, and cumulative trajectory.
    """
    s1       = float(entity_data.get("scope1_emissions_tco2", 0.0))
    s2       = float(entity_data.get("scope2_emissions_tco2", 0.0))
    s3       = float(entity_data.get("scope3_emissions_tco2", 0.0))
    revenue  = float(entity_data.get("revenue_eur", 1_000_000.0)) or 1_000_000.0
    nze_yr   = int(entity_data.get("sbti_target_year", 2050))
    base_em  = float(entity_data.get("base_year_emissions_tco2", s1 + s2 + s3))

    _IPCC_REMAINING_BUDGET_GTCO2 = 380.0
    _GLOBAL_GDP_EUR               = 100_000_000_000_000.0
    current_total                 = s1 + s2 + s3

    entity_share       = min(revenue / _GLOBAL_GDP_EUR, 1.0)
    entity_budget_tco2 = _IPCC_REMAINING_BUDGET_GTCO2 * 1e9 * entity_share

    if current_total > 0:
        exhaustion_year = int(2024 + entity_budget_tco2 / current_total)
    else:
        exhaustion_year = 2100

    years_to_nze       = max(nze_yr - 2024, 1)
    budget_lim_current = entity_budget_tco2 * 2 / years_to_nze
    req_reduction_pct  = max(
        0.0,
        (1 - (budget_lim_current / current_total) ** (1 / years_to_nze)) * 100
        if current_total > 0 else 0.0,
    )

    trajectory: List[Dict[str, Any]] = []
    for yr in range(2024, 2051, 5):
        ahead   = yr - 2024
        rem_pct = max(0.0, 1 - (req_reduction_pct / 100) * ahead)
        em_yr   = current_total * rem_pct
        trajectory.append({
            "year":             yr,
            "emissions_tco2":   round(em_yr, 0),
            "pct_of_base":      round(rem_pct * 100, 1),
        })

    return {
        "scenario":                      scenario,
        "current_annual_emissions_tco2": round(current_total, 0),
        "base_year_emissions_tco2":      round(base_em, 0),
        "entity_carbon_budget_tco2":     round(entity_budget_tco2, 0),
        "budget_exhaustion_year":        exhaustion_year,
        "budget_exhausted_before_2050":  exhaustion_year < 2050,
        "required_annual_reduction_pct": round(req_reduction_pct, 2),
        "net_zero_target_year":          nze_yr,
        "years_to_net_zero":             years_to_nze,
        "ipcc_remaining_budget_gtco2":   _IPCC_REMAINING_BUDGET_GTCO2,
        "entity_revenue_share_global":   round(entity_share * 100, 6),
        "cumulative_trajectory":         trajectory,
        "paris_aligned":                 exhaustion_year >= nze_yr,
    }


def calculate_nze_economics(entity_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Calculate NZE investment NPV/IRR/payback and build abatement cost curve by category.
    """
    total_em   = float(entity_data.get("total_emissions_tco2", 10_000.0))
    icp_price  = float(entity_data.get("icp_price_eur_t", 135.0))
    investment = float(entity_data.get("nze_investment_eur", 5_000_000.0))
    horizon    = int(entity_data.get("investment_horizon_years", 15))
    wacc       = float(entity_data.get("wacc", 0.08))
    ebitda     = float(entity_data.get("ebitda_eur", 10_000_000.0)) or 10_000_000.0
    ab_target  = float(entity_data.get("abatement_target_pct", 0.50))

    target_reduction_tco2 = total_em * ab_target
    annual_carbon_saving  = target_reduction_tco2 * icp_price
    annual_energy_saving  = investment * 0.03
    total_annual_benefit  = annual_carbon_saving + annual_energy_saving
    cash_flows            = [total_annual_benefit] * horizon

    green_wacc = max(0.01, wacc - 0.005)
    npv_val    = sum(cf / ((1 + green_wacc) ** t) for t, cf in enumerate(cash_flows, 1)) - investment
    payback    = investment / total_annual_benefit if total_annual_benefit > 0 else 999.0

    # IRR via Newton-Raphson
    irr = 0.10
    flows_irr = [-investment] + cash_flows
    for _ in range(200):
        npv_i  = sum(f / ((1 + irr) ** t) for t, f in enumerate(flows_irr))
        d_npv  = sum(-t * f / ((1 + irr) ** (t + 1)) for t, f in enumerate(flows_irr))
        if abs(d_npv) < 1e-12:
            break
        irr_new = irr - npv_i / d_npv
        if abs(irr_new - irr) < 1e-8:
            irr = irr_new
            break
        irr = irr_new
    irr = max(-1.0, min(irr, 5.0))

    # Abatement cost curve
    _GLOBAL_EM = 37_400_000_000.0
    entity_frac = total_em / _GLOBAL_EM if _GLOBAL_EM > 0 else 0
    remaining   = target_reduction_tco2
    curve: List[Dict[str, Any]] = []
    cost_effective_cats: List[str] = []

    for cat in sorted(ABATEMENT_COST_CATEGORIES, key=lambda x: x["cost_eur_tco2_low"]):
        if remaining <= 0:
            break
        mid_cost  = (cat["cost_eur_tco2_low"] + cat["cost_eur_tco2_high"]) / 2
        potential = cat["potential_mtco2_yr"] * 1e6 * entity_frac
        used      = min(potential, remaining)
        remaining -= used
        if mid_cost <= icp_price:
            cost_effective_cats.append(cat["category"])
        curve.append({
            "category":                   cat["category"],
            "cost_eur_tco2_mid":          round(mid_cost, 1),
            "cost_eur_tco2_low":          cat["cost_eur_tco2_low"],
            "cost_eur_tco2_high":         cat["cost_eur_tco2_high"],
            "abatement_potential_tco2":   round(potential, 0),
            "abatement_used_tco2":        round(used, 0),
            "total_cost_eur":             round(used * mid_cost, 0),
            "cost_effective_vs_icp":      mid_cost <= icp_price,
            "readiness":                  cat["readiness"],
        })

    cost_eff_abatement = sum(c["abatement_used_tco2"] for c in curve if c["cost_effective_vs_icp"])

    return {
        "total_emissions_tco2":          round(total_em, 0),
        "abatement_target_tco2":         round(total_em * ab_target, 0),
        "nze_investment_eur":            round(investment, 0),
        "investment_horizon_years":      horizon,
        "wacc":                          wacc,
        "annual_carbon_savings_eur":     round(annual_carbon_saving, 0),
        "annual_energy_savings_eur":     round(annual_energy_saving, 0),
        "total_annual_benefit_eur":      round(total_annual_benefit, 0),
        "nze_npv_eur":                   round(npv_val, 0),
        "nze_irr_pct":                   round(irr * 100, 2),
        "payback_years":                 round(payback, 1),
        "investment_per_tco2_eur":       round(investment / max(total_em * ab_target, 1), 2),
        "ebitda_investment_ratio":       round(investment / ebitda, 2),
        "abatement_cost_curve":          curve,
        "cost_effective_categories":     cost_effective_cats,
        "cost_effective_abatement_tco2": round(cost_eff_abatement, 0),
        "investment_positive_npv":       npv_val > 0,
    }


def calculate_ets_exposure(entity_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Calculate EU ETS Phase 4 free allocation vs verified emissions, ETS2
    exposure (buildings / transport), and combined compliance cost.
    """
    inst_type   = entity_data.get("installation_type", "")
    prod_units  = float(entity_data.get("production_units", 0.0))
    verified_em = float(entity_data.get("verified_emissions_tco2", 0.0))
    ets_price   = float(entity_data.get("ets_price_eur_t", 75.0))
    floor_area  = float(entity_data.get("building_floor_area_sqm", 0.0))
    fleet_km    = float(entity_data.get("vehicle_fleet_km_annual", 0.0))
    trajectory  = entity_data.get("trajectory", "net_zero_2050")
    year        = int(entity_data.get("year", 2024))

    benchmark = EU_ETS_PHASE4_BENCHMARKS.get(inst_type)
    if benchmark and prod_units > 0:
        cscf           = max(0.70, 1.0 - (year - 2021) * 0.025)
        calc_alloc     = prod_units * benchmark * cscf
    else:
        calc_alloc     = float(entity_data.get("free_allocation_tco2", 0.0))

    free_alloc             = max(calc_alloc, float(entity_data.get("free_allocation_tco2", calc_alloc)))
    net_position           = verified_em - free_alloc
    phase4_compliance_cost = max(0.0, net_position) * ets_price
    phase4_surplus_value   = max(0.0, -net_position) * ets_price * 0.9

    # ETS2
    ets2_building_em  = floor_area * 35.0 / 1000.0    # kgCO2/m²/yr → tCO2
    ets2_transport_em = fleet_km * 115.0 / 1_000_000.0  # gCO2/km → tCO2
    ets2_total        = ets2_building_em + ets2_transport_em
    ets2_price        = max(45.0, _ets_price_from_trajectory(year, trajectory) * 0.6)
    ets2_exposure     = ets2_total * ets2_price

    price_2030        = _ets_price_from_trajectory(2030, trajectory)
    phase4_2030_cost  = max(0.0, net_position * 1.05) * price_2030
    ets2_2030_cost    = ets2_total * 1.10 * price_2030 * 0.6

    return {
        "installation_type":   inst_type or "unspecified",
        "assessment_year":     year,
        "trajectory":          trajectory,
        "phase4": {
            "benchmark_tco2_per_unit":    benchmark,
            "production_units":           round(prod_units, 0),
            "calculated_allocation_tco2": round(calc_alloc, 0),
            "free_allocation_tco2":       round(free_alloc, 0),
            "verified_emissions_tco2":    round(verified_em, 0),
            "net_position_tco2":          round(net_position, 0),
            "position_type":              "deficit" if net_position > 0 else "surplus",
            "ets_price_eur_t":            ets_price,
            "compliance_cost_eur":        round(phase4_compliance_cost, 0),
            "surplus_value_eur":          round(phase4_surplus_value, 0),
        },
        "ets2": {
            "building_floor_area_sqm":    floor_area,
            "building_emissions_tco2":    round(ets2_building_em, 0),
            "vehicle_fleet_km_annual":    fleet_km,
            "transport_emissions_tco2":   round(ets2_transport_em, 0),
            "total_ets2_emissions_tco2":  round(ets2_total, 0),
            "ets2_price_eur_t":           round(ets2_price, 2),
            "ets2_exposure_eur":          round(ets2_exposure, 0),
            "operative_from":             2027,
        },
        "combined": {
            "total_ets_exposure_eur":     round(phase4_compliance_cost + ets2_exposure, 0),
            "phase4_2030_projection_eur": round(phase4_2030_cost, 0),
            "ets2_2030_projection_eur":   round(ets2_2030_cost, 0),
            "total_2030_exposure_eur":    round(phase4_2030_cost + ets2_2030_cost, 0),
            "ets_price_2030_eur_t":       round(price_2030, 2),
        },
        "ets_phase4_exposure_eur": round(phase4_compliance_cost, 0),
        "ets2_exposure_eur":       round(ets2_exposure, 0),
    }


def run_full_assessment(entity_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Orchestrate all E84 sub-methods and produce a consolidated assessment.
    Produces: icp_score, icp_maturity_tier, total_carbon_cost_eur,
    carbon_cost_pct_ebitda, nze_npv_eur, nze_irr_pct, ets_phase4_exposure_eur,
    ets2_exposure_eur, sbti_icp_guidance_met, abatement_cost_curve.
    """
    icp_price  = float(entity_data.get("icp_price_eur_t", 100.0))
    trajectory = entity_data.get("trajectory", "net_zero_2050")
    scenario   = entity_data.get("scenario", "net_zero_2050")

    icp_result    = assess_icp_mechanism(entity_data)
    costs_result  = compute_scope_carbon_costs(entity_data, icp_price, trajectory)
    budget_result = model_carbon_budget(entity_data, scenario)
    nze_result    = calculate_nze_economics(entity_data)
    ets_result    = calculate_ets_exposure(entity_data)

    # Composite NZE score (0-100)
    nze_score = 0.0
    if nze_result["investment_positive_npv"]:
        nze_score += 20.0
    if nze_result["nze_irr_pct"] > 8.0:
        nze_score += 15.0
    if budget_result["paris_aligned"]:
        nze_score += 30.0
    if icp_result["sbti_icp_guidance_met"]:
        nze_score += 20.0
    nze_score += min(15.0, icp_result["emission_coverage_pct"] / 100 * 15)

    return {
        "entity_id":                    entity_data.get("entity_id", "unknown"),
        "icp_score":                    icp_result["maturity_score"],
        "icp_maturity_tier":            icp_result["maturity_tier"],
        "nze_composite_score":          round(nze_score, 1),
        "sbti_icp_guidance_met":        icp_result["sbti_icp_guidance_met"],
        "total_carbon_cost_eur":        costs_result["total_carbon_cost_eur"],
        "carbon_cost_pct_ebitda":       costs_result["carbon_cost_pct_ebitda"],
        "nze_npv_eur":                  nze_result["nze_npv_eur"],
        "nze_irr_pct":                  nze_result["nze_irr_pct"],
        "nze_payback_years":            nze_result["payback_years"],
        "ets_phase4_exposure_eur":      ets_result["ets_phase4_exposure_eur"],
        "ets2_exposure_eur":            ets_result["ets2_exposure_eur"],
        "carbon_budget_exhaustion_yr":  budget_result["budget_exhaustion_year"],
        "paris_aligned":                budget_result["paris_aligned"],
        "required_annual_reduction_pct": budget_result["required_annual_reduction_pct"],
        "abatement_cost_curve":         nze_result["abatement_cost_curve"],
        "emission_coverage_pct":        icp_result["emission_coverage_pct"],
        "gaps":                         icp_result["gaps"],
        # Sub-results
        "icp_mechanism":  icp_result,
        "scope_costs":    costs_result,
        "carbon_budget":  budget_result,
        "nze_economics":  nze_result,
        "ets_exposure":   ets_result,
    }
