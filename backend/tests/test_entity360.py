"""
Tests for Entity 360 & Counterparty Master
=============================================
"""
import pytest

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from services.entity360_engine import (
    Entity360Engine,
    MODULE_REGISTRY,
    ENTITY_TYPES,
    SECTOR_MAP,
)

_engine = Entity360Engine()


# Helper — full module data for a well-covered entity
def _full_module_data():
    return {
        "carbon_calculator": {
            "scope1_tco2e": 50000,
            "scope2_tco2e": 20000,
            "scope3_tco2e": 80000,
            "total_tco2e": 150000,
            "intensity_revenue": 85,
        },
        "climate_risk": {
            "transition_risk_eur": 5000000,
            "physical_risk_eur": 2000000,
            "combined_risk_score": 45,
            "scenario_alignment": 0.7,
        },
        "ecl_calculator": {
            "pd_1yr": 0.02,
            "lgd_pct": 45,
            "ead_eur": 10000000,
            "ecl_eur": 90000,
            "ecl_stage": 1,
            "climate_overlay_eur": 5000,
        },
        "pcaf_calculator": {
            "financed_tco2e": 300000,
            "attribution_factor": 0.65,
            "data_quality_score": 2.5,
            "asset_class": 1,
        },
        "nature_risk": {
            "nature_risk_score": 35,
            "water_risk_score": 40,
            "biodiversity_score": 30,
            "tnfd_leap_priority": 2,
        },
        "taxonomy_alignment": {
            "taxonomy_eligible_pct": 80,
            "taxonomy_aligned_pct": 45,
            "dnsh_pass": 1,
            "minimum_safeguards": 1,
        },
        "scenario_analysis": {
            "nze_alignment_score": 0.65,
            "transition_pathway": 1,
            "stranded_asset_risk": 0.1,
            "carbon_price_impact": 500000,
        },
        "sfdr_pai": {
            "pai_1_ghg": 150000,
            "pai_2_footprint": 85,
            "pai_3_intensity": 120,
            "pai_4_fossil": 15,
            "pai_count_flagged": 2,
        },
        "real_estate": {
            "market_value": 25000000,
            "green_premium_pct": 8.5,
            "crrem_stranding_year": 2038,
            "epc_rating": 2,
        },
        "supply_chain": {
            "scope3_cat_breakdown": 80000,
            "supplier_risk_score": 60,
            "sbti_target_status": 1,
        },
    }


# ═══════════════════════════════════════════════════════════════════════════
# Entity 360 Profile Tests
# ═══════════════════════════════════════════════════════════════════════════

class TestEntity360Basic:
    """Basic profile building tests."""

    def test_empty_modules(self):
        res = _engine.build_profile("Empty Corp", "E001")
        assert res.entity_name == "Empty Corp"
        assert res.entity_id == "E001"
        assert res.modules_available == 0
        assert res.modules_total == 10
        assert res.data_completeness_pct == 0.0

    def test_full_modules(self):
        res = _engine.build_profile("Full Corp", "E002", module_data=_full_module_data())
        assert res.modules_available == 10
        assert res.data_completeness_pct == 100.0

    def test_partial_modules(self):
        data = {
            "carbon_calculator": {"total_tco2e": 100000},
            "climate_risk": {"combined_risk_score": 50},
        }
        res = _engine.build_profile("Partial Corp", "E003", module_data=data)
        assert res.modules_available == 2
        assert 15 < res.data_completeness_pct < 25

    def test_entity_type(self):
        res = _engine.build_profile("FI Corp", "E004", entity_type="fi")
        assert res.entity_type == "fi"

    def test_sector_label(self):
        res = _engine.build_profile("Energy Corp", "E005", sector="energy")
        assert res.sector_label == "Energy (Oil & Gas / Utilities)"

    def test_unknown_sector(self):
        res = _engine.build_profile("Unknown Corp", "E006", sector="unknown_sector")
        assert res.sector_label == "unknown_sector"

    def test_reporting_year(self):
        res = _engine.build_profile("Year Corp", "E007", reporting_year=2025)
        assert res.reporting_year == 2025


class TestModuleScores:
    """Module score detail tests."""

    def test_module_count(self):
        res = _engine.build_profile("Mod Corp", "M001", module_data=_full_module_data())
        assert len(res.module_scores) == 10

    def test_high_quality_module(self):
        data = {
            "carbon_calculator": {
                "scope1_tco2e": 50000,
                "scope2_tco2e": 20000,
                "scope3_tco2e": 80000,
                "total_tco2e": 150000,
                "intensity_revenue": 85,
            }
        }
        res = _engine.build_profile("HQ Corp", "M002", module_data=data)
        carbon_mod = next(m for m in res.module_scores if m.module_id == "carbon_calculator")
        assert carbon_mod.data_available is True
        assert carbon_mod.data_quality == "high"

    def test_medium_quality_module(self):
        data = {
            "carbon_calculator": {
                "scope1_tco2e": 50000,
                "total_tco2e": 100000,
                "intensity_revenue": 90,
            }
        }
        res = _engine.build_profile("MQ Corp", "M003", module_data=data)
        carbon_mod = next(m for m in res.module_scores if m.module_id == "carbon_calculator")
        assert carbon_mod.data_quality == "medium"

    def test_low_quality_module(self):
        data = {"carbon_calculator": {"total_tco2e": 100000}}
        res = _engine.build_profile("LQ Corp", "M004", module_data=data)
        carbon_mod = next(m for m in res.module_scores if m.module_id == "carbon_calculator")
        assert carbon_mod.data_quality == "low"

    def test_no_data_module(self):
        res = _engine.build_profile("NoData Corp", "M005")
        carbon_mod = next(m for m in res.module_scores if m.module_id == "carbon_calculator")
        assert carbon_mod.data_available is False
        assert carbon_mod.data_quality == "none"


class TestRiskProfile:
    """Risk profile aggregation tests."""

    def test_full_risk_scores(self):
        res = _engine.build_profile("Risk Corp", "R001", module_data=_full_module_data())
        rp = res.risk_profile
        assert rp.credit_risk_score is not None
        assert rp.climate_risk_score is not None
        assert rp.nature_risk_score is not None
        assert rp.regulatory_risk_score is not None
        assert rp.composite_risk_score > 0

    def test_no_data_default_risk(self):
        res = _engine.build_profile("Default Corp", "R002")
        assert res.risk_profile.composite_risk_score == 50
        assert res.risk_profile.risk_band == "medium"

    def test_low_risk_band(self):
        data = {
            "ecl_calculator": {"pd_1yr": 0.005},
            "climate_risk": {"combined_risk_score": 10},
            "nature_risk": {"nature_risk_score": 10},
            "taxonomy_alignment": {"taxonomy_aligned_pct": 90},
        }
        res = _engine.build_profile("Low Risk", "R003", module_data=data)
        assert res.risk_profile.risk_band == "low"

    def test_high_risk_band(self):
        data = {
            "ecl_calculator": {"pd_1yr": 0.08},
            "climate_risk": {"combined_risk_score": 80},
            "nature_risk": {"nature_risk_score": 85},
            "taxonomy_alignment": {"taxonomy_aligned_pct": 5},
        }
        res = _engine.build_profile("High Risk", "R004", module_data=data)
        assert res.risk_profile.risk_band in ("high", "very_high")

    def test_credit_risk_pd_scaling(self):
        data = {"ecl_calculator": {"pd_1yr": 0.05}}
        res = _engine.build_profile("PD Corp", "R005", module_data=data)
        # 0.05 * 1000 = 50
        assert res.risk_profile.credit_risk_score == 50.0

    def test_regulatory_risk_from_taxonomy(self):
        data = {"taxonomy_alignment": {"taxonomy_aligned_pct": 30}}
        res = _engine.build_profile("Tax Corp", "R006", module_data=data)
        # 100 - 30 = 70
        assert res.risk_profile.regulatory_risk_score == 70.0


class TestESGProfile:
    """ESG profile tests."""

    def test_full_esg(self):
        res = _engine.build_profile("ESG Corp", "G001", module_data=_full_module_data())
        ep = res.esg_profile
        assert ep.total_ghg_tco2e == 150000
        assert ep.ghg_intensity == 85
        assert ep.taxonomy_aligned_pct == 45
        assert ep.pai_flags == 2

    def test_no_data_esg(self):
        res = _engine.build_profile("NoESG Corp", "G002")
        ep = res.esg_profile
        assert ep.total_ghg_tco2e is None
        assert ep.esg_rating in ("B", "C")  # Baseline 50 + low pai → 60 → B

    def test_high_esg_rating(self):
        data = {
            "carbon_calculator": {
                "total_tco2e": 50000,
                "intensity_revenue": 40,
            },
            "taxonomy_alignment": {"taxonomy_aligned_pct": 60},
            "sfdr_pai": {"pai_count_flagged": 1},
        }
        res = _engine.build_profile("Green Corp", "G003", module_data=data)
        assert res.esg_profile.esg_rating == "A"

    def test_low_esg_rating(self):
        data = {
            "carbon_calculator": {
                "total_tco2e": 500000,
                "intensity_revenue": 300,
            },
            "taxonomy_alignment": {"taxonomy_aligned_pct": 5},
            "sfdr_pai": {"pai_count_flagged": 8},
        }
        res = _engine.build_profile("Brown Corp", "G004", module_data=data)
        assert res.esg_profile.esg_rating in ("C", "D")


class TestRegulatoryStatus:
    """Regulatory status assessment tests."""

    def test_all_assessed(self):
        res = _engine.build_profile("Reg Corp", "REG01", module_data=_full_module_data())
        assert "EU_Taxonomy" in res.regulatory_status
        assert "SFDR_PAI" in res.regulatory_status
        assert "CSRD_E1" in res.regulatory_status
        assert "TCFD" in res.regulatory_status

    def test_taxonomy_aligned(self):
        data = {"taxonomy_alignment": {"taxonomy_aligned_pct": 45}}
        res = _engine.build_profile("Aligned Corp", "REG02", module_data=data)
        assert res.regulatory_status["EU_Taxonomy"] == "aligned"

    def test_taxonomy_partial(self):
        data = {"taxonomy_alignment": {"taxonomy_aligned_pct": 10}}
        res = _engine.build_profile("Partial Align", "REG03", module_data=data)
        assert res.regulatory_status["EU_Taxonomy"] == "partially_aligned"

    def test_no_assessment(self):
        res = _engine.build_profile("NoReg Corp", "REG04")
        assert res.regulatory_status["EU_Taxonomy"] == "not_assessed"
        assert res.regulatory_status["SFDR_PAI"] == "not_assessed"

    def test_sfdr_compliant(self):
        data = {"sfdr_pai": {"pai_count_flagged": 2}}
        res = _engine.build_profile("SFDR Corp", "REG05", module_data=data)
        assert res.regulatory_status["SFDR_PAI"] == "compliant"

    def test_sfdr_review_needed(self):
        data = {"sfdr_pai": {"pai_count_flagged": 5}}
        res = _engine.build_profile("SFDR Bad", "REG06", module_data=data)
        assert res.regulatory_status["SFDR_PAI"] == "review_needed"


class TestRecommendations:
    """Recommendation generation tests."""

    def test_empty_has_recommendations(self):
        res = _engine.build_profile("Rec Corp", "REC01")
        assert len(res.recommendations) > 0

    def test_carbon_recommended_when_missing(self):
        res = _engine.build_profile("NoCO2 Corp", "REC02")
        recs = " | ".join(res.recommendations)
        assert "Carbon Calculator" in recs

    def test_ecl_recommended_when_missing(self):
        res = _engine.build_profile("NoECL Corp", "REC03")
        recs = " | ".join(res.recommendations)
        assert "ECL Calculator" in recs

    def test_high_risk_triggers_edd(self):
        data = {
            "ecl_calculator": {"pd_1yr": 0.08},
            "climate_risk": {"combined_risk_score": 80},
            "nature_risk": {"nature_risk_score": 85},
            "taxonomy_alignment": {"taxonomy_aligned_pct": 5},
        }
        res = _engine.build_profile("HighRisk Corp", "REC04", module_data=data)
        recs = " | ".join(res.recommendations)
        assert "enhanced due diligence" in recs.lower()

    def test_max_six_recommendations(self):
        res = _engine.build_profile("Capped Corp", "REC05")
        assert len(res.recommendations) <= 6


class TestDataGaps:
    """Data gap identification tests."""

    def test_empty_has_all_gaps(self):
        res = _engine.build_profile("Gaps Corp", "GAP01")
        assert len(res.data_gaps) == 10  # All modules missing

    def test_full_has_no_gaps(self):
        res = _engine.build_profile("Full Corp", "GAP02", module_data=_full_module_data())
        assert len(res.data_gaps) == 0

    def test_partial_gaps(self):
        data = {"carbon_calculator": {"total_tco2e": 100000}}
        res = _engine.build_profile("Partial Corp", "GAP03", module_data=data)
        assert len(res.data_gaps) == 9


# ═══════════════════════════════════════════════════════════════════════════
# Counterparty Master Tests
# ═══════════════════════════════════════════════════════════════════════════

class TestCounterpartyMaster:
    """Counterparty master build tests."""

    def test_basic_master(self):
        cps = [
            {"entity_id": "C001", "entity_name": "Alpha Corp", "lei": "52990067Q1LKZLGZTH72", "sector": "energy", "country": "DE"},
            {"entity_id": "C002", "entity_name": "Beta Ltd", "lei": "549300NBLHT5Z7ZV1T08", "sector": "financials", "country": "NL"},
        ]
        res = _engine.build_counterparty_master(cps)
        assert res.total_counterparties == 2
        assert len(res.counterparties) == 2

    def test_empty_master(self):
        res = _engine.build_counterparty_master([])
        assert res.total_counterparties == 0
        assert res.data_quality_avg == 0

    def test_duplicate_detection(self):
        cps = [
            {"entity_id": "D001", "entity_name": "Acme Corp"},
            {"entity_id": "D002", "entity_name": "Acme Corp"},
            {"entity_id": "D003", "entity_name": "Other Inc"},
        ]
        res = _engine.build_counterparty_master(cps)
        assert len(res.duplicate_groups) == 1
        assert res.duplicate_groups[0]["canonical_id"] == "D001"
        assert "D002" in res.duplicate_groups[0]["duplicates"]

    def test_dedup_case_insensitive(self):
        cps = [
            {"entity_id": "D010", "entity_name": "Alpha Corp"},
            {"entity_id": "D011", "entity_name": "alpha corp"},
        ]
        res = _engine.build_counterparty_master(cps)
        assert len(res.duplicate_groups) == 1

    def test_dedup_whitespace_normalised(self):
        cps = [
            {"entity_id": "D020", "entity_name": "Beta  Corp"},
            {"entity_id": "D021", "entity_name": "BetaCorp"},
        ]
        res = _engine.build_counterparty_master(cps)
        assert len(res.duplicate_groups) == 1


class TestCounterpartyQuality:
    """Data quality scoring tests."""

    def test_max_quality(self):
        cp = {
            "entity_id": "Q001",
            "entity_name": "Quality Corp",
            "lei": "52990067Q1LKZLGZTH72",
            "sector": "energy",
            "country": "DE",
            "group_name": "Quality Group",
            "modules_linked": ["carbon_calculator", "ecl_calculator", "climate_risk"],
        }
        res = _engine.build_counterparty_master([cp])
        assert res.counterparties[0].data_quality_score == 100

    def test_minimal_quality(self):
        cp = {"entity_id": "Q002", "entity_name": "Bare Corp"}
        res = _engine.build_counterparty_master([cp])
        assert res.counterparties[0].data_quality_score == 0

    def test_lei_adds_30(self):
        cp_with = {"entity_id": "Q010", "entity_name": "A", "lei": "52990067Q1LKZLGZTH72"}
        cp_without = {"entity_id": "Q011", "entity_name": "B", "lei": ""}
        res = _engine.build_counterparty_master([cp_with, cp_without])
        assert res.counterparties[0].data_quality_score - res.counterparties[1].data_quality_score == 30

    def test_low_quality_count(self):
        cps = [
            {"entity_id": "Q020", "entity_name": "A"},
            {"entity_id": "Q021", "entity_name": "B"},
            {"entity_id": "Q022", "entity_name": "C", "lei": "52990067Q1LKZLGZTH72", "sector": "energy", "country": "DE"},
        ]
        res = _engine.build_counterparty_master(cps)
        assert res.low_quality_count == 2  # A and B have score 0


class TestCounterpartyDistributions:
    """Distribution analytics tests."""

    def test_sector_distribution(self):
        cps = [
            {"entity_id": "S001", "entity_name": "A", "sector": "energy"},
            {"entity_id": "S002", "entity_name": "B", "sector": "energy"},
            {"entity_id": "S003", "entity_name": "C", "sector": "financials"},
        ]
        res = _engine.build_counterparty_master(cps)
        assert res.sector_distribution["energy"] == 2
        assert res.sector_distribution["financials"] == 1

    def test_entity_type_distribution(self):
        cps = [
            {"entity_id": "T001", "entity_name": "A", "entity_type": "corporate"},
            {"entity_id": "T002", "entity_name": "B", "entity_type": "fi"},
            {"entity_id": "T003", "entity_name": "C", "entity_type": "fi"},
        ]
        res = _engine.build_counterparty_master(cps)
        assert res.entity_type_distribution["fi"] == 2
        assert res.entity_type_distribution["corporate"] == 1


# ═══════════════════════════════════════════════════════════════════════════
# Reference Data Tests
# ═══════════════════════════════════════════════════════════════════════════

class TestRefData:
    """Reference data endpoint tests."""

    def test_module_registry(self):
        reg = _engine.get_module_registry()
        assert len(reg) == 10
        assert "carbon_calculator" in reg
        assert "outputs" in reg["carbon_calculator"]

    def test_entity_types(self):
        types = _engine.get_entity_types()
        assert len(types) == 7
        ids = [t["id"] for t in types]
        assert "corporate" in ids
        assert "fi" in ids

    def test_sectors(self):
        sectors = _engine.get_sectors()
        assert len(sectors) == 12
        assert "energy" in sectors
        assert "financials" in sectors
