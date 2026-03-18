"""
EU Taxonomy Alignment Engine
==============================
Regulation (EU) 2020/852 — EU Taxonomy for Sustainable Activities

Implements the full EU Taxonomy framework including:
  * Climate Delegated Act (2021/2139) — applicable Jan 2022
  * Complementary Climate Delegated Act (2022/1214) — applicable Jan 2023
  * Environmental Delegated Act (2023/2486) — applicable Jan 2024
  * Climate DA Amendments (2023/2485) — applicable Jan 2024

Covers all 6 environmental objectives (Article 9), 80+ NACE activities across
all 4 Delegated Acts, technical screening criteria, DNSH matrix, minimum
safeguards (Article 18), KPI definitions (Article 8 / DR 2021/2178),
and financial undertaking KPIs (GAR, BTAR).

References:
  - Regulation (EU) 2020/852 (Taxonomy Regulation)
  - Commission Delegated Regulation (EU) 2021/2139 (Climate DA)
  - Commission Delegated Regulation (EU) 2022/1214 (Complementary Climate DA)
  - Commission Delegated Regulation (EU) 2023/2486 (Environmental DA)
  - Commission Delegated Regulation (EU) 2023/2485 (Climate DA Amendments)
  - Commission Delegated Regulation (EU) 2021/2178 (Article 8 Disclosures)
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional
import hashlib
import datetime

# ═══════════════════════════════════════════════════════════════════════════════
# 1. REFERENCE DATA — Environmental Objectives (Article 9)
# ═══════════════════════════════════════════════════════════════════════════════

ENVIRONMENTAL_OBJECTIVES: dict = {
    "CCM": {
        "id": "CCM", "name": "Climate Change Mitigation",
        "article": "Article 10", "description": "Substantial contribution to climate change mitigation through GHG avoidance/reduction or enhancement of GHG removals",
        "delegated_act": "Climate DA 2021/2139 Annex I",
    },
    "CCA": {
        "id": "CCA", "name": "Climate Change Adaptation",
        "article": "Article 11", "description": "Substantial contribution to climate change adaptation by reducing material physical climate risk",
        "delegated_act": "Climate DA 2021/2139 Annex II",
    },
    "WTR": {
        "id": "WTR", "name": "Sustainable Use and Protection of Water and Marine Resources",
        "article": "Article 12", "description": "Substantial contribution to sustainable use and protection of water and marine resources",
        "delegated_act": "Environmental DA 2023/2486 Annex I",
    },
    "CE": {
        "id": "CE", "name": "Transition to a Circular Economy",
        "article": "Article 13", "description": "Substantial contribution to the transition to a circular economy including waste prevention, re-use, recycling",
        "delegated_act": "Environmental DA 2023/2486 Annex II",
    },
    "POL": {
        "id": "POL", "name": "Pollution Prevention and Control",
        "article": "Article 14", "description": "Substantial contribution to pollution prevention and control",
        "delegated_act": "Environmental DA 2023/2486 Annex III",
    },
    "BIO": {
        "id": "BIO", "name": "Protection and Restoration of Biodiversity and Ecosystems",
        "article": "Article 15", "description": "Substantial contribution to the protection and restoration of biodiversity and ecosystems",
        "delegated_act": "Environmental DA 2023/2486 Annex IV",
    },
}

# ═══════════════════════════════════════════════════════════════════════════════
# 2. NACE ACTIVITIES — All 4 Delegated Acts
# ═══════════════════════════════════════════════════════════════════════════════
# Each activity: nace_code, name, sector, delegated_act_source, eligible_objectives,
# sc_thresholds (per objective), dnsh_criteria, transitional, enabling

NACE_ACTIVITIES: list[dict] = [
    # ── Climate Delegated Act 2021/2139 — Annex I (CCM) ─────────────────────
    # FORESTRY
    {"nace_code": "A1", "name": "Afforestation", "sector": "Forestry",
     "delegated_act": "Climate DA 2021/2139", "eligible_objectives": ["CCM", "CCA"],
     "sc_thresholds": {"CCM": {"type": "qualitative", "criteria": "Forest management plan, net carbon sink, sustainable forest management certification"}},
     "transitional": False, "enabling": False},
    {"nace_code": "A2", "name": "Rehabilitation and restoration of forests", "sector": "Forestry",
     "delegated_act": "Climate DA 2021/2139", "eligible_objectives": ["CCM", "CCA"],
     "sc_thresholds": {"CCM": {"type": "qualitative", "criteria": "Degraded land restoration, biodiversity-positive, carbon stock recovery plan"}},
     "transitional": False, "enabling": False},
    {"nace_code": "A3", "name": "Forest management", "sector": "Forestry",
     "delegated_act": "Climate DA 2021/2139", "eligible_objectives": ["CCM", "CCA"],
     "sc_thresholds": {"CCM": {"type": "qualitative", "criteria": "Forest management plan with carbon benefit analysis, maintained/increased carbon stocks"}},
     "transitional": False, "enabling": False},
    {"nace_code": "A4", "name": "Conservation forestry", "sector": "Forestry",
     "delegated_act": "Climate DA 2021/2139", "eligible_objectives": ["CCM", "CCA"],
     "sc_thresholds": {"CCM": {"type": "qualitative", "criteria": "Area maintained as forest, biodiversity conservation, natural disturbance resilience"}},
     "transitional": False, "enabling": False},

    # ENVIRONMENTAL PROTECTION & RESTORATION
    {"nace_code": "E3.6_1", "name": "Restoration of wetlands", "sector": "Environmental Protection",
     "delegated_act": "Climate DA 2021/2139", "eligible_objectives": ["CCM", "CCA"],
     "sc_thresholds": {"CCM": {"type": "qualitative", "criteria": "Wetland restoration plan, net GHG emission reduction, peatland rewetting"}},
     "transitional": False, "enabling": False},

    # MANUFACTURING
    {"nace_code": "C3.1", "name": "Manufacture of renewable energy technologies", "sector": "Manufacturing",
     "delegated_act": "Climate DA 2021/2139", "eligible_objectives": ["CCM"],
     "sc_thresholds": {"CCM": {"type": "qualitative", "criteria": "Manufacturing wind, solar PV, solar thermal, geothermal, heat pump, ocean energy technologies"}},
     "transitional": False, "enabling": True},
    {"nace_code": "C3.2", "name": "Manufacture of equipment for hydrogen production", "sector": "Manufacturing",
     "delegated_act": "Climate DA 2021/2139", "eligible_objectives": ["CCM"],
     "sc_thresholds": {"CCM": {"type": "qualitative", "criteria": "Manufacture of electrolysers and hydrogen production equipment"}},
     "transitional": False, "enabling": True},
    {"nace_code": "C3.3", "name": "Manufacture of low carbon transport technologies", "sector": "Manufacturing",
     "delegated_act": "Climate DA 2021/2139", "eligible_objectives": ["CCM"],
     "sc_thresholds": {"CCM": {"type": "quantitative", "threshold": 0, "unit": "gCO2/km (tailpipe)", "criteria": "Zero direct CO2 emissions for passenger cars and light commercial vehicles (0 gCO2/km)"}},
     "transitional": False, "enabling": True},
    {"nace_code": "C3.4", "name": "Manufacture of batteries", "sector": "Manufacturing",
     "delegated_act": "Climate DA 2021/2139", "eligible_objectives": ["CCM"],
     "sc_thresholds": {"CCM": {"type": "qualitative", "criteria": "Manufacture of rechargeable batteries, battery packs and accumulators for transport, stationary and off-grid energy storage"}},
     "transitional": False, "enabling": True},
    {"nace_code": "C3.5", "name": "Manufacture of energy efficiency equipment for buildings", "sector": "Manufacturing",
     "delegated_act": "Climate DA 2021/2139", "eligible_objectives": ["CCM"],
     "sc_thresholds": {"CCM": {"type": "qualitative", "criteria": "Windows, doors, wall systems, insulation, roofing, heating/cooling systems, domestic hot water"}},
     "transitional": False, "enabling": True},
    {"nace_code": "C3.6", "name": "Manufacture of other low carbon technologies", "sector": "Manufacturing",
     "delegated_act": "Climate DA 2021/2139", "eligible_objectives": ["CCM"],
     "sc_thresholds": {"CCM": {"type": "qualitative", "criteria": "Technologies aimed at substantial GHG reduction in other sectors, lifecycle GHG savings demonstrated"}},
     "transitional": False, "enabling": True},
    {"nace_code": "C20", "name": "Manufacture of hydrogen", "sector": "Manufacturing",
     "delegated_act": "Climate DA 2021/2139", "eligible_objectives": ["CCM"],
     "sc_thresholds": {"CCM": {"type": "quantitative", "threshold": 3.0, "unit": "tCO2e/tH2", "criteria": "Life cycle GHG emissions below 3 tCO2e per tonne of hydrogen"}},
     "transitional": False, "enabling": False},
    {"nace_code": "C23.5.1", "name": "Manufacture of cement", "sector": "Manufacturing",
     "delegated_act": "Climate DA 2021/2139", "eligible_objectives": ["CCM"],
     "sc_thresholds": {"CCM": {"type": "quantitative", "threshold": 0.498, "unit": "tCO2/t clinker", "criteria": "Specific GHG emissions <= 0.498 tCO2/t clinker (grey) or 0.469 tCO2/t cement-equivalent for other cements"}},
     "transitional": True, "enabling": False},
    {"nace_code": "C24.1", "name": "Manufacture of iron and steel", "sector": "Manufacturing",
     "delegated_act": "Climate DA 2021/2139", "eligible_objectives": ["CCM"],
     "sc_thresholds": {"CCM": {"type": "quantitative", "threshold": 1.331, "unit": "tCO2e/t product", "criteria": "GHG <= 1.331 tCO2e/t hot metal (integrated) or 0.266 tCO2e/t EAF steel"}},
     "transitional": True, "enabling": False},
    {"nace_code": "C24.2", "name": "Manufacture of aluminium", "sector": "Manufacturing",
     "delegated_act": "Climate DA 2021/2139", "eligible_objectives": ["CCM"],
     "sc_thresholds": {"CCM": {"type": "quantitative", "threshold": 1.514, "unit": "tCO2e/t Al", "criteria": "GHG emissions <= 1.514 tCO2e/t aluminium (primary production)"}},
     "transitional": True, "enabling": False},
    {"nace_code": "C23.1", "name": "Manufacture of glass", "sector": "Manufacturing",
     "delegated_act": "Climate DA Amendments 2023/2485", "eligible_objectives": ["CCM"],
     "sc_thresholds": {"CCM": {"type": "quantitative", "threshold": 0.7, "unit": "tCO2e/t melted glass", "criteria": "GHG emissions <= 0.7 tCO2e per tonne melted glass"}},
     "transitional": True, "enabling": False},
    {"nace_code": "C23.2", "name": "Manufacture of refractory products", "sector": "Manufacturing",
     "delegated_act": "Climate DA Amendments 2023/2485", "eligible_objectives": ["CCM"],
     "sc_thresholds": {"CCM": {"type": "quantitative", "threshold": 0.3, "unit": "tCO2e/t product", "criteria": "GHG emissions specific threshold by product type"}},
     "transitional": True, "enabling": False},
    {"nace_code": "C23.3", "name": "Manufacture of ceramic products", "sector": "Manufacturing",
     "delegated_act": "Climate DA Amendments 2023/2485", "eligible_objectives": ["CCM"],
     "sc_thresholds": {"CCM": {"type": "quantitative", "threshold": 0.25, "unit": "tCO2e/t fired product", "criteria": "GHG emissions per tonne fired product"}},
     "transitional": True, "enabling": False},
    {"nace_code": "C17", "name": "Manufacture of paper and cardboard", "sector": "Manufacturing",
     "delegated_act": "Climate DA Amendments 2023/2485", "eligible_objectives": ["CCM"],
     "sc_thresholds": {"CCM": {"type": "quantitative", "threshold": 0.6, "unit": "tCO2e/t", "criteria": "GHG emissions from pulp and paper production"}},
     "transitional": True, "enabling": False},
    {"nace_code": "C25", "name": "Manufacture of carbon black", "sector": "Manufacturing",
     "delegated_act": "Climate DA Amendments 2023/2485", "eligible_objectives": ["CCM"],
     "sc_thresholds": {"CCM": {"type": "quantitative", "threshold": 1.8, "unit": "tCO2e/t", "criteria": "Specific GHG emission benchmark for carbon black"}},
     "transitional": True, "enabling": False},
    {"nace_code": "C20.1", "name": "Manufacture of basic organic chemicals", "sector": "Manufacturing",
     "delegated_act": "Climate DA 2021/2139", "eligible_objectives": ["CCM"],
     "sc_thresholds": {"CCM": {"type": "quantitative", "threshold": 0.0, "unit": "varies by chemical", "criteria": "GHG below relevant EU ETS benchmark per product"}},
     "transitional": True, "enabling": False},
    {"nace_code": "C20.2", "name": "Manufacture of plastics in primary form", "sector": "Manufacturing",
     "delegated_act": "Climate DA 2021/2139", "eligible_objectives": ["CCM"],
     "sc_thresholds": {"CCM": {"type": "qualitative", "criteria": "Chemical recycling or feedstock from non-fossil origin, lifecycle GHG reduction vs fossil incumbent"}},
     "transitional": False, "enabling": False},

    # ENERGY — ELECTRICITY GENERATION
    {"nace_code": "D35.11_solar", "name": "Electricity generation from solar PV", "sector": "Energy",
     "delegated_act": "Climate DA 2021/2139", "eligible_objectives": ["CCM"],
     "sc_thresholds": {"CCM": {"type": "quantitative", "threshold": 100, "unit": "gCO2e/kWh", "criteria": "Lifecycle GHG emissions < 100 gCO2e/kWh (solar easily qualifies at ~20-50 gCO2e/kWh)"}},
     "transitional": False, "enabling": False},
    {"nace_code": "D35.11_wind", "name": "Electricity generation from wind power", "sector": "Energy",
     "delegated_act": "Climate DA 2021/2139", "eligible_objectives": ["CCM"],
     "sc_thresholds": {"CCM": {"type": "quantitative", "threshold": 100, "unit": "gCO2e/kWh", "criteria": "Lifecycle GHG emissions < 100 gCO2e/kWh (onshore ~7-15, offshore ~12-23 gCO2e/kWh)"}},
     "transitional": False, "enabling": False},
    {"nace_code": "D35.11_hydro", "name": "Electricity generation from hydropower", "sector": "Energy",
     "delegated_act": "Climate DA 2021/2139", "eligible_objectives": ["CCM"],
     "sc_thresholds": {"CCM": {"type": "quantitative", "threshold": 100, "unit": "gCO2e/kWh", "criteria": "Lifecycle GHG < 100 gCO2e/kWh; for power density >5 W/m2 or reservoir <0.01 tCO2e/GWh/yr"}},
     "transitional": False, "enabling": False},
    {"nace_code": "D35.11_ocean", "name": "Electricity generation from ocean energy", "sector": "Energy",
     "delegated_act": "Climate DA 2021/2139", "eligible_objectives": ["CCM"],
     "sc_thresholds": {"CCM": {"type": "quantitative", "threshold": 100, "unit": "gCO2e/kWh", "criteria": "Lifecycle GHG < 100 gCO2e/kWh, tidal/wave/OTEC"}},
     "transitional": False, "enabling": False},
    {"nace_code": "D35.11_geo", "name": "Electricity generation from geothermal", "sector": "Energy",
     "delegated_act": "Climate DA 2021/2139", "eligible_objectives": ["CCM"],
     "sc_thresholds": {"CCM": {"type": "quantitative", "threshold": 100, "unit": "gCO2e/kWh", "criteria": "Lifecycle GHG < 100 gCO2e/kWh"}},
     "transitional": False, "enabling": False},
    {"nace_code": "D35.11_bio", "name": "Electricity generation from bioenergy", "sector": "Energy",
     "delegated_act": "Climate DA 2021/2139", "eligible_objectives": ["CCM"],
     "sc_thresholds": {"CCM": {"type": "quantitative", "threshold": 100, "unit": "gCO2e/kWh", "criteria": "Lifecycle GHG < 100 gCO2e/kWh; RED II sustainability criteria; no food/feed crop feedstock"}},
     "transitional": False, "enabling": False},

    # Complementary Climate DA 2022/1214 — Nuclear and Gas
    {"nace_code": "D35.11_nuclear", "name": "Electricity generation from nuclear energy", "sector": "Energy",
     "delegated_act": "Complementary Climate DA 2022/1214", "eligible_objectives": ["CCM"],
     "sc_thresholds": {"CCM": {"type": "quantitative", "threshold": 100, "unit": "gCO2e/kWh", "criteria": "Lifecycle GHG < 100 gCO2e/kWh; construction permit before 2045; accident-tolerant fuel by 2025; Gen III+ technology; radioactive waste management plan; decommissioning fund"}},
     "transitional": True, "enabling": False},
    {"nace_code": "D35.11_gas", "name": "Electricity generation from fossil gaseous fuels", "sector": "Energy",
     "delegated_act": "Complementary Climate DA 2022/1214", "eligible_objectives": ["CCM"],
     "sc_thresholds": {"CCM": {"type": "quantitative", "threshold": 270, "unit": "gCO2e/kWh OR 550 kgCO2e/kW avg 20yr", "criteria": "Direct emissions <270 gCO2e/kWh OR lifecycle <550 kgCO2e/kW annual avg over 20 years; replaces coal/oil; 100% renewable/low-carbon gas by 2035; construction permit before 2030"}},
     "transitional": True, "enabling": False},
    {"nace_code": "D35.11_chp_gas", "name": "High-efficiency CHP from fossil gaseous fuels", "sector": "Energy",
     "delegated_act": "Complementary Climate DA 2022/1214", "eligible_objectives": ["CCM"],
     "sc_thresholds": {"CCM": {"type": "quantitative", "threshold": 270, "unit": "gCO2e/kWh", "criteria": "Direct emissions < 270 gCO2e/kWh; high-efficiency CHP as per Directive 2012/27/EU; construction permit before 2030; switch to renewable gas by 2035"}},
     "transitional": True, "enabling": False},

    # ENERGY — HEAT, STORAGE, GRIDS
    {"nace_code": "D35.30_heat", "name": "Cogeneration of heat/cool and power from solar/geothermal", "sector": "Energy",
     "delegated_act": "Climate DA 2021/2139", "eligible_objectives": ["CCM"],
     "sc_thresholds": {"CCM": {"type": "quantitative", "threshold": 100, "unit": "gCO2e/kWh", "criteria": "Lifecycle GHG < 100 gCO2e/kWh for CHP from renewable sources"}},
     "transitional": False, "enabling": False},
    {"nace_code": "D35.30_dh", "name": "District heating/cooling distribution", "sector": "Energy",
     "delegated_act": "Climate DA 2021/2139", "eligible_objectives": ["CCM", "CCA"],
     "sc_thresholds": {"CCM": {"type": "qualitative", "criteria": "System efficiency meeting Directive 2012/27/EU; connected to taxonomy-aligned heat source or >= 50% renewable/waste heat"}},
     "transitional": True, "enabling": False},
    {"nace_code": "D35_storage", "name": "Electricity storage", "sector": "Energy",
     "delegated_act": "Climate DA 2021/2139", "eligible_objectives": ["CCM"],
     "sc_thresholds": {"CCM": {"type": "qualitative", "criteria": "Pumped hydro, battery, compressed air, flywheel, hydrogen storage — no direct fossil fuel use"}},
     "transitional": False, "enabling": True},
    {"nace_code": "D35_grid", "name": "Transmission and distribution of electricity", "sector": "Energy",
     "delegated_act": "Climate DA 2021/2139", "eligible_objectives": ["CCM"],
     "sc_thresholds": {"CCM": {"type": "qualitative", "criteria": "Interconnected European system or third-country system; direct connection to taxonomy-aligned generation; smart grid infrastructure; SF6-free switchgear"}},
     "transitional": False, "enabling": True},
    {"nace_code": "D35_hp", "name": "Installation and operation of heat pumps", "sector": "Energy",
     "delegated_act": "Climate DA 2021/2139", "eligible_objectives": ["CCM"],
     "sc_thresholds": {"CCM": {"type": "quantitative", "threshold": 100, "unit": "gCO2e/kWh", "criteria": "Lifecycle GHG < 100 gCO2e/kWh; GWP of refrigerant <= 675"}},
     "transitional": False, "enabling": False},
    {"nace_code": "D35_biogas", "name": "Production of biogas and biofuels", "sector": "Energy",
     "delegated_act": "Climate DA 2021/2139", "eligible_objectives": ["CCM"],
     "sc_thresholds": {"CCM": {"type": "quantitative", "threshold": 100, "unit": "gCO2e/MJ (lifecycle)", "criteria": "Lifecycle GHG savings >= 65% vs fossil comparator per RED II; no food/feed crop feedstock"}},
     "transitional": False, "enabling": False},

    # WATER / WASTE
    {"nace_code": "E36", "name": "Water collection, treatment and supply", "sector": "Water",
     "delegated_act": "Climate DA 2021/2139", "eligible_objectives": ["CCM", "CCA", "WTR"],
     "sc_thresholds": {"CCM": {"type": "qualitative", "criteria": "Energy efficiency of water system; net energy consumption <= average for EU-27; leakage rate improvement"}},
     "transitional": False, "enabling": False},
    {"nace_code": "E37", "name": "Centralised wastewater treatment", "sector": "Water",
     "delegated_act": "Climate DA 2021/2139", "eligible_objectives": ["CCM", "CCA", "WTR"],
     "sc_thresholds": {"CCM": {"type": "qualitative", "criteria": "Energy efficiency; biogas recovery; GHG reduction vs untreated discharge; nutrient removal"}},
     "transitional": False, "enabling": False},
    {"nace_code": "E38.1", "name": "Collection and transport of non-hazardous waste", "sector": "Waste",
     "delegated_act": "Climate DA 2021/2139", "eligible_objectives": ["CCM", "CE"],
     "sc_thresholds": {"CCM": {"type": "qualitative", "criteria": "Separate collection for recycling/composting; no mixing; waste tracking system"}},
     "transitional": False, "enabling": True},
    {"nace_code": "E38.2", "name": "Anaerobic digestion of sewage sludge and bio-waste", "sector": "Waste",
     "delegated_act": "Climate DA 2021/2139", "eligible_objectives": ["CCM"],
     "sc_thresholds": {"CCM": {"type": "qualitative", "criteria": "Biogas capture and use for energy; digestate quality meeting fertiliser standards; methane leakage monitoring"}},
     "transitional": False, "enabling": False},
    {"nace_code": "E38.3", "name": "Composting of bio-waste", "sector": "Waste",
     "delegated_act": "Climate DA 2021/2139", "eligible_objectives": ["CCM", "CE"],
     "sc_thresholds": {"CCM": {"type": "qualitative", "criteria": "Source-separated bio-waste; enclosed composting; output meeting EU fertiliser standards"}},
     "transitional": False, "enabling": False},
    {"nace_code": "E39_ccs", "name": "Carbon capture and storage (CCS)", "sector": "Waste",
     "delegated_act": "Climate DA 2021/2139", "eligible_objectives": ["CCM"],
     "sc_thresholds": {"CCM": {"type": "qualitative", "criteria": "CO2 transport and permanent geological storage; monitoring plan; >90% capture rate; Directive 2009/31/EC compliant"}},
     "transitional": False, "enabling": True},
    {"nace_code": "E39_ccu", "name": "Carbon capture and utilisation (CCU)", "sector": "Waste",
     "delegated_act": "Climate DA Amendments 2023/2485", "eligible_objectives": ["CCM"],
     "sc_thresholds": {"CCM": {"type": "qualitative", "criteria": "Net GHG reduction over lifecycle; CO2 permanently bound or long-duration storage; not used for enhanced fossil fuel recovery"}},
     "transitional": False, "enabling": True},
    {"nace_code": "E39_dac", "name": "Direct air capture of CO2", "sector": "Waste",
     "delegated_act": "Climate DA Amendments 2023/2485", "eligible_objectives": ["CCM"],
     "sc_thresholds": {"CCM": {"type": "qualitative", "criteria": "Powered by renewable/low-carbon energy; permanently stored or used in long-lived product; net-negative lifecycle emissions"}},
     "transitional": False, "enabling": False},

    # TRANSPORT
    {"nace_code": "H49.10", "name": "Passenger interurban rail transport", "sector": "Transport",
     "delegated_act": "Climate DA 2021/2139", "eligible_objectives": ["CCM"],
     "sc_thresholds": {"CCM": {"type": "quantitative", "threshold": 0, "unit": "gCO2/p-km (direct)", "criteria": "Zero direct (tailpipe) CO2 emissions"}},
     "transitional": False, "enabling": False},
    {"nace_code": "H49.20", "name": "Freight rail transport", "sector": "Transport",
     "delegated_act": "Climate DA 2021/2139", "eligible_objectives": ["CCM"],
     "sc_thresholds": {"CCM": {"type": "quantitative", "threshold": 0, "unit": "gCO2/t-km (direct)", "criteria": "Zero direct (tailpipe) CO2 emissions; or trains with <= 50% fossil fuel use on non-electrified lines"}},
     "transitional": False, "enabling": False},
    {"nace_code": "H49.3", "name": "Urban and suburban passenger land transport", "sector": "Transport",
     "delegated_act": "Climate DA 2021/2139", "eligible_objectives": ["CCM"],
     "sc_thresholds": {"CCM": {"type": "quantitative", "threshold": 0, "unit": "gCO2/vehicle-km (tailpipe)", "criteria": "Zero direct CO2 emissions (electric buses, trams, metro); or below 50g CO2/p-km for diesel/CNG until 2025"}},
     "transitional": False, "enabling": False},
    {"nace_code": "H49.4", "name": "Freight transport by road", "sector": "Transport",
     "delegated_act": "Climate DA 2021/2139", "eligible_objectives": ["CCM"],
     "sc_thresholds": {"CCM": {"type": "quantitative", "threshold": 0, "unit": "gCO2/t-km (tailpipe)", "criteria": "Zero direct CO2 emissions for vehicles in categories N1/N2/N3; transitional for heavy-duty Euro VI+"}},
     "transitional": False, "enabling": False},
    {"nace_code": "H50_sea", "name": "Sea and coastal passenger/freight water transport", "sector": "Transport",
     "delegated_act": "Climate DA 2021/2139", "eligible_objectives": ["CCM"],
     "sc_thresholds": {"CCM": {"type": "quantitative", "threshold": 0, "unit": "gCO2/t-km (direct)", "criteria": "Zero direct CO2 emissions; OR hybrid/dual-fuel vessels with >= 25% reduction vs IMO EEDI reference; OR vessels with EEDI 10% below IMO requirement"}},
     "transitional": True, "enabling": False},
    {"nace_code": "H50_iw", "name": "Inland passenger/freight water transport", "sector": "Transport",
     "delegated_act": "Climate DA 2021/2139", "eligible_objectives": ["CCM"],
     "sc_thresholds": {"CCM": {"type": "quantitative", "threshold": 0, "unit": "gCO2/t-km (direct)", "criteria": "Zero direct CO2 emissions; or 50% lower emissions than inland waterway reference"}},
     "transitional": True, "enabling": False},
    {"nace_code": "H51", "name": "Passenger and freight air transport", "sector": "Transport",
     "delegated_act": "Climate DA Amendments 2023/2485", "eligible_objectives": ["CCM"],
     "sc_thresholds": {"CCM": {"type": "quantitative", "threshold": 0, "unit": "gCO2/p-km or /t-km", "criteria": "Zero direct CO2 emissions aircraft; or SAF usage >= 10%; transitional pathway to low-carbon aviation fuels"}},
     "transitional": True, "enabling": False},
    {"nace_code": "H_infra_road", "name": "Infrastructure for low-carbon road transport", "sector": "Transport",
     "delegated_act": "Climate DA 2021/2139", "eligible_objectives": ["CCM"],
     "sc_thresholds": {"CCM": {"type": "qualitative", "criteria": "EV charging infrastructure, hydrogen refuelling, dedicated cycling/pedestrian infrastructure"}},
     "transitional": False, "enabling": True},
    {"nace_code": "H_infra_rail", "name": "Infrastructure for rail transport", "sector": "Transport",
     "delegated_act": "Climate DA 2021/2139", "eligible_objectives": ["CCM"],
     "sc_thresholds": {"CCM": {"type": "qualitative", "criteria": "Electrified rail infrastructure; not dedicated to fossil fuel transport"}},
     "transitional": False, "enabling": True},
    {"nace_code": "H_infra_water", "name": "Infrastructure for water transport", "sector": "Transport",
     "delegated_act": "Climate DA 2021/2139", "eligible_objectives": ["CCM"],
     "sc_thresholds": {"CCM": {"type": "qualitative", "criteria": "Port infrastructure for zero-emission vessels; shore-side electricity; LNG bunkering"}},
     "transitional": False, "enabling": True},
    {"nace_code": "H_cycling", "name": "Infrastructure for personal mobility and cycling", "sector": "Transport",
     "delegated_act": "Climate DA 2021/2139", "eligible_objectives": ["CCM"],
     "sc_thresholds": {"CCM": {"type": "qualitative", "criteria": "Dedicated cycling lanes, bike-sharing infrastructure, pedestrianisation projects"}},
     "transitional": False, "enabling": True},

    # CONSTRUCTION & REAL ESTATE
    {"nace_code": "F41.1", "name": "Construction of new buildings", "sector": "Construction",
     "delegated_act": "Climate DA 2021/2139", "eligible_objectives": ["CCM", "CCA"],
     "sc_thresholds": {"CCM": {"type": "quantitative", "threshold": 10, "unit": "% below NZEB (kWh/m2/yr)", "criteria": "Primary energy demand at least 10% below NZEB threshold; air-tightness and thermal-bridge testing; lifecycle GWP for buildings >5000m2"}},
     "transitional": False, "enabling": False},
    {"nace_code": "F41.2", "name": "Renovation of existing buildings", "sector": "Construction",
     "delegated_act": "Climate DA 2021/2139", "eligible_objectives": ["CCM", "CCA"],
     "sc_thresholds": {"CCM": {"type": "quantitative", "threshold": 30, "unit": "% primary energy reduction", "criteria": "Major renovation achieving >= 30% reduction in primary energy demand; or individual measures meeting component-level requirements"}},
     "transitional": False, "enabling": False},
    {"nace_code": "F42_infra", "name": "Infrastructure for climate change adaptation", "sector": "Construction",
     "delegated_act": "Climate DA 2021/2139", "eligible_objectives": ["CCA"],
     "sc_thresholds": {"CCA": {"type": "qualitative", "criteria": "Climate risk assessment per RCP 8.5; adaptation solutions implemented; physical resilience demonstrated"}},
     "transitional": False, "enabling": False},
    {"nace_code": "F43_ee", "name": "Installation of energy efficiency equipment", "sector": "Construction",
     "delegated_act": "Climate DA 2021/2139", "eligible_objectives": ["CCM"],
     "sc_thresholds": {"CCM": {"type": "qualitative", "criteria": "Installation of insulation, windows, heating/cooling systems, lighting meeting top energy class requirements"}},
     "transitional": False, "enabling": True},
    {"nace_code": "F43_ev", "name": "Installation of EV charging stations", "sector": "Construction",
     "delegated_act": "Climate DA 2021/2139", "eligible_objectives": ["CCM"],
     "sc_thresholds": {"CCM": {"type": "qualitative", "criteria": "Installation of EV charging stations in buildings or associated parking areas"}},
     "transitional": False, "enabling": True},
    {"nace_code": "F43_re", "name": "Installation of renewable energy technologies", "sector": "Construction",
     "delegated_act": "Climate DA 2021/2139", "eligible_objectives": ["CCM"],
     "sc_thresholds": {"CCM": {"type": "qualitative", "criteria": "On-site installation of solar PV, solar thermal, heat pumps, wind, geothermal"}},
     "transitional": False, "enabling": True},

    # REAL ESTATE
    {"nace_code": "L68_own", "name": "Acquisition and ownership of buildings", "sector": "Real Estate",
     "delegated_act": "Climate DA 2021/2139", "eligible_objectives": ["CCM", "CCA"],
     "sc_thresholds": {"CCM": {"type": "quantitative", "threshold": 0, "unit": "EPC class", "criteria": "EPC class A; or top 15% national/regional building stock; or for pre-2021 buildings within top 15% after renovation"}},
     "transitional": False, "enabling": False},

    # ICT
    {"nace_code": "J61", "name": "Telecommunications", "sector": "ICT",
     "delegated_act": "Climate DA Amendments 2023/2485", "eligible_objectives": ["CCM"],
     "sc_thresholds": {"CCM": {"type": "qualitative", "criteria": "Network infrastructure supporting >50% renewable energy; energy-efficient equipment; waste heat recovery"}},
     "transitional": False, "enabling": True},
    {"nace_code": "J62_63", "name": "Computer programming, data hosting, and data-driven solutions", "sector": "ICT",
     "delegated_act": "Climate DA 2021/2139", "eligible_objectives": ["CCM"],
     "sc_thresholds": {"CCM": {"type": "qualitative", "criteria": "Data centre PUE <= 1.5 (new) or 1.4 (existing after renovation); EU Code of Conduct on Data Centre Energy Efficiency; waste heat recovery policy; water consumption efficiency (WUE)"}},
     "transitional": False, "enabling": True},

    # RESEARCH & DEVELOPMENT
    {"nace_code": "M72", "name": "Research, development and innovation for direct air capture", "sector": "Research",
     "delegated_act": "Climate DA Amendments 2023/2485", "eligible_objectives": ["CCM"],
     "sc_thresholds": {"CCM": {"type": "qualitative", "criteria": "R&D for CO2 removal technologies, negative emission solutions, or climate mitigation breakthrough technologies"}},
     "transitional": False, "enabling": True},

    # FINANCE — Complementary Climate DA
    {"nace_code": "K64_nuclear", "name": "Pre-commercial stages of advanced nuclear technologies", "sector": "Finance",
     "delegated_act": "Complementary Climate DA 2022/1214", "eligible_objectives": ["CCM"],
     "sc_thresholds": {"CCM": {"type": "qualitative", "criteria": "Research and development of Generation IV and SMR nuclear technologies; accident-tolerant fuel research; fusion energy development"}},
     "transitional": False, "enabling": True},

    # ── Environmental Delegated Act 2023/2486 ──────────────────────────────
    # WATER (WTR)
    {"nace_code": "WTR_5.1", "name": "Construction, extension and operation of water collection", "sector": "Water",
     "delegated_act": "Environmental DA 2023/2486", "eligible_objectives": ["WTR"],
     "sc_thresholds": {"WTR": {"type": "qualitative", "criteria": "Water supply efficiency; non-revenue water < 20%; WFD good ecological status; water efficiency measures"}},
     "transitional": False, "enabling": False},
    {"nace_code": "WTR_5.2", "name": "Water treatment", "sector": "Water",
     "delegated_act": "Environmental DA 2023/2486", "eligible_objectives": ["WTR"],
     "sc_thresholds": {"WTR": {"type": "qualitative", "criteria": "Advanced treatment technologies; nutrient recovery; energy-neutral or -positive treatment; sludge management"}},
     "transitional": False, "enabling": False},
    {"nace_code": "WTR_5.3", "name": "Sustainable urban drainage systems (SuDS)", "sector": "Water",
     "delegated_act": "Environmental DA 2023/2486", "eligible_objectives": ["WTR", "CCA"],
     "sc_thresholds": {"WTR": {"type": "qualitative", "criteria": "Permeable surfaces, bioretention, constructed wetlands, rainwater harvesting, flood risk reduction"}},
     "transitional": False, "enabling": False},

    # CIRCULAR ECONOMY (CE)
    {"nace_code": "CE_1.1", "name": "Manufacture of plastic packaging goods using recycled content", "sector": "Manufacturing",
     "delegated_act": "Environmental DA 2023/2486", "eligible_objectives": ["CE"],
     "sc_thresholds": {"CE": {"type": "quantitative", "threshold": 30, "unit": "% recycled content", "criteria": "Minimum 30% post-consumer recycled plastic; design for recyclability; no hazardous additives"}},
     "transitional": False, "enabling": False},
    {"nace_code": "CE_1.2", "name": "Manufacture of electrical and electronic equipment for reuse/refurbishment", "sector": "Manufacturing",
     "delegated_act": "Environmental DA 2023/2486", "eligible_objectives": ["CE"],
     "sc_thresholds": {"CE": {"type": "qualitative", "criteria": "Design for durability, repairability, upgradability; availability of spare parts for >= 7 years; product-as-a-service model"}},
     "transitional": False, "enabling": False},
    {"nace_code": "CE_2.1", "name": "Material recovery from non-hazardous waste", "sector": "Waste",
     "delegated_act": "Environmental DA 2023/2486", "eligible_objectives": ["CE"],
     "sc_thresholds": {"CE": {"type": "quantitative", "threshold": 50, "unit": "% by weight recovered", "criteria": "At least 50% of non-hazardous waste input converted to secondary raw materials; quality standards met"}},
     "transitional": False, "enabling": False},
    {"nace_code": "CE_3.1", "name": "Repair, refurbishment and remanufacturing", "sector": "Services",
     "delegated_act": "Environmental DA 2023/2486", "eligible_objectives": ["CE"],
     "sc_thresholds": {"CE": {"type": "qualitative", "criteria": "Product life extension through repair/refurb/reman; warranty on remanufactured products; quality comparable to new"}},
     "transitional": False, "enabling": False},
    {"nace_code": "CE_4.1", "name": "Sale of second-hand goods", "sector": "Services",
     "delegated_act": "Environmental DA 2023/2486", "eligible_objectives": ["CE"],
     "sc_thresholds": {"CE": {"type": "qualitative", "criteria": "Quality checks, product testing, warranty provision, marketplace platforms for used goods"}},
     "transitional": False, "enabling": False},
    {"nace_code": "CE_5.1", "name": "Product-as-a-service and sharing economy models", "sector": "Services",
     "delegated_act": "Environmental DA 2023/2486", "eligible_objectives": ["CE"],
     "sc_thresholds": {"CE": {"type": "qualitative", "criteria": "Demonstrated reduction in product volumes vs ownership model; maintenance obligation; end-of-life take-back"}},
     "transitional": False, "enabling": False},

    # POLLUTION PREVENTION (POL)
    {"nace_code": "POL_1.1", "name": "Manufacture of active pharmaceutical ingredients (API)", "sector": "Manufacturing",
     "delegated_act": "Environmental DA 2023/2486", "eligible_objectives": ["POL"],
     "sc_thresholds": {"POL": {"type": "qualitative", "criteria": "Green chemistry principles; solvent recovery >= 80%; PBT substance phase-out plan; emission treatment BAT compliance"}},
     "transitional": False, "enabling": False},
    {"nace_code": "POL_2.1", "name": "Remediation of contaminated sites and areas", "sector": "Environmental Protection",
     "delegated_act": "Environmental DA 2023/2486", "eligible_objectives": ["POL", "BIO"],
     "sc_thresholds": {"POL": {"type": "qualitative", "criteria": "Risk-based remediation; contaminant source removal; monitored natural attenuation; land restored to usable status"}},
     "transitional": False, "enabling": False},
    {"nace_code": "POL_3.1", "name": "Collection and treatment of hazardous waste", "sector": "Waste",
     "delegated_act": "Environmental DA 2023/2486", "eligible_objectives": ["POL"],
     "sc_thresholds": {"POL": {"type": "qualitative", "criteria": "BAT compliance; PFAS-free treatment; mercury/POPs destruction; residue management; worker protection"}},
     "transitional": False, "enabling": False},

    # BIODIVERSITY (BIO)
    {"nace_code": "BIO_1.1", "name": "Conservation including restoration of habitats and ecosystems", "sector": "Environmental Protection",
     "delegated_act": "Environmental DA 2023/2486", "eligible_objectives": ["BIO"],
     "sc_thresholds": {"BIO": {"type": "qualitative", "criteria": "Habitat restoration per Natura 2000 or national equivalent; species recovery; invasive species management; connectivity improvement"}},
     "transitional": False, "enabling": False},
    {"nace_code": "BIO_1.2", "name": "Nature-based solutions for flood and erosion prevention", "sector": "Environmental Protection",
     "delegated_act": "Environmental DA 2023/2486", "eligible_objectives": ["BIO", "CCA"],
     "sc_thresholds": {"BIO": {"type": "qualitative", "criteria": "Natural flood management; riparian buffer zones; green infrastructure; biodiversity net gain demonstration"}},
     "transitional": False, "enabling": False},
    {"nace_code": "BIO_2.1", "name": "Accommodation and food service activities for ecotourism", "sector": "Tourism",
     "delegated_act": "Environmental DA 2023/2486", "eligible_objectives": ["BIO"],
     "sc_thresholds": {"BIO": {"type": "qualitative", "criteria": "GSTC criteria compliance; biodiversity monitoring programme; no habitat degradation; community engagement"}},
     "transitional": False, "enabling": False},
]

# ═══════════════════════════════════════════════════════════════════════════════
# 3. DNSH CROSS-CHECK MATRIX (6×6)
# ═══════════════════════════════════════════════════════════════════════════════

DNSH_MATRIX: dict = {
    "CCM": {
        "CCA": "Climate risk assessment per RCP 8.5/4.5; physical risk adaptation measures",
        "WTR": "Water Framework Directive compliance; no deterioration of water status; Environmental Impact Assessment",
        "CE": "Waste hierarchy compliance; circular design; no planned obsolescence",
        "POL": "IED BAT compliance; REACH regulation; no POPs/mercury release; air quality standards",
        "BIO": "Environmental Impact Assessment; no conversion of high-biodiversity land; Natura 2000 protection",
    },
    "CCA": {
        "CCM": "No significant GHG increase; no lock-in of carbon-intensive assets",
        "WTR": "Water resource protection in adaptation measures; no water quality degradation",
        "CE": "Adaptation materials meet circularity criteria; no unnecessary waste generation",
        "POL": "No pollution increase from adaptation infrastructure; soil protection",
        "BIO": "Nature-based solutions preferred; no biodiversity harm from grey infrastructure",
    },
    "WTR": {
        "CCM": "Energy efficiency in water treatment; renewable energy use",
        "CCA": "Climate-resilient water infrastructure; drought contingency planning",
        "CE": "Water reuse and recycling; nutrient recovery from wastewater",
        "POL": "Effluent quality standards; no micropollutant discharge; sludge management",
        "BIO": "Ecological flow maintenance; fish passage; riparian habitat protection",
    },
    "CE": {
        "CCM": "Net lifecycle GHG reduction vs linear model; no increased transport emissions",
        "CCA": "Material resilience to climate impacts; supply chain climate risk",
        "WTR": "Water efficiency in recycling processes; no water contamination from recycled materials",
        "POL": "No hazardous substance dispersion through recycling; clean material streams",
        "BIO": "No increased resource extraction pressure; sustainable sourcing of virgin content",
    },
    "POL": {
        "CCM": "No GHG increase from pollution control measures; energy-efficient treatment",
        "CCA": "Resilience of pollution control infrastructure to climate impacts",
        "WTR": "No transfer of pollution to water bodies; effluent treatment",
        "CE": "Waste minimisation from remediation; secondary material recovery",
        "BIO": "Remediation supports ecosystem recovery; no ecological disruption",
    },
    "BIO": {
        "CCM": "Carbon stock maintenance; no deforestation; no peat drainage",
        "CCA": "Ecosystem-based adaptation; natural resilience maintenance",
        "WTR": "Watershed protection; natural water purification maintenance",
        "CE": "Sustainable biomass use; no overexploitation of biological resources",
        "POL": "No pesticide/herbicide use exceeding thresholds; integrated pest management",
    },
}

# ═══════════════════════════════════════════════════════════════════════════════
# 4. MINIMUM SAFEGUARDS (Article 18)
# ═══════════════════════════════════════════════════════════════════════════════

MINIMUM_SAFEGUARDS: dict = {
    "frameworks": [
        {"name": "OECD Guidelines for Multinational Enterprises on Responsible Business Conduct",
         "version": "2023 update", "requirements": ["Human rights due diligence", "Anti-corruption policies", "Environmental responsibility", "Consumer interests", "Science and technology", "Competition", "Taxation"]},
        {"name": "UN Guiding Principles on Business and Human Rights",
         "version": "2011", "requirements": ["Policy commitment", "Human rights due diligence", "Remediation mechanisms", "State duty to protect", "Corporate responsibility to respect"]},
        {"name": "ILO Declaration on Fundamental Principles and Rights at Work",
         "version": "2022 amended", "core_conventions": [
             "C087 Freedom of Association", "C098 Right to Organise and Collective Bargaining",
             "C029 Forced Labour", "C105 Abolition of Forced Labour",
             "C138 Minimum Age", "C182 Worst Forms of Child Labour",
             "C100 Equal Remuneration", "C111 Discrimination (Employment and Occupation)",
             "C155 Occupational Safety and Health", "C187 Promotional Framework for OSH"]},
        {"name": "International Bill of Human Rights",
         "components": ["Universal Declaration of Human Rights (1948)", "ICCPR (1966)", "ICESCR (1966)"]},
    ],
    "assessment_areas": [
        {"area": "human_rights", "weight": 0.30, "indicators": ["HR policy", "HR due diligence", "Remediation process", "No forced/child labour"]},
        {"area": "labour", "weight": 0.25, "indicators": ["Freedom of association", "Collective bargaining", "Non-discrimination", "OSH standards"]},
        {"area": "anti_corruption", "weight": 0.20, "indicators": ["Anti-bribery policy", "Whistleblower protection", "Training programme", "Third-party due diligence"]},
        {"area": "taxation", "weight": 0.15, "indicators": ["Tax governance", "Country-by-country reporting", "No aggressive tax planning"]},
        {"area": "fair_competition", "weight": 0.10, "indicators": ["Competition compliance", "No cartel behaviour", "Fair dealing"]},
    ],
}

# ═══════════════════════════════════════════════════════════════════════════════
# 5. KPI DEFINITIONS — Article 8 / DR 2021/2178
# ═══════════════════════════════════════════════════════════════════════════════

KPI_DEFINITIONS: dict = {
    "turnover": {
        "name": "Turnover KPI", "article": "Article 8(2)(a)",
        "numerator": "Revenue from taxonomy-aligned activities",
        "denominator": "Total net revenue per IAS 1.82(a)",
        "notes": "Revenue from products/services associated with taxonomy-aligned economic activities; double-counting prevention per objective",
    },
    "capex": {
        "name": "CapEx KPI", "article": "Article 8(2)(b)",
        "numerator": "Capital expenditure on taxonomy-aligned activities + CapEx plans",
        "denominator": "Total CapEx per IAS 16, 38, 40 and IFRS 16",
        "notes": "Includes CapEx plans: expenditures aimed at expanding or making taxonomy-aligned activities within 5-year plan; must have specific timeline",
    },
    "opex": {
        "name": "OpEx KPI", "article": "Article 8(2)(c)",
        "numerator": "Operating expenditure on taxonomy-aligned activities",
        "denominator": "Total direct non-capitalised costs (R&D, building renovation, short-term lease, maintenance, repair, day-to-day servicing)",
        "notes": "Narrower OpEx definition than IFRS; specific categories only; materiality exemption if denominator < EUR 1M",
    },
}

FINANCIAL_KPI_DEFINITIONS: dict = {
    "gar": {
        "name": "Green Asset Ratio (GAR)", "applicable_to": "Credit institutions (CRR)",
        "numerator": "Taxonomy-aligned exposures in banking book",
        "denominator": "Total covered assets (excluding central bank exposures, sovereign, trading book)",
        "notes": "Phase-in: 2024 eligibility only, 2025+ alignment; by objective breakdown; sector breakdown",
    },
    "btar": {
        "name": "Banking Book Taxonomy Alignment Ratio (BTAR)",
        "applicable_to": "Credit institutions (voluntary)",
        "numerator": "Banking book assets financing taxonomy-aligned activities",
        "denominator": "Total banking book assets",
        "notes": "Broader denominator than GAR; includes sovereign and interbank; voluntary disclosure",
    },
    "insurance_gar": {
        "name": "Insurance Undertaking Taxonomy KPI", "applicable_to": "Insurance (Solvency II)",
        "numerator": "Taxonomy-aligned investments",
        "denominator": "Total investments (excl. sovereign and unit-linked)",
        "notes": "Includes underwriting KPI for non-life; by objective breakdown",
    },
    "asset_manager_kpi": {
        "name": "Asset Manager Taxonomy KPI", "applicable_to": "Asset managers (UCITS/AIF)",
        "numerator": "Weighted average taxonomy alignment of investees",
        "denominator": "Total AuM (by fund and at entity level)",
        "notes": "Fund-level and entity-level; SFDR Art 5/6 alignment",
    },
}

# ═══════════════════════════════════════════════════════════════════════════════
# 6. CROSS-FRAMEWORK MAPPING
# ═══════════════════════════════════════════════════════════════════════════════

CROSS_FRAMEWORK_MAP: list[dict] = [
    {"taxonomy_element": "Turnover KPI", "csrd_esrs": "ESRS 2 SBM-1, ESRS E1-1", "sfdr": "Article 5(1) / Article 6 SFDR RTS Annex III", "issb": "IFRS S2 para 29(a)", "gri": "GRI 201-1", "cdp": "C-FS14.1", "tcfd": "Metrics & Targets (b)"},
    {"taxonomy_element": "CapEx KPI", "csrd_esrs": "ESRS 2 SBM-1, ESRS E1-3", "sfdr": "Article 5(1) / Article 6 SFDR RTS Annex III", "issb": "IFRS S2 para 29(b)", "gri": "GRI 201-1", "cdp": "C-FS14.1", "tcfd": "Metrics & Targets (b)"},
    {"taxonomy_element": "OpEx KPI", "csrd_esrs": "ESRS 2 SBM-1", "sfdr": "Article 5(1) / Article 6 SFDR RTS Annex III", "issb": "IFRS S2 para 29(c)", "gri": "N/A", "cdp": "N/A", "tcfd": "N/A"},
    {"taxonomy_element": "DNSH CCM/CCA", "csrd_esrs": "ESRS E1 / ESRS E1-9/E1-10", "sfdr": "Article 2(17) SFDR", "issb": "IFRS S2 para 21-22", "gri": "GRI 305", "cdp": "C2.3-C2.4", "tcfd": "Risk Management (a)"},
    {"taxonomy_element": "DNSH WTR", "csrd_esrs": "ESRS E3", "sfdr": "PAI #8 water emissions", "issb": "IFRS S2 para 21(b)", "gri": "GRI 303", "cdp": "W1-W8", "tcfd": "N/A"},
    {"taxonomy_element": "DNSH CE", "csrd_esrs": "ESRS E5", "sfdr": "PAI #13 non-recycled waste", "issb": "N/A", "gri": "GRI 301, 306", "cdp": "N/A", "tcfd": "N/A"},
    {"taxonomy_element": "DNSH POL", "csrd_esrs": "ESRS E2", "sfdr": "PAI #1-9 various pollution", "issb": "N/A", "gri": "GRI 305.7, 306.3", "cdp": "N/A", "tcfd": "N/A"},
    {"taxonomy_element": "DNSH BIO", "csrd_esrs": "ESRS E4", "sfdr": "PAI #7 biodiversity", "issb": "N/A", "gri": "GRI 304", "cdp": "C15 (Biodiversity)", "tcfd": "N/A"},
    {"taxonomy_element": "Minimum Safeguards", "csrd_esrs": "ESRS S1, S2, S3, S4, G1", "sfdr": "PAI #10-14 social/governance", "issb": "IFRS S1 para 25", "gri": "GRI 400 series", "cdp": "C12.3", "tcfd": "Governance"},
    {"taxonomy_element": "GAR", "csrd_esrs": "ESRS 2 SBM-1 (FI)", "sfdr": "Article 5-6 Entity-level", "issb": "IFRS S2 para 29(a) FI", "gri": "GRI FS7, FS8", "cdp": "C-FS14.1", "tcfd": "Metrics FI"},
]

# ═══════════════════════════════════════════════════════════════════════════════
# 7. SECTOR THRESHOLDS (key quantitative from Climate DA)
# ═══════════════════════════════════════════════════════════════════════════════

SECTOR_THRESHOLDS: dict = {
    "electricity_generation": {"threshold": 100, "unit": "gCO2e/kWh", "basis": "lifecycle", "article": "Climate DA Annex I Section 4.1-4.8"},
    "cement": {"threshold": 0.498, "unit": "tCO2/t clinker", "basis": "direct", "article": "Climate DA Annex I Section 3.7"},
    "iron_steel": {"threshold": 1.331, "unit": "tCO2e/t hot metal", "basis": "direct", "article": "Climate DA Annex I Section 3.9"},
    "aluminium": {"threshold": 1.514, "unit": "tCO2e/t Al", "basis": "direct", "article": "Climate DA Annex I Section 3.8"},
    "hydrogen": {"threshold": 3.0, "unit": "tCO2e/tH2", "basis": "lifecycle", "article": "Climate DA Annex I Section 3.10"},
    "buildings_new": {"threshold": 10, "unit": "% below NZEB", "basis": "primary energy", "article": "Climate DA Annex I Section 7.1"},
    "buildings_renovation": {"threshold": 30, "unit": "% primary energy reduction", "basis": "primary energy", "article": "Climate DA Annex I Section 7.2"},
    "fossil_gas_electricity": {"threshold": 270, "unit": "gCO2e/kWh", "basis": "direct", "article": "Complementary Climate DA 2022/1214"},
    "passenger_cars": {"threshold": 0, "unit": "gCO2/km tailpipe", "basis": "direct", "article": "Climate DA Annex I Section 3.3"},
    "data_centres_new": {"threshold": 1.5, "unit": "PUE", "basis": "operational", "article": "Climate DA Annex I Section 8.1"},
    "data_centres_existing": {"threshold": 1.4, "unit": "PUE", "basis": "operational post-renovation", "article": "Climate DA Amendments 2023/2485"},
    "bioenergy": {"threshold": 100, "unit": "gCO2e/kWh", "basis": "lifecycle", "article": "Climate DA Annex I Section 4.8"},
    "glass": {"threshold": 0.7, "unit": "tCO2e/t melted glass", "basis": "direct", "article": "Climate DA Amendments 2023/2485"},
    "nuclear": {"threshold": 100, "unit": "gCO2e/kWh", "basis": "lifecycle", "article": "Complementary Climate DA 2022/1214"},
    "recycled_plastic_content": {"threshold": 30, "unit": "% post-consumer recycled", "basis": "weight", "article": "Environmental DA 2023/2486 Annex II"},
    "water_non_revenue": {"threshold": 20, "unit": "% non-revenue water", "basis": "volume", "article": "Environmental DA 2023/2486 Annex I"},
    "material_recovery_rate": {"threshold": 50, "unit": "% by weight", "basis": "input-output", "article": "Environmental DA 2023/2486 Annex II"},
}


# ═══════════════════════════════════════════════════════════════════════════════
# 8. DATACLASS RESULTS
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class TaxonomyActivityAssessment:
    """Result of assessing one NACE activity against one environmental objective."""
    activity_id: str = ""
    nace_code: str = ""
    activity_name: str = ""
    sector: str = ""
    objective_assessed: str = ""
    substantial_contribution_met: bool = False
    sc_score: float = 0.0
    sc_evidence: dict = field(default_factory=dict)
    dnsh_results: dict = field(default_factory=dict)
    minimum_safeguards_met: bool = False
    ms_evidence: dict = field(default_factory=dict)
    taxonomy_aligned: bool = False
    taxonomy_eligible: bool = False
    transitional_activity: bool = False
    enabling_activity: bool = False


@dataclass
class EntityTaxonomyAlignment:
    """Full entity-level taxonomy alignment assessment."""
    entity_name: str = ""
    reporting_year: int = 2025
    total_turnover_eur: float = 0.0
    aligned_turnover_eur: float = 0.0
    turnover_alignment_pct: float = 0.0
    total_capex_eur: float = 0.0
    aligned_capex_eur: float = 0.0
    capex_alignment_pct: float = 0.0
    total_opex_eur: float = 0.0
    aligned_opex_eur: float = 0.0
    opex_alignment_pct: float = 0.0
    activity_assessments: list = field(default_factory=list)
    objective_breakdown: dict = field(default_factory=dict)
    eligibility_vs_alignment: dict = field(default_factory=dict)
    transitional_share_pct: float = 0.0
    enabling_share_pct: float = 0.0
    cross_framework_disclosures: dict = field(default_factory=dict)
    improvement_recommendations: list = field(default_factory=list)
    data_quality_flags: list = field(default_factory=list)


@dataclass
class PortfolioTaxonomyAlignment:
    """Portfolio-level taxonomy alignment for financial institutions."""
    portfolio_id: str = ""
    portfolio_name: str = ""
    reporting_year: int = 2025
    green_asset_ratio: float = 0.0
    btar: float = 0.0
    weighted_alignment_by_objective: dict = field(default_factory=dict)
    investee_assessments: list = field(default_factory=list)
    sector_breakdown: dict = field(default_factory=dict)
    sfdr_article_classification: str = ""


# ═══════════════════════════════════════════════════════════════════════════════
# 9. ENGINE CLASS
# ═══════════════════════════════════════════════════════════════════════════════

class EUTaxonomyEngine:
    """
    EU Taxonomy Alignment Engine
    ==============================
    Implements Regulation (EU) 2020/852 with all 4 Delegated Acts.
    """

    # ── Activity lookup helpers ──────────────────────────────────────────

    @staticmethod
    def _find_activity(nace_code: str) -> Optional[dict]:
        """Look up NACE activity by code."""
        for act in NACE_ACTIVITIES:
            if act["nace_code"] == nace_code:
                return act
        return None

    # ── Core Assessment Methods ──────────────────────────────────────────

    def assess_activity(
        self,
        nace_code: str,
        objective: str,
        evidence_data: dict,
    ) -> TaxonomyActivityAssessment:
        """
        Assess a single NACE activity against one environmental objective.

        Implements the 3-step Article 3 test:
          1. Substantial Contribution (Article 10-15)
          2. Do No Significant Harm (Article 17)
          3. Minimum Safeguards (Article 18)

        Parameters:
            nace_code: NACE code of the activity
            objective: Environmental objective (CCM/CCA/WTR/CE/POL/BIO)
            evidence_data: Dict with keys like emission_intensity, energy_source,
                          epc_class, recycled_content_pct, water_efficiency, etc.
        """
        activity = self._find_activity(nace_code)
        aid = hashlib.md5(f"{nace_code}_{objective}".encode()).hexdigest()[:16]

        result = TaxonomyActivityAssessment(activity_id=aid, nace_code=nace_code, objective_assessed=objective)

        if not activity:
            result.sc_evidence = {"error": f"NACE code {nace_code} not found in taxonomy"}
            return result

        result.activity_name = activity["name"]
        result.sector = activity["sector"]
        result.transitional_activity = activity.get("transitional", False)
        result.enabling_activity = activity.get("enabling", False)

        # Check eligibility
        if objective in activity.get("eligible_objectives", []):
            result.taxonomy_eligible = True
        else:
            result.sc_evidence = {"status": "not_eligible", "reason": f"Activity {nace_code} not eligible for objective {objective}"}
            return result

        # Step 1: Substantial Contribution
        sc_met, sc_score, sc_ev = self._evaluate_substantial_contribution(activity, objective, evidence_data)
        result.substantial_contribution_met = sc_met
        result.sc_score = sc_score
        result.sc_evidence = sc_ev

        # Step 2: DNSH
        dnsh = self._evaluate_dnsh(objective, evidence_data)
        result.dnsh_results = dnsh

        all_dnsh_met = all(v.get("met", False) for v in dnsh.values())

        # Step 3: Minimum Safeguards
        ms_met, ms_ev = self._evaluate_minimum_safeguards(evidence_data)
        result.minimum_safeguards_met = ms_met
        result.ms_evidence = ms_ev

        # Final alignment determination
        result.taxonomy_aligned = sc_met and all_dnsh_met and ms_met

        return result

    def _evaluate_substantial_contribution(
        self, activity: dict, objective: str, evidence: dict
    ) -> tuple:
        """Evaluate substantial contribution against TSC thresholds."""
        tsc = activity.get("sc_thresholds", {}).get(objective, {})
        if not tsc:
            return False, 0.0, {"status": "no_tsc", "reason": f"No TSC defined for {objective}"}

        tsc_type = tsc.get("type", "qualitative")

        if tsc_type == "quantitative":
            threshold = tsc.get("threshold", 0)
            unit = tsc.get("unit", "")

            # Determine the relevant evidence value
            actual_value = None
            if "gCO2" in unit or "tCO2" in unit:
                actual_value = evidence.get("emission_intensity", evidence.get("ghg_emissions"))
            elif "kWh" in unit or "MWh" in unit:
                actual_value = evidence.get("energy_demand")
            elif "PUE" in unit:
                actual_value = evidence.get("pue")
            elif "% below NZEB" in unit:
                actual_value = evidence.get("nzeb_reduction_pct")
            elif "% primary energy" in unit:
                actual_value = evidence.get("energy_reduction_pct")
            elif "% recycled" in unit or "% post-consumer" in unit:
                actual_value = evidence.get("recycled_content_pct")
            elif "% by weight" in unit:
                actual_value = evidence.get("recovery_rate_pct")
            elif "% non-revenue" in unit:
                actual_value = evidence.get("non_revenue_water_pct")
            elif "gCO2/km" in unit or "gCO2/p-km" in unit or "gCO2/t-km" in unit:
                actual_value = evidence.get("emission_intensity", evidence.get("tailpipe_emissions"))
            elif "EPC" in unit:
                epc = evidence.get("epc_class", "").upper()
                actual_value = 1 if epc == "A" else 0
                threshold = 1
            else:
                actual_value = evidence.get("metric_value")

            if actual_value is None:
                return False, 0.0, {"status": "no_data", "threshold": threshold, "unit": unit, "criteria": tsc.get("criteria", "")}

            # For most thresholds, lower is better (emissions)
            # For reductions (% below, % reduction), higher is better
            if "below" in unit.lower() or "reduction" in unit.lower() or "recycled" in unit.lower() or "recovery" in unit.lower():
                met = actual_value >= threshold
                score = min(100.0, (actual_value / max(threshold, 0.001)) * 100) if threshold > 0 else (100.0 if actual_value > 0 else 0.0)
            else:
                met = actual_value <= threshold
                if threshold > 0:
                    score = max(0.0, min(100.0, (1.0 - actual_value / threshold) * 100))
                else:
                    score = 100.0 if actual_value == 0 else 0.0

            return met, round(score, 1), {
                "status": "assessed", "met": met, "actual": actual_value,
                "threshold": threshold, "unit": unit, "criteria": tsc.get("criteria", "")
            }

        else:  # qualitative
            criteria = tsc.get("criteria", "")
            # Score based on qualitative evidence provided
            qual_keys = ["management_plan", "certification", "assessment_report", "policy_document", "monitoring_data"]
            provided = sum(1 for k in qual_keys if evidence.get(k))
            score = min(100.0, provided * 25.0)
            met = score >= 50.0

            return met, round(score, 1), {
                "status": "qualitative_assessment", "met": met, "criteria": criteria,
                "evidence_items_provided": provided, "evidence_items_expected": len(qual_keys),
            }

    def _evaluate_dnsh(self, sc_objective: str, evidence: dict) -> dict:
        """Evaluate DNSH for all other 5 objectives."""
        dnsh_results = {}
        other_objectives = [o for o in ENVIRONMENTAL_OBJECTIVES if o != sc_objective]

        for obj in other_objectives:
            criteria = DNSH_MATRIX.get(sc_objective, {}).get(obj, "No specific DNSH criteria defined")
            # Check evidence for DNSH compliance
            dnsh_key = f"dnsh_{obj.lower()}"
            dnsh_evidence = evidence.get(dnsh_key, {})

            if isinstance(dnsh_evidence, dict) and dnsh_evidence.get("compliant"):
                met = True
                score = float(dnsh_evidence.get("score", 80))
            elif isinstance(dnsh_evidence, bool):
                met = dnsh_evidence
                score = 100.0 if met else 0.0
            else:
                # Default: assume not demonstrated
                met = False
                score = 0.0

            dnsh_results[obj] = {
                "met": met, "score": round(score, 1),
                "criteria": criteria, "evidence_provided": bool(dnsh_evidence),
            }

        return dnsh_results

    def _evaluate_minimum_safeguards(self, evidence: dict) -> tuple:
        """Evaluate Article 18 minimum safeguards."""
        safeguards = evidence.get("minimum_safeguards", {})
        total_score = 0.0
        total_weight = 0.0
        details = {}

        for area_info in MINIMUM_SAFEGUARDS["assessment_areas"]:
            area = area_info["area"]
            weight = area_info["weight"]
            area_data = safeguards.get(area, {})

            if isinstance(area_data, dict):
                indicators = area_info["indicators"]
                present = sum(1 for ind in indicators if area_data.get(ind.lower().replace(" ", "_")))
                area_score = (present / max(len(indicators), 1)) * 100
            elif isinstance(area_data, (int, float)):
                area_score = float(area_data)
            else:
                area_score = 0.0

            total_score += area_score * weight
            total_weight += weight
            details[area] = {"score": round(area_score, 1), "weight": weight}

        final_score = total_score / max(total_weight, 0.001)
        met = final_score >= 50.0

        return met, {"met": met, "score": round(final_score, 1), "area_scores": details}

    def assess_entity(
        self,
        entity_name: str,
        reporting_year: int,
        activities_data: list[dict],
        financials: dict,
    ) -> EntityTaxonomyAlignment:
        """
        Full entity-level taxonomy alignment assessment.

        Calculates turnover/capex/opex KPIs per Article 8 / DR 2021/2178.

        Parameters:
            entity_name: Company name
            reporting_year: Fiscal year
            activities_data: List of dicts with keys: nace_code, objective, evidence_data,
                            turnover_eur, capex_eur, opex_eur
            financials: Dict with total_turnover_eur, total_capex_eur, total_opex_eur
        """
        result = EntityTaxonomyAlignment(
            entity_name=entity_name,
            reporting_year=reporting_year,
            total_turnover_eur=financials.get("total_turnover_eur", 0.0),
            total_capex_eur=financials.get("total_capex_eur", 0.0),
            total_opex_eur=financials.get("total_opex_eur", 0.0),
        )

        aligned_turnover = 0.0
        aligned_capex = 0.0
        aligned_opex = 0.0
        eligible_turnover = 0.0
        eligible_capex = 0.0
        transitional_turnover = 0.0
        enabling_turnover = 0.0
        obj_breakdown = {o: {"aligned_turnover": 0.0, "aligned_capex": 0.0} for o in ENVIRONMENTAL_OBJECTIVES}
        assessments = []
        quality_flags = []

        for act_data in activities_data:
            nace = act_data.get("nace_code", "")
            obj = act_data.get("objective", "CCM")
            evidence = act_data.get("evidence_data", {})
            act_turnover = act_data.get("turnover_eur", 0.0)
            act_capex = act_data.get("capex_eur", 0.0)
            act_opex = act_data.get("opex_eur", 0.0)

            assessment = self.assess_activity(nace, obj, evidence)
            assessments.append(assessment)

            if assessment.taxonomy_eligible:
                eligible_turnover += act_turnover
                eligible_capex += act_capex

            if assessment.taxonomy_aligned:
                aligned_turnover += act_turnover
                aligned_capex += act_capex
                aligned_opex += act_opex
                obj_breakdown[obj]["aligned_turnover"] += act_turnover
                obj_breakdown[obj]["aligned_capex"] += act_capex

                if assessment.transitional_activity:
                    transitional_turnover += act_turnover
                if assessment.enabling_activity:
                    enabling_turnover += act_turnover
            else:
                if not assessment.sc_evidence.get("met", False) and assessment.taxonomy_eligible:
                    quality_flags.append(f"{nace}: Eligible but SC not met ({assessment.sc_score:.0f}%)")

        result.aligned_turnover_eur = aligned_turnover
        result.aligned_capex_eur = aligned_capex
        result.aligned_opex_eur = aligned_opex

        total_t = max(result.total_turnover_eur, 0.001)
        total_c = max(result.total_capex_eur, 0.001)
        total_o = max(result.total_opex_eur, 0.001)

        result.turnover_alignment_pct = round((aligned_turnover / total_t) * 100, 2)
        result.capex_alignment_pct = round((aligned_capex / total_c) * 100, 2)
        result.opex_alignment_pct = round((aligned_opex / total_o) * 100, 2)

        result.activity_assessments = assessments
        result.objective_breakdown = {
            o: {
                "aligned_turnover_pct": round((v["aligned_turnover"] / total_t) * 100, 2),
                "aligned_capex_pct": round((v["aligned_capex"] / total_c) * 100, 2),
            }
            for o, v in obj_breakdown.items()
        }
        result.eligibility_vs_alignment = {
            "eligible_turnover_pct": round((eligible_turnover / total_t) * 100, 2),
            "aligned_turnover_pct": result.turnover_alignment_pct,
            "gap_pct": round(((eligible_turnover - aligned_turnover) / total_t) * 100, 2),
        }
        result.transitional_share_pct = round((transitional_turnover / max(aligned_turnover, 0.001)) * 100, 2) if aligned_turnover > 0 else 0.0
        result.enabling_share_pct = round((enabling_turnover / max(aligned_turnover, 0.001)) * 100, 2) if aligned_turnover > 0 else 0.0
        result.data_quality_flags = quality_flags

        # Cross-framework disclosures
        result.cross_framework_disclosures = {
            "sfdr_taxonomy_disclosure": {
                "turnover_aligned_pct": result.turnover_alignment_pct,
                "capex_aligned_pct": result.capex_alignment_pct,
            },
            "csrd_esrs2_sbm1": {
                "taxonomy_aligned_revenue": aligned_turnover,
                "taxonomy_aligned_capex": aligned_capex,
            },
        }

        # Recommendations
        recs = []
        if result.turnover_alignment_pct < 20:
            recs.append("Consider expanding taxonomy-aligned activities to improve turnover KPI")
        if result.capex_alignment_pct < result.turnover_alignment_pct:
            recs.append("CapEx alignment lags turnover — increase green CapEx investment")
        if quality_flags:
            recs.append(f"Address {len(quality_flags)} eligible-but-not-aligned activities to improve alignment")
        result.improvement_recommendations = recs

        return result

    def assess_portfolio(
        self,
        portfolio_id: str,
        portfolio_name: str,
        investees_data: list[dict],
    ) -> PortfolioTaxonomyAlignment:
        """
        Portfolio-level taxonomy alignment for financial institutions.

        Calculates GAR, BTAR, and SFDR article classification.

        Parameters:
            portfolio_id: Portfolio identifier
            portfolio_name: Display name
            investees_data: List of dicts with keys: entity_name, reporting_year,
                           activities_data, financials, exposure_eur
        """
        result = PortfolioTaxonomyAlignment(
            portfolio_id=portfolio_id,
            portfolio_name=portfolio_name,
        )

        total_exposure = 0.0
        aligned_exposure = 0.0
        investee_results = []
        sector_totals = {}
        obj_weighted = {o: 0.0 for o in ENVIRONMENTAL_OBJECTIVES}

        for inv in investees_data:
            exposure = inv.get("exposure_eur", 0.0)
            total_exposure += exposure

            entity_result = self.assess_entity(
                entity_name=inv.get("entity_name", ""),
                reporting_year=inv.get("reporting_year", 2025),
                activities_data=inv.get("activities_data", []),
                financials=inv.get("financials", {}),
            )
            investee_results.append(entity_result)

            # Weight by exposure
            inv_aligned_share = entity_result.turnover_alignment_pct / 100.0
            aligned_exposure += exposure * inv_aligned_share

            sector = inv.get("sector", "Other")
            sector_totals.setdefault(sector, {"exposure": 0.0, "aligned": 0.0})
            sector_totals[sector]["exposure"] += exposure
            sector_totals[sector]["aligned"] += exposure * inv_aligned_share

            for obj in ENVIRONMENTAL_OBJECTIVES:
                obj_pct = entity_result.objective_breakdown.get(obj, {}).get("aligned_turnover_pct", 0.0)
                obj_weighted[obj] += exposure * (obj_pct / 100.0)

        total_exp = max(total_exposure, 0.001)
        result.green_asset_ratio = round((aligned_exposure / total_exp) * 100, 2)
        result.btar = result.green_asset_ratio  # simplified: same calc for BTAR
        result.investee_assessments = investee_results
        result.weighted_alignment_by_objective = {
            o: round((v / total_exp) * 100, 2) for o, v in obj_weighted.items()
        }
        result.sector_breakdown = {
            s: {"exposure_eur": v["exposure"], "aligned_pct": round((v["aligned"] / max(v["exposure"], 0.001)) * 100, 2)}
            for s, v in sector_totals.items()
        }

        # SFDR classification suggestion
        gar = result.green_asset_ratio
        if gar >= 70:
            result.sfdr_article_classification = "Article 9 (dark green)"
        elif gar >= 20:
            result.sfdr_article_classification = "Article 8 (light green)"
        else:
            result.sfdr_article_classification = "Article 6 (mainstream)"

        if investees_data:
            result.reporting_year = investees_data[0].get("reporting_year", 2025)

        return result

    # ── Static Reference Methods ─────────────────────────────────────────

    @staticmethod
    def get_environmental_objectives() -> dict:
        """6 Environmental Objectives per Article 9."""
        return ENVIRONMENTAL_OBJECTIVES

    @staticmethod
    def get_nace_activities() -> list[dict]:
        """All NACE activities across 4 Delegated Acts."""
        return NACE_ACTIVITIES

    @staticmethod
    def get_tsc_for_activity(nace_code: str, objective: str = "CCM") -> dict:
        """Get Technical Screening Criteria for a specific activity/objective pair."""
        for act in NACE_ACTIVITIES:
            if act["nace_code"] == nace_code:
                return act.get("sc_thresholds", {}).get(objective, {})
        return {}

    @staticmethod
    def get_dnsh_matrix() -> dict:
        """6x6 DNSH cross-check matrix."""
        return DNSH_MATRIX

    @staticmethod
    def get_minimum_safeguards() -> dict:
        """Article 18 Minimum Safeguards."""
        return MINIMUM_SAFEGUARDS

    @staticmethod
    def get_kpi_definitions() -> dict:
        """Turnover/CapEx/OpEx KPI definitions per DR 2021/2178."""
        return KPI_DEFINITIONS

    @staticmethod
    def get_transitional_activities() -> list[dict]:
        """Transitional activities per Article 10(2)."""
        return [a for a in NACE_ACTIVITIES if a.get("transitional")]

    @staticmethod
    def get_enabling_activities() -> list[dict]:
        """Enabling activities per Article 10(1)."""
        return [a for a in NACE_ACTIVITIES if a.get("enabling")]

    @staticmethod
    def get_cross_framework_map() -> list[dict]:
        """Cross-framework mapping: Taxonomy -> CSRD/SFDR/ISSB/GRI/CDP/TCFD."""
        return CROSS_FRAMEWORK_MAP

    @staticmethod
    def get_financial_kpi_definitions() -> dict:
        """GAR, BTAR, insurance and asset manager KPI definitions."""
        return FINANCIAL_KPI_DEFINITIONS

    @staticmethod
    def get_sector_thresholds() -> dict:
        """Key quantitative thresholds by sector from all Delegated Acts."""
        return SECTOR_THRESHOLDS
