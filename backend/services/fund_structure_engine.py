"""
Fund Structure Engine
=====================
Manages fund hierarchy (fund -> share classes -> holdings -> investors)
and computes fund-level analytics: NAV, WACI, taxonomy alignment,
active share, tracking error, and LP waterfall.

References:
- SFDR RTS Annex II/IV (periodic reporting template)
- INREV NAV Guidelines (fund-level)
- EU Taxonomy Regulation Art.5-8 (disclosure)
- GIPS (Global Investment Performance Standards)
"""
from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal, ROUND_HALF_UP
from typing import Optional
from enum import Enum
import math


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class SFDRClassification(str, Enum):
    ART_6 = "art6"          # No ESG characteristics promoted
    ART_8 = "art8"          # Environmental/social characteristics
    ART_8_PLUS = "art8plus" # Art.8 with sustainable investment objective
    ART_9 = "art9"          # Sustainable investment objective


class AssetClass(str, Enum):
    EQUITY = "equity"
    FIXED_INCOME = "fixed_income"
    CASH = "cash"
    ALTERNATIVE = "alternative"
    DERIVATIVE = "derivative"


class ESGStrategy(str, Enum):
    EXCLUSION = "exclusion"
    BEST_IN_CLASS = "best_in_class"
    INTEGRATION = "integration"
    IMPACT = "impact"
    ENGAGEMENT = "engagement"
    THEMATIC = "thematic"


# ---------------------------------------------------------------------------
# Data Classes — Fund Structure
# ---------------------------------------------------------------------------

@dataclass
class Holding:
    """Single holding/position in a fund."""
    holding_id: str
    security_name: str
    isin: Optional[str] = None
    ticker: Optional[str] = None
    asset_class: str = "equity"
    sector: str = "Other"
    country: str = "US"
    weight_pct: float = 0.0         # Portfolio weight %
    market_value: float = 0.0       # EUR
    acquisition_cost: float = 0.0
    quantity: float = 0.0
    carbon_intensity: float = 0.0   # tCO2e/MEUR revenue
    esg_score: float = 0.0          # 0-100
    taxonomy_aligned_pct: float = 0.0
    dnsh_compliant: bool = True
    exclusion_flag: bool = False
    exclusion_reason: Optional[str] = None


@dataclass
class BenchmarkHolding:
    """Single holding in a benchmark index."""
    security_name: str
    isin: Optional[str] = None
    sector: str = "Other"
    country: str = "US"
    weight_pct: float = 0.0
    carbon_intensity: float = 0.0
    esg_score: float = 0.0


@dataclass
class ShareClass:
    """Fund share class."""
    class_id: str
    class_name: str
    isin: Optional[str] = None
    currency: str = "EUR"
    nav_per_share: float = 0.0
    total_shares: float = 0.0
    ter_pct: float = 0.0
    management_fee_pct: float = 0.0
    performance_fee_pct: float = 0.0
    distribution_type: str = "acc"   # acc / dist


@dataclass
class Investor:
    """LP/investor in a fund."""
    investor_id: str
    name: str
    investor_type: str = "institutional"
    commitment: float = 0.0
    called: float = 0.0
    distributed: float = 0.0
    nav_share: float = 0.0
    ownership_pct: float = 0.0


@dataclass
class FundDefinition:
    """Complete fund structure."""
    fund_id: str
    fund_name: str
    sfdr_classification: str = "art8"
    fund_type: str = "ucits"
    base_currency: str = "EUR"
    aum: float = 0.0
    benchmark_index: Optional[str] = None
    esg_strategy: str = "integration"
    minimum_taxonomy_pct: float = 0.0
    minimum_sustainable_pct: float = 0.0
    holdings: list[Holding] = field(default_factory=list)
    benchmark_holdings: list[BenchmarkHolding] = field(default_factory=list)
    share_classes: list[ShareClass] = field(default_factory=list)
    investors: list[Investor] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Data Classes — Outputs
# ---------------------------------------------------------------------------

@dataclass
class SectorAllocation:
    sector: str
    portfolio_weight_pct: float
    benchmark_weight_pct: float
    active_weight_pct: float     # Portfolio - benchmark
    portfolio_carbon_intensity: float
    benchmark_carbon_intensity: float


@dataclass
class FundAnalyticsResult:
    """Comprehensive fund-level analytics."""
    fund_id: str
    fund_name: str
    sfdr_classification: str

    # NAV & AUM
    total_aum: float
    total_nav: float                    # Sum of share_class NAV * shares
    holdings_count: int
    asset_class_breakdown: dict[str, float]  # asset_class -> weight %

    # Carbon metrics
    waci: float                         # Weighted Average Carbon Intensity (tCO2e/MEUR)
    carbon_footprint: float             # Total financed emissions / AUM * 1M
    total_financed_emissions: float     # Sum(weight * carbon_intensity * AUM / 1M)

    # ESG metrics
    avg_esg_score: float                # Weighted average ESG score
    taxonomy_aligned_pct: float         # Weighted average taxonomy alignment
    sustainable_investment_pct: float   # % meeting SFDR sustainable investment criteria
    dnsh_compliant_pct: float           # % passing DNSH

    # Benchmark comparison
    benchmark_waci: float
    waci_vs_benchmark: float            # % better(negative) or worse(positive)
    benchmark_esg_score: float
    esg_delta_vs_benchmark: float

    # Risk metrics
    active_share_pct: float             # % holdings differing from benchmark
    tracking_error_est: float           # Estimated tracking error (simplified)
    concentration_top10_pct: float      # Weight of top 10 holdings

    # Sector allocation
    sector_allocations: list[SectorAllocation]

    # Exclusion compliance
    exclusion_breach_count: int
    exclusion_breaches: list[dict]

    # LP summary
    total_commitment: float
    total_called: float
    total_distributed: float
    fund_dpi: float
    fund_tvpi: float


# ---------------------------------------------------------------------------
# Engine
# ---------------------------------------------------------------------------

class FundStructureEngine:
    """Compute fund-level analytics from holdings, benchmark, and investors."""

    def analyse_fund(self, fund: FundDefinition) -> FundAnalyticsResult:
        """Run full fund analytics."""
        holdings = fund.holdings
        bench = fund.benchmark_holdings

        # Normalise weights
        total_weight = sum(h.weight_pct for h in holdings)
        if total_weight > 0 and abs(total_weight - 100.0) > 0.1:
            # Normalise to 100%
            for h in holdings:
                h.weight_pct = h.weight_pct / total_weight * 100.0

        # NAV from share classes
        total_nav = sum(
            sc.nav_per_share * sc.total_shares
            for sc in fund.share_classes
        )
        aum = fund.aum if fund.aum > 0 else total_nav

        # Asset class breakdown
        ac_breakdown: dict[str, float] = {}
        for h in holdings:
            ac = h.asset_class
            ac_breakdown[ac] = ac_breakdown.get(ac, 0) + h.weight_pct

        # WACI (tCO2e / MEUR revenue)
        waci = sum(h.weight_pct / 100.0 * h.carbon_intensity for h in holdings)

        # Carbon footprint = total financed emissions / AUM * 1M
        total_fe = sum(
            h.weight_pct / 100.0 * h.carbon_intensity * aum / 1_000_000
            for h in holdings
        ) if aum > 0 else 0.0
        carbon_fp = total_fe / aum * 1_000_000 if aum > 0 else 0.0

        # ESG score (weighted)
        avg_esg = sum(h.weight_pct / 100.0 * h.esg_score for h in holdings)

        # Taxonomy alignment (weighted)
        tax_aligned = sum(h.weight_pct / 100.0 * h.taxonomy_aligned_pct for h in holdings)

        # Sustainable investment % (holdings with esg_score > 50 and dnsh_compliant)
        sustainable_wt = sum(
            h.weight_pct for h in holdings
            if h.esg_score >= 50 and h.dnsh_compliant
        )
        sustainable_pct = sustainable_wt  # Already in %

        # DNSH compliant %
        dnsh_wt = sum(h.weight_pct for h in holdings if h.dnsh_compliant)
        dnsh_pct = dnsh_wt

        # Benchmark comparison
        bench_waci = sum(b.weight_pct / 100.0 * b.carbon_intensity for b in bench) if bench else 0.0
        waci_vs = ((waci - bench_waci) / bench_waci * 100) if bench_waci > 0 else 0.0
        bench_esg = sum(b.weight_pct / 100.0 * b.esg_score for b in bench) if bench else 0.0
        esg_delta = avg_esg - bench_esg

        # Active share
        active_share = self._calculate_active_share(holdings, bench)

        # Tracking error (simplified: std of active weights * sector vol proxy)
        tracking_err = self._estimate_tracking_error(holdings, bench)

        # Concentration
        sorted_h = sorted(holdings, key=lambda h: h.weight_pct, reverse=True)
        top10 = sum(h.weight_pct for h in sorted_h[:10])

        # Sector allocation
        sectors = self._sector_allocation(holdings, bench)

        # Exclusion breaches
        breaches = [
            {"holding_id": h.holding_id, "security_name": h.security_name,
             "reason": h.exclusion_reason or "unspecified"}
            for h in holdings if h.exclusion_flag
        ]

        # LP summary
        total_commit = sum(inv.commitment for inv in fund.investors)
        total_called = sum(inv.called for inv in fund.investors)
        total_dist = sum(inv.distributed for inv in fund.investors)
        dpi = total_dist / total_called if total_called > 0 else 0.0
        total_nav_inv = sum(inv.nav_share for inv in fund.investors)
        tvpi = (total_dist + total_nav_inv) / total_called if total_called > 0 else 0.0

        return FundAnalyticsResult(
            fund_id=fund.fund_id,
            fund_name=fund.fund_name,
            sfdr_classification=fund.sfdr_classification,
            total_aum=round(aum, 2),
            total_nav=round(total_nav, 2),
            holdings_count=len(holdings),
            asset_class_breakdown={k: round(v, 2) for k, v in ac_breakdown.items()},
            waci=round(waci, 4),
            carbon_footprint=round(carbon_fp, 4),
            total_financed_emissions=round(total_fe, 4),
            avg_esg_score=round(avg_esg, 2),
            taxonomy_aligned_pct=round(tax_aligned, 2),
            sustainable_investment_pct=round(sustainable_pct, 2),
            dnsh_compliant_pct=round(dnsh_pct, 2),
            benchmark_waci=round(bench_waci, 4),
            waci_vs_benchmark=round(waci_vs, 2),
            benchmark_esg_score=round(bench_esg, 2),
            esg_delta_vs_benchmark=round(esg_delta, 2),
            active_share_pct=round(active_share, 2),
            tracking_error_est=round(tracking_err, 4),
            concentration_top10_pct=round(top10, 2),
            sector_allocations=sectors,
            exclusion_breach_count=len(breaches),
            exclusion_breaches=breaches,
            total_commitment=round(total_commit, 2),
            total_called=round(total_called, 2),
            total_distributed=round(total_dist, 2),
            fund_dpi=round(dpi, 4),
            fund_tvpi=round(tvpi, 4),
        )

    # -------------------------------------------------------------------
    # Helpers
    # -------------------------------------------------------------------

    def _calculate_active_share(
        self, holdings: list[Holding], bench: list[BenchmarkHolding]
    ) -> float:
        """Active share = 0.5 * sum(|w_p - w_b|) across all securities."""
        if not bench:
            return 100.0  # No benchmark = 100% active

        # Map by ISIN
        bench_map: dict[str, float] = {}
        for b in bench:
            if b.isin:
                bench_map[b.isin] = b.weight_pct

        port_map: dict[str, float] = {}
        for h in holdings:
            if h.isin:
                port_map[h.isin] = port_map.get(h.isin, 0) + h.weight_pct

        all_isins = set(port_map.keys()) | set(bench_map.keys())
        diff_sum = sum(
            abs(port_map.get(isin, 0) - bench_map.get(isin, 0))
            for isin in all_isins
        )
        return min(100.0, diff_sum / 2.0)

    def _estimate_tracking_error(
        self, holdings: list[Holding], bench: list[BenchmarkHolding]
    ) -> float:
        """Simplified tracking error estimate based on active weights.
        Real TE needs covariance matrix; this is a rough proxy."""
        if not bench:
            return 0.0

        # Sector-level active weights
        port_sectors: dict[str, float] = {}
        for h in holdings:
            port_sectors[h.sector] = port_sectors.get(h.sector, 0) + h.weight_pct

        bench_sectors: dict[str, float] = {}
        for b in bench:
            bench_sectors[b.sector] = bench_sectors.get(b.sector, 0) + b.weight_pct

        all_sectors = set(port_sectors.keys()) | set(bench_sectors.keys())
        # Rough TE ~ sqrt(sum(active_weight^2)) * sector_vol_proxy (20% annualised)
        sq_sum = sum(
            (port_sectors.get(s, 0) - bench_sectors.get(s, 0)) ** 2
            for s in all_sectors
        )
        return math.sqrt(sq_sum) * 0.20 / 100.0  # Convert to decimal, scale by vol proxy

    def _sector_allocation(
        self, holdings: list[Holding], bench: list[BenchmarkHolding]
    ) -> list[SectorAllocation]:
        """Compute sector-level allocation and carbon comparison."""
        port_sectors: dict[str, dict] = {}
        for h in holdings:
            s = h.sector
            if s not in port_sectors:
                port_sectors[s] = {"weight": 0.0, "ci_weighted": 0.0}
            port_sectors[s]["weight"] += h.weight_pct
            port_sectors[s]["ci_weighted"] += h.weight_pct * h.carbon_intensity

        bench_sectors: dict[str, dict] = {}
        for b in bench:
            s = b.sector
            if s not in bench_sectors:
                bench_sectors[s] = {"weight": 0.0, "ci_weighted": 0.0}
            bench_sectors[s]["weight"] += b.weight_pct
            bench_sectors[s]["ci_weighted"] += b.weight_pct * b.carbon_intensity

        all_sectors = sorted(set(port_sectors.keys()) | set(bench_sectors.keys()))
        result = []
        for s in all_sectors:
            pw = port_sectors.get(s, {}).get("weight", 0.0)
            bw = bench_sectors.get(s, {}).get("weight", 0.0)
            p_ci = port_sectors.get(s, {}).get("ci_weighted", 0.0) / pw if pw > 0 else 0.0
            b_ci = bench_sectors.get(s, {}).get("ci_weighted", 0.0) / bw if bw > 0 else 0.0
            result.append(SectorAllocation(
                sector=s,
                portfolio_weight_pct=round(pw, 2),
                benchmark_weight_pct=round(bw, 2),
                active_weight_pct=round(pw - bw, 2),
                portfolio_carbon_intensity=round(p_ci, 4),
                benchmark_carbon_intensity=round(b_ci, 4),
            ))
        return result
