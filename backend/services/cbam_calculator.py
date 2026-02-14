"""
CBAM Calculation Engine — emissions, costs, projections, compliance scoring.

Implements EU CBAM regulation methodology:
- Specific Embedded Emissions (SEE) per Article 7
- CBAM certificate cost per Article 21
- Free allocation phase-out per Article 31
- Default values with markup per Article 4
"""

from decimal import Decimal, ROUND_HALF_UP
from typing import Dict, List, Optional, Tuple
from sqlalchemy.orm import Session

from db.models.cbam import (
    CBAMProductCategory, CBAMSupplier, CBAMEmbeddedEmissions,
    CBAMCountryRisk, CBAMCertificatePrice,
)


class CBAMEmissionsCalculator:
    """Calculate embedded emissions for CBAM goods per EU regulation."""

    # Default value markup per Article 4(3) of CBAM Implementing Regulation
    DEFAULT_MARKUP_FULL = Decimal("0.30")      # 30% when no actual data available
    DEFAULT_MARKUP_PARTIAL = Decimal("0.10")   # 10% when partial data available
    CO2_MOLECULAR_RATIO = Decimal("3.664")     # CO2/C molecular weight ratio

    # Global average grid emission factor (tCO2/MWh) — IEA 2023
    GLOBAL_AVG_GRID_EF = Decimal("0.436")

    def __init__(self, db: Session):
        self.db = db

    def calculate_embedded_emissions(
        self,
        supplier_id: str,
        product_category_id: str,
        production_volume_tonnes: Decimal,
        direct_emissions_data: Optional[Dict] = None,
        indirect_emissions_data: Optional[Dict] = None,
        electricity_consumed_mwh: Optional[Decimal] = None,
        use_defaults: bool = False,
    ) -> Dict:
        """
        Calculate Specific Embedded Emissions (SEE) for CBAM goods.

        SEE = (direct attributed emissions + indirect attributed emissions) / production volume

        Returns calculation result with specific emissions per tonne of product.
        """
        import uuid

        product = self.db.get(CBAMProductCategory, product_category_id)
        supplier = self.db.get(CBAMSupplier, supplier_id)

        if production_volume_tonnes <= 0:
            raise ValueError("Production volume must be positive")

        # --- Direct emissions ---
        if use_defaults or not direct_emissions_data:
            # Use default values from product category
            see_direct = Decimal(str(product.default_direct_emissions or 0)) if product else Decimal("0")
            direct_attributed = see_direct * production_volume_tonnes
            direct_is_default = True
        else:
            direct_attributed = self._calculate_direct_from_data(direct_emissions_data)
            see_direct = direct_attributed / production_volume_tonnes
            direct_is_default = False

        # --- Indirect emissions ---
        if use_defaults or (not indirect_emissions_data and electricity_consumed_mwh is None):
            see_indirect = Decimal(str(product.default_indirect_emissions or 0)) if product else Decimal("0")
            indirect_attributed = see_indirect * production_volume_tonnes
            indirect_is_default = True
        else:
            if electricity_consumed_mwh is not None:
                # Calculate from electricity consumption + grid emission factor
                grid_ef = self._get_grid_emission_factor(supplier.country_code if supplier else None)
                indirect_attributed = electricity_consumed_mwh * grid_ef
            else:
                indirect_attributed = self._calculate_indirect_from_data(indirect_emissions_data)
            see_indirect = indirect_attributed / production_volume_tonnes
            indirect_is_default = False

        # --- Apply default value markup ---
        uses_defaults = direct_is_default or indirect_is_default
        markup = Decimal("0")
        if direct_is_default and indirect_is_default:
            markup = self.DEFAULT_MARKUP_FULL
        elif direct_is_default or indirect_is_default:
            markup = self.DEFAULT_MARKUP_PARTIAL

        see_total = see_direct + see_indirect
        if markup > 0:
            see_total = see_total * (Decimal("1") + markup)

        total_embedded = see_total * production_volume_tonnes

        return {
            "calculation_id": str(uuid.uuid4()),
            "supplier_id": supplier_id,
            "product_category_id": product_category_id,
            "production_volume_tonnes": float(production_volume_tonnes),
            "specific_direct_emissions": float(see_direct.quantize(Decimal("0.000001"), ROUND_HALF_UP)),
            "specific_indirect_emissions": float(see_indirect.quantize(Decimal("0.000001"), ROUND_HALF_UP)),
            "specific_total_emissions": float(see_total.quantize(Decimal("0.000001"), ROUND_HALF_UP)),
            "total_embedded_emissions_tco2": float(total_embedded.quantize(Decimal("0.01"), ROUND_HALF_UP)),
            "direct_attributed_tco2": float(direct_attributed.quantize(Decimal("0.01"), ROUND_HALF_UP)),
            "indirect_attributed_tco2": float(indirect_attributed.quantize(Decimal("0.01"), ROUND_HALF_UP)),
            "uses_default_values": uses_defaults,
            "default_value_markup_applied": float(markup),
            "markup_type": "full" if markup == self.DEFAULT_MARKUP_FULL else ("partial" if markup > 0 else "none"),
        }

    def _calculate_direct_from_data(self, data: Dict) -> Decimal:
        """
        Calculate direct emissions from source stream data.
        Standard method: Sum of (activity data × emission factor) for each source stream.
        """
        total = Decimal("0")
        for source in data.get("source_streams", []):
            activity = Decimal(str(source.get("quantity", 0)))
            ef = Decimal(str(source.get("emission_factor", 0)))
            oxidation = Decimal(str(source.get("oxidation_factor", 1)))
            total += activity * ef * oxidation

        # Add process emissions if any
        process = Decimal(str(data.get("process_emissions", 0)))
        total += process

        return total

    def _calculate_indirect_from_data(self, data: Dict) -> Decimal:
        """Calculate indirect emissions from electricity/heat consumption data."""
        total = Decimal("0")
        for source in data.get("electricity_sources", []):
            mwh = Decimal(str(source.get("mwh_consumed", 0)))
            ef = Decimal(str(source.get("emission_factor", self.GLOBAL_AVG_GRID_EF)))
            total += mwh * ef
        return total

    def _get_grid_emission_factor(self, country_code: Optional[str]) -> Decimal:
        """Get grid emission factor for a country. Falls back to global average."""
        if country_code:
            country = self.db.query(CBAMCountryRisk).filter(
                CBAMCountryRisk.country_code == country_code
            ).first()
            if country and country.grid_emission_factor:
                return Decimal(str(country.grid_emission_factor))
        return self.GLOBAL_AVG_GRID_EF


class CBAMCostProjector:
    """Project CBAM certificate costs over time."""

    # EU CBAM free allocation phase-out schedule
    FREE_ALLOCATION_SCHEDULE = {
        2025: Decimal("100"),  # Transitional period — reporting only, no certificates
        2026: Decimal("97.5"),
        2027: Decimal("95.0"),
        2028: Decimal("90.0"),
        2029: Decimal("77.5"),
        2030: Decimal("51.5"),
        2031: Decimal("39.0"),
        2032: Decimal("26.5"),
        2033: Decimal("14.0"),
        2034: Decimal("0"),
    }

    # Default ETS price scenarios (EUR/tCO2)
    ETS_SCENARIOS = {
        "current_trend": {
            2025: 70, 2026: 75, 2027: 80, 2028: 85, 2029: 90,
            2030: 95, 2031: 100, 2032: 108, 2033: 115, 2034: 125,
            2035: 135, 2040: 165, 2045: 185, 2050: 210,
        },
        "ambitious": {
            2025: 80, 2026: 95, 2027: 115, 2028: 135, 2029: 155,
            2030: 180, 2031: 200, 2032: 230, 2033: 260, 2034: 300,
            2035: 340, 2040: 420, 2045: 470, 2050: 520,
        },
        "conservative": {
            2025: 60, 2026: 63, 2027: 65, 2028: 68, 2029: 70,
            2030: 75, 2031: 78, 2032: 80, 2033: 83, 2034: 85,
            2035: 90, 2040: 110, 2045: 120, 2050: 135,
        },
    }

    def __init__(self, db: Session):
        self.db = db
        self.emissions_calc = CBAMEmissionsCalculator(db)

    def project_supplier_costs(
        self,
        supplier_id: str,
        start_year: int = 2026,
        end_year: int = 2040,
        scenario: str = "current_trend",
    ) -> List[Dict]:
        """
        Project CBAM costs for a supplier from start_year to end_year.

        Methodology:
        1. Get latest emissions data for supplier
        2. For each projection year:
           a. Get EU ETS price (from scenario or DB)
           b. Get free allocation percentage
           c. Get domestic carbon price credit
           d. Calculate: net_cost = (emissions × ETS_price) - domestic_credit - free_allocation_reduction
        """
        supplier = self.db.get(CBAMSupplier, supplier_id)
        if not supplier:
            return []

        # Get latest emissions record
        latest_emissions = self.db.query(CBAMEmbeddedEmissions).filter(
            CBAMEmbeddedEmissions.supplier_id == supplier_id
        ).order_by(CBAMEmbeddedEmissions.reporting_year.desc()).first()

        if not latest_emissions:
            return []

        annual_volume = float(latest_emissions.import_volume_tonnes or 0)
        specific_emissions = float(latest_emissions.specific_total or 0)
        if specific_emissions == 0:
            specific_emissions = float(latest_emissions.direct_emissions or 0) / max(annual_volume, 1)
        annual_emissions = annual_volume * specific_emissions

        domestic_price = float(supplier.domestic_carbon_price or 0)
        ets_prices = self.ETS_SCENARIOS.get(scenario, self.ETS_SCENARIOS["current_trend"])

        projections = []
        for year in range(start_year, end_year + 1):
            ets_price = self._interpolate_price(ets_prices, year)
            free_pct = float(self.FREE_ALLOCATION_SCHEDULE.get(year, Decimal("0")))

            gross_cost = annual_emissions * ets_price
            domestic_credit = annual_emissions * domestic_price
            free_reduction = gross_cost * (free_pct / 100)
            net_cost = max(0, gross_cost - domestic_credit - free_reduction)

            projections.append({
                "year": year,
                "scenario": scenario,
                "import_volume_tonnes": round(annual_volume, 2),
                "embedded_emissions_tco2": round(annual_emissions, 4),
                "eu_ets_price_eur": round(ets_price, 2),
                "domestic_carbon_credit_eur": round(domestic_credit, 2),
                "free_allocation_pct": round(free_pct, 1),
                "gross_cbam_cost_eur": round(gross_cost, 2),
                "net_cbam_cost_eur": round(net_cost, 2),
            })

        return projections

    def calculate_portfolio_exposure(
        self,
        supplier_ids: List[str],
        year: int = 2030,
        scenario: str = "current_trend",
    ) -> Dict:
        """Calculate total CBAM exposure across multiple suppliers."""
        total_cost = 0
        total_emissions = 0
        supplier_details = []

        for sid in supplier_ids:
            projections = self.project_supplier_costs(sid, year, year, scenario)
            if projections:
                p = projections[0]
                total_cost += p["net_cbam_cost_eur"]
                total_emissions += p["embedded_emissions_tco2"]
                supplier = self.db.get(CBAMSupplier, sid)
                supplier_details.append({
                    "supplier_id": sid,
                    "supplier_name": supplier.supplier_name if supplier else "Unknown",
                    "country_code": supplier.country_code if supplier else "??",
                    "net_cost": p["net_cbam_cost_eur"],
                    "emissions": p["embedded_emissions_tco2"],
                })

        return {
            "year": year,
            "scenario": scenario,
            "total_net_cbam_cost_eur": round(total_cost, 2),
            "total_embedded_emissions_tco2": round(total_emissions, 4),
            "supplier_count": len(supplier_details),
            "supplier_details": sorted(supplier_details, key=lambda x: x["net_cost"], reverse=True),
        }

    def _interpolate_price(self, prices: Dict, year: int) -> float:
        """Interpolate ETS price for a given year."""
        years = sorted(prices.keys())
        if year in prices:
            return prices[year]
        if year < years[0]:
            return prices[years[0]]
        if year > years[-1]:
            return prices[years[-1]]
        # Linear interpolation
        prev_y = max(y for y in years if y <= year)
        next_y = min(y for y in years if y >= year)
        if prev_y == next_y:
            return prices[prev_y]
        frac = (year - prev_y) / (next_y - prev_y)
        return prices[prev_y] + frac * (prices[next_y] - prices[prev_y])


class CBAMComplianceScorer:
    """Score compliance readiness for CBAM reporting."""

    def __init__(self, db: Session):
        self.db = db

    def score_supplier_compliance(self, supplier_id: str) -> Dict:
        """
        Score a supplier's CBAM compliance readiness (0-100).

        Factors:
        - Verification status (30%)
        - Data completeness (30%)
        - Domestic carbon pricing (20%)
        - Country risk (20%)
        """
        supplier = self.db.get(CBAMSupplier, supplier_id)
        if not supplier:
            return {"score": 0, "status": "unknown"}

        scores = {}

        # Verification (30%)
        verification_scores = {"verified": 100, "pending": 50, "unverified": 10, "expired": 0}
        scores["verification"] = verification_scores.get(supplier.verification_status, 10)

        # Data completeness (30%)
        emissions = self.db.query(CBAMEmbeddedEmissions).filter(
            CBAMEmbeddedEmissions.supplier_id == supplier_id
        ).all()
        if emissions:
            verified_count = sum(1 for e in emissions if e.is_verified)
            default_count = sum(1 for e in emissions if e.uses_default_values)
            scores["data_completeness"] = min(100, (len(emissions) - default_count) / max(len(emissions), 1) * 80 + 20)
        else:
            scores["data_completeness"] = 0

        # Domestic carbon pricing (20%)
        scores["carbon_pricing"] = 80 if supplier.has_domestic_carbon_price else 20

        # Country risk (20%)
        country = self.db.query(CBAMCountryRisk).filter(
            CBAMCountryRisk.country_code == supplier.country_code
        ).first()
        risk_scores = {"Low": 90, "Medium": 60, "High": 35, "Very High": 15}
        scores["country_risk"] = risk_scores.get(country.risk_category, 40) if country else 40

        # Weighted total
        total = (
            scores["verification"] * 0.30 +
            scores["data_completeness"] * 0.30 +
            scores["carbon_pricing"] * 0.20 +
            scores["country_risk"] * 0.20
        )

        status = "compliant" if total >= 70 else ("at_risk" if total >= 40 else "non_compliant")

        return {
            "supplier_id": supplier_id,
            "overall_score": round(total, 1),
            "status": status,
            "breakdown": scores,
            "recommendations": self._generate_recommendations(scores),
        }

    def _generate_recommendations(self, scores: Dict) -> List[str]:
        """Generate actionable recommendations based on scores."""
        recs = []
        if scores.get("verification", 0) < 50:
            recs.append("Initiate third-party verification of emissions data")
        if scores.get("data_completeness", 0) < 50:
            recs.append("Replace default emission values with actual measured data")
        if scores.get("carbon_pricing", 0) < 50:
            recs.append("Explore suppliers in countries with domestic carbon pricing for cost offsets")
        if scores.get("country_risk", 0) < 50:
            recs.append("Consider supply chain diversification to lower-risk jurisdictions")
        if not recs:
            recs.append("Maintain current compliance posture — all indicators healthy")
        return recs
