"""
CSRD Entity Data Bridge Service
================================
Translates the seeded CSRD/ESRS/FI/Energy data into module-ready input formats
so all calculation modules (Carbon, ECL, Nature Risk, Stranded Assets, etc.)
can consume real data from the database rather than requiring manual entry.

Entity registry has 8 entities:
  FI (4):     ABN AMRO, BNP Paribas, ING Group, Rabobank
  Energy (4): EDP, ENGIE, Ørsted, RWE Group
"""

from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import Optional


# ── Entity list ────────────────────────────────────────────────────────────────

def get_entity_list(db: Session) -> list[dict]:
    """Return all 8 CSRD entities with a top-level summary."""
    rows = db.execute(text("""
        SELECT
            cer.id,
            cer.legal_name,
            cer.primary_sector,
            cer.country_iso,
            cer.net_turnover_meur,
            cer.balance_sheet_total_meur,
            cer.employee_count,
            cer.fi_entity_id,
            cer.energy_entity_id,
            ghg.scope1_gross_tco2e,
            ghg.scope2_market_based_tco2e,
            ghg.scope3_total_tco2e,
            en.renewable_energy_pct,
            gen.renewables_capacity_share_pct,
            gen.avg_carbon_intensity_gco2_kwh,
            s1.gender_pay_gap_pct,
            s1.employees_headcount
        FROM csrd_entity_registry cer
        LEFT JOIN esrs_e1_ghg_emissions ghg ON ghg.entity_registry_id = cer.id AND ghg.reporting_year = 2024
        LEFT JOIN esrs_e1_energy en ON en.entity_registry_id = cer.id AND en.reporting_year = 2024
        LEFT JOIN energy_entities ee ON ee.id = cer.energy_entity_id
        LEFT JOIN energy_generation_mix gen ON gen.entity_id = ee.id AND gen.reporting_year = 2024
        LEFT JOIN esrs_s1_workforce s1 ON s1.entity_registry_id = cer.id AND s1.reporting_year = 2024
        ORDER BY cer.primary_sector, cer.legal_name
    """)).fetchall()

    return [
        {
            "id": str(r[0]),
            "legal_name": r[1],
            "sector": r[2],
            "country_iso": r[3],
            "net_turnover_meur": float(r[4]) if r[4] is not None else None,
            "balance_sheet_meur": float(r[5]) if r[5] is not None else None,
            "employees": int(r[6]) if r[6] is not None else None,
            "fi_entity_id": str(r[7]) if r[7] else None,
            "energy_entity_id": str(r[8]) if r[8] else None,
            "scope1_tco2e": float(r[9]) if r[9] is not None else None,
            "scope2_market_tco2e": float(r[10]) if r[10] is not None else None,
            "scope3_total_tco2e": float(r[11]) if r[11] is not None else None,
            "renewable_energy_pct": float(r[12]) if r[12] is not None else None,
            "renewables_capacity_pct": float(r[13]) if r[13] is not None else None,
            "carbon_intensity_gco2_kwh": float(r[14]) if r[14] is not None else None,
            "gender_pay_gap_pct": float(r[15]) if r[15] is not None else None,
            "headcount": int(r[16]) if r[16] is not None else None,
        }
        for r in rows
    ]


# ── Full entity profile ─────────────────────────────────────────────────────────

def get_entity_profile(entity_id: str, db: Session) -> Optional[dict]:
    """Return the complete cross-module data profile for one entity."""
    # Base entity
    ent = db.execute(text("""
        SELECT id, legal_name, primary_sector, sector_subtype, country_iso, jurisdiction,
               net_turnover_meur, balance_sheet_total_meur, employee_count,
               is_in_scope_csrd, is_in_scope_sfdr, sfdr_article_classification,
               is_in_scope_eu_taxonomy, is_in_scope_tcfd, is_in_scope_issb,
               fi_entity_id, energy_entity_id
        FROM csrd_entity_registry WHERE id = :eid
    """), {"eid": entity_id}).fetchone()
    if not ent:
        return None

    profile = {
        "entity": {
            "id": str(ent[0]), "legal_name": ent[1],
            "sector": ent[2], "sector_subtype": ent[3],
            "country_iso": ent[4], "jurisdiction": ent[5],
            "net_turnover_meur": float(ent[6]) if ent[6] else None,
            "balance_sheet_meur": float(ent[7]) if ent[7] else None,
            "employees": int(ent[8]) if ent[8] else None,
            "csrd": bool(ent[9]), "sfdr": bool(ent[10]),
            "sfdr_article": ent[11],
            "eu_taxonomy": bool(ent[12]), "tcfd": bool(ent[13]), "issb": bool(ent[14]),
        },
        "ghg": _get_ghg(entity_id, db),
        "energy": _get_energy(entity_id, db),
        "water": _get_water(entity_id, db),
        "biodiversity": _get_biodiversity(entity_id, db),
        "pollution": _get_pollution(entity_id, db),
        "circular": _get_circular(entity_id, db),
        "workforce": _get_workforce(entity_id, db),
        "governance": _get_governance(entity_id, db),
        "financial_effects": _get_financial_effects(entity_id, db),
    }

    # Sector-specific data
    if ent[15]:  # fi_entity_id
        profile["fi"] = _get_fi_data(str(ent[15]), db)
    if ent[16]:  # energy_entity_id
        profile["energy_ops"] = _get_energy_ops(str(ent[16]), db)

    return profile


# ── Module-specific input builders ─────────────────────────────────────────────

def get_carbon_inputs(entity_id: str, db: Session) -> Optional[dict]:
    """
    Return pre-filled inputs for the Carbon Calculator module.
    Maps esrs_e1_ghg_emissions + esrs_e1_energy to carbon calc format.
    """
    ent = db.execute(text(
        "SELECT legal_name, country_iso, net_turnover_meur FROM csrd_entity_registry WHERE id=:eid"
    ), {"eid": entity_id}).fetchone()
    if not ent:
        return None

    ghg = _get_ghg(entity_id, db)
    en = _get_energy(entity_id, db)

    return {
        "entity_id": entity_id,
        "company_name": ent[0],
        "country_iso": ent[1],
        "reporting_year": 2024,
        # Scope 1
        "scope1_total_tco2e": ghg.get("scope1_gross_tco2e") if ghg else None,
        "scope1_stationary_tco2e": ghg.get("scope1_stationary_combustion_tco2e") if ghg else None,
        "scope1_mobile_tco2e": ghg.get("scope1_mobile_combustion_tco2e") if ghg else None,
        "scope1_process_tco2e": ghg.get("scope1_process_emissions_tco2e") if ghg else None,
        "scope1_fugitive_tco2e": ghg.get("scope1_fugitive_emissions_tco2e") if ghg else None,
        # Scope 2
        "scope2_location_tco2e": ghg.get("scope2_location_based_tco2e") if ghg else None,
        "scope2_market_tco2e": ghg.get("scope2_market_based_tco2e") if ghg else None,
        # Scope 3
        "scope3_total_tco2e": ghg.get("scope3_total_tco2e") if ghg else None,
        "scope3_cat01_tco2e": ghg.get("scope3_cat01_purchased_goods_services_tco2e") if ghg else None,
        "scope3_cat03_tco2e": ghg.get("scope3_cat03_fuel_energy_tco2e") if ghg else None,
        "scope3_cat06_tco2e": ghg.get("scope3_cat06_business_travel_tco2e") if ghg else None,
        "scope3_cat07_tco2e": ghg.get("scope3_cat07_employee_commuting_tco2e") if ghg else None,
        "scope3_cat15_tco2e": ghg.get("scope3_cat15_investments_tco2e") if ghg else None,
        # GHG intensity
        "ghg_intensity_location": ghg.get("ghg_intensity_location_based_tco2e_per_meur") if ghg else None,
        "ghg_intensity_market": ghg.get("ghg_intensity_market_based_tco2e_per_meur") if ghg else None,
        # Energy
        "total_energy_mwh": en.get("total_energy_consumption_mwh") if en else None,
        "fossil_energy_mwh": en.get("energy_from_fossil_sources_mwh") if en else None,
        "renewable_energy_mwh": en.get("energy_from_renewable_sources_mwh") if en else None,
        "renewable_pct": en.get("renewable_energy_pct") if en else None,
        # Financial context
        "revenue_meur": float(ent[2]) if ent[2] else None,
    }


def get_ecl_inputs(entity_id: str, db: Session) -> Optional[dict]:
    """
    Return pre-filled inputs for the ECL/Climate Risk module.
    Maps fi_financials + fi_loan_books + fi_csrd_e1_climate to ECL format.
    Only populated for FI entities (primary_sector = financial_institution).
    """
    ent = db.execute(text(
        "SELECT legal_name, country_iso, fi_entity_id FROM csrd_entity_registry WHERE id=:eid"
    ), {"eid": entity_id}).fetchone()
    if not ent or not ent[2]:
        return None  # not a financial institution

    fi_id = str(ent[2])
    fi = _get_fi_data(fi_id, db)
    if not fi:
        return None

    fin = fi.get("financials", {})
    lb = fi.get("loan_book", {})
    climate = fi.get("csrd_e1", {})

    total_ead = float(lb.get("total_ead", 0)) if lb.get("total_ead") else None
    total_ead_eur = total_ead * 1_000_000 if total_ead else None  # mEUR → EUR

    return {
        "entity_id": entity_id,
        "company_name": ent[0],
        "country_iso": ent[1],
        "reporting_year": 2024,
        # Balance sheet
        "total_assets_meur": float(fin.get("total_assets", 0)) if fin.get("total_assets") else None,
        "loans_gross_meur": float(fin.get("loans_and_advances_gross", 0)) if fin.get("loans_and_advances_gross") else None,
        "npl_ratio_pct": float(fin.get("npl_ratio_pct", 0)) if fin.get("npl_ratio_pct") else None,
        "cet1_ratio_pct": float(fin.get("cet1_ratio_pct", 0)) if fin.get("cet1_ratio_pct") else None,
        "rwa_meur": float(fin.get("rwa", 0)) if fin.get("rwa") else None,
        "cost_of_risk_bps": float(fin.get("cost_of_risk_bps", 0)) if fin.get("cost_of_risk_bps") else None,
        # IFRS 9 staging (from actual reported ratios)
        "stage1_pct": float(fin.get("stage1_loans_pct", 70)) if fin.get("stage1_loans_pct") else 70.0,
        "stage2_pct": float(fin.get("stage2_loans_pct", 20)) if fin.get("stage2_loans_pct") else 20.0,
        "stage3_pct": float(fin.get("stage3_loans_pct", 10)) if fin.get("stage3_loans_pct") else 10.0,
        # Loan book risk breakdown
        "total_ead_meur": total_ead,
        "carbon_intensive_pct": float(lb.get("carbon_intensive_sectors_pct", 0)) if lb.get("carbon_intensive_sectors_pct") else None,
        "physical_risk_high_pct": float(lb.get("physical_risk_high_pct", 0)) if lb.get("physical_risk_high_pct") else None,
        "paris_aligned_pct": float(lb.get("paris_aligned_pct", 0)) if lb.get("paris_aligned_pct") else None,
        "fossil_fuel_ead_meur": float(lb.get("fossil_fuel_extraction_ead", 0)) if lb.get("fossil_fuel_extraction_ead") else None,
        "real_estate_ead_meur": (
            (float(lb.get("real_estate_commercial_ead", 0)) + float(lb.get("real_estate_residential_ead", 0)))
            if lb.get("real_estate_commercial_ead") else None
        ),
        # Sector EAD breakdown (mEUR)
        "sector_ead": {
            "energy_oil_gas": float(lb.get("energy_oil_gas_ead", 0)) if lb.get("energy_oil_gas_ead") else 0,
            "energy_renewables": float(lb.get("energy_renewables_ead", 0)) if lb.get("energy_renewables_ead") else 0,
            "industrials": float(lb.get("industrials_ead", 0)) if lb.get("industrials_ead") else 0,
            "transport": float(lb.get("transport_ead", 0)) if lb.get("transport_ead") else 0,
            "real_estate_commercial": float(lb.get("real_estate_commercial_ead", 0)) if lb.get("real_estate_commercial_ead") else 0,
            "real_estate_residential": float(lb.get("real_estate_residential_ead", 0)) if lb.get("real_estate_residential_ead") else 0,
            "retail_mortgage": float(lb.get("retail_mortgage_ead", 0)) if lb.get("retail_mortgage_ead") else 0,
        },
        # Climate data from CSRD E1
        "financed_emissions_scope3_cat15_tco2e": climate.get("financed_emissions_scope3_cat15_tco2e") if climate else None,
        "waci_evic": climate.get("waci_tco2e_per_meur_evic") if climate else None,
        "paris_alignment_score": climate.get("portfolio_temperature_alignment_c") if climate else None,
    }


def get_nature_inputs(entity_id: str, db: Session) -> Optional[dict]:
    """
    Return pre-filled inputs for the Nature Risk / TNFD module.
    Maps esrs_e4_biodiversity + esrs_e3_water to TNFD LEAP input format.
    """
    ent = db.execute(text(
        "SELECT legal_name, country_iso FROM csrd_entity_registry WHERE id=:eid"
    ), {"eid": entity_id}).fetchone()
    if not ent:
        return None

    bio = _get_biodiversity(entity_id, db)
    water = _get_water(entity_id, db)
    ghg = _get_ghg(entity_id, db)

    return {
        "entity_id": entity_id,
        "company_name": ent[0],
        "country_iso": ent[1],
        "reporting_year": 2024,
        # Biodiversity (ESRS E4)
        "sites_in_kba_count": bio.get("sites_in_near_protected_or_kba_count") if bio else None,
        "sites_in_kba_area_ha": bio.get("sites_in_near_protected_or_kba_area_ha") if bio else None,
        "total_land_use_ha": bio.get("total_land_use_area_ha") if bio else None,
        "sealed_area_ha": bio.get("sealed_area_ha") if bio else None,
        "tnfd_locate_done": bio.get("tnfd_locate_complete") if bio else None,
        "tnfd_evaluate_done": bio.get("tnfd_evaluate_complete") if bio else None,
        "tnfd_assess_done": bio.get("tnfd_assess_complete") if bio else None,
        "tnfd_prepare_done": bio.get("tnfd_prepare_complete") if bio else None,
        "biodiversity_financial_risk_eur": bio.get("biodiversity_financial_effects_risk_eur") if bio else None,
        # Water (ESRS E3)
        "total_water_consumption_m3": water.get("total_water_consumption_m3") if water else None,
        "water_at_risk_m3": water.get("water_consumption_at_water_risk_m3") if water else None,
        "water_recycled_m3": water.get("total_water_recycled_reused_m3") if water else None,
        "water_withdrawals_m3": water.get("total_water_withdrawals_m3") if water else None,
        "withdrawal_high_stress_pct": water.get("withdrawal_high_stress_areas_pct") if water else None,
        # GHG for carbon-biodiversity link
        "scope1_biogenic_tco2": ghg.get("scope1_biogenic_co2_tco2") if ghg else None,
    }


def get_stranded_inputs(entity_id: str, db: Session) -> Optional[dict]:
    """
    Return pre-filled inputs for the Stranded Asset Calculator.
    Maps energy_generation_mix + energy_stranded_assets_register to stranded calc format.
    Only populated for energy entities.
    """
    ent = db.execute(text(
        "SELECT legal_name, country_iso, energy_entity_id FROM csrd_entity_registry WHERE id=:eid"
    ), {"eid": entity_id}).fetchone()
    if not ent or not ent[2]:
        return None  # not an energy entity

    energy_id = str(ent[2])
    energy_ops = _get_energy_ops(energy_id, db)
    if not energy_ops:
        return None

    gen = energy_ops.get("generation_mix", {})
    stranded = energy_ops.get("stranded_assets", [])

    return {
        "entity_id": entity_id,
        "company_name": ent[0],
        "country_iso": ent[1],
        "reporting_year": 2024,
        # Generation mix
        "total_installed_gw": float(gen.get("total_installed_gw", 0)) if gen.get("total_installed_gw") else None,
        "coal_installed_gw": float(gen.get("coal_installed_gw", 0)) if gen.get("coal_installed_gw") else None,
        "lignite_installed_gw": float(gen.get("lignite_installed_gw", 0)) if gen.get("lignite_installed_gw") else None,
        "gas_ccgt_installed_gw": float(gen.get("gas_ccgt_installed_gw", 0)) if gen.get("gas_ccgt_installed_gw") else None,
        "gas_ocgt_installed_gw": float(gen.get("gas_ocgt_installed_gw", 0)) if gen.get("gas_ocgt_installed_gw") else None,
        "nuclear_installed_gw": float(gen.get("nuclear_installed_gw", 0)) if gen.get("nuclear_installed_gw") else None,
        "wind_onshore_installed_gw": float(gen.get("wind_onshore_installed_gw", 0)) if gen.get("wind_onshore_installed_gw") else None,
        "wind_offshore_installed_gw": float(gen.get("wind_offshore_installed_gw", 0)) if gen.get("wind_offshore_installed_gw") else None,
        "solar_pv_installed_gw": float(gen.get("solar_pv_installed_gw", 0)) if gen.get("solar_pv_installed_gw") else None,
        "total_renewables_gw": float(gen.get("total_renewables_installed_gw", 0)) if gen.get("total_renewables_installed_gw") else None,
        "renewables_capacity_pct": float(gen.get("renewables_capacity_share_pct", 0)) if gen.get("renewables_capacity_share_pct") else None,
        "avg_carbon_intensity_gco2_kwh": float(gen.get("avg_carbon_intensity_gco2_kwh", 0)) if gen.get("avg_carbon_intensity_gco2_kwh") else None,
        # ETS
        "eu_ets_cost_meur": float(gen.get("eu_ets_cost_meur", 0)) if gen.get("eu_ets_cost_meur") else None,
        "eu_ets_price_avg": float(gen.get("eu_ets_price_avg_eur_t", 0)) if gen.get("eu_ets_price_avg_eur_t") else None,
        # Stranded assets register
        "stranded_assets": [
            {
                "asset_name": a.get("asset_name"),
                "fuel_type": a.get("fuel_type"),
                "capacity_mw": float(a.get("installed_capacity_mw", 0)) if a.get("installed_capacity_mw") else None,
                "commissioning_year": a.get("commissioning_year"),
                "planned_retirement_year": a.get("planned_retirement_year"),
                "status": a.get("status"),
                "book_value_meur": float(a.get("book_value_meur", 0)) if a.get("book_value_meur") else None,
                "stranded_risk_pct": float(a.get("stranded_value_at_risk_pct", 0)) if a.get("stranded_value_at_risk_pct") else None,
            }
            for a in stranded
        ],
    }


def get_sector_inputs(entity_id: str, db: Session) -> Optional[dict]:
    """
    Return pre-filled inputs for the Sector Assessments module (Power Plant / Energy).
    """
    ent = db.execute(text(
        "SELECT legal_name, country_iso, energy_entity_id FROM csrd_entity_registry WHERE id=:eid"
    ), {"eid": entity_id}).fetchone()
    if not ent or not ent[2]:
        return None

    energy_ops = _get_energy_ops(str(ent[2]), db)
    if not energy_ops:
        return None

    gen = energy_ops.get("generation_mix", {})
    fin = energy_ops.get("financials", {})
    pipeline = energy_ops.get("renewable_pipeline", [])

    return {
        "entity_id": entity_id,
        "company_name": ent[0],
        "country_iso": ent[1],
        "reporting_year": 2024,
        # Power plant context
        "total_capacity_gw": float(gen.get("total_installed_gw", 0)) if gen.get("total_installed_gw") else None,
        "renewables_gw": float(gen.get("total_renewables_installed_gw", 0)) if gen.get("total_renewables_installed_gw") else None,
        "total_generation_twh": float(gen.get("total_generation_twh", 0)) if gen.get("total_generation_twh") else None,
        "carbon_intensity_gco2_kwh": float(gen.get("avg_carbon_intensity_gco2_kwh", 0)) if gen.get("avg_carbon_intensity_gco2_kwh") else None,
        "capex_total_meur": float(fin.get("total_capex", 0)) if fin.get("total_capex") else None,
        "green_capex_pct": float(fin.get("green_capex_pct", 0)) if fin.get("green_capex_pct") else None,
        "revenue_meur": float(fin.get("total_revenues", 0)) if fin.get("total_revenues") else None,
        # Renewable pipeline summary
        "pipeline_projects": len(pipeline),
        "pipeline_capacity_gw": sum(
            float(p.get("capacity_mw", 0)) / 1000 for p in pipeline if p.get("capacity_mw")
        ),
    }


def get_portfolio_asset_spec(entity_id: str, db: Session) -> Optional[dict]:
    """
    Return an assets_pg-compatible record for this entity.
    Used to seed portfolio holdings with real entity data.
    """
    ent = db.execute(text("""
        SELECT cer.legal_name, cer.primary_sector, cer.country_iso,
               cer.net_turnover_meur, cer.balance_sheet_total_meur,
               cer.fi_entity_id, cer.energy_entity_id
        FROM csrd_entity_registry cer WHERE cer.id = :eid
    """), {"eid": entity_id}).fetchone()
    if not ent:
        return None

    sector_map = {
        "financial_institution": "Financials",
        "energy_developer": "Utilities",
    }
    asset_type_map = {
        "financial_institution": "corporate_bond",
        "energy_developer": "project_finance",
    }

    # Rating proxy from credit context
    rating_defaults = {
        "financial_institution": "A",
        "energy_developer": "BBB",
    }
    pd_defaults = {
        "financial_institution": 0.0042,
        "energy_developer": 0.0068,
    }

    sector = ent[1]
    exposure = float(ent[4]) * 0.05 if ent[4] else 1000.0  # 5% of balance sheet
    market_value = float(ent[3]) * 0.08 if ent[3] else 800.0  # 8% of revenue

    # For FI entities, use actual loan book data for more precise exposure
    if ent[5]:  # fi_entity_id
        lb = db.execute(text(
            "SELECT total_ead FROM fi_loan_books WHERE entity_id=:fid LIMIT 1"
        ), {"fid": str(ent[5])}).fetchone()
        if lb and lb[0]:
            exposure = float(lb[0]) * 0.01  # 1% sample slice

    return {
        "entity_registry_id": entity_id,
        "company_name": ent[0],
        "company_sector": sector_map.get(sector, "Industrials"),
        "company_subsector": sector,
        "asset_type": asset_type_map.get(sector, "corporate_bond"),
        "exposure": round(exposure, 2),
        "market_value": round(market_value, 2),
        "base_pd": pd_defaults.get(sector, 0.005),
        "base_lgd": 0.45,
        "rating": rating_defaults.get(sector, "BBB"),
        "maturity_years": 5,
    }


# ── Internal helpers ────────────────────────────────────────────────────────────

def _row_to_dict(row) -> dict:
    if row is None:
        return {}
    return dict(zip(row.keys(), row))


def _get_ghg(entity_id: str, db: Session) -> Optional[dict]:
    row = db.execute(text("""
        SELECT scope1_gross_tco2e, scope1_stationary_combustion_tco2e, scope1_mobile_combustion_tco2e,
               scope1_process_emissions_tco2e, scope1_fugitive_emissions_tco2e, scope1_biogenic_co2_tco2,
               scope2_location_based_tco2e, scope2_market_based_tco2e,
               scope3_total_tco2e,
               scope3_cat01_purchased_goods_services_tco2e, scope3_cat02_capital_goods_tco2e,
               scope3_cat03_fuel_energy_tco2e, scope3_cat04_upstream_transport_tco2e,
               scope3_cat05_waste_operations_tco2e, scope3_cat06_business_travel_tco2e,
               scope3_cat07_employee_commuting_tco2e, scope3_cat08_upstream_leased_assets_tco2e,
               scope3_cat09_downstream_transport_tco2e, scope3_cat10_processing_sold_products_tco2e,
               scope3_cat11_use_of_sold_products_tco2e, scope3_cat12_end_of_life_treatment_tco2e,
               scope3_cat13_downstream_leased_assets_tco2e, scope3_cat14_franchises_tco2e,
               scope3_cat15_investments_tco2e,
               total_ghg_tco2e, total_ghg_market_based_tco2e,
               ghg_intensity_location_based_tco2e_per_meur, ghg_intensity_market_based_tco2e_per_meur,
               gwp_standard, base_year
        FROM esrs_e1_ghg_emissions WHERE entity_registry_id=:eid AND reporting_year=2024
    """), {"eid": entity_id}).fetchone()
    if not row:
        return {}
    keys = [
        "scope1_gross_tco2e", "scope1_stationary_combustion_tco2e", "scope1_mobile_combustion_tco2e",
        "scope1_process_emissions_tco2e", "scope1_fugitive_emissions_tco2e", "scope1_biogenic_co2_tco2",
        "scope2_location_based_tco2e", "scope2_market_based_tco2e",
        "scope3_total_tco2e",
        "scope3_cat01_purchased_goods_services_tco2e", "scope3_cat02_capital_goods_tco2e",
        "scope3_cat03_fuel_energy_tco2e", "scope3_cat04_upstream_transport_tco2e",
        "scope3_cat05_waste_operations_tco2e", "scope3_cat06_business_travel_tco2e",
        "scope3_cat07_employee_commuting_tco2e", "scope3_cat08_upstream_leased_assets_tco2e",
        "scope3_cat09_downstream_transport_tco2e", "scope3_cat10_processing_sold_products_tco2e",
        "scope3_cat11_use_of_sold_products_tco2e", "scope3_cat12_end_of_life_treatment_tco2e",
        "scope3_cat13_downstream_leased_assets_tco2e", "scope3_cat14_franchises_tco2e",
        "scope3_cat15_investments_tco2e",
        "total_ghg_tco2e", "total_ghg_market_based_tco2e",
        "ghg_intensity_location_based_tco2e_per_meur", "ghg_intensity_market_based_tco2e_per_meur",
        "gwp_standard", "base_year",
    ]
    return {k: (float(v) if v is not None and k not in ("gwp_standard",) else v) for k, v in zip(keys, row)}


def _get_energy(entity_id: str, db: Session) -> Optional[dict]:
    row = db.execute(text("""
        SELECT total_energy_consumption_mwh, energy_from_fossil_sources_mwh,
               energy_from_nuclear_sources_mwh, energy_from_renewable_sources_mwh,
               renewable_energy_pct
        FROM esrs_e1_energy WHERE entity_registry_id=:eid AND reporting_year=2024
    """), {"eid": entity_id}).fetchone()
    if not row:
        return {}
    return {
        "total_energy_consumption_mwh": float(row[0]) if row[0] else None,
        "energy_from_fossil_sources_mwh": float(row[1]) if row[1] else None,
        "energy_from_nuclear_sources_mwh": float(row[2]) if row[2] else None,
        "energy_from_renewable_sources_mwh": float(row[3]) if row[3] else None,
        "renewable_energy_pct": float(row[4]) if row[4] else None,
    }


def _get_water(entity_id: str, db: Session) -> Optional[dict]:
    row = db.execute(text("""
        SELECT total_water_consumption_m3, water_consumption_at_water_risk_m3,
               total_water_recycled_reused_m3, total_water_withdrawals_m3,
               withdrawal_groundwater_m3, withdrawal_third_party_municipal_m3,
               withdrawal_high_stress_areas_m3, withdrawal_high_stress_areas_pct
        FROM esrs_e3_water WHERE entity_registry_id=:eid AND reporting_year=2024
    """), {"eid": entity_id}).fetchone()
    if not row:
        return {}
    keys = ["total_water_consumption_m3", "water_consumption_at_water_risk_m3",
            "total_water_recycled_reused_m3", "total_water_withdrawals_m3",
            "withdrawal_groundwater_m3", "withdrawal_third_party_municipal_m3",
            "withdrawal_high_stress_areas_m3", "withdrawal_high_stress_areas_pct"]
    return {k: float(v) if v is not None else None for k, v in zip(keys, row)}


def _get_biodiversity(entity_id: str, db: Session) -> Optional[dict]:
    row = db.execute(text("""
        SELECT sites_in_near_protected_or_kba_count, sites_in_near_protected_or_kba_area_ha,
               total_land_use_area_ha, sealed_area_ha,
               tnfd_locate_complete, tnfd_evaluate_complete, tnfd_assess_complete, tnfd_prepare_complete,
               biodiversity_financial_effects_risk_eur, ecosystem_services_value_at_risk_eur
        FROM esrs_e4_biodiversity WHERE entity_registry_id=:eid AND reporting_year=2024
    """), {"eid": entity_id}).fetchone()
    if not row:
        return {}
    return {
        "sites_in_near_protected_or_kba_count": int(row[0]) if row[0] is not None else None,
        "sites_in_near_protected_or_kba_area_ha": float(row[1]) if row[1] is not None else None,
        "total_land_use_area_ha": float(row[2]) if row[2] is not None else None,
        "sealed_area_ha": float(row[3]) if row[3] is not None else None,
        "tnfd_locate_complete": bool(row[4]),
        "tnfd_evaluate_complete": bool(row[5]),
        "tnfd_assess_complete": bool(row[6]),
        "tnfd_prepare_complete": bool(row[7]),
        "biodiversity_financial_effects_risk_eur": float(row[8]) if row[8] is not None else None,
        "ecosystem_services_value_at_risk_eur": float(row[9]) if row[9] is not None else None,
    }


def _get_pollution(entity_id: str, db: Session) -> Optional[dict]:
    row = db.execute(text("""
        SELECT air_nox_tonnes, air_sox_tonnes, air_pm25_tonnes, air_voc_tonnes,
               water_nitrogen_tonnes, water_phosphorus_tonnes
        FROM esrs_e2_pollution WHERE entity_registry_id=:eid AND reporting_year=2024
    """), {"eid": entity_id}).fetchone()
    if not row:
        return {}
    return {
        "air_nox_tonnes": float(row[0]) if row[0] is not None else None,
        "air_sox_tonnes": float(row[1]) if row[1] is not None else None,
        "air_pm25_tonnes": float(row[2]) if row[2] is not None else None,
        "air_voc_tonnes": float(row[3]) if row[3] is not None else None,
        "water_nitrogen_tonnes": float(row[4]) if row[4] is not None else None,
        "water_phosphorus_tonnes": float(row[5]) if row[5] is not None else None,
    }


def _get_circular(entity_id: str, db: Session) -> Optional[dict]:
    row = db.execute(text("""
        SELECT total_materials_consumed_tonnes, secondary_reused_recycled_materials_tonnes,
               secondary_reused_recycled_materials_pct, total_waste_generated_tonnes,
               total_hazardous_waste_tonnes, non_hazardous_waste_directed_to_disposal_tonnes
        FROM esrs_e5_circular WHERE entity_registry_id=:eid AND reporting_year=2024
    """), {"eid": entity_id}).fetchone()
    if not row:
        return {}
    return {
        "total_materials_tonnes": float(row[0]) if row[0] else None,
        "secondary_materials_tonnes": float(row[1]) if row[1] else None,
        "secondary_materials_pct": float(row[2]) if row[2] else None,
        "total_waste_tonnes": float(row[3]) if row[3] else None,
        "hazardous_waste_tonnes": float(row[4]) if row[4] else None,
        "non_hazardous_disposal_tonnes": float(row[5]) if row[5] else None,
    }


def _get_workforce(entity_id: str, db: Session) -> Optional[dict]:
    row = db.execute(text("""
        SELECT employees_headcount, employees_male, employees_female,
               employees_permanent, employees_temporary, employees_covered_by_cba_pct,
               gender_pay_gap_pct, fatalities_total_own_workforce,
               days_lost_own_workforce, annual_total_remuneration_ratio
        FROM esrs_s1_workforce WHERE entity_registry_id=:eid AND reporting_year=2024
    """), {"eid": entity_id}).fetchone()
    if not row:
        return {}
    return {
        "headcount": int(row[0]) if row[0] else None,
        "male": int(row[1]) if row[1] else None,
        "female": int(row[2]) if row[2] else None,
        "permanent": int(row[3]) if row[3] else None,
        "temporary": int(row[4]) if row[4] else None,
        "cba_coverage_pct": float(row[5]) if row[5] else None,
        "gender_pay_gap_pct": float(row[6]) if row[6] else None,
        "fatalities": int(row[7]) if row[7] is not None else 0,
        "days_lost": int(row[8]) if row[8] is not None else 0,
        "remuneration_ratio": float(row[9]) if row[9] else None,
    }


def _get_governance(entity_id: str, db: Session) -> Optional[dict]:
    row = db.execute(text("""
        SELECT code_of_conduct_published, anti_corruption_policy_published,
               whistleblowing_mechanism_exists, functions_at_risk_covered_by_training_pct,
               convictions_anticorruption_antibribery_count, confirmed_corruption_incidents_count,
               avg_days_to_pay_invoice, payments_aligned_standard_terms_pct
        FROM esrs_g1_conduct WHERE entity_registry_id=:eid AND reporting_year=2024
    """), {"eid": entity_id}).fetchone()
    if not row:
        return {}
    return {
        "code_of_conduct": bool(row[0]),
        "anti_corruption_policy": bool(row[1]),
        "whistleblowing": bool(row[2]),
        "training_coverage_pct": float(row[3]) if row[3] else None,
        "corruption_convictions": int(row[4]) if row[4] is not None else 0,
        "corruption_incidents": int(row[5]) if row[5] is not None else 0,
        "avg_days_to_pay": float(row[6]) if row[6] else None,
        "payment_terms_compliance_pct": float(row[7]) if row[7] else None,
    }


def _get_financial_effects(entity_id: str, db: Session) -> Optional[dict]:
    row = db.execute(text("""
        SELECT scenario_set_used,
               assets_at_material_physical_risk_eur, assets_at_physical_risk_pct,
               assets_at_material_transition_risk_eur, assets_at_transition_risk_pct,
               stranded_assets_estimated_eur,
               monetised_scope1_scope2_ghg_eur, monetised_total_ghg_eur
        FROM esrs_e1_financial_effects WHERE entity_registry_id=:eid AND reporting_year=2024
    """), {"eid": entity_id}).fetchone()
    if not row:
        return {}
    return {
        "scenario": row[0],
        "physical_risk_eur": float(row[1]) if row[1] else None,
        "physical_risk_pct": float(row[2]) if row[2] else None,
        "transition_risk_eur": float(row[3]) if row[3] else None,
        "transition_risk_pct": float(row[4]) if row[4] else None,
        "stranded_assets_eur": float(row[5]) if row[5] else None,
        "monetised_scope12_eur": float(row[6]) if row[6] else None,
        "monetised_total_eur": float(row[7]) if row[7] else None,
    }


def _get_fi_data(fi_entity_id: str, db: Session) -> Optional[dict]:
    """Fetch FI-sector specific data."""
    fin = db.execute(text("""
        SELECT total_assets, loans_and_advances_gross, loans_and_advances_net,
               npl_ratio_pct, npl_coverage_ratio_pct, cet1_ratio_pct, tier1_ratio_pct,
               total_capital_ratio_pct, rwa, lcr_pct, nsfr_pct,
               cost_of_risk_bps, stage1_loans_pct, stage2_loans_pct, stage3_loans_pct,
               roe, rote, cost_income_ratio, net_interest_income, net_profit
        FROM fi_financials WHERE entity_id=:fid AND reporting_year=2024
    """), {"fid": fi_entity_id}).fetchone()

    lb = db.execute(text("""
        SELECT total_ead, total_loans_gross, carbon_intensive_sectors_pct,
               paris_aligned_pct, paris_aligned_ead,
               physical_risk_high_pct, physical_risk_high_ead,
               fossil_fuel_extraction_ead, coal_mining_ead, thermal_power_ead,
               green_loans_ead, sustainability_linked_loans_ead,
               real_estate_commercial_ead, real_estate_residential_ead,
               energy_oil_gas_ead, energy_renewables_ead, industrials_ead,
               transport_ead, retail_mortgage_ead
        FROM fi_loan_books WHERE entity_id=:fid AND reporting_year=2024
    """), {"fid": fi_entity_id}).fetchone()

    climate = db.execute(text("""
        SELECT financed_emissions_scope3_cat15_tco2e, waci_tco2e_per_meur_evic,
               portfolio_temperature_alignment_c, pcaf_data_quality_score_avg
        FROM fi_csrd_e1_climate WHERE entity_id=:fid AND reporting_year=2024
    """), {"fid": fi_entity_id}).fetchone()

    paris = db.execute(text("""
        SELECT net_zero_target_year, interim_2030_target_pct, coal_phase_out_committed,
               oil_sands_exclusion, arctic_drilling_exclusion,
               new_coal_financing_stopped, thermal_coal_threshold_pct
        FROM fi_paris_alignment WHERE entity_id=:fid
    """), {"fid": fi_entity_id}).fetchone()

    fin_keys = ["total_assets", "loans_gross", "loans_net",
                "npl_ratio_pct", "npl_coverage_pct", "cet1_ratio_pct", "tier1_ratio_pct",
                "total_capital_pct", "rwa", "lcr_pct", "nsfr_pct",
                "cost_of_risk_bps", "stage1_pct", "stage2_pct", "stage3_pct",
                "roe", "rote", "cost_income_ratio", "net_interest_income", "net_profit"]

    lb_keys = ["total_ead", "total_loans_gross", "carbon_intensive_pct",
               "paris_aligned_pct", "paris_aligned_ead",
               "physical_risk_high_pct", "physical_risk_high_ead",
               "fossil_fuel_ead", "coal_ead", "thermal_power_ead",
               "green_loans_ead", "sll_ead",
               "re_commercial_ead", "re_residential_ead",
               "energy_og_ead", "energy_ren_ead", "industrials_ead",
               "transport_ead", "retail_mortgage_ead"]

    return {
        "financials": dict(zip(fin_keys, [float(v) if v is not None and not isinstance(v, bool) else v for v in fin])) if fin else {},
        "loan_book": dict(zip(lb_keys, [float(v) if v is not None and not isinstance(v, bool) else v for v in lb])) if lb else {},
        "csrd_e1": {
            "financed_emissions_scope3_cat15_tco2e": float(climate[0]) if climate and climate[0] else None,
            "waci_tco2e_per_meur_evic": float(climate[1]) if climate and climate[1] else None,
            "portfolio_temperature_alignment_c": float(climate[2]) if climate and climate[2] else None,
            "pcaf_dqs_avg": float(climate[3]) if climate and climate[3] else None,
        } if climate else {},
        "paris_alignment": {
            "net_zero_target_year": int(paris[0]) if paris and paris[0] else None,
            "interim_2030_target_pct": float(paris[1]) if paris and paris[1] else None,
            "coal_phase_out": bool(paris[2]) if paris else False,
            "oil_sands_exclusion": bool(paris[3]) if paris else False,
            "arctic_exclusion": bool(paris[4]) if paris else False,
            "no_new_coal": bool(paris[5]) if paris else False,
            "coal_threshold_pct": float(paris[6]) if paris and paris[6] else None,
        } if paris else {},
    }


def _get_energy_ops(energy_entity_id: str, db: Session) -> Optional[dict]:
    """Fetch energy-sector specific operational data."""
    gen = db.execute(text("""
        SELECT total_installed_gw, coal_installed_gw, lignite_installed_gw,
               gas_ccgt_installed_gw, gas_ocgt_installed_gw, oil_installed_gw,
               nuclear_installed_gw, hydro_installed_gw,
               wind_onshore_installed_gw, wind_offshore_installed_gw,
               solar_pv_installed_gw, biomass_installed_gw,
               total_renewables_installed_gw, renewables_capacity_share_pct,
               low_carbon_capacity_share_pct,
               total_generation_twh, total_renewables_twh, renewables_generation_share_pct,
               avg_carbon_intensity_gco2_kwh,
               eu_ets_allowances_allocated, eu_ets_allowances_purchased,
               eu_ets_cost_meur, eu_ets_price_avg_eur_t,
               wind_onshore_cf_pct, wind_offshore_cf_pct, solar_cf_pct
        FROM energy_generation_mix WHERE entity_id=:eid AND reporting_year=2024
    """), {"eid": energy_entity_id}).fetchone()

    gen_keys = [
        "total_installed_gw", "coal_installed_gw", "lignite_installed_gw",
        "gas_ccgt_installed_gw", "gas_ocgt_installed_gw", "oil_installed_gw",
        "nuclear_installed_gw", "hydro_installed_gw",
        "wind_onshore_installed_gw", "wind_offshore_installed_gw",
        "solar_pv_installed_gw", "biomass_installed_gw",
        "total_renewables_installed_gw", "renewables_capacity_share_pct",
        "low_carbon_capacity_share_pct",
        "total_generation_twh", "total_renewables_twh", "renewables_generation_share_pct",
        "avg_carbon_intensity_gco2_kwh",
        "eu_ets_allowances_allocated", "eu_ets_allowances_purchased",
        "eu_ets_cost_meur", "eu_ets_price_avg_eur_t",
        "wind_onshore_cf_pct", "wind_offshore_cf_pct", "solar_cf_pct",
    ]

    fin = db.execute(text("""
        SELECT total_revenues, electricity_revenues, ebitda, ebitda_margin_pct,
               total_assets, net_debt, net_debt_to_ebitda,
               total_capex, growth_capex, green_capex, green_capex_pct,
               eu_taxonomy_aligned_capex_pct,
               green_bonds_outstanding_meur, sustainability_linked_bonds_meur
        FROM energy_financials WHERE entity_id=:eid AND reporting_year=2024
    """), {"eid": energy_entity_id}).fetchone()

    fin_keys = ["total_revenues", "electricity_revenues", "ebitda", "ebitda_margin_pct",
                "total_assets", "net_debt", "net_debt_to_ebitda",
                "total_capex", "growth_capex", "green_capex", "green_capex_pct",
                "eu_taxonomy_capex_pct",
                "green_bonds_meur", "sll_bonds_meur"]

    stranded = db.execute(text("""
        SELECT asset_name, fuel_type, country_iso, installed_capacity_mw,
               commissioning_year, planned_retirement_year, status,
               book_value_meur, stranded_value_at_risk_pct, stranded_value_at_risk_meur
        FROM energy_stranded_assets_register WHERE entity_id=:eid
    """), {"eid": energy_entity_id}).fetchall()

    pipeline = db.execute(text("""
        SELECT project_name, project_type, country_iso, capacity_mw,
               stage, cod_target_year, total_capex_meur, project_irr_pct,
               ppa_price_eur_mwh, eu_taxonomy_aligned
        FROM energy_renewable_pipeline WHERE entity_id=:eid
    """), {"eid": energy_entity_id}).fetchall()

    climate = db.execute(text("""
        SELECT scope1_gross_tco2e, scope2_market_based_tco2e, scope3_total_tco2e,
               carbon_intensity_scope1_gco2_kwh, carbon_intensity_scope12_gco2_kwh,
               e1_climate_status
        FROM energy_csrd_e1_climate WHERE entity_id=:eid AND reporting_year=2024
    """), {"eid": energy_entity_id}).fetchone()

    return {
        "generation_mix": dict(zip(gen_keys, [float(v) if v is not None else None for v in gen])) if gen else {},
        "financials": dict(zip(fin_keys, [float(v) if v is not None else None for v in fin])) if fin else {},
        "stranded_assets": [
            {
                "asset_name": r[0], "fuel_type": r[1], "country_iso": r[2],
                "installed_capacity_mw": float(r[3]) if r[3] else None,
                "commissioning_year": r[4], "planned_retirement_year": r[5], "status": r[6],
                "book_value_meur": float(r[7]) if r[7] else None,
                "stranded_value_at_risk_pct": float(r[8]) if r[8] else None,
                "stranded_value_at_risk_meur": float(r[9]) if r[9] else None,
            } for r in stranded
        ],
        "renewable_pipeline": [
            {
                "project_name": r[0], "project_type": r[1], "country_iso": r[2],
                "capacity_mw": float(r[3]) if r[3] else None,
                "stage": r[4], "cod_year": r[5],
                "capex_meur": float(r[6]) if r[6] else None,
                "irr_pct": float(r[7]) if r[7] else None,
                "ppa_price": float(r[8]) if r[8] else None,
                "eu_taxonomy_aligned": bool(r[9]),
            } for r in pipeline
        ],
        "climate": {
            "scope1_tco2e": float(climate[0]) if climate and climate[0] else None,
            "scope2_market_tco2e": float(climate[1]) if climate and climate[1] else None,
            "scope3_tco2e": float(climate[2]) if climate and climate[2] else None,
            "carbon_intensity_scope1": float(climate[3]) if climate and climate[3] else None,
            "carbon_intensity_scope12": float(climate[4]) if climate and climate[4] else None,
            "status": climate[5] if climate else None,
        },
    }
