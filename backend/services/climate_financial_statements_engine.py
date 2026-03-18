"""
Climate Financial Statement Adjustments Engine — E86
======================================================
Standards covered:
- IFRS S2 Climate-Related Disclosures (ISSB June 2023) — Financial Effects paras 29-36
- IAS 36 Impairment of Assets — IASB climate integration guidance (2024)
- IAS 37 Provisions, Contingent Liabilities and Contingent Assets — carbon provisions
- EU ETS Directive 2003/87/EC as amended — ETS allowance accounting
- TCFD Final Report 2017 — financial impact categorisation
- IPCC AR6 WG III (2022) — scenario carbon price pathways
- IEA Net Zero Emissions by 2050 (NZE2050) — stranded asset trigger dates
"""
from __future__ import annotations

import random
from typing import Any

# ---------------------------------------------------------------------------
# Reference data
# ---------------------------------------------------------------------------

IFRS_S2_FINANCIAL_EFFECT_CATEGORIES: list[dict[str, Any]] = [
    {
        "category": "transition_risk_revenue",
        "description": (
            "Revenue impacts from transition to a lower-carbon economy — demand destruction "
            "for carbon-intensive products/services, pricing pressure from low-carbon "
            "alternatives, and loss of market share to clean technology competitors."
        ),
        "income_statement_impact": True,
        "balance_sheet_impact": False,
        "disclosure_required": True,
        "ifrs_s2_reference": "IFRS S2 para 29(a)",
        "typical_sectors": ["oil_gas", "coal", "utilities_fossil", "automotive_ice", "aviation"],
        "quantification_approach": "Sector revenue sensitivity × carbon price delta + structural demand shift modelling",
    },
    {
        "category": "transition_risk_cost",
        "description": (
            "Increased operating and capital costs from carbon pricing, energy efficiency "
            "mandates, input cost changes (green steel, low-carbon fuels), compliance "
            "expenditure, policy levies and supply chain decarbonisation pass-through."
        ),
        "income_statement_impact": True,
        "balance_sheet_impact": True,
        "disclosure_required": True,
        "ifrs_s2_reference": "IFRS S2 para 29(b)",
        "typical_sectors": ["industrials", "materials", "utilities_fossil", "manufacturing", "real_estate"],
        "quantification_approach": "Scope 1+2 emissions × carbon price + energy efficiency gap + green premium on inputs",
    },
    {
        "category": "physical_risk_asset",
        "description": (
            "Asset value impairment and increased insurance costs driven by acute physical "
            "climate hazards (floods, cyclones, wildfires) and chronic hazards (sea-level "
            "rise, heat stress, water scarcity). Requires IAS 36 impairment assessment "
            "under paragraphs 12-14."
        ),
        "income_statement_impact": True,
        "balance_sheet_impact": True,
        "disclosure_required": True,
        "ifrs_s2_reference": "IFRS S2 para 29(c)",
        "typical_sectors": ["real_estate", "agriculture", "infrastructure", "insurance", "coastal_utilities"],
        "quantification_approach": "GEMS expected annual loss uplift × asset exposure + IAS 36 VIU recalculation",
    },
    {
        "category": "climate_opportunity_revenue",
        "description": (
            "Revenue upside from climate-related opportunities — renewable energy products, "
            "energy efficiency services, green product premium, low-carbon transport, "
            "sustainable finance origination, green building and cleantech licensing."
        ),
        "income_statement_impact": True,
        "balance_sheet_impact": False,
        "disclosure_required": True,
        "ifrs_s2_reference": "IFRS S2 para 29(d)",
        "typical_sectors": ["renewables", "cleantech", "ev_manufacturers", "green_finance", "sustainable_real_estate"],
        "quantification_approach": "Green product addressable market × capture rate + greenium on green bond issuance",
    },
    {
        "category": "carbon_provision",
        "description": (
            "IAS 37 provision for ETS allowance deficit and voluntary carbon offset "
            "purchase obligations. Recognised when entity has a present obligation, "
            "outflow is probable (>50%), and amount can be reliably estimated. "
            "Measured at ETS allowance spot price or contracted forward price."
        ),
        "income_statement_impact": True,
        "balance_sheet_impact": True,
        "disclosure_required": True,
        "ifrs_s2_reference": "IFRS S2 para 29(e); IAS 37 paras 14-26",
        "typical_sectors": ["utilities_fossil", "industrials", "oil_gas", "cement", "steel", "aviation"],
        "quantification_approach": "Allowance deficit tonnes × EUA spot price + offset obligation × voluntary carbon price",
    },
    {
        "category": "stranded_asset_write_down",
        "description": (
            "Impairment or write-down of assets whose economic value is diminished earlier "
            "than expected due to climate transition — fossil fuel reserves, coal power plants, "
            "ICE vehicle fleets, brown real estate, and carbon-intensive production facilities. "
            "IEA NZE2050 used as trigger reference for unburnable reserves."
        ),
        "income_statement_impact": True,
        "balance_sheet_impact": True,
        "disclosure_required": True,
        "ifrs_s2_reference": "IFRS S2 para 29(f); IAS 36",
        "typical_sectors": ["oil_gas", "coal", "utilities_fossil", "automotive_ice", "real_estate_brown"],
        "quantification_approach": "IAS 36 VIU under NZE2050 cash flows vs carrying amount; write-down = excess",
    },
    {
        "category": "climate_capex",
        "description": (
            "Capital expenditure required for climate transition and adaptation — renewable "
            "energy capacity additions, energy efficiency retrofits, grid modernisation, "
            "adaptation infrastructure, R&D for low-carbon processes, and asset replacement "
            "to avoid premature stranding and regulatory non-compliance."
        ),
        "income_statement_impact": False,
        "balance_sheet_impact": True,
        "disclosure_required": True,
        "ifrs_s2_reference": "IFRS S2 para 29(g)",
        "typical_sectors": ["utilities", "industrials", "real_estate", "transport", "oil_gas_transition"],
        "quantification_approach": "Green CapEx ratio vs total CapEx; NPV of transition investment programme; CRREM pathway cost",
    },
    {
        "category": "climate_litigation",
        "description": (
            "Contingent liabilities arising from climate-related litigation — shareholder "
            "derivative suits for climate inaction, regulatory enforcement actions, government "
            "recovery suits (Dutch Shell, Milieudefensie model), consumer class actions for "
            "greenwashing, and director liability claims for inadequate climate governance."
        ),
        "income_statement_impact": True,
        "balance_sheet_impact": True,
        "disclosure_required": True,
        "ifrs_s2_reference": "IFRS S2 para 29(h); IAS 37 paras 27-30",
        "typical_sectors": ["oil_gas", "coal", "utilities_fossil", "financial_services", "insurance"],
        "quantification_approach": "Legal exposure assessment × probability of adverse judgment; D&O claim modelling",
    },
]

IAS36_CLIMATE_INDICATORS: list[dict[str, Any]] = [
    {
        "indicator_name": "carbon_price_exceeds_allowance_cost",
        "indicator_id": "EXT-01",
        "type": "external",
        "trigger_description": (
            "Market carbon price has increased beyond the entity's ETS allowance cost basis, "
            "reducing the recoverable value of carbon-intensive assets and production facilities. "
            "Triggered when spot EUA > €80/t or entity faces >20% allowance deficit vs free allocation."
        ),
        "asset_classes_affected": ["production_facilities", "power_plants", "refineries", "cement_plants"],
        "threshold_guidance": "EUA spot > €80/t or allowance deficit > 20% of annual emissions",
        "ias36_reference": "IAS 36 para 12(a) — significant decline in market value; para 12(d) — external environment change",
        "impairment_probability": 0.72,
        "severity": "high",
    },
    {
        "indicator_name": "regulatory_phase_out_announced",
        "indicator_id": "EXT-02",
        "type": "external",
        "trigger_description": (
            "Government or regulator has announced phase-out schedule for asset type "
            "(e.g. ICE vehicle ban by 2035, coal power closure dates, fossil fuel extraction "
            "licence non-renewal). Remaining useful life is shorter than current depreciation schedule."
        ),
        "asset_classes_affected": ["ice_vehicle_fleets", "coal_power_plants", "fossil_fuel_reserves", "gas_networks"],
        "threshold_guidance": "Enacted legislation with closure/ban date within current depreciation period",
        "ias36_reference": "IAS 36 para 12(b) — significant changes in technological, market, economic or legal environment",
        "impairment_probability": 0.85,
        "severity": "high",
    },
    {
        "indicator_name": "physical_hazard_asset_damage",
        "indicator_id": "EXT-03",
        "type": "external",
        "trigger_description": (
            "Acute physical climate event (flood, wildfire, cyclone, storm surge) has caused or "
            "is projected to cause material damage to assets. Triggered by insured loss > 5% of "
            "asset carrying value or asset location within 1-in-50-year flood zone without adequate protection."
        ),
        "asset_classes_affected": ["real_estate", "coastal_infrastructure", "agricultural_assets", "port_facilities"],
        "threshold_guidance": "Physical loss > 5% of carrying value, or WRI Aqueduct Flood Risk > High",
        "ias36_reference": "IAS 36 para 12(a) — evidence of obsolescence or physical damage",
        "impairment_probability": 0.58,
        "severity": "high",
    },
    {
        "indicator_name": "stranded_fossil_reserve",
        "indicator_id": "EXT-04",
        "type": "external",
        "trigger_description": (
            "Proved fossil fuel reserves (oil, gas, coal) are unextractable under IEA Net Zero 2050 "
            "scenario pathway. 1P/2P reserves on balance sheet exceed the carbon budget-consistent "
            "extraction volume for the reporting entity's asset mix."
        ),
        "asset_classes_affected": ["oil_gas_reserves", "coal_reserves", "exploration_assets", "EP_goodwill"],
        "threshold_guidance": "Reserves exceed NZE2050-consistent extraction volume by > 15%",
        "ias36_reference": "IAS 36 para 12(d) — changes in market; IAS 36 para 13 — internal indicators",
        "impairment_probability": 0.68,
        "severity": "high",
    },
    {
        "indicator_name": "green_premium_erosion",
        "indicator_id": "EXT-05",
        "type": "external",
        "trigger_description": (
            "Brown discount / green premium dynamics have resulted in declining market values for "
            "carbon-intensive real estate or infrastructure assets. Observable market evidence "
            "(transaction data, valuer reports) indicates carrying value exceeds recoverable amount."
        ),
        "asset_classes_affected": ["brown_real_estate", "energy_inefficient_buildings", "high_emission_industrial_property"],
        "threshold_guidance": "Market transactions showing > 10% brown discount to energy-efficient comparables",
        "ias36_reference": "IAS 36 para 12(a) — significant decline in market value",
        "impairment_probability": 0.45,
        "severity": "medium",
    },
    {
        "indicator_name": "climate_capex_not_budgeted",
        "indicator_id": "EXT-06",
        "type": "external",
        "trigger_description": (
            "Entity has not budgeted climate transition CapEx required to maintain competitiveness "
            "and regulatory compliance — indicating carrying value assumes profitable operation "
            "that is no longer supportable without significant capital outlay not currently approved."
        ),
        "asset_classes_affected": ["production_facilities", "vehicle_fleets", "energy_systems", "industrial_assets"],
        "threshold_guidance": "Required transition CapEx > 20% of current asset carrying value not in approved budget",
        "ias36_reference": "IAS 36 para 12(f) — plans to restructure or discontinue operations",
        "impairment_probability": 0.52,
        "severity": "medium",
    },
    {
        "indicator_name": "demand_destruction_revenue_decline",
        "indicator_id": "INT-01",
        "type": "internal",
        "trigger_description": (
            "Market demand for entity's carbon-intensive products/services is declining materially "
            "due to structural climate transition — evidenced by > 10% volume decline over two "
            "consecutive years or management forecast showing permanent demand impairment."
        ),
        "asset_classes_affected": ["fossil_fuel_assets", "aviation_assets", "shipping_assets", "coal_assets"],
        "threshold_guidance": "Revenue volume decline > 10% for 2+ consecutive years, or management forecast of permanent decline",
        "ias36_reference": "IAS 36 para 12(d) — unfavourable changes in market environment",
        "impairment_probability": 0.61,
        "severity": "high",
    },
    {
        "indicator_name": "insurance_withdrawal",
        "indicator_id": "INT-02",
        "type": "internal",
        "trigger_description": (
            "Physical climate risk has led to insurance non-renewal or unaffordable premium "
            "increases for assets, reducing their economic utility and supportable carrying value. "
            "Particularly relevant for coastal, flood-prone and wildfire-exposed assets."
        ),
        "asset_classes_affected": ["coastal_real_estate", "flood_zone_assets", "wildfire_exposed_property", "climate_vulnerable_infrastructure"],
        "threshold_guidance": "Insurance unavailable or premium > 3% of asset value per annum",
        "ias36_reference": "IAS 36 para 12(b) — significant adverse change in technological, market, economic or legal environment",
        "impairment_probability": 0.49,
        "severity": "medium",
    },
    {
        "indicator_name": "transition_plan_technology_disruption",
        "indicator_id": "INT-03",
        "type": "internal",
        "trigger_description": (
            "Technological disruption accelerated by climate transition (battery cost decline, "
            "green hydrogen cost reduction, solar LCOE collapse) renders existing technology "
            "assets uncompetitive before end of their useful life as per depreciation schedule."
        ),
        "asset_classes_affected": ["fossil_power_generation", "ICE_drivetrain_assets", "petrochemical_assets", "gas_boilers"],
        "threshold_guidance": "Technology substitution cost crossover within 7 years; or > 30% LCOE disadvantage vs clean alternative",
        "ias36_reference": "IAS 36 para 12(b) — technological obsolescence",
        "impairment_probability": 0.56,
        "severity": "medium",
    },
    {
        "indicator_name": "ndc_policy_tightening",
        "indicator_id": "INT-04",
        "type": "internal",
        "trigger_description": (
            "Government NDC revision or domestic climate legislation imposes significantly more "
            "stringent requirements than previously assumed in management's cash flow projections "
            "— affecting cost base, carbon liability and regulatory compliance timeline."
        ),
        "asset_classes_affected": ["all_carbon_intensive_assets", "regulated_utilities", "emission_intensive_manufacturing"],
        "threshold_guidance": "New legislation implies > 15% increase in compliance cost vs prior-year CGU assumption",
        "ias36_reference": "IAS 36 para 12(d) — adverse changes in economic/legal environment",
        "impairment_probability": 0.43,
        "severity": "medium",
    },
    {
        "indicator_name": "water_stress_operational_curtailment",
        "indicator_id": "INT-05",
        "type": "internal",
        "trigger_description": (
            "Chronic water scarcity or acute water stress events are curtailing operations and "
            "reducing expected cash flows for water-intensive businesses (mining, agriculture, "
            "power generation, semiconductors). WRI Aqueduct Baseline Water Stress > 4.0."
        ),
        "asset_classes_affected": ["mining_assets", "agricultural_assets", "thermal_power_plants", "industrial_facilities"],
        "threshold_guidance": "WRI Aqueduct Baseline Water Stress > 4.0 (Extremely High); operational curtailment > 10% in prior year",
        "ias36_reference": "IAS 36 para 12(a) — evidence of damage / obsolescence; para 12(d) — market changes",
        "impairment_probability": 0.38,
        "severity": "medium",
    },
    {
        "indicator_name": "biodiversity_regulation_compliance_cost",
        "indicator_id": "INT-06",
        "type": "internal",
        "trigger_description": (
            "EU Nature Restoration Law, national biodiversity protection legislation or "
            "TNFD-aligned regulation imposes significant compliance costs or operational "
            "restrictions on assets in or adjacent to sensitive ecosystems — IUCN I-IV "
            "protected areas, Ramsar sites or Key Biodiversity Areas."
        ),
        "asset_classes_affected": ["agricultural_land", "forestry_assets", "mining_concessions", "coastal_assets"],
        "threshold_guidance": "Assets within IUCN I-IV or Ramsar sites facing new compliance obligations with > 5% EBITDA impact",
        "ias36_reference": "IAS 36 para 12(d) — significant adverse change in legal environment",
        "impairment_probability": 0.34,
        "severity": "low",
    },
]

CARBON_PROVISION_THRESHOLDS: dict[str, dict[str, Any]] = {
    "utilities_fossil": {
        "description": "Coal, gas and dual-fuel power generation; district heating from fossil sources",
        "provision_probability": 0.88,
        "typical_provision_basis": "EUA spot price × annual allowance deficit tonnes",
        "ets_exposure_guidance": "Typically 40-80% of annual CO2 allowances must be purchased at market under EU ETS Phase IV",
        "provision_recognition_threshold": "Probable outflow when allowance deficit > 5% of verified emissions",
        "typical_provision_range_eur_per_tonne": {"low": 65, "mid": 95, "high": 130},
        "ias37_reference": "IAS 37 para 14 — present obligation, probable outflow, reliable estimate",
        "notes": "Free allocation (EU ETS Phase IV CAPs) reduces but does not eliminate deficit; aviation sector uses separate benchmark",
    },
    "oil_gas": {
        "description": "Upstream E&P, midstream pipeline, downstream refining and petrochemicals",
        "provision_probability": 0.74,
        "typical_provision_basis": "EUA price × scope 1 emissions deficit; flaring provision at local carbon price",
        "ets_exposure_guidance": "Refining benchmark ~0.595 t CO2/t throughput; E&P typically outside ETS scope 1 unless flaring",
        "provision_recognition_threshold": "Probable when verified scope 1 exceeds free allocation by > 10,000 t CO2e",
        "typical_provision_range_eur_per_tonne": {"low": 55, "mid": 90, "high": 125},
        "ias37_reference": "IAS 37 para 14",
        "notes": "EU Methane Regulation 2024 may create additional provision trigger for methane flaring",
    },
    "industrials": {
        "description": "Steel, aluminium, cement, glass, ceramics, paper and pulp under EU ETS",
        "provision_probability": 0.81,
        "typical_provision_basis": "Product benchmark shortfall × EUA spot; CBAM liability for imported carbon",
        "ets_exposure_guidance": "Steel: ~1.45 t CO2/t hot metal benchmark; cement: ~0.766 t CO2/t clinker (Decision 2021/927)",
        "provision_recognition_threshold": "Probable when actual emissions exceed product benchmark by > 8%",
        "typical_provision_range_eur_per_tonne": {"low": 60, "mid": 90, "high": 120},
        "ias37_reference": "IAS 37 para 14",
        "notes": "CBAM fully operational from 2026 — creates additional import cost provision for third-country competitors",
    },
    "aviation": {
        "description": "Commercial aviation within EU ETS and CORSIA scope",
        "provision_probability": 0.79,
        "typical_provision_basis": "CORSIA eligible unit price × CO2 offsetting obligation; EU ETS aviation benchmark",
        "ets_exposure_guidance": "EU ETS aviation: ~0.699 kg CO2/RTK benchmark; CORSIA Phase I 2024-2026 applies",
        "provision_recognition_threshold": "Probable when intra-EU flight verified CO2 exceeds free allocation",
        "typical_provision_range_eur_per_tonne": {"low": 20, "mid": 55, "high": 95},
        "ias37_reference": "IAS 37 para 14",
        "notes": "SAF blending mandates (ReFuelEU Aviation) create separate CapEx obligation; CORSIA unit prices diverge from EUA",
    },
    "shipping": {
        "description": "Maritime transport — EU ETS inclusion from 2024; FuelEU Maritime from 2025",
        "provision_probability": 0.66,
        "typical_provision_basis": "EU ETS maritime: 100% of intra-EU voyage CO2 × EUA price (from 2026 phase-in complete)",
        "ets_exposure_guidance": "Phase-in: 40% 2024, 70% 2025, 100% 2026; GHG intensity limits from FuelEU Maritime Regulation",
        "provision_recognition_threshold": "Probable when vessel GHG intensity > FuelEU annual intensity target",
        "typical_provision_range_eur_per_tonne": {"low": 50, "mid": 85, "high": 115},
        "ias37_reference": "IAS 37 para 14",
        "notes": "FuelEU surcharge of €2,400/t VLFSO equivalent for non-compliance; pooling mechanism available 2025-2034",
    },
    "real_estate": {
        "description": "Commercial and residential real estate — energy performance and carbon tax exposure",
        "provision_probability": 0.42,
        "typical_provision_basis": "Carbon tax on building emissions × EPC rating deficit; renovation obligation cost",
        "ets_exposure_guidance": "EU ETS Buildings (ETS2) from 2027; national carbon taxes (UK CCL, German CO2 price) already applicable",
        "provision_recognition_threshold": "Probable when building fails minimum EPC threshold before regulatory deadline",
        "typical_provision_range_eur_per_tonne": {"low": 25, "mid": 55, "high": 90},
        "ias37_reference": "IAS 37 para 14",
        "notes": "EPBD recast requires minimum EPC D by 2033 (residential) — creates renovation obligation provision trigger",
    },
    "agriculture": {
        "description": "Agriculture, forestry and land use — voluntary carbon markets and methane levies",
        "provision_probability": 0.31,
        "typical_provision_basis": "Methane levy (where applicable) × livestock CH4 emissions GWP-100; EUDR compliance cost",
        "ets_exposure_guidance": "NZ ETS includes agriculture from 2025; EU LULUCF Regulation compliance obligation for Member States",
        "provision_recognition_threshold": "Probable when methane levy or EUDR deforestation liability is legally enforceable",
        "typical_provision_range_eur_per_tonne": {"low": 10, "mid": 30, "high": 65},
        "ias37_reference": "IAS 37 para 14; IAS 41 Agriculture",
        "notes": "EUDR operator liability for non-compliant commodities creates contingent liability under IAS 37",
    },
    "financial_services": {
        "description": "Banks, insurers and asset managers — facilitated and financed emissions indirect exposure",
        "provision_probability": 0.28,
        "typical_provision_basis": "Portfolio carbon exposure × expected stranded asset write-down; litigation contingency",
        "ets_exposure_guidance": "No direct ETS obligation; indirect exposure via PCAF financed emissions and loan book climate overlay",
        "provision_recognition_threshold": "Probable when borrower carbon liability creates material ECL uplift > 10 bps",
        "typical_provision_range_eur_per_tonne": {"low": 5, "mid": 20, "high": 60},
        "ias37_reference": "IAS 37 para 27 — contingent liability; IFRS 9 ECL climate overlay",
        "notes": "Climate litigation contingency disclosure required even when provision not recognised; D&O liability rising",
    },
}

STRANDED_ASSET_TRIGGERS: list[dict[str, Any]] = [
    {
        "trigger_name": "iea_nze2050_reserve_unburnable",
        "description": (
            "Fossil fuel proved reserves (1P/2P) exceed the volume consistent with IEA Net Zero "
            "Emissions by 2050 scenario carbon budget. Reserves that cannot be commercially "
            "extracted under NZE2050 pathway should be tested for impairment under IAS 36."
        ),
        "write_down_probability": 0.73,
        "asset_types": ["oil_reserves", "gas_reserves", "coal_reserves", "tar_sands", "arctic_exploration"],
        "time_horizon": "2025-2040 (accelerating post-2030 under NZE2050)",
        "regulatory_trigger": "IFRS S2 para 29(f); IAS 36; SEC enhanced climate disclosure Rule 33-11275",
        "write_down_range_pct_of_carrying_value": {"low": 15, "mid": 35, "high": 65},
    },
    {
        "trigger_name": "coal_power_regulatory_closure",
        "description": (
            "Coal-fired power plants facing mandatory closure dates under EU, UK, US or national "
            "energy legislation before end of asset's technical useful life. Carrying value must "
            "reflect shortened useful life and accelerated decommissioning / remediation liability."
        ),
        "write_down_probability": 0.86,
        "asset_types": ["coal_power_plants", "coal_boilers", "coal_handling_infrastructure", "coal_mine_mouth_assets"],
        "time_horizon": "2025-2038 (EU by 2030, US/Asia by 2035-2040)",
        "regulatory_trigger": "IAS 36 para 12(b); IAS 16 useful life revision; IAS 37 decommissioning provision",
        "write_down_range_pct_of_carrying_value": {"low": 25, "mid": 55, "high": 90},
    },
    {
        "trigger_name": "ice_vehicle_sales_ban",
        "description": (
            "EU 2035 ICE ban and equivalent legislation (UK, California, Canada) renders ICE vehicle "
            "production assets, tooling and powertrain factories uncompetitive before economic "
            "depreciation end-date. Includes legacy dealer networks and petrol station assets."
        ),
        "write_down_probability": 0.67,
        "asset_types": ["ICE_production_lines", "powertrain_tooling", "transmission_factories", "fuel_retail_assets"],
        "time_horizon": "2028-2038 (sales ban 2035 implies manufacturing wind-down by 2033)",
        "regulatory_trigger": "IAS 36 para 12(b) — regulatory phase-out; IAS 16 useful life revision",
        "write_down_range_pct_of_carrying_value": {"low": 20, "mid": 40, "high": 70},
    },
    {
        "trigger_name": "brown_building_epc_obsolescence",
        "description": (
            "Commercial and residential buildings rated EPC E, F, G face mandatory minimum energy "
            "performance requirements under EPBD recast (2033: EPC D residential; 2030: worst "
            "performing 16% non-residential). Unlettable / unsaleable assets face brown discount write-down."
        ),
        "write_down_probability": 0.54,
        "asset_types": ["EPC_EFG_offices", "EPC_EFG_retail", "EPC_EFG_residential", "high_energy_intensity_industrial"],
        "time_horizon": "2027-2035 (staggered by asset class and jurisdiction)",
        "regulatory_trigger": "IAS 36 para 12(a) — market value decline; EPBD Directive 2024/1275",
        "write_down_range_pct_of_carrying_value": {"low": 8, "mid": 20, "high": 40},
    },
    {
        "trigger_name": "gas_infrastructure_stranding",
        "description": (
            "Natural gas distribution networks, storage assets and LNG terminals face material "
            "stranding risk as EU heating decarbonisation mandates (heat pump targets, gas boiler "
            "phase-out), hydrogen repurposing uncertainty, and declining throughput undermine "
            "asset utilisation and regulated asset base assumptions."
        ),
        "write_down_probability": 0.59,
        "asset_types": ["gas_distribution_networks", "gas_storage", "LNG_terminals", "gas_boiler_fleets"],
        "time_horizon": "2030-2045 (earlier in high-ambition jurisdictions — UK, NL, DE)",
        "regulatory_trigger": "IAS 36 para 12(d); REPowerEU; EU Gas Decarbonisation Package 2023",
        "write_down_range_pct_of_carrying_value": {"low": 15, "mid": 35, "high": 60},
    },
    {
        "trigger_name": "petrochemical_feedstock_disruption",
        "description": (
            "Petrochemical and plastics assets face stranding from bio-based feedstock substitution, "
            "circular economy legislation (PPWR — Packaging and Packaging Waste Regulation), "
            "microplastics restrictions, and falling demand for virgin plastics in packaging "
            "and single-use applications. Recycled content mandates compress margins."
        ),
        "write_down_probability": 0.48,
        "asset_types": ["steam_crackers", "polymerisation_plants", "plastics_compounding", "petrochemical_storage"],
        "time_horizon": "2028-2040",
        "regulatory_trigger": "IAS 36 para 12(b) — technological change; EU PPWR 2024; SUP Directive",
        "write_down_range_pct_of_carrying_value": {"low": 10, "mid": 25, "high": 50},
    },
]

SCENARIO_FINANCIAL_MULTIPLIERS: dict[str, dict[str, Any]] = {
    "oil_gas": {
        "1_5c_impact_pct": -42.0,
        "2c_impact_pct": -28.0,
        "3c_impact_pct": -12.0,
        "revenue_sensitivity": "high",
        "primary_driver": "Demand destruction for fossil fuels under rapid transition; IEA NZE2050 — no new fields beyond 2021",
        "notes": "Revenue cliff post-2030 under 1.5°C; 3°C scenario provides near-term revenue upside vs transition scenarios",
    },
    "utilities_fossil": {
        "1_5c_impact_pct": -38.0,
        "2c_impact_pct": -24.0,
        "3c_impact_pct": -8.0,
        "revenue_sensitivity": "high",
        "primary_driver": "Accelerated coal/gas phase-out; carbon price cost pass-through limits; stranded plant closures pre-2035",
        "notes": "Decommissioning costs accelerate EBITDA impact under 1.5°C; renewable utilities see opposite signal",
    },
    "industrials": {
        "1_5c_impact_pct": -18.0,
        "2c_impact_pct": -11.0,
        "3c_impact_pct": -4.5,
        "revenue_sensitivity": "medium",
        "primary_driver": "CBAM, ETS cost, green steel/cement CapEx drag; EPBD retrofit demand provides partial offset",
        "notes": "Early movers benefit from CBAM protection; green product premium may offset 3-5% of revenue impact",
    },
    "real_estate": {
        "1_5c_impact_pct": -14.0,
        "2c_impact_pct": -9.0,
        "3c_impact_pct": -16.0,
        "revenue_sensitivity": "medium",
        "primary_driver": "3°C: physical damage dominates; 1.5°C: transition retrofit cost and brown discount dominate",
        "notes": "Non-linear — 3°C worse than 2°C due to acute physical hazard accumulation post-2040; coastal assets most exposed",
    },
    "financials": {
        "1_5c_impact_pct": -8.0,
        "2c_impact_pct": -5.5,
        "3c_impact_pct": -11.0,
        "revenue_sensitivity": "low_to_medium",
        "primary_driver": "Loan book ECL uplift (transition); NatCat losses on balance sheet (physical); sovereign risk contagion",
        "notes": "3°C worse due to NatCat insurance losses and sovereign risk contagion in EM loan portfolios",
    },
    "agriculture": {
        "1_5c_impact_pct": -6.0,
        "2c_impact_pct": -13.0,
        "3c_impact_pct": -28.0,
        "revenue_sensitivity": "high_under_physical",
        "primary_driver": "Yield loss from heat stress, drought, flooding — non-linear above 2°C per IPCC AR6",
        "notes": "IPCC AR6: global crop yield decline accelerates sharply above 1.5°C; adaptation CapEx provides partial offset",
    },
}


# ---------------------------------------------------------------------------
# Helper utilities
# ---------------------------------------------------------------------------

def _rng(seed_str: str) -> random.Random:
    return random.Random(hash(seed_str) & 0xFFFF_FFFF)


def _safe_float(val: Any, default: float = 0.0) -> float:
    try:
        return float(val)
    except (TypeError, ValueError):
        return default


def _clamp(val: float, lo: float = 0.0, hi: float = 100.0) -> float:
    return max(lo, min(hi, val))


# ---------------------------------------------------------------------------
# Engine class
# ---------------------------------------------------------------------------

class ClimateFinancialStatementsEngine:
    """
    E86 — Climate Financial Statement Adjustments Engine.

    Covers IFRS S2 financial effects identification and quantification,
    IAS 36 climate impairment testing, IAS 37 carbon provisions,
    stranded asset write-down assessment and scenario-adjusted financials.
    """

    # ------------------------------------------------------------------
    # 1. IFRS S2 Financial Effects
    # ------------------------------------------------------------------
    def assess_ifrs_s2_financial_effects(self, entity_data: dict) -> dict:
        """
        Identify and quantify the 8 IFRS S2 financial effect categories.
        Returns disclosure completeness score (0-100) and gap identification.
        """
        entity_id = entity_data.get("entity_id", "unknown")
        sector = entity_data.get("sector", "industrials").lower().replace(" ", "_")
        revenue_m = _safe_float(entity_data.get("revenue_m", 1_000))
        ebitda_m = _safe_float(entity_data.get("ebitda_m", 200))
        total_assets_m = _safe_float(entity_data.get("total_assets_m", 2_000))
        carbon_intensity = _safe_float(entity_data.get("carbon_intensity_tco2_per_mrevenue", 80))
        disclosed_categories = entity_data.get("disclosed_categories", [])
        eua_spot = _safe_float(entity_data.get("eua_spot_price_eur", 88.0))

        rng = _rng(entity_id + sector)

        effects: list[dict] = []
        total_income_impact_m = 0.0
        total_bs_impact_m = 0.0
        gaps: list[str] = []

        mult = SCENARIO_FINANCIAL_MULTIPLIERS.get(
            sector,
            {"1_5c_impact_pct": -10.0, "2c_impact_pct": -6.0, "3c_impact_pct": -15.0},
        )

        for cat in IFRS_S2_FINANCIAL_EFFECT_CATEGORIES:
            cat_key = cat["category"]
            sector_relevant = sector in [
                s.lower().replace(" ", "_") for s in cat.get("typical_sectors", [])
            ]
            base_relevance = 0.80 if sector_relevant else 0.35

            # Estimate magnitude per category
            if cat_key == "transition_risk_revenue":
                income_m = abs(revenue_m * abs(_safe_float(mult.get("2c_impact_pct", -10))) / 100 * base_relevance * rng.uniform(0.7, 1.3))
                bs_m = 0.0

            elif cat_key == "transition_risk_cost":
                income_m = abs(ebitda_m * 0.12 * base_relevance * rng.uniform(0.8, 1.4))
                bs_m = income_m * 0.6  # CapEx component capitalised

            elif cat_key == "physical_risk_asset":
                income_m = abs(total_assets_m * 0.03 * base_relevance * rng.uniform(0.5, 1.5)) * 0.4
                bs_m = abs(total_assets_m * 0.03 * base_relevance * rng.uniform(0.5, 1.5))

            elif cat_key == "climate_opportunity_revenue":
                income_m = abs(revenue_m * 0.05 * base_relevance * rng.uniform(0.6, 1.2))
                bs_m = 0.0

            elif cat_key == "carbon_provision":
                ets_profile = CARBON_PROVISION_THRESHOLDS.get(sector, CARBON_PROVISION_THRESHOLDS["industrials"])
                price_mid = ets_profile["typical_provision_range_eur_per_tonne"]["mid"]
                annual_emissions_kt = carbon_intensity * revenue_m / 1_000
                provision_deficit_pct = rng.uniform(0.05, 0.25)
                income_m = annual_emissions_kt * 1_000 * provision_deficit_pct * price_mid / 1_000_000
                bs_m = income_m

            elif cat_key == "stranded_asset_write_down":
                income_m = abs(total_assets_m * 0.08 * base_relevance * rng.uniform(0.4, 1.2))
                bs_m = income_m

            elif cat_key == "climate_capex":
                income_m = 0.0  # Capitalised — no immediate P&L hit
                bs_m = abs(total_assets_m * 0.04 * base_relevance * rng.uniform(0.8, 1.6))

            elif cat_key == "climate_litigation":
                income_m = abs(revenue_m * 0.015 * base_relevance * rng.uniform(0.3, 1.0)) * 0.5
                bs_m = abs(revenue_m * 0.015 * base_relevance * rng.uniform(0.3, 1.0)) * 0.3

            else:
                income_m = 0.0
                bs_m = 0.0

            is_disclosed = cat_key in disclosed_categories
            if not is_disclosed and cat["disclosure_required"]:
                gaps.append(f"{cat_key}: not disclosed — {cat['ifrs_s2_reference']}")

            total_income_impact_m += income_m
            total_bs_impact_m += bs_m

            effects.append({
                "category": cat_key,
                "description": cat["description"][:130] + "...",
                "income_statement_impact": cat["income_statement_impact"],
                "balance_sheet_impact": cat["balance_sheet_impact"],
                "estimated_income_impact_m": round(income_m, 2),
                "estimated_bs_impact_m": round(bs_m, 2),
                "sector_relevant": sector_relevant,
                "disclosed": is_disclosed,
                "ifrs_s2_reference": cat["ifrs_s2_reference"],
                "quantification_approach": cat.get("quantification_approach", ""),
            })

        total_required = sum(1 for c in IFRS_S2_FINANCIAL_EFFECT_CATEGORIES if c["disclosure_required"])
        disclosed_count = sum(
            1 for c in IFRS_S2_FINANCIAL_EFFECT_CATEGORIES
            if c["category"] in disclosed_categories
        )
        disclosure_completeness = round(
            _clamp(disclosed_count / max(total_required, 1) * 100), 1
        )

        ifrs_s2_score = round(
            _clamp(
                disclosure_completeness * 0.60
                + (1 - len(gaps) / max(total_required, 1)) * 40
            ),
            1,
        )

        return {
            "entity_id": entity_id,
            "sector": sector,
            "ifrs_s2_score": ifrs_s2_score,
            "disclosure_completeness_pct": disclosure_completeness,
            "financial_effects": effects,
            "total_income_statement_impact_m": round(total_income_impact_m, 2),
            "total_balance_sheet_impact_m": round(total_bs_impact_m, 2),
            "disclosure_gaps": gaps,
            "gap_count": len(gaps),
            "categories_assessed": len(IFRS_S2_FINANCIAL_EFFECT_CATEGORIES),
            "standard": "IFRS S2 Climate-Related Disclosures — ISSB June 2023 (effective 1 Jan 2024)",
        }

    # ------------------------------------------------------------------
    # 2. IAS 36 Climate Impairment
    # ------------------------------------------------------------------
    def assess_ias36_climate_impairment(self, entity_data: dict) -> dict:
        """
        Evaluate all 12 IAS 36 climate impairment indicators.
        Returns triggered indicators, estimated impairment amount and impairment-tested assets.
        """
        entity_id = entity_data.get("entity_id", "unknown")
        sector = entity_data.get("sector", "industrials").lower().replace(" ", "_")
        total_assets_m = _safe_float(entity_data.get("total_assets_m", 2_000))
        ppe_m = _safe_float(entity_data.get("ppe_m", total_assets_m * 0.45))
        intangibles_m = _safe_float(entity_data.get("intangibles_m", total_assets_m * 0.10))
        goodwill_m = _safe_float(entity_data.get("goodwill_m", total_assets_m * 0.08))
        asset_classes_held = entity_data.get("asset_classes_held", [
            "production_facilities", "real_estate",
        ])
        eua_price = _safe_float(entity_data.get("eua_price_eur", 88.0))
        allowance_deficit_pct = _safe_float(entity_data.get("allowance_deficit_pct", 15.0))

        rng = _rng(entity_id + "ias36")

        high_risk_sectors = {"oil_gas", "utilities_fossil", "coal", "industrials", "real_estate", "aviation", "shipping"}
        triggered: list[dict] = []
        all_indicators: list[dict] = []

        for ind in IAS36_CLIMATE_INDICATORS:
            affected = ind["asset_classes_affected"]
            held_overlap = any(
                any(a.lower() in ac.lower() or ac.lower() in a.lower() for a in asset_classes_held)
                for ac in affected
            )
            sector_trigger = sector in high_risk_sectors

            base_prob = ind["impairment_probability"]
            if held_overlap or sector_trigger:
                adjusted_prob = base_prob
            else:
                adjusted_prob = base_prob * 0.30

            # Specific overrides
            if (
                ind["indicator_name"] == "carbon_price_exceeds_allowance_cost"
                and eua_price > 80
                and allowance_deficit_pct > 20
            ):
                adjusted_prob = min(0.95, adjusted_prob * 1.30)
            if ind["indicator_name"] == "stranded_fossil_reserve" and sector == "oil_gas":
                adjusted_prob = min(0.92, adjusted_prob * 1.20)

            triggered_flag = rng.random() < adjusted_prob

            impairment_m = 0.0
            if triggered_flag:
                iname = ind["indicator_name"]
                if "reserve" in iname or "fossil" in iname or "stranded" in iname:
                    impairment_m = ppe_m * rng.uniform(0.12, 0.35)
                elif "building" in iname or "real_estate" in iname or "green_premium" in iname:
                    impairment_m = ppe_m * 0.40 * rng.uniform(0.08, 0.22)
                elif "goodwill" in iname or "demand" in iname or "revenue" in iname:
                    impairment_m = (goodwill_m + intangibles_m) * rng.uniform(0.10, 0.30)
                else:
                    impairment_m = ppe_m * rng.uniform(0.05, 0.18)

                triggered.append({
                    "indicator_name": ind["indicator_name"],
                    "indicator_id": ind.get("indicator_id", ""),
                    "type": ind.get("type", "external"),
                    "trigger_description": ind["trigger_description"][:120] + "...",
                    "asset_classes_affected": ind["asset_classes_affected"],
                    "estimated_impairment_m": round(impairment_m, 2),
                    "ias36_reference": ind["ias36_reference"],
                    "threshold_guidance": ind["threshold_guidance"],
                    "severity": ind.get("severity", "medium"),
                })

            all_indicators.append({
                "indicator_name": ind["indicator_name"],
                "indicator_id": ind.get("indicator_id", ""),
                "type": ind.get("type", "external"),
                "triggered": triggered_flag,
                "trigger_probability": round(adjusted_prob, 3),
                "estimated_impairment_m": round(impairment_m, 2),
                "ias36_reference": ind["ias36_reference"],
                "severity": ind.get("severity", "medium"),
            })

        total_impairment_m = sum(t["estimated_impairment_m"] for t in triggered)

        # Compile unique asset classes requiring formal test
        impairment_tested_assets: list[str] = []
        if triggered:
            tested_set: set[str] = set()
            for t in triggered:
                ind_match = next(
                    (i for i in IAS36_CLIMATE_INDICATORS if i["indicator_name"] == t["indicator_name"]),
                    None,
                )
                if ind_match:
                    tested_set.update(ind_match["asset_classes_affected"])
            impairment_tested_assets = sorted(tested_set)

        impairment_severity = (
            "critical" if total_impairment_m > total_assets_m * 0.15
            else "material" if total_impairment_m > total_assets_m * 0.05
            else "moderate" if total_impairment_m > total_assets_m * 0.01
            else "low"
        )

        return {
            "entity_id": entity_id,
            "sector": sector,
            "indicators_assessed": len(IAS36_CLIMATE_INDICATORS),
            "indicators_triggered": len(triggered),
            "triggered_indicators": triggered,
            "all_indicator_results": all_indicators,
            "total_potential_impairment_m": round(total_impairment_m, 2),
            "impairment_severity": impairment_severity,
            "impairment_tested_assets": impairment_tested_assets,
            "ppe_m": round(ppe_m, 2),
            "goodwill_intangibles_m": round(goodwill_m + intangibles_m, 2),
            "requires_formal_impairment_test": len(triggered) >= 2,
            "eua_price_used": round(eua_price, 2),
            "standard": "IAS 36 Impairment of Assets — IASB climate integration guidance (2024)",
        }

    # ------------------------------------------------------------------
    # 3. Carbon Provisions
    # ------------------------------------------------------------------
    def calculate_carbon_provisions(self, entity_data: dict) -> dict:
        """
        Calculate IAS 37 carbon provision for ETS allowance deficit.
        Returns provision amount, basis, probability and ETS compliance cost.
        """
        entity_id = entity_data.get("entity_id", "unknown")
        sector = entity_data.get("sector", "industrials").lower().replace(" ", "_")
        annual_verified_emissions_kt = _safe_float(entity_data.get("annual_verified_emissions_kt", 250))
        free_allocation_kt = _safe_float(entity_data.get("free_allocation_kt", 200))
        eua_spot_price = _safe_float(entity_data.get("eua_spot_price_eur", 88.0))
        voluntary_offset_price = _safe_float(entity_data.get("voluntary_offset_price_usd", 18.0))
        carbon_tax_rate = _safe_float(entity_data.get("carbon_tax_rate_eur_per_t", 0.0))
        has_corsia_obligation = bool(entity_data.get("has_corsia_obligation", False))

        rng = _rng(entity_id + "provision")

        profile = CARBON_PROVISION_THRESHOLDS.get(sector, CARBON_PROVISION_THRESHOLDS["industrials"])

        # ETS allowance deficit
        deficit_kt = max(0.0, annual_verified_emissions_kt - free_allocation_kt)
        deficit_pct = deficit_kt / max(annual_verified_emissions_kt, 1.0) * 100

        # IAS 37 recognition threshold — probable (>50%) + reliable estimate
        provision_probability = profile["provision_probability"]
        if deficit_pct < 5:
            provision_probability *= 0.40  # Low deficit — contingent only
        elif deficit_pct > 20:
            provision_probability = min(0.97, provision_probability * 1.15)

        provision_required = provision_probability >= 0.50

        # ETS purchase cost
        ets_purchase_cost_m = deficit_kt * 1_000 * eua_spot_price / 1_000_000

        # Carbon tax (UK CCL, German CO2 price, etc.)
        carbon_tax_cost_m = annual_verified_emissions_kt * 1_000 * carbon_tax_rate / 1_000_000

        # CORSIA offsetting obligation (aviation)
        corsia_cost_m = 0.0
        if has_corsia_obligation:
            corsia_offset_kt = annual_verified_emissions_kt * 0.10  # Phase I indicative rate
            corsia_cost_m = corsia_offset_kt * 1_000 * voluntary_offset_price / 1_000_000

        total_provision_m = (
            ets_purchase_cost_m + carbon_tax_cost_m + corsia_cost_m
            if provision_required
            else 0.0
        )
        contingent_m = (
            ets_purchase_cost_m + carbon_tax_cost_m + corsia_cost_m
            if not provision_required
            else 0.0
        )

        # 3-year forward cost (10-18% annual carbon price appreciation)
        forward_carbon_price = eua_spot_price * rng.uniform(1.08, 1.18) ** 3
        forward_provision_m = deficit_kt * 1_000 * forward_carbon_price / 1_000_000

        return {
            "entity_id": entity_id,
            "sector": sector,
            "annual_verified_emissions_kt": round(annual_verified_emissions_kt, 1),
            "free_allocation_kt": round(free_allocation_kt, 1),
            "allowance_deficit_kt": round(deficit_kt, 1),
            "deficit_pct": round(deficit_pct, 2),
            "eua_spot_price_eur": round(eua_spot_price, 2),
            "ets_purchase_cost_m": round(ets_purchase_cost_m, 3),
            "carbon_tax_cost_m": round(carbon_tax_cost_m, 3),
            "corsia_cost_m": round(corsia_cost_m, 3),
            "total_provision_m": round(total_provision_m, 3),
            "contingent_liability_m": round(contingent_m, 3),
            "provision_required": provision_required,
            "provision_probability": round(provision_probability, 3),
            "provision_basis": profile["typical_provision_basis"],
            "provision_recognition_threshold": profile["provision_recognition_threshold"],
            "forward_provision_3yr_m": round(forward_provision_m, 3),
            "forward_carbon_price_eur": round(forward_carbon_price, 2),
            "ias37_recognition": "recognised" if provision_required else "contingent_disclosure_only",
            "ias37_reference": profile.get("ias37_reference", "IAS 37 para 14"),
            "standard": "IAS 37 Provisions, Contingent Liabilities and Contingent Assets",
        }

    # ------------------------------------------------------------------
    # 4. Stranded Assets
    # ------------------------------------------------------------------
    def assess_stranded_assets(self, entity_data: dict) -> dict:
        """
        Identify triggered stranded asset write-down scenarios.
        Returns write-down estimate, timeline and affected assets.
        """
        entity_id = entity_data.get("entity_id", "unknown")
        sector = entity_data.get("sector", "oil_gas").lower().replace(" ", "_")
        total_assets_m = _safe_float(entity_data.get("total_assets_m", 2_000))
        ppe_m = _safe_float(entity_data.get("ppe_m", total_assets_m * 0.55))
        reserves_m = _safe_float(entity_data.get("reserves_carrying_value_m", 0.0))
        asset_types_held = entity_data.get("asset_types_held", [])
        scenario = entity_data.get("scenario", "below_2c")

        rng = _rng(entity_id + "stranded")

        scenario_severity = {
            "net_zero_2050": 1.40,
            "below_2c": 1.00,
            "delayed_transition": 0.70,
            "current_policies": 0.40,
        }.get(scenario, 1.00)

        triggered_list: list[dict] = []
        total_write_down_m = 0.0

        sector_map: dict[str, list[str]] = {
            "iea_nze2050_reserve_unburnable": ["oil_gas", "coal"],
            "coal_power_regulatory_closure": ["utilities_fossil", "coal"],
            "ice_vehicle_sales_ban": ["automotive", "automotive_ice"],
            "brown_building_epc_obsolescence": ["real_estate"],
            "gas_infrastructure_stranding": ["utilities", "gas", "oil_gas"],
            "petrochemical_feedstock_disruption": ["chemicals", "oil_gas", "industrials"],
        }

        for trigger in STRANDED_ASSET_TRIGGERS:
            t_name = trigger["trigger_name"]
            asset_overlap = any(
                any(
                    at.lower() in ta.lower() or ta.lower() in at.lower()
                    for ta in trigger["asset_types"]
                )
                for at in asset_types_held
            )
            relevant_sectors = sector_map.get(t_name, [])
            sector_relevant = sector in relevant_sectors or any(s in sector for s in relevant_sectors)

            base_prob = trigger["write_down_probability"]
            if sector_relevant or asset_overlap:
                adjusted_prob = min(0.97, base_prob * scenario_severity)
            else:
                adjusted_prob = base_prob * 0.20 * scenario_severity

            if rng.random() < adjusted_prob:
                if "reserve" in t_name or "nze" in t_name:
                    asset_base = max(reserves_m, ppe_m * 0.30)
                elif "building" in t_name or "epc" in t_name:
                    asset_base = ppe_m * 0.35
                elif "gas_infra" in t_name:
                    asset_base = ppe_m * 0.25
                else:
                    asset_base = ppe_m * 0.20

                wd_range = trigger["write_down_range_pct_of_carrying_value"]
                wd_pct = rng.uniform(wd_range["low"] / 100, wd_range["high"] / 100)
                write_down_m = asset_base * wd_pct
                total_write_down_m += write_down_m

                triggered_list.append({
                    "trigger_name": t_name,
                    "description": trigger["description"][:130] + "...",
                    "write_down_m": round(write_down_m, 2),
                    "write_down_pct_of_ppe": round(write_down_m / max(ppe_m, 1) * 100, 2),
                    "timeline": trigger["time_horizon"],
                    "asset_types": trigger["asset_types"],
                    "regulatory_trigger": trigger["regulatory_trigger"],
                    "write_down_range_pct": wd_range,
                })

        stranding_severity = (
            "critical" if total_write_down_m > ppe_m * 0.25
            else "material" if total_write_down_m > ppe_m * 0.10
            else "moderate" if total_write_down_m > ppe_m * 0.03
            else "low"
        )

        return {
            "entity_id": entity_id,
            "sector": sector,
            "scenario": scenario,
            "triggers_assessed": len(STRANDED_ASSET_TRIGGERS),
            "triggers_fired": len(triggered_list),
            "triggered_write_downs": triggered_list,
            "total_write_down_m": round(total_write_down_m, 2),
            "write_down_pct_of_ppe": round(total_write_down_m / max(ppe_m, 1) * 100, 2),
            "write_down_pct_of_total_assets": round(total_write_down_m / max(total_assets_m, 1) * 100, 2),
            "stranding_severity": stranding_severity,
            "ppe_m": round(ppe_m, 2),
            "total_assets_m": round(total_assets_m, 2),
            "scenario_severity_modifier": scenario_severity,
            "standards": [
                "IAS 36 Impairment of Assets",
                "IFRS S2 para 29(f)",
                "IEA Net Zero Emissions by 2050 (2021)",
                "NGFS Phase IV Scenarios 2023",
            ],
        }

    # ------------------------------------------------------------------
    # 5. Climate-Adjusted Financials
    # ------------------------------------------------------------------
    def compute_climate_adjusted_financials(self, entity_data: dict) -> dict:
        """
        Compute climate-adjusted revenue, EBITDA and PAT across three
        temperature scenarios (1.5°C / 2°C / 3°C).
        """
        entity_id = entity_data.get("entity_id", "unknown")
        sector = entity_data.get("sector", "industrials").lower().replace(" ", "_")
        revenue_m = _safe_float(entity_data.get("revenue_m", 1_000))
        ebitda_m = _safe_float(entity_data.get("ebitda_m", 200))
        pat_m = _safe_float(entity_data.get("pat_m", ebitda_m * 0.45))
        carbon_provision_m = _safe_float(entity_data.get("carbon_provision_m", 0.0))
        climate_capex_annual_m = _safe_float(entity_data.get("climate_capex_annual_m", 0.0))

        rng = _rng(entity_id + "financials")

        mult = SCENARIO_FINANCIAL_MULTIPLIERS.get(
            sector,
            {"1_5c_impact_pct": -8.0, "2c_impact_pct": -5.0, "3c_impact_pct": -12.0},
        )

        def _adj(base: float, impact_pct: float, lever: float = 1.0) -> float:
            return round(
                base * (1 + impact_pct / 100 * lever) * (1 + rng.uniform(-0.05, 0.05)),
                2,
            )

        # Revenue
        rev_1_5c = _adj(revenue_m, mult["1_5c_impact_pct"])
        rev_2c = _adj(revenue_m, mult["2c_impact_pct"])
        rev_3c = _adj(revenue_m, mult["3c_impact_pct"])

        # EBITDA (carbon provision + CapEx drag applied before scenario)
        ebitda_base = ebitda_m - carbon_provision_m - climate_capex_annual_m * 0.15
        ebitda_1_5c = _adj(ebitda_base, mult["1_5c_impact_pct"], lever=1.30)
        ebitda_2c = _adj(ebitda_base, mult["2c_impact_pct"], lever=1.30)
        ebitda_3c = _adj(ebitda_base, mult["3c_impact_pct"], lever=1.30)

        # PAT
        pat_1_5c = _adj(pat_m, mult["1_5c_impact_pct"], lever=1.80)
        pat_2c = _adj(pat_m, mult["2c_impact_pct"], lever=1.80)
        pat_3c = _adj(pat_m, mult["3c_impact_pct"], lever=1.80)

        ebitda_impact_pct_2c = round(
            (ebitda_2c - ebitda_m) / max(abs(ebitda_m), 1) * 100, 2
        )

        scenario_table = [
            {
                "scenario": "1.5°C — Net Zero 2050 (orderly)",
                "temp_rise_c": 1.5,
                "revenue_m": rev_1_5c,
                "ebitda_m": ebitda_1_5c,
                "pat_m": pat_1_5c,
                "revenue_impact_pct": round(mult["1_5c_impact_pct"], 1),
                "ebitda_impact_pct": round((ebitda_1_5c - ebitda_m) / max(abs(ebitda_m), 1) * 100, 2),
                "primary_risk": "Transition (high carbon cost, demand shift, rapid decarbonisation)",
                "ngfs_scenario_reference": "net_zero_2050",
            },
            {
                "scenario": "2°C — Below 2°C / Delayed Transition (disorderly)",
                "temp_rise_c": 2.0,
                "revenue_m": rev_2c,
                "ebitda_m": ebitda_2c,
                "pat_m": pat_2c,
                "revenue_impact_pct": round(mult["2c_impact_pct"], 1),
                "ebitda_impact_pct": round((ebitda_2c - ebitda_m) / max(abs(ebitda_m), 1) * 100, 2),
                "primary_risk": "Balanced transition and physical risk; disorderly policy response",
                "ngfs_scenario_reference": "below_2c",
            },
            {
                "scenario": "3°C — Current Policies / Hot House World",
                "temp_rise_c": 3.0,
                "revenue_m": rev_3c,
                "ebitda_m": ebitda_3c,
                "pat_m": pat_3c,
                "revenue_impact_pct": round(mult["3c_impact_pct"], 1),
                "ebitda_impact_pct": round((ebitda_3c - ebitda_m) / max(abs(ebitda_m), 1) * 100, 2),
                "primary_risk": "Physical risk dominates (NatCat, yield loss, asset damage, sea-level rise)",
                "ngfs_scenario_reference": "current_policies",
            },
        ]

        most_adverse = min(scenario_table, key=lambda s: s["ebitda_m"])

        return {
            "entity_id": entity_id,
            "sector": sector,
            "base_revenue_m": round(revenue_m, 2),
            "base_ebitda_m": round(ebitda_m, 2),
            "base_pat_m": round(pat_m, 2),
            "carbon_provision_drag_m": round(carbon_provision_m, 3),
            "climate_capex_drag_m": round(climate_capex_annual_m * 0.15, 3),
            "ebitda_impact_2c_pct": ebitda_impact_pct_2c,
            "climate_adjusted_ebitda_2c_m": ebitda_2c,
            "scenario_table": scenario_table,
            "most_adverse_scenario": most_adverse["scenario"],
            "sector_revenue_sensitivity": mult.get("revenue_sensitivity", "medium"),
            "primary_driver": mult.get("primary_driver", "N/A"),
            "standard": "IFRS S2 para 29; NGFS Phase IV 2023; IPCC AR6 WG III damage functions",
        }

    # ------------------------------------------------------------------
    # 6. Full Assessment
    # ------------------------------------------------------------------
    def run_full_assessment(self, entity_data: dict) -> dict:
        """
        Orchestrate all sub-assessments and produce consolidated E86 scores.

        Returns:
            ifrs_s2_score (0-100), climate_financial_risk_score (0-100),
            materiality_tier, disclosure_completeness_pct,
            potential_impairment_m, carbon_provision_required_m,
            stranded_asset_exposure_m, climate_adjusted_ebitda_m,
            scenario_1_5c_impact_m — plus full detail blocks.
        """
        entity_id = entity_data.get("entity_id", "unknown")
        sector = entity_data.get("sector", "industrials")
        total_assets_m = _safe_float(entity_data.get("total_assets_m", 2_000))
        ebitda_m = _safe_float(entity_data.get("ebitda_m", 200))

        # Run all sub-assessments
        ifrs_s2 = self.assess_ifrs_s2_financial_effects(entity_data)
        ias36 = self.assess_ias36_climate_impairment(entity_data)
        carbon_prov = self.calculate_carbon_provisions(entity_data)
        stranded = self.assess_stranded_assets(entity_data)

        # Feed carbon provision into adjusted financials
        entity_data_adj = dict(entity_data)
        entity_data_adj["carbon_provision_m"] = carbon_prov["total_provision_m"]
        adj_fin = self.compute_climate_adjusted_financials(entity_data_adj)

        # Top-level KPIs
        ifrs_s2_score = ifrs_s2["ifrs_s2_score"]
        disclosure_completeness_pct = ifrs_s2["disclosure_completeness_pct"]
        potential_impairment_m = ias36["total_potential_impairment_m"]
        carbon_provision_required_m = carbon_prov["total_provision_m"]
        stranded_asset_exposure_m = stranded["total_write_down_m"]
        climate_adjusted_ebitda_m = adj_fin["climate_adjusted_ebitda_2c_m"]
        scenario_1_5c_ebitda = adj_fin["scenario_table"][0]["ebitda_m"]
        scenario_1_5c_impact_m = round(scenario_1_5c_ebitda - ebitda_m, 2)

        # Climate financial risk score (0-100; higher = more risk)
        impairment_risk = _clamp(potential_impairment_m / max(total_assets_m, 1) * 400, 0, 40)
        stranded_risk = _clamp(stranded_asset_exposure_m / max(total_assets_m, 1) * 300, 0, 30)
        disclosure_gap_risk = _clamp((100 - disclosure_completeness_pct) * 0.30, 0, 30)
        climate_financial_risk_score = round(
            _clamp(impairment_risk + stranded_risk + disclosure_gap_risk), 1
        )

        materiality_tier = (
            "tier_1_material"
            if climate_financial_risk_score >= 65
            else "tier_2_potentially_material"
            if climate_financial_risk_score >= 35
            else "tier_3_immaterial"
        )

        return {
            "entity_id": entity_id,
            "sector": sector,
            # Top-level scores
            "ifrs_s2_score": ifrs_s2_score,
            "climate_financial_risk_score": climate_financial_risk_score,
            "materiality_tier": materiality_tier,
            "disclosure_completeness_pct": disclosure_completeness_pct,
            # Financial quantum
            "potential_impairment_m": potential_impairment_m,
            "carbon_provision_required_m": round(carbon_provision_required_m, 3),
            "stranded_asset_exposure_m": stranded_asset_exposure_m,
            "climate_adjusted_ebitda_m": round(climate_adjusted_ebitda_m, 2),
            "scenario_1_5c_impact_m": scenario_1_5c_impact_m,
            # Sub-assessment summaries
            "ifrs_s2_gap_count": ifrs_s2["gap_count"],
            "ias36_indicators_triggered": ias36["indicators_triggered"],
            "ias36_severity": ias36["impairment_severity"],
            "stranded_triggers_fired": stranded["triggers_fired"],
            "stranding_severity": stranded["stranding_severity"],
            "provision_required": carbon_prov["provision_required"],
            "allowance_deficit_kt": carbon_prov["allowance_deficit_kt"],
            "most_adverse_scenario": adj_fin["most_adverse_scenario"],
            # Full detail blocks
            "ifrs_s2_detail": ifrs_s2,
            "ias36_detail": ias36,
            "carbon_provision_detail": carbon_prov,
            "stranded_asset_detail": stranded,
            "climate_adjusted_financials_detail": adj_fin,
            "assessment_standards": [
                "IFRS S2 Climate-Related Disclosures (ISSB June 2023, effective 1 Jan 2024)",
                "IAS 36 Impairment of Assets — IASB Climate Guidance 2024",
                "IAS 37 Provisions — Carbon Provision Application",
                "EU ETS Directive 2003/87/EC (as amended to 2023)",
                "NGFS Phase IV Scenarios 2023",
                "IPCC AR6 WG III 2022 Damage Functions",
                "IEA Net Zero Emissions by 2050 (NZE2050)",
            ],
        }
