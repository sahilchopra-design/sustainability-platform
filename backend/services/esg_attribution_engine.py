"""
ESG Attribution Engine
=======================
Decomposes portfolio ESG/carbon performance into attribution effects
using the Brinson-Fachler framework adapted for sustainability metrics.

References:
- Brinson, Hood & Beebower (1986) — original return attribution
- Adapted for carbon intensity (WACI), ESG scores, taxonomy alignment
- SFDR RTS Annex II/IV — periodic PAI reporting
- TCFD — carbon attribution requirements
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional
import math


# ---------------------------------------------------------------------------
# Data Classes — Inputs
# ---------------------------------------------------------------------------

@dataclass
class HoldingAttribution:
    """Holding-level data for attribution."""
    holding_id: str
    security_name: str
    isin: Optional[str] = None
    sector: str = "Other"
    weight_pct: float = 0.0
    carbon_intensity: float = 0.0   # tCO2e/MEUR
    esg_score: float = 0.0          # 0-100
    taxonomy_aligned_pct: float = 0.0


@dataclass
class BenchmarkAttribution:
    """Benchmark holding data for attribution."""
    security_name: str
    isin: Optional[str] = None
    sector: str = "Other"
    weight_pct: float = 0.0
    carbon_intensity: float = 0.0
    esg_score: float = 0.0
    taxonomy_aligned_pct: float = 0.0


@dataclass
class PAIIndicator:
    """Principal Adverse Impact indicator value."""
    indicator_id: str
    indicator_name: str
    portfolio_value: float
    benchmark_value: float
    unit: str
    direction: str = "lower_is_better"  # lower_is_better / higher_is_better

    @property
    def delta(self) -> float:
        return self.portfolio_value - self.benchmark_value

    @property
    def is_outperforming(self) -> bool:
        if self.direction == "lower_is_better":
            return self.portfolio_value < self.benchmark_value
        return self.portfolio_value > self.benchmark_value


@dataclass
class AttributionInput:
    """Complete input for ESG attribution analysis."""
    fund_id: str
    fund_name: str
    portfolio_holdings: list[HoldingAttribution] = field(default_factory=list)
    benchmark_holdings: list[BenchmarkAttribution] = field(default_factory=list)
    pai_indicators: list[PAIIndicator] = field(default_factory=list)
    # Optional prior period for YoY
    prior_waci: Optional[float] = None
    prior_esg_score: Optional[float] = None


# ---------------------------------------------------------------------------
# Data Classes — Outputs
# ---------------------------------------------------------------------------

@dataclass
class SectorEffect:
    """Brinson-Fachler attribution effects for one sector."""
    sector: str
    portfolio_weight_pct: float
    benchmark_weight_pct: float
    portfolio_metric: float       # e.g. carbon intensity or ESG score
    benchmark_metric: float
    allocation_effect: float      # Impact from weight differences
    selection_effect: float       # Impact from metric differences within sector
    interaction_effect: float     # Cross-term
    total_effect: float


@dataclass
class AttributionResult:
    """Full attribution analysis output."""
    fund_id: str
    fund_name: str
    metric_name: str              # "carbon_intensity" / "esg_score" / "taxonomy_pct"

    # Portfolio vs Benchmark
    portfolio_metric: float
    benchmark_metric: float
    active_metric: float          # portfolio - benchmark

    # Brinson-Fachler decomposition
    total_allocation_effect: float
    total_selection_effect: float
    total_interaction_effect: float
    total_active_effect: float    # Should equal active_metric

    # Sector-level detail
    sector_effects: list[SectorEffect]

    # Direction
    metric_direction: str         # "lower_is_better" / "higher_is_better"
    is_outperforming: bool


@dataclass
class BenchmarkAnalyticsResult:
    """Comprehensive benchmark comparison analytics."""
    fund_id: str
    fund_name: str

    # Carbon attribution
    carbon_attribution: AttributionResult

    # ESG attribution
    esg_attribution: AttributionResult

    # Taxonomy attribution
    taxonomy_attribution: AttributionResult

    # Active share (ISIN-based)
    active_share_pct: float

    # Tracking error (ex-post proxy from sector active weights)
    tracking_error_pct: float

    # Information ratios (excess metric / tracking error)
    carbon_information_ratio: float   # Lower carbon = better
    esg_information_ratio: float      # Higher ESG = better

    # PAI comparison
    pai_comparison: list[PAIIndicator]
    pai_outperformance_count: int
    pai_total_count: int

    # YoY changes
    waci_yoy_change_pct: Optional[float]
    esg_yoy_change_pct: Optional[float]


# ---------------------------------------------------------------------------
# Engine
# ---------------------------------------------------------------------------

class ESGAttributionEngine:
    """Brinson-Fachler attribution analysis adapted for ESG/carbon metrics."""

    def analyse(self, inp: AttributionInput) -> BenchmarkAnalyticsResult:
        """Run full ESG attribution and benchmark comparison."""
        port = inp.portfolio_holdings
        bench = inp.benchmark_holdings

        # Carbon attribution (lower is better)
        carbon_attr = self._brinson_fachler(
            port, bench, metric_fn=lambda h: h.carbon_intensity,
            metric_name="carbon_intensity", direction="lower_is_better",
        )

        # ESG score attribution (higher is better)
        esg_attr = self._brinson_fachler(
            port, bench, metric_fn=lambda h: h.esg_score,
            metric_name="esg_score", direction="higher_is_better",
        )

        # Taxonomy alignment attribution (higher is better)
        tax_attr = self._brinson_fachler(
            port, bench, metric_fn=lambda h: h.taxonomy_aligned_pct,
            metric_name="taxonomy_aligned_pct", direction="higher_is_better",
        )

        # Active share
        active_share = self._active_share(port, bench)

        # Tracking error proxy
        te = self._tracking_error_proxy(port, bench)

        # Information ratios
        # Carbon: lower is better, so "excess" = -(port_waci - bench_waci)
        carbon_excess = -(carbon_attr.active_metric)
        carbon_ir = carbon_excess / te if te > 0 else 0.0

        # ESG: higher is better, excess = port_esg - bench_esg
        esg_excess = esg_attr.active_metric
        esg_ir = esg_excess / te if te > 0 else 0.0

        # PAI comparison
        pai_out = sum(1 for p in inp.pai_indicators if p.is_outperforming)

        # YoY
        waci_yoy = None
        if inp.prior_waci is not None and inp.prior_waci > 0:
            waci_yoy = round(
                (carbon_attr.portfolio_metric - inp.prior_waci) / inp.prior_waci * 100, 2
            )
        esg_yoy = None
        if inp.prior_esg_score is not None and inp.prior_esg_score > 0:
            esg_yoy = round(
                (esg_attr.portfolio_metric - inp.prior_esg_score) / inp.prior_esg_score * 100, 2
            )

        return BenchmarkAnalyticsResult(
            fund_id=inp.fund_id,
            fund_name=inp.fund_name,
            carbon_attribution=carbon_attr,
            esg_attribution=esg_attr,
            taxonomy_attribution=tax_attr,
            active_share_pct=round(active_share, 2),
            tracking_error_pct=round(te, 4),
            carbon_information_ratio=round(carbon_ir, 4),
            esg_information_ratio=round(esg_ir, 4),
            pai_comparison=inp.pai_indicators,
            pai_outperformance_count=pai_out,
            pai_total_count=len(inp.pai_indicators),
            waci_yoy_change_pct=waci_yoy,
            esg_yoy_change_pct=esg_yoy,
        )

    # -------------------------------------------------------------------
    # Brinson-Fachler
    # -------------------------------------------------------------------

    def _brinson_fachler(
        self, port: list, bench: list,
        metric_fn, metric_name: str, direction: str,
    ) -> AttributionResult:
        """
        Brinson-Fachler attribution by sector.

        For each sector s:
          Allocation  = (w_p,s - w_b,s) * (M_b,s - M_b_total)
          Selection   = w_b,s * (M_p,s - M_b,s)
          Interaction = (w_p,s - w_b,s) * (M_p,s - M_b,s)
          Total       = Allocation + Selection + Interaction
        """
        # Aggregate by sector
        port_sectors = self._aggregate_by_sector(port, metric_fn)
        bench_sectors = self._aggregate_by_sector(bench, metric_fn)

        all_sectors = sorted(set(port_sectors.keys()) | set(bench_sectors.keys()))

        # Portfolio and benchmark total weighted metrics
        port_total = sum(
            s["weight"] / 100.0 * s["metric"] for s in port_sectors.values()
        )
        bench_total = sum(
            s["weight"] / 100.0 * s["metric"] for s in bench_sectors.values()
        )

        sector_effects = []
        total_alloc = 0.0
        total_selec = 0.0
        total_inter = 0.0

        for s in all_sectors:
            pw = port_sectors.get(s, {"weight": 0.0, "metric": 0.0})["weight"]
            bw = bench_sectors.get(s, {"weight": 0.0, "metric": 0.0})["weight"]
            pm = port_sectors.get(s, {"weight": 0.0, "metric": 0.0})["metric"]
            bm = bench_sectors.get(s, {"weight": 0.0, "metric": 0.0})["metric"]

            # Brinson-Fachler effects (weights in %, so divide by 100)
            alloc = (pw - bw) / 100.0 * (bm - bench_total)
            selec = bw / 100.0 * (pm - bm)
            inter = (pw - bw) / 100.0 * (pm - bm)
            total = alloc + selec + inter

            sector_effects.append(SectorEffect(
                sector=s,
                portfolio_weight_pct=round(pw, 2),
                benchmark_weight_pct=round(bw, 2),
                portfolio_metric=round(pm, 4),
                benchmark_metric=round(bm, 4),
                allocation_effect=round(alloc, 4),
                selection_effect=round(selec, 4),
                interaction_effect=round(inter, 4),
                total_effect=round(total, 4),
            ))

            total_alloc += alloc
            total_selec += selec
            total_inter += inter

        active = port_total - bench_total

        if direction == "lower_is_better":
            outperforming = port_total < bench_total
        else:
            outperforming = port_total > bench_total

        return AttributionResult(
            fund_id="",  # Filled by caller
            fund_name="",
            metric_name=metric_name,
            portfolio_metric=round(port_total, 4),
            benchmark_metric=round(bench_total, 4),
            active_metric=round(active, 4),
            total_allocation_effect=round(total_alloc, 4),
            total_selection_effect=round(total_selec, 4),
            total_interaction_effect=round(total_inter, 4),
            total_active_effect=round(total_alloc + total_selec + total_inter, 4),
            sector_effects=sector_effects,
            metric_direction=direction,
            is_outperforming=outperforming,
        )

    def _aggregate_by_sector(self, holdings: list, metric_fn) -> dict:
        """Aggregate holdings by sector: compute weight and weighted-average metric."""
        sectors: dict[str, dict] = {}
        for h in holdings:
            s = h.sector
            if s not in sectors:
                sectors[s] = {"weight": 0.0, "weighted_metric": 0.0}
            sectors[s]["weight"] += h.weight_pct
            sectors[s]["weighted_metric"] += h.weight_pct * metric_fn(h)

        result = {}
        for s, data in sectors.items():
            w = data["weight"]
            result[s] = {
                "weight": w,
                "metric": data["weighted_metric"] / w if w > 0 else 0.0,
            }
        return result

    # -------------------------------------------------------------------
    # Active Share
    # -------------------------------------------------------------------

    def _active_share(self, port: list, bench: list) -> float:
        """Active share = 0.5 * sum(|w_p - w_b|) using ISIN matching."""
        if not bench:
            return 100.0

        port_map: dict[str, float] = {}
        for h in port:
            if h.isin:
                port_map[h.isin] = port_map.get(h.isin, 0) + h.weight_pct

        bench_map: dict[str, float] = {}
        for b in bench:
            if b.isin:
                bench_map[b.isin] = bench_map.get(b.isin, 0) + b.weight_pct

        all_isins = set(port_map.keys()) | set(bench_map.keys())
        diff = sum(
            abs(port_map.get(i, 0) - bench_map.get(i, 0))
            for i in all_isins
        )
        return min(100.0, diff / 2.0)

    # -------------------------------------------------------------------
    # Tracking Error Proxy
    # -------------------------------------------------------------------

    def _tracking_error_proxy(self, port: list, bench: list) -> float:
        """Simplified ex-ante TE: sqrt(sum(active_weight^2)) * vol_proxy.
        Real TE requires covariance matrix; this is a rough heuristic."""
        if not bench:
            return 0.0

        port_sec: dict[str, float] = {}
        for h in port:
            port_sec[h.sector] = port_sec.get(h.sector, 0) + h.weight_pct

        bench_sec: dict[str, float] = {}
        for b in bench:
            bench_sec[b.sector] = bench_sec.get(b.sector, 0) + b.weight_pct

        all_sec = set(port_sec.keys()) | set(bench_sec.keys())
        sq_sum = sum(
            (port_sec.get(s, 0) - bench_sec.get(s, 0)) ** 2
            for s in all_sec
        )
        # Scale by annualised volatility proxy (~20%) and convert from % to decimal
        return math.sqrt(sq_sum) * 0.20 / 100.0
