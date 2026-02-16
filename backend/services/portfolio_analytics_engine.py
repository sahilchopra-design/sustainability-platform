"""
Portfolio Aggregation and Analytics Engine
Consolidates property valuations into portfolio-level analytics
"""

from decimal import Decimal
from typing import Dict, List, Optional, Any, Tuple
from uuid import uuid4, UUID
from datetime import date, datetime, timezone
import copy
import random
import math

from schemas.portfolio_analytics import (
    PortfolioType, InvestmentStrategy, ReportType, RiskLevel,
    PortfolioSummary, RiskMetrics, StrandingAnalysis,
    SustainabilityMetrics, ConcentrationMetrics, ConcentrationAnalysis,
    PortfolioAnalyticsResponse, ScenarioComparisonRow, ScenarioComparisonResult,
    KPICard, ChartData, Alert, DashboardResponse,
    PropertySummary, ReportContent,
)


# ============ Sample Data ============

def get_sample_portfolios() -> Dict[str, Dict]:
    """Sample portfolios for demonstration."""
    return {
        "portfolio-001": {
            "id": "00000000-0000-0000-0000-000000000101",
            "name": "Core Real Estate Fund I",
            "description": "Diversified core real estate portfolio focused on Class A office and multifamily assets",
            "portfolio_type": "fund",
            "investment_strategy": "core",
            "target_return": Decimal("7.5"),
            "aum": Decimal("2500000000"),
            "currency": "USD",
            "inception_date": date(2015, 6, 1),
            "owner_id": None,
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
        },
        "portfolio-002": {
            "id": "00000000-0000-0000-0000-000000000102",
            "name": "Value-Add Opportunity Fund II",
            "description": "Value-add strategy targeting repositioning opportunities in secondary markets",
            "portfolio_type": "fund",
            "investment_strategy": "value_add",
            "target_return": Decimal("12.0"),
            "aum": Decimal("850000000"),
            "currency": "USD",
            "inception_date": date(2020, 3, 15),
            "owner_id": None,
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
        },
        "portfolio-003": {
            "id": "00000000-0000-0000-0000-000000000103",
            "name": "Green Building REIT",
            "description": "Focused on certified green buildings with strong sustainability credentials",
            "portfolio_type": "reit",
            "investment_strategy": "core_plus",
            "target_return": Decimal("9.0"),
            "aum": Decimal("1200000000"),
            "currency": "USD",
            "inception_date": date(2018, 9, 1),
            "owner_id": None,
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
        },
    }


def get_sample_holdings() -> Dict[str, List[Dict]]:
    """Sample holdings for each portfolio."""
    return {
        "00000000-0000-0000-0000-000000000101": [
            {
                "id": str(uuid4()),
                "portfolio_id": "00000000-0000-0000-0000-000000000101",
                "property_id": "00000000-0000-0000-0000-000000000001",
                "property_name": "Downtown Office Tower",
                "property_type": "office",
                "property_location": "New York, NY",
                "acquisition_date": date(2016, 3, 15),
                "acquisition_cost": Decimal("380000000"),
                "current_value": Decimal("435000000"),
                "ownership_percentage": Decimal("1.0"),
                "annual_income": Decimal("23940000"),
                "unrealized_gain_loss": Decimal("55000000"),
                "gresb_score": 76,
                "certifications": ["LEED Gold"],
                "risk_score": 35,
                "is_stranded": False,
            },
            {
                "id": str(uuid4()),
                "portfolio_id": "00000000-0000-0000-0000-000000000101",
                "property_id": "00000000-0000-0000-0000-000000000002",
                "property_name": "Suburban Retail Center",
                "property_type": "retail",
                "property_location": "Chicago, IL",
                "acquisition_date": date(2017, 8, 22),
                "acquisition_cost": Decimal("68000000"),
                "current_value": Decimal("74770000"),
                "ownership_percentage": Decimal("1.0"),
                "annual_income": Decimal("4860000"),
                "unrealized_gain_loss": Decimal("6770000"),
                "gresb_score": None,
                "certifications": [],
                "risk_score": 55,
                "is_stranded": False,
            },
            {
                "id": str(uuid4()),
                "portfolio_id": "00000000-0000-0000-0000-000000000101",
                "property_id": "00000000-0000-0000-0000-000000000003",
                "property_name": "Industrial Distribution Hub",
                "property_type": "industrial",
                "property_location": "Dallas, TX",
                "acquisition_date": date(2019, 2, 10),
                "acquisition_cost": Decimal("275000000"),
                "current_value": Decimal("301670000"),
                "ownership_percentage": Decimal("1.0"),
                "annual_income": Decimal("14480000"),
                "unrealized_gain_loss": Decimal("26670000"),
                "gresb_score": 68,
                "certifications": ["BREEAM Very Good"],
                "risk_score": 25,
                "is_stranded": False,
            },
            {
                "id": str(uuid4()),
                "portfolio_id": "00000000-0000-0000-0000-000000000101",
                "property_id": "00000000-0000-0000-0000-000000000004",
                "property_name": "Luxury Multifamily Complex",
                "property_type": "multifamily",
                "property_location": "San Francisco, CA",
                "acquisition_date": date(2018, 5, 30),
                "acquisition_cost": Decimal("250000000"),
                "current_value": Decimal("280000000"),
                "ownership_percentage": Decimal("1.0"),
                "annual_income": Decimal("9450000"),
                "unrealized_gain_loss": Decimal("30000000"),
                "gresb_score": 82,
                "certifications": ["LEED Platinum"],
                "risk_score": 30,
                "is_stranded": False,
            },
            {
                "id": str(uuid4()),
                "portfolio_id": "00000000-0000-0000-0000-000000000101",
                "property_id": "00000000-0000-0000-0000-000000000005",
                "property_name": "Legacy Office Park",
                "property_type": "office",
                "property_location": "Houston, TX",
                "acquisition_date": date(2015, 11, 15),
                "acquisition_cost": Decimal("145000000"),
                "current_value": Decimal("125000000"),
                "ownership_percentage": Decimal("1.0"),
                "annual_income": Decimal("8750000"),
                "unrealized_gain_loss": Decimal("-20000000"),
                "gresb_score": 45,
                "certifications": [],
                "risk_score": 72,
                "is_stranded": True,
                "years_to_stranding": 8,
            },
        ],
        "00000000-0000-0000-0000-000000000102": [
            {
                "id": str(uuid4()),
                "portfolio_id": "00000000-0000-0000-0000-000000000102",
                "property_id": "00000000-0000-0000-0000-000000000006",
                "property_name": "Value-Add Office Building",
                "property_type": "office",
                "property_location": "Phoenix, AZ",
                "acquisition_date": date(2021, 1, 20),
                "acquisition_cost": Decimal("85000000"),
                "current_value": Decimal("92000000"),
                "ownership_percentage": Decimal("1.0"),
                "annual_income": Decimal("5520000"),
                "unrealized_gain_loss": Decimal("7000000"),
                "gresb_score": None,
                "certifications": [],
                "risk_score": 48,
                "is_stranded": False,
            },
            {
                "id": str(uuid4()),
                "portfolio_id": "00000000-0000-0000-0000-000000000102",
                "property_id": "00000000-0000-0000-0000-000000000007",
                "property_name": "Suburban Strip Mall",
                "property_type": "retail",
                "property_location": "Atlanta, GA",
                "acquisition_date": date(2020, 6, 15),
                "acquisition_cost": Decimal("42000000"),
                "current_value": Decimal("38000000"),
                "ownership_percentage": Decimal("1.0"),
                "annual_income": Decimal("3040000"),
                "unrealized_gain_loss": Decimal("-4000000"),
                "gresb_score": None,
                "certifications": [],
                "risk_score": 68,
                "is_stranded": True,
                "years_to_stranding": 5,
            },
        ],
        "00000000-0000-0000-0000-000000000103": [
            {
                "id": str(uuid4()),
                "portfolio_id": "00000000-0000-0000-0000-000000000103",
                "property_id": "00000000-0000-0000-0000-000000000008",
                "property_name": "Net Zero Office Tower",
                "property_type": "office",
                "property_location": "Seattle, WA",
                "acquisition_date": date(2019, 4, 1),
                "acquisition_cost": Decimal("320000000"),
                "current_value": Decimal("385000000"),
                "ownership_percentage": Decimal("1.0"),
                "annual_income": Decimal("19250000"),
                "unrealized_gain_loss": Decimal("65000000"),
                "gresb_score": 92,
                "certifications": ["LEED Platinum", "WELL Gold"],
                "risk_score": 18,
                "is_stranded": False,
            },
            {
                "id": str(uuid4()),
                "portfolio_id": "00000000-0000-0000-0000-000000000103",
                "property_id": "00000000-0000-0000-0000-000000000009",
                "property_name": "Green Multifamily Development",
                "property_type": "multifamily",
                "property_location": "Denver, CO",
                "acquisition_date": date(2020, 9, 15),
                "acquisition_cost": Decimal("180000000"),
                "current_value": Decimal("210000000"),
                "ownership_percentage": Decimal("1.0"),
                "annual_income": Decimal("10500000"),
                "unrealized_gain_loss": Decimal("30000000"),
                "gresb_score": 85,
                "certifications": ["LEED Gold", "Energy Star"],
                "risk_score": 22,
                "is_stranded": False,
            },
        ],
    }


# ============ Storage (In-Memory) ============

_portfolios_store: Dict[str, Dict] = {}
_holdings_store: Dict[str, List[Dict]] = {}
_reports_store: Dict[str, Dict] = {}


def init_sample_data():
    """Initialize with sample data."""
    global _portfolios_store, _holdings_store
    _portfolios_store = {p["id"]: p for p in get_sample_portfolios().values()}
    _holdings_store = get_sample_holdings()


# Initialize on module load
init_sample_data()


def get_portfolio(portfolio_id: str) -> Optional[Dict]:
    """Get portfolio by ID."""
    return _portfolios_store.get(portfolio_id)


def get_holdings(portfolio_id: str) -> List[Dict]:
    """Get holdings for a portfolio."""
    return _holdings_store.get(portfolio_id, [])


def save_portfolio(portfolio_id: str, portfolio_data: Dict) -> None:
    """Save portfolio to store."""
    _portfolios_store[portfolio_id] = portfolio_data


def save_holding(portfolio_id: str, holding_data: Dict) -> None:
    """Save holding to store."""
    if portfolio_id not in _holdings_store:
        _holdings_store[portfolio_id] = []
    _holdings_store[portfolio_id].append(holding_data)


def remove_holding(portfolio_id: str, property_id: str) -> bool:
    """Remove holding from store."""
    if portfolio_id in _holdings_store:
        original_len = len(_holdings_store[portfolio_id])
        _holdings_store[portfolio_id] = [
            h for h in _holdings_store[portfolio_id] 
            if h.get("property_id") != property_id
        ]
        return len(_holdings_store[portfolio_id]) < original_len
    return False


def list_portfolios() -> List[Dict]:
    """List all portfolios."""
    return list(_portfolios_store.values())


def save_report(report_id: str, report_data: Dict) -> None:
    """Save report to store."""
    _reports_store[report_id] = report_data


def get_report(report_id: str) -> Optional[Dict]:
    """Get report by ID."""
    return _reports_store.get(report_id)


# ============ Analytics Engine ============

class PortfolioAnalyticsEngine:
    """Engine for calculating portfolio-level analytics."""
    
    def calculate_analytics(
        self,
        portfolio_id: str,
        scenario_id: Optional[str] = None,
        time_horizon: int = 10,
        as_of_date: Optional[date] = None
    ) -> PortfolioAnalyticsResponse:
        """Calculate comprehensive portfolio analytics."""
        
        portfolio = get_portfolio(portfolio_id)
        if not portfolio:
            raise ValueError(f"Portfolio {portfolio_id} not found")
        
        holdings = get_holdings(portfolio_id)
        if not holdings:
            # Return empty analytics
            return self._empty_analytics(portfolio_id, as_of_date or date.today())
        
        # Calculate base and adjusted values
        total_base_value = Decimal("0")
        total_adjusted_value = Decimal("0")
        total_income = Decimal("0")
        
        risk_scores = []
        stranded_assets = []
        gresb_scores = []
        certifications_count = 0
        certifications_breakdown = {}
        
        sector_values = {}
        location_values = {}
        risk_buckets = {"low": 0, "moderate": 0, "high": 0, "very_high": 0}
        
        for holding in holdings:
            ownership = Decimal(str(holding.get("ownership_percentage", 1)))
            current_value = Decimal(str(holding.get("current_value", 0)))
            acquisition_cost = Decimal(str(holding.get("acquisition_cost", current_value)))
            annual_income = Decimal(str(holding.get("annual_income", 0)))
            
            # Apply scenario adjustment (simplified)
            if scenario_id:
                adjustment = self._get_scenario_adjustment(scenario_id, holding)
                adjusted_value = current_value * (1 + adjustment)
            else:
                adjusted_value = current_value
            
            weighted_base = acquisition_cost * ownership
            weighted_adjusted = adjusted_value * ownership
            weighted_income = annual_income * ownership
            
            total_base_value += weighted_base
            total_adjusted_value += weighted_adjusted
            total_income += weighted_income
            
            # Risk score
            risk = holding.get("risk_score", 50)
            risk_scores.append(risk)
            
            # Risk bucket
            if risk < 30:
                risk_buckets["low"] += 1
            elif risk < 50:
                risk_buckets["moderate"] += 1
            elif risk < 70:
                risk_buckets["high"] += 1
            else:
                risk_buckets["very_high"] += 1
            
            # Stranding
            if holding.get("is_stranded"):
                stranded_assets.append({
                    "value": float(weighted_adjusted),
                    "years": holding.get("years_to_stranding", 10),
                    "sector": holding.get("property_type"),
                })
            
            # Sustainability
            if holding.get("gresb_score"):
                gresb_scores.append(holding["gresb_score"])
            
            certs = holding.get("certifications", [])
            if certs:
                certifications_count += 1
                for cert in certs:
                    cert_type = cert.split()[0]  # "LEED Gold" -> "LEED"
                    certifications_breakdown[cert_type] = certifications_breakdown.get(cert_type, 0) + 1
            
            # Concentration
            sector = holding.get("property_type", "unknown")
            sector_values[sector] = sector_values.get(sector, Decimal("0")) + weighted_adjusted
            
            location = holding.get("property_location", "Unknown").split(",")[0]  # City only
            location_values[location] = location_values.get(location, Decimal("0")) + weighted_adjusted
        
        # Calculate metrics
        value_change = total_adjusted_value - total_base_value
        value_change_pct = (value_change / total_base_value * 100) if total_base_value else Decimal("0")
        
        avg_risk = sum(risk_scores) / len(risk_scores) if risk_scores else Decimal("0")
        var_95 = self._calculate_var(total_adjusted_value, avg_risk)
        
        avg_gresb = sum(gresb_scores) / len(gresb_scores) if gresb_scores else None
        pct_certified = (Decimal(str(certifications_count)) / Decimal(str(len(holdings))) * 100) if holdings else Decimal("0")
        
        stranded_value = sum(s["value"] for s in stranded_assets)
        stranded_pct = Decimal(str(stranded_value / float(total_adjusted_value) * 100)) if total_adjusted_value else Decimal("0")
        avg_years = sum(s["years"] for s in stranded_assets) / len(stranded_assets) if stranded_assets else None
        
        # Concentration analysis
        geo_conc = self._calculate_concentration(location_values, total_adjusted_value)
        sector_conc = self._calculate_concentration(sector_values, total_adjusted_value)
        
        # Determine risk level
        if float(avg_risk) < 30:
            risk_level = RiskLevel.LOW
        elif float(avg_risk) < 50:
            risk_level = RiskLevel.MODERATE
        elif float(avg_risk) < 70:
            risk_level = RiskLevel.HIGH
        else:
            risk_level = RiskLevel.VERY_HIGH
        
        return PortfolioAnalyticsResponse(
            portfolio_id=UUID(portfolio_id),
            calculation_date=as_of_date or date.today(),
            scenario_name="Base Case" if not scenario_id else f"Scenario {scenario_id[:8]}",
            portfolio_summary=PortfolioSummary(
                total_properties=len(holdings),
                total_base_value=total_base_value,
                total_adjusted_value=total_adjusted_value,
                total_value_change=value_change,
                value_change_pct=value_change_pct.quantize(Decimal("0.01")),
                total_income=total_income,
                avg_yield=(total_income / total_adjusted_value * 100).quantize(Decimal("0.01")) if total_adjusted_value else None,
            ),
            risk_metrics=RiskMetrics(
                weighted_avg_risk_score=Decimal(str(avg_risk)).quantize(Decimal("0.1")),
                value_at_risk_95=var_95,
                risk_level=risk_level,
                risk_distribution=risk_buckets,
            ),
            stranding_analysis=StrandingAnalysis(
                stranded_assets_count=len(stranded_assets),
                stranded_assets_value=Decimal(str(stranded_value)),
                stranded_pct=stranded_pct.quantize(Decimal("0.01")),
                avg_years_to_stranding=Decimal(str(avg_years)).quantize(Decimal("0.1")) if avg_years else None,
                stranded_by_sector={s["sector"]: 1 for s in stranded_assets},
            ),
            sustainability_metrics=SustainabilityMetrics(
                avg_gresb_score=Decimal(str(avg_gresb)).quantize(Decimal("0.1")) if avg_gresb else None,
                pct_certified=pct_certified.quantize(Decimal("0.1")),
                certified_count=certifications_count,
                certifications_breakdown=certifications_breakdown,
            ),
            concentration_analysis=ConcentrationAnalysis(
                geographic=geo_conc,
                sector=sector_conc,
            ),
        )
    
    def _empty_analytics(self, portfolio_id: str, calc_date: date) -> PortfolioAnalyticsResponse:
        """Return empty analytics for portfolio with no holdings."""
        return PortfolioAnalyticsResponse(
            portfolio_id=UUID(portfolio_id),
            calculation_date=calc_date,
            portfolio_summary=PortfolioSummary(
                total_properties=0,
                total_base_value=Decimal("0"),
                total_adjusted_value=Decimal("0"),
                total_value_change=Decimal("0"),
                value_change_pct=Decimal("0"),
            ),
            risk_metrics=RiskMetrics(
                weighted_avg_risk_score=Decimal("0"),
                value_at_risk_95=Decimal("0"),
                risk_level=RiskLevel.LOW,
                risk_distribution={},
            ),
            stranding_analysis=StrandingAnalysis(
                stranded_assets_count=0,
                stranded_assets_value=Decimal("0"),
                stranded_pct=Decimal("0"),
            ),
            sustainability_metrics=SustainabilityMetrics(
                pct_certified=Decimal("0"),
                certified_count=0,
            ),
            concentration_analysis=ConcentrationAnalysis(
                geographic=ConcentrationMetrics(hhi=Decimal("0"), concentration_level="low", top_items=[]),
                sector=ConcentrationMetrics(hhi=Decimal("0"), concentration_level="low", top_items=[]),
            ),
        )
    
    def _get_scenario_adjustment(self, scenario_id: str, holding: Dict) -> Decimal:
        """Get scenario-specific value adjustment for a holding."""
        # Simplified: would integrate with scenario engine
        risk = holding.get("risk_score", 50)
        # Higher risk properties have larger adjustments
        adjustment = Decimal(str(random.uniform(-0.05, 0.05) * (risk / 50)))
        return adjustment
    
    def _calculate_var(self, portfolio_value: Decimal, avg_risk: float) -> Decimal:
        """Calculate simplified Value at Risk (95% confidence)."""
        # Simplified VaR: higher risk = higher VaR
        volatility = 0.05 + (avg_risk / 100) * 0.15  # 5-20% volatility
        z_score = 1.645  # 95% confidence
        var = float(portfolio_value) * volatility * z_score
        return Decimal(str(var)).quantize(Decimal("0.01"))
    
    def _calculate_concentration(
        self, 
        values_dict: Dict[str, Decimal], 
        total: Decimal
    ) -> ConcentrationMetrics:
        """Calculate concentration metrics (HHI)."""
        if not total or not values_dict:
            return ConcentrationMetrics(hhi=Decimal("0"), concentration_level="low", top_items=[])
        
        total_float = float(total)
        shares = [float(v) / total_float for v in values_dict.values()]
        hhi = sum(s ** 2 for s in shares)
        
        if hhi > 0.25:
            level = "high"
        elif hhi > 0.15:
            level = "moderate"
        else:
            level = "low"
        
        # Top items
        sorted_items = sorted(values_dict.items(), key=lambda x: x[1], reverse=True)[:5]
        top_items = [
            {"name": k, "value": float(v), "pct": float(v / total * 100)}
            for k, v in sorted_items
        ]
        
        return ConcentrationMetrics(
            hhi=Decimal(str(hhi)).quantize(Decimal("0.0001")),
            concentration_level=level,
            top_items=top_items,
        )
    
    def compare_scenarios(
        self,
        portfolio_id: str,
        scenario_ids: List[str],
        time_horizon: int = 10
    ) -> ScenarioComparisonResult:
        """Compare multiple scenarios for a portfolio."""
        portfolio = get_portfolio(portfolio_id)
        if not portfolio:
            raise ValueError(f"Portfolio {portfolio_id} not found")
        
        # Get base analytics
        base_analytics = self.calculate_analytics(portfolio_id, None, time_horizon)
        base_value = base_analytics.portfolio_summary.total_adjusted_value
        
        comparison_rows = []
        
        # Base case
        comparison_rows.append(ScenarioComparisonRow(
            scenario_id=UUID(int=0),
            scenario_name="Base Case",
            total_value=base_value,
            value_change=Decimal("0"),
            value_change_pct=Decimal("0"),
            stranded_count=base_analytics.stranding_analysis.stranded_assets_count,
            stranded_value=base_analytics.stranding_analysis.stranded_assets_value,
            var_95=base_analytics.risk_metrics.value_at_risk_95,
            avg_risk_score=base_analytics.risk_metrics.weighted_avg_risk_score,
        ))
        
        # Each scenario (simulated)
        scenario_names = [
            "Optimistic Growth", "Recession Stress", "Climate Transition",
            "Green Premium", "Rising Rates"
        ]
        
        for i, sid in enumerate(scenario_ids):
            # Simulate scenario impact
            adjustment = Decimal(str(random.uniform(-0.15, 0.12)))
            scenario_value = base_value * (1 + adjustment)
            stranded_adj = int(base_analytics.stranding_analysis.stranded_assets_count * float(1 + adjustment * 2))
            
            comparison_rows.append(ScenarioComparisonRow(
                scenario_id=UUID(sid) if len(sid) == 36 else UUID(int=i+1),
                scenario_name=scenario_names[i % len(scenario_names)],
                total_value=scenario_value.quantize(Decimal("0.01")),
                value_change=(scenario_value - base_value).quantize(Decimal("0.01")),
                value_change_pct=(adjustment * 100).quantize(Decimal("0.01")),
                stranded_count=max(0, stranded_adj),
                stranded_value=base_analytics.stranding_analysis.stranded_assets_value * (1 + adjustment),
                var_95=base_analytics.risk_metrics.value_at_risk_95 * (1 + abs(adjustment) * 0.5),
                avg_risk_score=base_analytics.risk_metrics.weighted_avg_risk_score * (1 + adjustment * 0.3),
            ))
        
        # Find best/worst
        sorted_rows = sorted(comparison_rows, key=lambda x: x.total_value, reverse=True)
        best = sorted_rows[0].scenario_name
        worst = sorted_rows[-1].scenario_name
        
        value_spread = sorted_rows[0].total_value - sorted_rows[-1].total_value
        
        insights = [
            f"Value spread across scenarios: ${float(value_spread)/1e6:.1f}M",
            f"Best scenario '{best}' outperforms worst by {float((sorted_rows[0].total_value - sorted_rows[-1].total_value) / sorted_rows[-1].total_value * 100):.1f}%",
        ]
        
        return ScenarioComparisonResult(
            portfolio_id=UUID(portfolio_id),
            base_value=base_value,
            comparison_table=comparison_rows,
            best_scenario=best,
            worst_scenario=worst,
            value_spread=value_spread,
            key_insights=insights,
        )


# ============ Dashboard Engine ============

class PortfolioDashboardEngine:
    """Engine for generating portfolio dashboard data."""
    
    def __init__(self):
        self.analytics_engine = PortfolioAnalyticsEngine()
    
    def get_dashboard(
        self,
        portfolio_id: str,
        scenario_id: Optional[str] = None,
        time_horizon: int = 10
    ) -> DashboardResponse:
        """Generate dashboard data for a portfolio."""
        portfolio = get_portfolio(portfolio_id)
        if not portfolio:
            raise ValueError(f"Portfolio {portfolio_id} not found")
        
        analytics = self.analytics_engine.calculate_analytics(
            portfolio_id, scenario_id, time_horizon
        )
        
        holdings = get_holdings(portfolio_id)
        
        # KPI Cards
        kpi_cards = [
            KPICard(
                id="total_value",
                label="Total Portfolio Value",
                value=float(analytics.portfolio_summary.total_adjusted_value),
                change=float(analytics.portfolio_summary.value_change_pct),
                change_period="from base",
                trend="up" if analytics.portfolio_summary.value_change_pct > 0 else "down",
                icon="DollarSign",
                color="emerald" if analytics.portfolio_summary.value_change_pct > 0 else "red",
            ),
            KPICard(
                id="property_count",
                label="Properties",
                value=analytics.portfolio_summary.total_properties,
                icon="Building2",
                color="blue",
            ),
            KPICard(
                id="avg_risk",
                label="Avg Risk Score",
                value=float(analytics.risk_metrics.weighted_avg_risk_score),
                trend="down" if analytics.risk_metrics.weighted_avg_risk_score < 50 else "up",
                icon="AlertTriangle",
                color="amber" if analytics.risk_metrics.weighted_avg_risk_score > 50 else "emerald",
            ),
            KPICard(
                id="var_95",
                label="Value at Risk (95%)",
                value=float(analytics.risk_metrics.value_at_risk_95),
                icon="TrendingDown",
                color="red",
            ),
            KPICard(
                id="stranded_count",
                label="Stranded Assets",
                value=analytics.stranding_analysis.stranded_assets_count,
                trend="up" if analytics.stranding_analysis.stranded_assets_count > 0 else "stable",
                icon="AlertCircle",
                color="red" if analytics.stranding_analysis.stranded_assets_count > 0 else "emerald",
            ),
            KPICard(
                id="sustainability",
                label="Avg GRESB Score",
                value=float(analytics.sustainability_metrics.avg_gresb_score) if analytics.sustainability_metrics.avg_gresb_score else 0,
                icon="Leaf",
                color="emerald",
            ),
            KPICard(
                id="certified_pct",
                label="Certified Assets",
                value=f"{float(analytics.sustainability_metrics.pct_certified):.1f}%",
                icon="Award",
                color="violet",
            ),
            KPICard(
                id="yield",
                label="Portfolio Yield",
                value=f"{float(analytics.portfolio_summary.avg_yield or 0):.2f}%",
                icon="Percent",
                color="blue",
            ),
        ]
        
        # Charts
        charts = {}
        
        # Sector allocation pie chart
        sector_data = analytics.concentration_analysis.sector.top_items
        charts["sector_allocation"] = ChartData(
            chart_type="pie",
            title="Sector Allocation",
            data=[{"name": item["name"].title(), "value": item["pct"]} for item in sector_data],
        )
        
        # Geographic distribution
        geo_data = analytics.concentration_analysis.geographic.top_items
        charts["geographic_distribution"] = ChartData(
            chart_type="bar",
            title="Geographic Distribution",
            data=[{"name": item["name"], "value": item["value"] / 1e6} for item in geo_data],
            config={"valueLabel": "Value ($M)"},
        )
        
        # Risk distribution
        charts["risk_distribution"] = ChartData(
            chart_type="bar",
            title="Risk Distribution",
            data=[
                {"name": "Low (<30)", "value": analytics.risk_metrics.risk_distribution.get("low", 0), "fill": "#22c55e"},
                {"name": "Moderate (30-50)", "value": analytics.risk_metrics.risk_distribution.get("moderate", 0), "fill": "#f59e0b"},
                {"name": "High (50-70)", "value": analytics.risk_metrics.risk_distribution.get("high", 0), "fill": "#f97316"},
                {"name": "Very High (70+)", "value": analytics.risk_metrics.risk_distribution.get("very_high", 0), "fill": "#ef4444"},
            ],
        )
        
        # Property values bar chart
        property_values = [
            {"name": h.get("property_name", "Unknown")[:15], "value": float(h.get("current_value", 0)) / 1e6}
            for h in holdings[:10]
        ]
        charts["property_values"] = ChartData(
            chart_type="bar",
            title="Property Values ($M)",
            data=property_values,
        )
        
        # Sustainability scores radar
        if holdings:
            avg_metrics = {
                "GRESB Score": float(analytics.sustainability_metrics.avg_gresb_score or 0),
                "Certified %": float(analytics.sustainability_metrics.pct_certified),
                "Low Risk %": analytics.risk_metrics.risk_distribution.get("low", 0) / len(holdings) * 100 if holdings else 0,
                "Yield %": float(analytics.portfolio_summary.avg_yield or 0) * 10,  # Scale up
            }
            charts["sustainability_radar"] = ChartData(
                chart_type="radar",
                title="Sustainability Profile",
                data=[{"metric": k, "value": v} for k, v in avg_metrics.items()],
            )
        
        # Alerts
        alerts = []
        
        # Stranded asset alert
        if analytics.stranding_analysis.stranded_assets_count > 0:
            alerts.append(Alert(
                id="stranded_warning",
                severity="critical",
                title="Stranded Asset Risk",
                message=f"{analytics.stranding_analysis.stranded_assets_count} assets at risk of stranding with total value ${float(analytics.stranding_analysis.stranded_assets_value)/1e6:.1f}M",
                action_required=True,
                created_at=datetime.now(timezone.utc),
            ))
        
        # High concentration alert
        if analytics.concentration_analysis.sector.concentration_level == "high":
            alerts.append(Alert(
                id="sector_concentration",
                severity="warning",
                title="High Sector Concentration",
                message="Portfolio has high concentration in a single sector. Consider diversification.",
                action_required=False,
                created_at=datetime.now(timezone.utc),
            ))
        
        # Low sustainability alert
        if analytics.sustainability_metrics.pct_certified < 50:
            alerts.append(Alert(
                id="low_certification",
                severity="info",
                title="Low Certification Rate",
                message=f"Only {float(analytics.sustainability_metrics.pct_certified):.0f}% of assets are certified. Consider certification programs.",
                action_required=False,
                created_at=datetime.now(timezone.utc),
            ))
        
        return DashboardResponse(
            portfolio_id=UUID(portfolio_id),
            portfolio_name=portfolio["name"],
            last_updated=datetime.now(timezone.utc),
            kpi_cards=kpi_cards,
            charts=charts,
            alerts=alerts,
            total_aum=Decimal(str(portfolio.get("aum", 0))),
            property_count=len(holdings),
            avg_risk_score=analytics.risk_metrics.weighted_avg_risk_score,
            sustainability_score=analytics.sustainability_metrics.avg_gresb_score,
        )


# ============ Report Engine ============

class PortfolioReportEngine:
    """Engine for generating portfolio reports."""
    
    def __init__(self):
        self.analytics_engine = PortfolioAnalyticsEngine()
    
    def generate_report(
        self,
        portfolio_id: str,
        report_type: ReportType,
        scenario_id: Optional[str] = None,
        time_horizon: int = 10,
        include_charts: bool = True,
        include_property_details: bool = False,
    ) -> Dict:
        """Generate a report for the portfolio."""
        portfolio = get_portfolio(portfolio_id)
        if not portfolio:
            raise ValueError(f"Portfolio {portfolio_id} not found")
        
        analytics = self.analytics_engine.calculate_analytics(
            portfolio_id, scenario_id, time_horizon
        )
        holdings = get_holdings(portfolio_id)
        
        report_id = str(uuid4())
        generated_at = datetime.now(timezone.utc)
        
        # Executive summary
        executive_summary = {
            "portfolio_name": portfolio["name"],
            "report_date": generated_at.isoformat(),
            "total_value": float(analytics.portfolio_summary.total_adjusted_value),
            "value_change_pct": float(analytics.portfolio_summary.value_change_pct),
            "property_count": analytics.portfolio_summary.total_properties,
            "avg_risk_score": float(analytics.risk_metrics.weighted_avg_risk_score),
            "stranded_assets": analytics.stranding_analysis.stranded_assets_count,
            "key_findings": self._generate_key_findings(analytics),
        }
        
        # Portfolio overview
        portfolio_overview = {
            "portfolio_type": portfolio.get("portfolio_type"),
            "investment_strategy": portfolio.get("investment_strategy"),
            "aum": float(portfolio.get("aum", 0)),
            "currency": portfolio.get("currency", "USD"),
            "inception_date": str(portfolio.get("inception_date")),
            "total_income": float(analytics.portfolio_summary.total_income or 0),
            "yield": float(analytics.portfolio_summary.avg_yield or 0),
        }
        
        # Type-specific sections
        report_content = {
            "report_id": report_id,
            "report_type": report_type.value,
            "generated_at": generated_at.isoformat(),
            "executive_summary": executive_summary,
            "portfolio_overview": portfolio_overview,
        }
        
        if report_type == ReportType.VALUATION:
            report_content["valuation_details"] = self._valuation_section(analytics, holdings)
        elif report_type == ReportType.CLIMATE_RISK:
            report_content["climate_risk_details"] = self._climate_risk_section(analytics, holdings)
        elif report_type == ReportType.SUSTAINABILITY:
            report_content["sustainability_details"] = self._sustainability_section(analytics, holdings)
        elif report_type == ReportType.TCFD:
            report_content["tcfd_details"] = self._tcfd_section(analytics, holdings)
        elif report_type in [ReportType.INVESTOR, ReportType.EXECUTIVE]:
            report_content["valuation_details"] = self._valuation_section(analytics, holdings)
            report_content["sustainability_details"] = self._sustainability_section(analytics, holdings)
        
        if include_property_details:
            report_content["property_details"] = [
                {
                    "name": h.get("property_name"),
                    "type": h.get("property_type"),
                    "location": h.get("property_location"),
                    "value": float(h.get("current_value", 0)),
                    "risk_score": h.get("risk_score"),
                    "certifications": h.get("certifications", []),
                }
                for h in holdings
            ]
        
        # Save report
        save_report(report_id, {
            "id": report_id,
            "portfolio_id": portfolio_id,
            "report_type": report_type.value,
            "status": "completed",
            "created_at": generated_at.isoformat(),
            "completed_at": generated_at.isoformat(),
            "content": report_content,
        })
        
        return report_content
    
    def _generate_key_findings(self, analytics: PortfolioAnalyticsResponse) -> List[str]:
        """Generate key findings from analytics."""
        findings = []
        
        if analytics.portfolio_summary.value_change_pct > 5:
            findings.append(f"Portfolio value increased by {float(analytics.portfolio_summary.value_change_pct):.1f}%")
        elif analytics.portfolio_summary.value_change_pct < -5:
            findings.append(f"Portfolio value decreased by {abs(float(analytics.portfolio_summary.value_change_pct)):.1f}%")
        
        if analytics.stranding_analysis.stranded_assets_count > 0:
            findings.append(f"{analytics.stranding_analysis.stranded_assets_count} assets identified as stranding risk")
        
        if analytics.sustainability_metrics.avg_gresb_score and analytics.sustainability_metrics.avg_gresb_score > 70:
            findings.append("Strong sustainability performance with above-average GRESB scores")
        
        if analytics.risk_metrics.risk_level in [RiskLevel.HIGH, RiskLevel.VERY_HIGH]:
            findings.append("Portfolio exhibits elevated risk profile - mitigation recommended")
        
        return findings[:5]
    
    def _valuation_section(self, analytics: PortfolioAnalyticsResponse, holdings: List[Dict]) -> Dict:
        """Generate valuation report section."""
        return {
            "total_base_value": float(analytics.portfolio_summary.total_base_value),
            "total_adjusted_value": float(analytics.portfolio_summary.total_adjusted_value),
            "value_change": float(analytics.portfolio_summary.total_value_change),
            "value_change_pct": float(analytics.portfolio_summary.value_change_pct),
            "valuation_date": str(analytics.calculation_date),
            "methodology": "Weighted average of DCF and direct capitalization approaches",
            "sector_breakdown": analytics.concentration_analysis.sector.top_items,
            "geographic_breakdown": analytics.concentration_analysis.geographic.top_items,
        }
    
    def _climate_risk_section(self, analytics: PortfolioAnalyticsResponse, holdings: List[Dict]) -> Dict:
        """Generate climate risk report section."""
        return {
            "physical_risk": {
                "flood_exposure": sum(1 for h in holdings if h.get("risk_score", 0) > 60) / len(holdings) * 100 if holdings else 0,
                "heat_stress": sum(1 for h in holdings if h.get("risk_score", 0) > 50) / len(holdings) * 100 if holdings else 0,
            },
            "transition_risk": {
                "avg_risk_score": float(analytics.risk_metrics.weighted_avg_risk_score),
                "risk_distribution": analytics.risk_metrics.risk_distribution,
            },
            "stranding_analysis": {
                "stranded_count": analytics.stranding_analysis.stranded_assets_count,
                "stranded_value": float(analytics.stranding_analysis.stranded_assets_value),
                "stranded_pct": float(analytics.stranding_analysis.stranded_pct),
                "avg_years_to_stranding": float(analytics.stranding_analysis.avg_years_to_stranding) if analytics.stranding_analysis.avg_years_to_stranding else None,
            },
            "var_95": float(analytics.risk_metrics.value_at_risk_95),
        }
    
    def _sustainability_section(self, analytics: PortfolioAnalyticsResponse, holdings: List[Dict]) -> Dict:
        """Generate sustainability report section."""
        return {
            "gresb_performance": {
                "avg_score": float(analytics.sustainability_metrics.avg_gresb_score) if analytics.sustainability_metrics.avg_gresb_score else None,
                "benchmark": 72,  # Industry average
                "peer_rank": "Above Average" if (analytics.sustainability_metrics.avg_gresb_score or 0) > 70 else "Average",
            },
            "certifications": {
                "certified_count": analytics.sustainability_metrics.certified_count,
                "certified_pct": float(analytics.sustainability_metrics.pct_certified),
                "breakdown": analytics.sustainability_metrics.certifications_breakdown,
            },
            "improvement_roadmap": [
                "Target LEED certification for uncertified office assets",
                "Implement energy efficiency upgrades in retail properties",
                "Conduct GRESB assessment for portfolio-level ESG benchmarking",
            ],
        }
    
    def _tcfd_section(self, analytics: PortfolioAnalyticsResponse, holdings: List[Dict]) -> Dict:
        """Generate TCFD report section."""
        return {
            "governance": {
                "board_oversight": "Climate risks reviewed quarterly by investment committee",
                "management_role": "Sustainability team monitors climate metrics monthly",
            },
            "strategy": {
                "climate_opportunities": ["Green building premium capture", "Energy efficiency improvements"],
                "climate_risks": ["Stranding risk in fossil fuel-intensive assets", "Physical risk from extreme weather"],
                "resilience": "Portfolio stress-tested against 1.5°C and 2°C scenarios",
            },
            "risk_management": {
                "identification": "CRREM-based transition risk assessment",
                "assessment": f"Average risk score: {float(analytics.risk_metrics.weighted_avg_risk_score):.1f}",
                "mitigation": "Targeted improvements for high-risk assets",
            },
            "metrics_targets": {
                "carbon_intensity_target": "30% reduction by 2030",
                "certification_target": "100% portfolio certified by 2030",
                "current_certification_rate": float(analytics.sustainability_metrics.pct_certified),
            },
        }


# ============ Main Engine Class ============

class PortfolioAggregationEngine:
    """Main engine combining all portfolio capabilities."""
    
    def __init__(self):
        self.analytics = PortfolioAnalyticsEngine()
        self.dashboard = PortfolioDashboardEngine()
        self.reports = PortfolioReportEngine()
    
    def get_analytics(self, portfolio_id: str, scenario_id: Optional[str] = None, time_horizon: int = 10):
        return self.analytics.calculate_analytics(portfolio_id, scenario_id, time_horizon)
    
    def compare_scenarios(self, portfolio_id: str, scenario_ids: List[str], time_horizon: int = 10):
        return self.analytics.compare_scenarios(portfolio_id, scenario_ids, time_horizon)
    
    def get_dashboard(self, portfolio_id: str, scenario_id: Optional[str] = None, time_horizon: int = 10):
        return self.dashboard.get_dashboard(portfolio_id, scenario_id, time_horizon)
    
    def generate_report(self, portfolio_id: str, report_type: ReportType, **kwargs):
        return self.reports.generate_report(portfolio_id, report_type, **kwargs)
