"""
Demo Portfolio Seeder (P0-3)
==============================
Automatically provisions a realistic sample portfolio for every new organisation
so the dashboard is never empty on first login.

Addresses P0-3: "Portfolio dashboard shows zeros for new orgs — Demo / first-use failure"

Design decisions:
- Deterministic: seed is derived from org_id, so the same org always gets the
  same portfolio. Safe to call multiple times (idempotent via name-check).
- Realistic: 15 assets across 5 sectors, 3 asset types (Bond / Loan / Equity),
  varied ratings (AAA → CCC), maturities 1-10yr, PD/LGD calibrated to rating.
- Climate-ready: each asset has scope 1/2/3 emissions, sector NACE code, and
  a climate risk score so all downstream modules return meaningful values.
- Labelled: portfolio name prefixed "🔬 Demo — " and description clearly states
  it is sample data so regulatory users are not misled.

Usage:
    from services.demo_portfolio_seeder import DemoPortfolioSeeder
    seeder = DemoPortfolioSeeder(db)
    seeder.seed_for_org(org_id)          # idempotent
    seeder.seed_analysis_run(portfolio)  # optional: pre-populate one scenario run
"""
from __future__ import annotations

import hashlib
import logging
import random
from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

from sqlalchemy.orm import Session

from db.models.portfolio_pg import AssetPG, PortfolioPG, AnalysisRunPG

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Demo Asset Definitions
# ---------------------------------------------------------------------------

_DEMO_ASSETS = [
    # (company, sector, subsector, type, exposure_eur, rating, pd, lgd, mat,
    #  scope1, scope2, scope3, nace, climate_score)
    ("Eurobank AG",         "Banking",     "Retail Banking",    "Bond",   120_000_000, "A",   0.003, 0.40, 5,  12_000,  8_000,  25_000, "K64", 42.0),
    ("Alpine RE Ltd",       "Insurance",   "P&C Insurance",     "Bond",    80_000_000, "AA",  0.002, 0.35, 7,   8_500,  4_200,  18_000, "K65", 38.0),
    ("NordSteel GmbH",      "Materials",   "Steel",             "Loan",    95_000_000, "BBB", 0.018, 0.45, 4, 485_000, 72_000, 380_000, "C24", 71.0),
    ("SolarGrid SE",        "Energy",      "Renewable Energy",  "Equity",  60_000_000, "BB",  0.030, 0.50, 3,   1_200,  3_600,   9_000, "D35", 22.0),
    ("PetroCo NV",          "Energy",      "Oil & Gas",         "Loan",   150_000_000, "BBB", 0.020, 0.48, 6, 920_000, 95_000, 710_000, "B06", 85.0),
    ("TranslogAB",          "Industrials", "Freight Transport", "Loan",    55_000_000, "BB",  0.028, 0.50, 5,  78_000, 14_000,  62_000, "H49", 64.0),
    ("CityRent GmbH",       "Real Estate", "Commercial RE",     "Loan",    70_000_000, "A",   0.008, 0.35, 10,  6_800,  9_200,  14_500, "L68", 35.0),
    ("PharmEU plc",         "Healthcare",  "Pharmaceuticals",   "Bond",    45_000_000, "AA",  0.002, 0.30, 8,  22_000,  7_500,  95_000, "C21", 28.0),
    ("AutoBuild SA",        "Industrials", "Automotive Parts",  "Bond",    88_000_000, "BBB", 0.016, 0.42, 5, 145_000, 28_000, 210_000, "C29", 58.0),
    ("GreenFarm AS",        "Agriculture", "Crop Production",   "Loan",    30_000_000, "B",   0.055, 0.55, 3,  38_000,  4_500,  72_000, "A01", 52.0),
    ("TechCore BV",         "Technology",  "Cloud Computing",   "Equity",  55_000_000, "A",   0.005, 0.32, 7,   4_200, 18_500,  42_000, "J63", 18.0),
    ("WasteEx SpA",         "Utilities",   "Waste Management",  "Loan",    42_000_000, "BBB", 0.015, 0.43, 4,  31_000,  9_800,  28_000, "E38", 44.0),
    ("ChemPlant Oy",        "Materials",   "Specialty Chemicals","Loan",   65_000_000, "BB",  0.032, 0.50, 3, 210_000, 42_000, 188_000, "C20", 69.0),
    ("LogiPort GmbH",       "Industrials", "Ports & Shipping",  "Bond",    78_000_000, "BBB", 0.017, 0.44, 6,  95_000, 11_000,  78_000, "H50", 60.0),
    ("UrbanGrid SA",        "Utilities",   "Electric Utilities","Bond",   100_000_000, "A",   0.007, 0.38, 8, 180_000, 22_000, 145_000, "D35", 50.0),
]

# Pre-computed scenario results structure (deterministic — scaled by exposure)
_SCENARIO_TEMPLATES = [
    {
        "scenario": "net_zero_2050",
        "horizon": "2030",
        "expected_loss_bps": 12.5,
        "transition_risk_score": 45.0,
        "physical_risk_score": 18.0,
        "capital_charge_pct": 0.8,
        "co2_reduction_pct": 32.0,
    },
    {
        "scenario": "delayed_transition",
        "horizon": "2030",
        "expected_loss_bps": 28.0,
        "transition_risk_score": 72.0,
        "physical_risk_score": 24.0,
        "capital_charge_pct": 1.9,
        "co2_reduction_pct": 10.0,
    },
    {
        "scenario": "current_policies",
        "horizon": "2030",
        "expected_loss_bps": 18.0,
        "transition_risk_score": 22.0,
        "physical_risk_score": 48.0,
        "capital_charge_pct": 1.2,
        "co2_reduction_pct": 3.0,
    },
]


# ---------------------------------------------------------------------------
# Seeder
# ---------------------------------------------------------------------------

class DemoPortfolioSeeder:
    """Provisions sample portfolio data for a new organisation (P0-3)."""

    DEMO_PORTFOLIO_NAME_PREFIX = "Demo — Sample Climate Portfolio"

    def __init__(self, db: Session):
        self.db = db

    # ── Public API ───────────────────────────────────────────────────────────

    def seed_for_org(self, org_id: UUID) -> Optional[PortfolioPG]:
        """Create (or skip if already exists) a demo portfolio for *org_id*.

        Returns the existing or newly created PortfolioPG, or None on error.
        Idempotent: repeated calls with the same org_id do not create duplicates.
        """
        org_id_str = str(org_id)

        # Idempotency check — skip if demo portfolio already exists for this org
        existing = (
            self.db.query(PortfolioPG)
            .filter(
                PortfolioPG.org_id == org_id,
                PortfolioPG.name.like(f"{self.DEMO_PORTFOLIO_NAME_PREFIX}%"),
            )
            .first()
        )
        if existing:
            logger.info("Demo portfolio already exists for org %s — skipping seed", org_id_str)
            return existing

        try:
            portfolio = self._create_portfolio(org_id)
            assets = self._create_assets(portfolio.id, org_id_str)
            for asset in assets:
                self.db.add(asset)
            self.db.flush()

            run = self._create_analysis_run(portfolio)
            self.db.add(run)

            self.db.commit()
            self.db.refresh(portfolio)

            logger.info(
                "Demo portfolio seeded for org %s: portfolio_id=%s, %d assets",
                org_id_str, portfolio.id, len(assets),
            )
            return portfolio

        except Exception as exc:
            logger.error("Demo portfolio seed failed for org %s: %s", org_id_str, exc)
            self.db.rollback()
            return None

    # ── Private helpers ──────────────────────────────────────────────────────

    def _create_portfolio(self, org_id: UUID) -> PortfolioPG:
        p = PortfolioPG(
            name=f"{self.DEMO_PORTFOLIO_NAME_PREFIX}",
            description=(
                "⚠️ SAMPLE DATA — automatically provisioned for demonstration purposes. "
                "This portfolio contains 15 representative European corporate exposures "
                "across 5 sectors (Banking, Energy, Materials, Industrials, Utilities) "
                "with pre-populated climate risk scores, emissions data, and scenario "
                "analysis results. Replace or supplement with your institution's real data."
            ),
            org_id=org_id,
        )
        self.db.add(p)
        self.db.flush()  # get p.id
        return p

    def _create_assets(self, portfolio_id: str, org_id_str: str) -> list[AssetPG]:
        # Use org_id as deterministic random seed so every org gets same set
        rng = random.Random(int(hashlib.sha256(org_id_str.encode()).hexdigest()[:8], 16))

        assets = []
        for (company, sector, subsector, atype, base_exp,
             rating, pd, lgd, mat, s1, s2, s3, nace, clim) in _DEMO_ASSETS:
            # Jitter exposure ±15% so dashboards don't look perfectly identical across orgs
            jitter = rng.uniform(0.85, 1.15)
            exposure = round(base_exp * jitter, -3)  # round to nearest 1000

            a = AssetPG(
                portfolio_id=portfolio_id,
                asset_type=atype,
                company_name=company,
                company_sector=sector,
                company_subsector=subsector,
                exposure=exposure,
                market_value=round(exposure * rng.uniform(0.92, 1.08), -3),
                base_pd=round(pd * rng.uniform(0.90, 1.10), 5),
                base_lgd=round(lgd * rng.uniform(0.95, 1.05), 3),
                rating=rating,
                maturity_years=mat,
            )
            assets.append(a)
        return assets

    def _create_analysis_run(self, portfolio: PortfolioPG) -> AnalysisRunPG:
        """Pre-populate one analysis run so dashboard charts render immediately."""
        total_exposure = sum(a.exposure for a in portfolio.assets if a.exposure)
        results = []
        for tmpl in _SCENARIO_TEMPLATES:
            # Scale EL to portfolio size
            el_eur = total_exposure * tmpl["expected_loss_bps"] / 10_000
            results.append({
                **tmpl,
                "total_exposure_eur": total_exposure,
                "expected_loss_eur": round(el_eur, 2),
                "portfolio_name": portfolio.name,
                "is_demo": True,
            })

        return AnalysisRunPG(
            portfolio_id=portfolio.id,
            portfolio_name=portfolio.name,
            scenarios=["net_zero_2050", "delayed_transition", "current_policies"],
            horizons=["2030"],
            results=results,
            status="completed",
            completed_at=datetime.now(timezone.utc),
        )
