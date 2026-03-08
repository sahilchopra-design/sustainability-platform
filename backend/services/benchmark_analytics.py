"""
Benchmark Analytics Service
============================
Higher-level analytics comparing portfolio ESG characteristics against
benchmark indices. Computes peer-relative positioning and period-over-period
trends for regulatory reporting (SFDR, TCFD).

References:
- SFDR RTS Art.11 — periodic disclosure including benchmark comparison
- TCFD — recommended metrics & targets (WACI comparison)
- EU BMR (Benchmarks Regulation) — climate benchmark alignment
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


# ---------------------------------------------------------------------------
# Reference: SFDR Mandatory PAI Indicators (Table 1, Annex I)
# ---------------------------------------------------------------------------

MANDATORY_PAI_INDICATORS = [
    {"id": "PAI_1", "name": "GHG Emissions (Scope 1)", "unit": "tCO2e", "direction": "lower_is_better"},
    {"id": "PAI_2", "name": "GHG Emissions (Scope 2)", "unit": "tCO2e", "direction": "lower_is_better"},
    {"id": "PAI_3", "name": "GHG Emissions (Scope 3)", "unit": "tCO2e", "direction": "lower_is_better"},
    {"id": "PAI_4", "name": "Carbon Footprint", "unit": "tCO2e/MEUR invested", "direction": "lower_is_better"},
    {"id": "PAI_5", "name": "GHG Intensity (WACI)", "unit": "tCO2e/MEUR revenue", "direction": "lower_is_better"},
    {"id": "PAI_6", "name": "Fossil Fuel Exposure", "unit": "%", "direction": "lower_is_better"},
    {"id": "PAI_7", "name": "Non-Renewable Energy Share", "unit": "%", "direction": "lower_is_better"},
    {"id": "PAI_8", "name": "Energy Intensity per NACE Sector", "unit": "GWh/MEUR", "direction": "lower_is_better"},
    {"id": "PAI_9", "name": "Activities Affecting Biodiversity", "unit": "% of investees", "direction": "lower_is_better"},
    {"id": "PAI_10", "name": "Water Emissions", "unit": "tonnes", "direction": "lower_is_better"},
    {"id": "PAI_11", "name": "Hazardous Waste Ratio", "unit": "tonnes", "direction": "lower_is_better"},
    {"id": "PAI_12", "name": "UNGC/OECD Violations", "unit": "% of investees", "direction": "lower_is_better"},
    {"id": "PAI_13", "name": "Gender Pay Gap", "unit": "%", "direction": "lower_is_better"},
    {"id": "PAI_14", "name": "Board Gender Diversity", "unit": "%", "direction": "higher_is_better"},
    {"id": "PAI_15", "name": "Controversial Weapons Exposure", "unit": "% of investees", "direction": "lower_is_better"},
    {"id": "PAI_16", "name": "GHG Intensity of Sovereigns", "unit": "tCO2e/MEUR GDP", "direction": "lower_is_better"},
    {"id": "PAI_17", "name": "Investee Countries with Social Violations", "unit": "% exposure", "direction": "lower_is_better"},
    {"id": "PAI_18", "name": "Real Estate Fossil Fuel Exposure", "unit": "% of assets", "direction": "lower_is_better"},
]


# ---------------------------------------------------------------------------
# Data Classes
# ---------------------------------------------------------------------------

@dataclass
class PeerFundMetrics:
    """Metrics for a single peer fund for relative comparison."""
    fund_id: str
    fund_name: str
    sfdr_classification: str
    waci: float = 0.0
    esg_score: float = 0.0
    taxonomy_aligned_pct: float = 0.0
    active_share_pct: float = 0.0
    exclusion_breach_count: int = 0


@dataclass
class PeerRanking:
    """How a fund ranks within its peer group."""
    metric_name: str
    fund_value: float
    peer_count: int
    rank: int                   # 1 = best
    percentile: float           # 0-100, higher = better
    peer_median: float
    peer_mean: float
    peer_min: float
    peer_max: float


@dataclass
class PeriodComparison:
    """Period-over-period metric comparison."""
    metric_name: str
    current_value: float
    prior_value: float
    absolute_change: float
    pct_change: float
    improved: bool


@dataclass
class BenchmarkComplianceCheck:
    """Check fund against EU Climate Benchmark requirements."""
    is_ctb_aligned: bool        # Climate Transition Benchmark
    is_pab_aligned: bool        # Paris-Aligned Benchmark
    ctb_reasons: list[str]
    pab_reasons: list[str]
    waci_reduction_pct: float   # vs parent benchmark
    fossil_fuel_exclusion_met: bool
    controversial_weapons_excluded: bool
    yoy_decarbonisation_pct: float


@dataclass
class PortfolioBenchmarkReport:
    """Full benchmark analytics report for a fund."""
    fund_id: str
    fund_name: str

    # Peer rankings
    peer_rankings: list[PeerRanking]

    # Period comparison
    period_comparisons: list[PeriodComparison]

    # Climate benchmark compliance
    benchmark_compliance: BenchmarkComplianceCheck

    # Summary scores
    overall_peer_percentile: float    # Average percentile across metrics
    improvement_count: int            # Number of metrics improved YoY
    deterioration_count: int


# ---------------------------------------------------------------------------
# Engine
# ---------------------------------------------------------------------------

class BenchmarkAnalyticsService:
    """Compute peer rankings, period comparisons, and benchmark compliance."""

    def compute_peer_rankings(
        self,
        fund: PeerFundMetrics,
        peers: list[PeerFundMetrics],
    ) -> list[PeerRanking]:
        """Rank a fund against peers on key ESG metrics."""
        all_funds = [fund] + peers
        rankings = []

        # WACI — lower is better
        rankings.append(self._rank_metric(
            "waci", fund.waci,
            [f.waci for f in all_funds],
            lower_is_better=True,
        ))

        # ESG Score — higher is better
        rankings.append(self._rank_metric(
            "esg_score", fund.esg_score,
            [f.esg_score for f in all_funds],
            lower_is_better=False,
        ))

        # Taxonomy alignment — higher is better
        rankings.append(self._rank_metric(
            "taxonomy_aligned_pct", fund.taxonomy_aligned_pct,
            [f.taxonomy_aligned_pct for f in all_funds],
            lower_is_better=False,
        ))

        # Active share — informational, higher = more active
        rankings.append(self._rank_metric(
            "active_share_pct", fund.active_share_pct,
            [f.active_share_pct for f in all_funds],
            lower_is_better=False,
        ))

        return rankings

    def compute_period_comparison(
        self,
        current: dict[str, float],
        prior: dict[str, float],
        directions: dict[str, str],
    ) -> list[PeriodComparison]:
        """Compare current period metrics against prior period."""
        comparisons = []
        for metric, curr_val in current.items():
            prev_val = prior.get(metric, 0.0)
            abs_change = curr_val - prev_val
            pct_change = (abs_change / prev_val * 100) if prev_val != 0 else 0.0

            direction = directions.get(metric, "lower_is_better")
            if direction == "lower_is_better":
                improved = curr_val < prev_val
            else:
                improved = curr_val > prev_val

            comparisons.append(PeriodComparison(
                metric_name=metric,
                current_value=round(curr_val, 4),
                prior_value=round(prev_val, 4),
                absolute_change=round(abs_change, 4),
                pct_change=round(pct_change, 2),
                improved=improved,
            ))
        return comparisons

    def check_climate_benchmark_compliance(
        self,
        fund_waci: float,
        benchmark_waci: float,
        prior_waci: Optional[float],
        fossil_fuel_pct: float,
        controversial_weapons_pct: float,
    ) -> BenchmarkComplianceCheck:
        """
        Check against EU Climate Benchmark Regulation:
        - CTB: 30% lower WACI than parent benchmark
        - PAB: 50% lower WACI + fossil fuel exclusions
        - Both require 7% annual decarbonisation trajectory
        """
        waci_reduction = 0.0
        if benchmark_waci > 0:
            waci_reduction = (benchmark_waci - fund_waci) / benchmark_waci * 100

        yoy_decarb = 0.0
        if prior_waci and prior_waci > 0:
            yoy_decarb = (prior_waci - fund_waci) / prior_waci * 100

        fossil_excluded = fossil_fuel_pct < 1.0  # PAB requires exclusion
        weapons_excluded = controversial_weapons_pct == 0.0

        # CTB: >=30% WACI reduction vs parent
        ctb_reasons = []
        ctb_aligned = waci_reduction >= 30.0
        if not ctb_aligned:
            ctb_reasons.append(f"WACI reduction {waci_reduction:.1f}% < 30% required")
        if yoy_decarb < 7.0 and prior_waci is not None:
            ctb_reasons.append(f"YoY decarbonisation {yoy_decarb:.1f}% < 7% required")
            ctb_aligned = False

        # PAB: >=50% WACI reduction + fossil fuel + weapons exclusions
        pab_reasons = []
        pab_aligned = waci_reduction >= 50.0
        if not pab_aligned:
            pab_reasons.append(f"WACI reduction {waci_reduction:.1f}% < 50% required")
        if not fossil_excluded:
            pab_reasons.append(f"Fossil fuel exposure {fossil_fuel_pct:.1f}% > 1% maximum")
            pab_aligned = False
        if not weapons_excluded:
            pab_reasons.append("Controversial weapons not fully excluded")
            pab_aligned = False
        if yoy_decarb < 7.0 and prior_waci is not None:
            pab_reasons.append(f"YoY decarbonisation {yoy_decarb:.1f}% < 7% required")
            pab_aligned = False

        return BenchmarkComplianceCheck(
            is_ctb_aligned=ctb_aligned,
            is_pab_aligned=pab_aligned,
            ctb_reasons=ctb_reasons,
            pab_reasons=pab_reasons,
            waci_reduction_pct=round(waci_reduction, 2),
            fossil_fuel_exclusion_met=fossil_excluded,
            controversial_weapons_excluded=weapons_excluded,
            yoy_decarbonisation_pct=round(yoy_decarb, 2),
        )

    def generate_report(
        self,
        fund: PeerFundMetrics,
        peers: list[PeerFundMetrics],
        current_metrics: dict[str, float],
        prior_metrics: dict[str, float],
        metric_directions: dict[str, str],
        benchmark_waci: float,
        fossil_fuel_pct: float = 0.0,
        controversial_weapons_pct: float = 0.0,
    ) -> PortfolioBenchmarkReport:
        """Generate comprehensive benchmark analytics report."""
        rankings = self.compute_peer_rankings(fund, peers)

        comparisons = self.compute_period_comparison(
            current_metrics, prior_metrics, metric_directions,
        )

        compliance = self.check_climate_benchmark_compliance(
            fund_waci=fund.waci,
            benchmark_waci=benchmark_waci,
            prior_waci=prior_metrics.get("waci"),
            fossil_fuel_pct=fossil_fuel_pct,
            controversial_weapons_pct=controversial_weapons_pct,
        )

        avg_pctl = (
            sum(r.percentile for r in rankings) / len(rankings)
            if rankings else 0.0
        )
        improved = sum(1 for c in comparisons if c.improved)
        deteriorated = sum(1 for c in comparisons if not c.improved and c.absolute_change != 0)

        return PortfolioBenchmarkReport(
            fund_id=fund.fund_id,
            fund_name=fund.fund_name,
            peer_rankings=rankings,
            period_comparisons=comparisons,
            benchmark_compliance=compliance,
            overall_peer_percentile=round(avg_pctl, 2),
            improvement_count=improved,
            deterioration_count=deteriorated,
        )

    # -------------------------------------------------------------------
    # Helpers
    # -------------------------------------------------------------------

    def _rank_metric(
        self, name: str, value: float, all_values: list[float],
        lower_is_better: bool,
    ) -> PeerRanking:
        """Rank a single metric against a peer group."""
        n = len(all_values)
        if n == 0:
            return PeerRanking(
                metric_name=name, fund_value=value,
                peer_count=0, rank=1, percentile=100.0,
                peer_median=0, peer_mean=0, peer_min=0, peer_max=0,
            )

        sorted_vals = sorted(all_values, reverse=not lower_is_better)
        rank = sorted_vals.index(value) + 1

        # Percentile: (N - rank) / (N - 1) * 100
        percentile = (n - rank) / max(n - 1, 1) * 100

        sorted_asc = sorted(all_values)
        median = sorted_asc[n // 2] if n % 2 == 1 else (sorted_asc[n // 2 - 1] + sorted_asc[n // 2]) / 2.0

        return PeerRanking(
            metric_name=name,
            fund_value=round(value, 4),
            peer_count=n,
            rank=rank,
            percentile=round(percentile, 2),
            peer_median=round(median, 4),
            peer_mean=round(sum(all_values) / n, 4),
            peer_min=round(min(all_values), 4),
            peer_max=round(max(all_values), 4),
        )
