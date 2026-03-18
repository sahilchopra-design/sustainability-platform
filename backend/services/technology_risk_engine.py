"""
Technology Sector Risk & Sustainability Engine
===============================================
Covers Gap Analysis P1 §3.4 — Technology Sector Module:
  - Data Centre Emissions (PUE, WUE, CUE, embodied carbon)
  - Cloud Computing (Scope 3 Cat 1 from AWS/Azure/GCP)
  - Semiconductor Supply Chain (water intensity, rare earth risk)
  - AI Model Carbon Footprint (training + inference)
  - Hardware Lifecycle (e-waste, circular economy)
  - Digital Product Carbon Labeling (ISO 14044 LCA proxy)
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


# ---------------------------------------------------------------------------
# Reference Data
# ---------------------------------------------------------------------------

# Regional grid carbon intensity (gCO2/kWh) — IEA 2024 estimates
GRID_EMISSION_FACTORS: dict[str, float] = {
    "us-east-1": 379.0,       # Virginia (PJM grid, coal/gas mix)
    "us-west-2": 89.0,        # Oregon (hydro-heavy)
    "eu-west-1": 296.0,       # Ireland (gas + wind)
    "eu-central-1": 338.0,    # Frankfurt (gas/lignite transition)
    "eu-north-1": 8.0,        # Stockholm (hydro/nuclear/wind)
    "ap-southeast-1": 408.0,  # Singapore (gas)
    "ap-northeast-1": 457.0,  # Tokyo (gas/coal/nuclear restart)
    "ap-south-1": 632.0,      # Mumbai (coal-heavy grid)
    "me-south-1": 528.0,      # Bahrain
    "global_avg": 436.0,
}

# Cloud provider PUE benchmarks (public disclosures 2024)
CLOUD_PROVIDER_PUE: dict[str, float] = {
    "aws": 1.135,
    "azure": 1.18,
    "gcp": 1.10,
    "oracle": 1.25,
    "alibaba": 1.25,
    "on_prem_avg": 1.58,
}

# Semiconductor water intensity (litres per cm² of wafer)
SEMICONDUCTOR_WATER_INTENSITY: dict[str, float] = {
    "logic_5nm": 30.0,
    "logic_7nm": 25.0,
    "logic_14nm": 18.0,
    "logic_28nm": 12.0,
    "memory_dram": 20.0,
    "memory_nand": 15.0,
    "analog": 8.0,
    "power": 6.0,
}

# Critical minerals dependency (HHI-style concentration, top 3 countries %)
RARE_EARTH_CONCENTRATION: dict[str, dict] = {
    "gallium": {"top3_pct": 98.0, "primary": "CN", "risk": "critical"},
    "germanium": {"top3_pct": 97.0, "primary": "CN", "risk": "critical"},
    "cobalt": {"top3_pct": 74.0, "primary": "CD", "risk": "high"},
    "lithium": {"top3_pct": 87.0, "primary": "AU", "risk": "high"},
    "silicon_metal": {"top3_pct": 78.0, "primary": "CN", "risk": "medium"},
    "copper": {"top3_pct": 42.0, "primary": "CL", "risk": "medium"},
    "tantalum": {"top3_pct": 60.0, "primary": "CD", "risk": "high"},
    "indium": {"top3_pct": 75.0, "primary": "CN", "risk": "high"},
    "tin": {"top3_pct": 62.0, "primary": "CN", "risk": "medium"},
    "platinum_group": {"top3_pct": 88.0, "primary": "ZA", "risk": "high"},
}

# E-waste category recycling rates (global average %)
EWASTE_RECYCLING_RATES: dict[str, float] = {
    "servers": 35.0,
    "networking": 20.0,
    "storage": 25.0,
    "desktops": 30.0,
    "laptops": 25.0,
    "monitors": 15.0,
    "mobile_phones": 15.0,
    "batteries": 10.0,
    "cables": 40.0,
}

# AI model training energy estimates (kWh) — published research
AI_TRAINING_BENCHMARKS: dict[str, dict] = {
    "gpt4_class": {"training_kwh": 62_000_000, "params_b": 1800, "source": "Epoch AI 2024 est."},
    "gpt3_class": {"training_kwh": 1_287_000, "params_b": 175, "source": "Patterson et al. 2021"},
    "llama3_70b": {"training_kwh": 6_500_000, "params_b": 70, "source": "Meta 2024 disclosure"},
    "bert_base": {"training_kwh": 1_536, "params_b": 0.11, "source": "Strubell et al. 2019"},
    "stable_diffusion": {"training_kwh": 150_000, "params_b": 0.9, "source": "Luccioni et al. 2023"},
    "custom_small": {"training_kwh": 500, "params_b": 0.01, "source": "Typical fine-tune"},
}

# PUE benchmarks by tier and cooling
PUE_BENCHMARKS: dict[str, dict[str, float]] = {
    "hyperscale": {"best": 1.08, "median": 1.12, "worst": 1.25},
    "colocation": {"best": 1.15, "median": 1.35, "worst": 1.60},
    "enterprise": {"best": 1.20, "median": 1.58, "worst": 2.20},
    "edge": {"best": 1.30, "median": 1.50, "worst": 1.80},
}

# WUE benchmarks (L/kWh IT load)
WUE_BENCHMARKS: dict[str, dict[str, float]] = {
    "air_cooled": {"best": 0.0, "median": 0.5, "worst": 1.2},
    "evaporative": {"best": 1.0, "median": 1.8, "worst": 3.5},
    "liquid": {"best": 0.0, "median": 0.2, "worst": 0.6},
    "adiabatic": {"best": 0.3, "median": 0.9, "worst": 2.0},
}


# ---------------------------------------------------------------------------
# Data Classes
# ---------------------------------------------------------------------------

@dataclass
class DataCentreInput:
    facility_name: str
    facility_type: str = "enterprise"       # enterprise/colocation/hyperscale/edge
    country_iso: str = "US"
    grid_region: str = "global_avg"
    pue_actual: float = 0.0                 # 0 = not measured
    wue_actual_l_kwh: float = 0.0           # litres per kWh IT
    it_load_mw: float = 1.0
    annual_it_energy_mwh: float = 0.0       # 0 = auto-calc from it_load_mw
    cooling_type: str = "air"               # air/liquid/adiabatic/immersion/hybrid
    renewable_pct: float = 0.0
    year_built: int = 2015
    total_floor_area_m2: float = 5000.0
    embodied_carbon_known_tco2e: float = 0.0  # 0 = estimate


@dataclass
class DataCentreResult:
    facility_name: str
    facility_type: str
    # Efficiency metrics
    pue: float
    pue_benchmark: str                      # best/median/worst vs. peers
    wue_l_kwh: float
    wue_benchmark: str
    cue: float                              # Carbon Usage Effectiveness
    # Energy & emissions
    total_energy_mwh: float                 # IT + overhead
    it_energy_mwh: float
    overhead_mwh: float
    scope2_tco2e: float
    scope2_market_tco2e: float              # after renewable credits
    embodied_carbon_tco2e: float
    total_carbon_tco2e: float
    carbon_intensity_kgco2_per_kwh_it: float
    # Water
    annual_water_m3: float
    # Recommendations
    efficiency_gap_pct: float               # vs. best-in-class
    recommendations: list[str] = field(default_factory=list)


@dataclass
class CloudEmissionsInput:
    provider: str = "aws"                   # aws/azure/gcp/oracle/on_prem_avg
    region: str = "us-east-1"
    compute_hours: float = 0.0             # vCPU-hours
    gpu_hours: float = 0.0                 # GPU-hours
    storage_tb_months: float = 0.0
    network_egress_tb: float = 0.0
    avg_cpu_utilization: float = 0.50
    instance_type: str = "general"          # general/compute/memory/gpu


@dataclass
class CloudEmissionsResult:
    provider: str
    region: str
    grid_ef_gco2_kwh: float
    pue: float
    # Energy
    compute_energy_kwh: float
    gpu_energy_kwh: float
    storage_energy_kwh: float
    network_energy_kwh: float
    total_energy_kwh: float
    total_energy_with_pue_kwh: float
    # Emissions
    scope3_cat1_tco2e: float               # purchased cloud = your Scope 3 Cat 1
    scope2_equivalent_tco2e: float          # if you ran it yourself
    cloud_savings_pct: float               # delta vs. on-prem
    # Benchmarks
    carbon_per_vcpu_hour_gco2: float
    recommendation: str


@dataclass
class AIModelCarbonInput:
    model_type: str = "custom_small"        # from AI_TRAINING_BENCHMARKS or custom
    training_kwh: float = 0.0               # 0 = use benchmark
    training_hours: float = 0.0
    gpu_count: int = 1
    gpu_tdp_w: float = 350.0               # A100=300W, H100=700W, A6000=300W
    inference_requests_per_day: float = 0.0
    inference_latency_ms: float = 50.0
    grid_region: str = "us-east-1"
    pue: float = 1.12
    model_lifetime_years: float = 2.0


@dataclass
class AIModelCarbonResult:
    model_type: str
    # Training
    training_energy_kwh: float
    training_co2_tco2e: float
    # Inference (annual)
    inference_energy_kwh_annual: float
    inference_co2_tco2e_annual: float
    # Lifetime total
    total_lifetime_tco2e: float
    training_share_pct: float
    inference_share_pct: float
    # Equivalences
    car_km_equivalent: float               # 1 tCO2e ≈ 6000 km avg car
    household_days_equivalent: float       # 1 tCO2e ≈ 37 days avg EU household
    # Efficiency metrics
    co2_per_1k_requests_gco2: float
    recommendation: str


@dataclass
class SemiconductorRiskInput:
    process_node: str = "logic_14nm"
    annual_wafer_starts: int = 10000
    wafer_size_mm: int = 300               # 200mm or 300mm
    fab_country: str = "TW"
    minerals_used: list[str] = field(default_factory=lambda: ["gallium", "copper", "silicon_metal"])


@dataclass
class SemiconductorRiskResult:
    process_node: str
    # Water risk
    water_per_wafer_litres: float
    annual_water_m3: float
    water_stress_rating: str               # low/medium/high/extremely_high
    # Supply chain risk
    mineral_risks: list[dict]              # [{mineral, risk, top3_pct, primary_country}]
    overall_supply_risk: str               # low/medium/high/critical
    hhi_avg: float                         # avg concentration score
    # Recommendations
    recommendations: list[str] = field(default_factory=list)


@dataclass
class EWasteInput:
    hardware_inventory: dict[str, int] = field(default_factory=dict)
    # e.g. {"servers": 200, "networking": 50, "storage": 30, "laptops": 500}
    avg_weight_kg: dict[str, float] = field(default_factory=lambda: {
        "servers": 25.0, "networking": 5.0, "storage": 15.0,
        "desktops": 8.0, "laptops": 2.5, "monitors": 5.0,
        "mobile_phones": 0.2, "batteries": 0.5, "cables": 0.3,
    })
    replacement_cycle_years: float = 4.0
    current_recycling_pct: float = 0.0     # 0 = use global avg


@dataclass
class EWasteResult:
    total_units: int
    total_weight_kg: float
    annual_ewaste_kg: float                 # weight / replacement_cycle
    annual_ewaste_tco2e: float             # embodied carbon proxy
    recycling_rate_pct: float
    recycled_kg: float
    landfill_kg: float
    circularity_score: float               # 0-100
    category_breakdown: list[dict]
    recommendations: list[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _dc_to_dict(r: DataCentreResult) -> dict:
    """Convert DataCentreResult dataclass to serialisable dict."""
    return {
        "facility_name": r.facility_name,
        "facility_type": r.facility_type,
        "pue": r.pue,
        "pue_benchmark": r.pue_benchmark,
        "wue_l_kwh": r.wue_l_kwh,
        "wue_benchmark": r.wue_benchmark,
        "cue": r.cue,
        "total_energy_mwh": r.total_energy_mwh,
        "it_energy_mwh": r.it_energy_mwh,
        "overhead_mwh": r.overhead_mwh,
        "scope2_tco2e": r.scope2_tco2e,
        "scope2_market_tco2e": r.scope2_market_tco2e,
        "embodied_carbon_tco2e": r.embodied_carbon_tco2e,
        "total_carbon_tco2e": r.total_carbon_tco2e,
        "carbon_intensity_kgco2_per_kwh_it": r.carbon_intensity_kgco2_per_kwh_it,
        "annual_water_m3": r.annual_water_m3,
        "efficiency_gap_pct": r.efficiency_gap_pct,
        "recommendations": r.recommendations,
    }


# ---------------------------------------------------------------------------
# Engine
# ---------------------------------------------------------------------------

class TechnologyRiskEngine:
    """Comprehensive technology sector sustainability assessment."""

    # ── Data Centre Assessment ──────────────────────────────────────────────

    def assess_data_centre(self, inp: DataCentreInput) -> DataCentreResult:
        """Full data centre efficiency + emissions assessment."""
        # Resolve PUE
        benchmarks = PUE_BENCHMARKS.get(inp.facility_type, PUE_BENCHMARKS["enterprise"])
        if inp.pue_actual > 0:
            pue = inp.pue_actual
        else:
            pue = benchmarks["median"]

        pue_bench = (
            "best" if pue <= benchmarks["best"]
            else "median" if pue <= benchmarks["median"]
            else "worst"
        )

        # IT energy
        if inp.annual_it_energy_mwh > 0:
            it_mwh = inp.annual_it_energy_mwh
        else:
            it_mwh = inp.it_load_mw * 8760 * 0.70  # 70% avg utilization

        total_mwh = it_mwh * pue
        overhead_mwh = total_mwh - it_mwh

        # Grid EF
        grid_ef = GRID_EMISSION_FACTORS.get(inp.grid_region, GRID_EMISSION_FACTORS["global_avg"])

        # Scope 2
        scope2_location = total_mwh * grid_ef / 1000  # tCO2e
        scope2_market = scope2_location * (1 - inp.renewable_pct / 100)

        # CUE = gCO2 / kWh IT
        cue = (scope2_market * 1_000_000) / max(it_mwh * 1000, 1)  # gCO2/kWh IT

        # WUE
        wue_bench_data = WUE_BENCHMARKS.get(
            inp.cooling_type if inp.cooling_type in WUE_BENCHMARKS else "air_cooled",
            WUE_BENCHMARKS["air_cooled"],
        )
        wue = inp.wue_actual_l_kwh if inp.wue_actual_l_kwh > 0 else wue_bench_data["median"]
        wue_bench = (
            "best" if wue <= wue_bench_data["best"]
            else "median" if wue <= wue_bench_data["median"]
            else "worst"
        )

        # Water consumption
        annual_water_m3 = wue * it_mwh * 1000 / 1000  # L → m3

        # Embodied carbon
        if inp.embodied_carbon_known_tco2e > 0:
            embodied = inp.embodied_carbon_known_tco2e
        else:
            # Rough estimate: ~350 kgCO2e per m2 for data centre construction
            embodied = inp.total_floor_area_m2 * 0.35  # tCO2e amortised

        total_carbon = scope2_market + embodied
        carbon_intensity = (scope2_market * 1000) / max(it_mwh, 1)  # kgCO2/kWh IT

        # Efficiency gap vs. best-in-class
        best_pue = benchmarks["best"]
        efficiency_gap = ((pue - best_pue) / best_pue) * 100 if pue > best_pue else 0

        # Recommendations
        recs = []
        if pue > benchmarks["median"]:
            recs.append(f"PUE of {pue:.2f} exceeds median ({benchmarks['median']:.2f}). Consider hot/cold aisle containment or free cooling upgrade.")
        if inp.renewable_pct < 50:
            recs.append(f"Renewable share at {inp.renewable_pct:.0f}% — target 100% via PPAs or on-site generation.")
        if wue > 1.5:
            recs.append(f"WUE of {wue:.1f} L/kWh is high. Evaluate liquid cooling or closed-loop systems.")
        if inp.year_built < 2015:
            recs.append("Facility >10 years old. Assess stranding risk from efficiency regulations (EU EED recast Art. 12).")
        if not recs:
            recs.append("Facility operating at or near best-in-class efficiency.")

        return DataCentreResult(
            facility_name=inp.facility_name,
            facility_type=inp.facility_type,
            pue=round(pue, 3),
            pue_benchmark=pue_bench,
            wue_l_kwh=round(wue, 2),
            wue_benchmark=wue_bench,
            cue=round(cue, 2),
            total_energy_mwh=round(total_mwh, 1),
            it_energy_mwh=round(it_mwh, 1),
            overhead_mwh=round(overhead_mwh, 1),
            scope2_tco2e=round(scope2_location, 2),
            scope2_market_tco2e=round(scope2_market, 2),
            embodied_carbon_tco2e=round(embodied, 2),
            total_carbon_tco2e=round(total_carbon, 2),
            carbon_intensity_kgco2_per_kwh_it=round(carbon_intensity, 2),
            annual_water_m3=round(annual_water_m3, 1),
            efficiency_gap_pct=round(efficiency_gap, 1),
            recommendations=recs,
        )

    # ── Cloud Emissions ─────────────────────────────────────────────────────

    def assess_cloud_emissions(self, inp: CloudEmissionsInput) -> CloudEmissionsResult:
        """Estimate Scope 3 Category 1 emissions from cloud services."""
        grid_ef = GRID_EMISSION_FACTORS.get(inp.region, GRID_EMISSION_FACTORS["global_avg"])
        pue = CLOUD_PROVIDER_PUE.get(inp.provider, CLOUD_PROVIDER_PUE["on_prem_avg"])

        # Energy estimates
        # CPU: ~10W per vCPU at 50% util, scales linearly
        cpu_power_w = 10 * max(inp.avg_cpu_utilization / 0.5, 0.4)
        compute_kwh = inp.compute_hours * cpu_power_w / 1000

        # GPU: direct TDP-based
        gpu_kwh = inp.gpu_hours * 0.350 / 1  # assume A100-class 350W

        # Storage: ~0.1 W per TB continuously
        storage_kwh = inp.storage_tb_months * 0.1 * 730 / 1000  # 730 hrs/month

        # Network: ~0.05 kWh per GB egress
        network_kwh = inp.network_egress_tb * 1000 * 0.05

        total_kwh = compute_kwh + gpu_kwh + storage_kwh + network_kwh
        total_with_pue = total_kwh * pue

        # Emissions
        scope3_cat1 = total_with_pue * grid_ef / 1_000_000  # tCO2e

        # Compare to on-prem
        on_prem_pue = CLOUD_PROVIDER_PUE["on_prem_avg"]
        scope2_on_prem = total_kwh * on_prem_pue * grid_ef / 1_000_000
        savings_pct = ((scope2_on_prem - scope3_cat1) / max(scope2_on_prem, 0.001)) * 100

        # Per-unit metrics
        carbon_per_vcpu = (scope3_cat1 * 1_000_000) / max(inp.compute_hours, 1)  # gCO2

        rec = "Consider "
        if grid_ef > 300:
            rec += f"migrating to lower-carbon region (e.g., eu-north-1 at {GRID_EMISSION_FACTORS['eu-north-1']}g). "
        if inp.avg_cpu_utilization < 0.30:
            rec += "right-sizing instances (utilization below 30%). "
        if inp.gpu_hours > 0:
            rec += "using spot/preemptible GPU instances to reduce idle waste. "
        if rec == "Consider ":
            rec = "Good cloud usage profile — continue monitoring utilization."

        return CloudEmissionsResult(
            provider=inp.provider,
            region=inp.region,
            grid_ef_gco2_kwh=grid_ef,
            pue=pue,
            compute_energy_kwh=round(compute_kwh, 2),
            gpu_energy_kwh=round(gpu_kwh, 2),
            storage_energy_kwh=round(storage_kwh, 2),
            network_energy_kwh=round(network_kwh, 2),
            total_energy_kwh=round(total_kwh, 2),
            total_energy_with_pue_kwh=round(total_with_pue, 2),
            scope3_cat1_tco2e=round(scope3_cat1, 4),
            scope2_equivalent_tco2e=round(scope2_on_prem, 4),
            cloud_savings_pct=round(savings_pct, 1),
            carbon_per_vcpu_hour_gco2=round(carbon_per_vcpu, 2),
            recommendation=rec,
        )

    # ── AI Model Carbon Footprint ───────────────────────────────────────────

    def assess_ai_carbon(self, inp: AIModelCarbonInput) -> AIModelCarbonResult:
        """Estimate AI model training + inference carbon footprint."""
        grid_ef = GRID_EMISSION_FACTORS.get(inp.grid_region, GRID_EMISSION_FACTORS["global_avg"])

        # Training energy
        if inp.training_kwh > 0:
            train_kwh = inp.training_kwh
        elif inp.training_hours > 0:
            train_kwh = inp.training_hours * inp.gpu_count * inp.gpu_tdp_w / 1000
        else:
            benchmark = AI_TRAINING_BENCHMARKS.get(inp.model_type, AI_TRAINING_BENCHMARKS["custom_small"])
            train_kwh = benchmark["training_kwh"]

        train_kwh_with_pue = train_kwh * inp.pue
        train_tco2e = train_kwh_with_pue * grid_ef / 1_000_000

        # Inference (annual)
        if inp.inference_requests_per_day > 0:
            # Power per request: GPU TDP * latency_sec / gpu_count
            power_per_request_wh = (inp.gpu_tdp_w * inp.inference_latency_ms / 1000) / 3600
            annual_requests = inp.inference_requests_per_day * 365
            infer_kwh = annual_requests * power_per_request_wh / 1000
        else:
            infer_kwh = 0.0

        infer_kwh_with_pue = infer_kwh * inp.pue
        infer_tco2e_annual = infer_kwh_with_pue * grid_ef / 1_000_000

        # Lifetime
        total_lifetime = train_tco2e + infer_tco2e_annual * inp.model_lifetime_years
        train_share = (train_tco2e / max(total_lifetime, 0.0001)) * 100
        infer_share = 100 - train_share

        # Equivalences
        car_km = total_lifetime * 6000  # avg car ~167 gCO2/km
        household_days = total_lifetime * 37  # avg EU household ~27 kgCO2/day

        # Per-request metric
        co2_per_1k = 0.0
        if inp.inference_requests_per_day > 0:
            annual_requests = inp.inference_requests_per_day * 365
            co2_per_1k = (infer_tco2e_annual * 1_000_000 / max(annual_requests, 1)) * 1000

        rec = ""
        if train_tco2e > 100:
            rec += f"Training carbon ({train_tco2e:.0f} tCO2e) is significant. Use renewable-powered regions. "
        if infer_share > 80:
            rec += "Inference dominates — optimize model (quantization, distillation, pruning). "
        if grid_ef > 400:
            rec += f"High-carbon grid ({grid_ef:.0f} gCO2/kWh). Migrate to cleaner region. "
        if not rec:
            rec = "Carbon footprint within reasonable bounds for model class."

        return AIModelCarbonResult(
            model_type=inp.model_type,
            training_energy_kwh=round(train_kwh_with_pue, 1),
            training_co2_tco2e=round(train_tco2e, 4),
            inference_energy_kwh_annual=round(infer_kwh_with_pue, 1),
            inference_co2_tco2e_annual=round(infer_tco2e_annual, 4),
            total_lifetime_tco2e=round(total_lifetime, 4),
            training_share_pct=round(train_share, 1),
            inference_share_pct=round(infer_share, 1),
            car_km_equivalent=round(car_km, 0),
            household_days_equivalent=round(household_days, 1),
            co2_per_1k_requests_gco2=round(co2_per_1k, 2),
            recommendation=rec,
        )

    # ── Semiconductor Supply Chain Risk ─────────────────────────────────────

    def assess_semiconductor_risk(self, inp: SemiconductorRiskInput) -> SemiconductorRiskResult:
        """Water intensity + mineral supply chain risk for semiconductor manufacturing."""
        # Water
        water_per_wafer = SEMICONDUCTOR_WATER_INTENSITY.get(
            inp.process_node, SEMICONDUCTOR_WATER_INTENSITY["logic_14nm"]
        )
        # Convert to litres per wafer (area-based)
        wafer_area_cm2 = 3.14159 * (inp.wafer_size_mm / 20) ** 2  # cm² from mm diameter
        water_per_wafer_l = water_per_wafer * wafer_area_cm2
        annual_water_m3 = (water_per_wafer_l * inp.annual_wafer_starts) / 1000

        # Water stress by country
        water_stress_map = {
            "TW": "extremely_high", "KR": "high", "JP": "medium",
            "US": "medium", "CN": "high", "DE": "medium",
            "SG": "high", "IE": "low", "IL": "extremely_high",
        }
        water_stress = water_stress_map.get(inp.fab_country, "medium")

        # Mineral risks
        mineral_risks = []
        hhi_scores = []
        for mineral in inp.minerals_used:
            info = RARE_EARTH_CONCENTRATION.get(mineral)
            if info:
                mineral_risks.append({
                    "mineral": mineral,
                    "risk": info["risk"],
                    "top3_concentration_pct": info["top3_pct"],
                    "primary_country": info["primary"],
                })
                hhi_scores.append(info["top3_pct"])

        hhi_avg = sum(hhi_scores) / max(len(hhi_scores), 1)
        overall_risk = (
            "critical" if hhi_avg > 90
            else "high" if hhi_avg > 70
            else "medium" if hhi_avg > 50
            else "low"
        )

        recs = []
        if water_stress in ("extremely_high", "high"):
            recs.append(f"Fab location ({inp.fab_country}) in {water_stress} water stress zone. Evaluate water recycling (target >85% UPW recovery).")
        if any(m["risk"] == "critical" for m in mineral_risks):
            critical = [m["mineral"] for m in mineral_risks if m["risk"] == "critical"]
            recs.append(f"Critical supply risk for: {', '.join(critical)}. Diversify sourcing or stockpile.")
        if inp.process_node.startswith("logic_5nm"):
            recs.append("Leading-edge 5nm uses ~2.5x more water per cm² than mature nodes. Prioritise recycling.")
        if not recs:
            recs.append("Supply chain risk within acceptable bounds.")

        return SemiconductorRiskResult(
            process_node=inp.process_node,
            water_per_wafer_litres=round(water_per_wafer_l, 1),
            annual_water_m3=round(annual_water_m3, 1),
            water_stress_rating=water_stress,
            mineral_risks=mineral_risks,
            overall_supply_risk=overall_risk,
            hhi_avg=round(hhi_avg, 1),
            recommendations=recs,
        )

    # ── E-Waste / Circular Economy ──────────────────────────────────────────

    def assess_ewaste(self, inp: EWasteInput) -> EWasteResult:
        """Hardware lifecycle e-waste and circularity assessment."""
        total_units = sum(inp.hardware_inventory.values())
        total_weight = 0.0
        category_breakdown = []

        for cat, count in inp.hardware_inventory.items():
            weight_per = inp.avg_weight_kg.get(cat, 5.0)
            cat_weight = count * weight_per
            total_weight += cat_weight

            recycling = (
                inp.current_recycling_pct
                if inp.current_recycling_pct > 0
                else EWASTE_RECYCLING_RATES.get(cat, 20.0)
            )
            category_breakdown.append({
                "category": cat,
                "units": count,
                "weight_kg": round(cat_weight, 1),
                "recycling_rate_pct": round(recycling, 1),
            })

        annual_ewaste = total_weight / max(inp.replacement_cycle_years, 1)
        # Embodied carbon proxy: ~100 kgCO2e per kg of electronics (avg)
        annual_tco2e = annual_ewaste * 0.1  # tCO2e

        avg_recycling = (
            inp.current_recycling_pct if inp.current_recycling_pct > 0
            else sum(EWASTE_RECYCLING_RATES.get(c, 20) for c in inp.hardware_inventory) / max(len(inp.hardware_inventory), 1)
        )
        recycled_kg = annual_ewaste * avg_recycling / 100
        landfill_kg = annual_ewaste - recycled_kg

        # Circularity score (0-100)
        # Based on: recycling %, replacement cycle, refurb potential
        recycle_score = min(avg_recycling, 100) * 0.5  # max 50 pts
        lifecycle_score = min(inp.replacement_cycle_years / 6, 1.0) * 30  # max 30 pts (6yr = perfect)
        diversity_score = min(len(inp.hardware_inventory) / 5, 1.0) * 20  # max 20 pts
        circularity = recycle_score + lifecycle_score + diversity_score

        recs = []
        if avg_recycling < 30:
            recs.append("Recycling rate below 30%. Implement ITAD (IT Asset Disposition) program.")
        if inp.replacement_cycle_years < 3:
            recs.append(f"Replacement cycle of {inp.replacement_cycle_years:.1f}y is aggressive. Extend server life to 5-6 years.")
        if landfill_kg > 1000:
            recs.append(f"Estimated {landfill_kg:.0f} kg/yr to landfill. Engage certified e-waste recycler (R2/e-Stewards).")
        if not recs:
            recs.append("Hardware lifecycle management is above average.")

        return EWasteResult(
            total_units=total_units,
            total_weight_kg=round(total_weight, 1),
            annual_ewaste_kg=round(annual_ewaste, 1),
            annual_ewaste_tco2e=round(annual_tco2e, 2),
            recycling_rate_pct=round(avg_recycling, 1),
            recycled_kg=round(recycled_kg, 1),
            landfill_kg=round(landfill_kg, 1),
            circularity_score=round(circularity, 1),
            category_breakdown=category_breakdown,
            recommendations=recs,
        )

    # ── EU EED Recast Art. 12 Compliance Check ─────────────────────────────

    def eed_compliance_check(self, inp: DataCentreInput) -> dict:
        """
        EU Energy Efficiency Directive (recast 2023/1791) Article 12 compliance.
        From 15 May 2024, data centres with IT load ≥500 kW must report to EU DB.
        Mandatory KPIs per Delegated Regulation (EU) 2024/1364:
        - PUE, WUE, REF (Renewable Energy Factor), ERF (Energy Reuse Factor)
        - Cooling system info, temperature setpoints, waste heat reuse
        """
        subject_to_reporting = inp.it_load_mw >= 0.5  # ≥500 kW threshold

        # Compute KPIs per ISO 30134 / EU Delegated Regulation
        dc_result = self.assess_data_centre(inp)

        # REF — Renewable Energy Factor
        ref_pct = inp.renewable_pct  # % of total energy from renewable sources

        # ERF — Energy Reuse Factor (waste heat recovered / total energy)
        # Without explicit waste heat data, estimate from cooling type
        erf_estimates = {
            "air": 0.0, "liquid": 0.05, "direct_liquid": 0.15,
            "immersion": 0.20, "adiabatic": 0.02, "hybrid": 0.08,
            "free_cooling": 0.0,
        }
        erf = erf_estimates.get(inp.cooling_type, 0.0)

        # Temperature compliance — EU recast requires reporting inlet temps
        # Best practice: ASHRAE A1 envelope 18-27°C
        temp_compliant = True  # Assumed unless flagged

        # Compile compliance items
        checks = []

        # 1. Reporting obligation
        checks.append({
            "requirement": "EED Art. 12(1) — Reporting to EU Database",
            "status": "applicable" if subject_to_reporting else "not_applicable",
            "detail": f"IT load {inp.it_load_mw:.2f} MW {'≥' if subject_to_reporting else '<'} 0.5 MW threshold",
        })

        # 2. PUE reporting
        pue_target_2025 = 1.5  # EED Art. 12 indicative target
        pue_target_2030 = 1.3
        checks.append({
            "requirement": "PUE reporting + target trajectory",
            "status": "compliant" if dc_result.pue <= pue_target_2025 else "non_compliant",
            "detail": f"PUE {dc_result.pue:.3f} vs. 2025 target {pue_target_2025}, 2030 target {pue_target_2030}",
            "pue": dc_result.pue,
            "target_2025": pue_target_2025,
            "target_2030": pue_target_2030,
        })

        # 3. WUE reporting
        checks.append({
            "requirement": "WUE reporting (L/kWh IT load)",
            "status": "reported",
            "detail": f"WUE {dc_result.wue_l_kwh:.2f} L/kWh ({dc_result.wue_benchmark} vs. benchmark)",
        })

        # 4. Renewable Energy Factor
        ref_target = 100.0  # EU long-term goal
        checks.append({
            "requirement": "REF — Renewable Energy Factor",
            "status": "compliant" if ref_pct >= 50 else "improvement_needed",
            "detail": f"REF {ref_pct:.0f}% (target path: 50% by 2025, 75% by 2028, 100% by 2030)",
            "ref_pct": ref_pct,
        })

        # 5. ERF — Waste Heat Reuse
        checks.append({
            "requirement": "ERF — Energy Reuse Factor (waste heat)",
            "status": "reported",
            "detail": f"Estimated ERF {erf:.0%} based on {inp.cooling_type} cooling",
            "erf": erf,
        })

        # 6. ISO 30134 KPI set
        iso_kpis = {
            "iso_30134_2_pue": dc_result.pue,
            "iso_30134_3_ref": ref_pct / 100,
            "iso_30134_4_cue": dc_result.cue,
            "iso_30134_6_erf": erf,
            "iso_30134_8_wue": dc_result.wue_l_kwh,
        }
        checks.append({
            "requirement": "ISO 30134 KPI suite (PUE/REF/CUE/ERF/WUE)",
            "status": "reported",
            "iso_kpis": iso_kpis,
        })

        overall_status = "compliant"
        for c in checks:
            if c["status"] == "non_compliant":
                overall_status = "non_compliant"
                break
            if c["status"] == "improvement_needed":
                overall_status = "improvement_needed"

        return {
            "subject_to_eed_reporting": subject_to_reporting,
            "overall_compliance_status": overall_status,
            "checks": checks,
            "iso_30134_kpis": iso_kpis,
            "data_centre_assessment": _dc_to_dict(dc_result),
            "methodology": "EU EED recast 2023/1791 Art. 12, Delegated Reg. 2024/1364, ISO 30134-2/3/4/6/8",
        }

    # ── Integrated Technology Entity Assessment ──────────────────────────────

    def integrated_assessment(
        self,
        entity_name: str,
        data_centres: list[DataCentreInput] | None = None,
        cloud_usage: CloudEmissionsInput | None = None,
        ai_models: list[AIModelCarbonInput] | None = None,
        semiconductor: SemiconductorRiskInput | None = None,
        ewaste: EWasteInput | None = None,
    ) -> dict:
        """
        Comprehensive technology entity sustainability assessment.
        Aggregates all sub-modules into a unified risk profile with
        ESG score, CSRD E1 data points, and regulatory readiness.
        """
        total_scope2_tco2e = 0.0
        total_scope3_tco2e = 0.0
        total_water_m3 = 0.0
        total_ewaste_kg = 0.0
        modules_assessed = []
        recommendations = []

        # Data centres
        dc_results = []
        if data_centres:
            for dc_inp in data_centres:
                r = self.assess_data_centre(dc_inp)
                dc_results.append(_dc_to_dict(r))
                total_scope2_tco2e += r.scope2_market_tco2e
                total_water_m3 += r.annual_water_m3
                recommendations.extend(r.recommendations)
            modules_assessed.append("data_centres")

        # Cloud
        cloud_result = None
        if cloud_usage:
            r = self.assess_cloud_emissions(cloud_usage)
            cloud_result = {
                "provider": r.provider, "region": r.region,
                "scope3_cat1_tco2e": r.scope3_cat1_tco2e,
                "total_energy_kwh": r.total_energy_with_pue_kwh,
                "cloud_savings_pct": r.cloud_savings_pct,
            }
            total_scope3_tco2e += r.scope3_cat1_tco2e
            recommendations.append(r.recommendation)
            modules_assessed.append("cloud")

        # AI
        ai_results = []
        if ai_models:
            for ai_inp in ai_models:
                r = self.assess_ai_carbon(ai_inp)
                ai_results.append({
                    "model_type": r.model_type,
                    "total_lifetime_tco2e": r.total_lifetime_tco2e,
                    "training_co2_tco2e": r.training_co2_tco2e,
                    "inference_co2_tco2e_annual": r.inference_co2_tco2e_annual,
                })
                # Training is Scope 2 or Scope 3 depending on ownership
                total_scope3_tco2e += r.inference_co2_tco2e_annual
                total_scope2_tco2e += r.training_co2_tco2e
                recommendations.append(r.recommendation)
            modules_assessed.append("ai_models")

        # Semiconductor
        semi_result = None
        if semiconductor:
            r = self.assess_semiconductor_risk(semiconductor)
            semi_result = {
                "process_node": r.process_node,
                "annual_water_m3": r.annual_water_m3,
                "overall_supply_risk": r.overall_supply_risk,
                "hhi_avg": r.hhi_avg,
            }
            total_water_m3 += r.annual_water_m3
            recommendations.extend(r.recommendations)
            modules_assessed.append("semiconductor")

        # E-waste
        ewaste_result = None
        if ewaste:
            r = self.assess_ewaste(ewaste)
            ewaste_result = {
                "annual_ewaste_kg": r.annual_ewaste_kg,
                "circularity_score": r.circularity_score,
                "recycling_rate_pct": r.recycling_rate_pct,
            }
            total_ewaste_kg += r.annual_ewaste_kg
            total_scope3_tco2e += r.annual_ewaste_tco2e
            recommendations.extend(r.recommendations)
            modules_assessed.append("ewaste")

        # Composite ESG score (tech-weighted)
        # E: carbon intensity + water + renewables (60%)
        # S: e-waste / circular economy + supply chain (20%)
        # G: regulatory compliance + disclosure readiness (20%)
        total_carbon = total_scope2_tco2e + total_scope3_tco2e

        # E score (lower carbon = higher score)
        if total_carbon <= 0:
            e_score = 50.0  # no data
        elif total_carbon < 100:
            e_score = 90.0
        elif total_carbon < 1000:
            e_score = 75.0
        elif total_carbon < 10000:
            e_score = 55.0
        elif total_carbon < 100000:
            e_score = 35.0
        else:
            e_score = 15.0

        # S score
        if ewaste_result:
            s_score = ewaste_result["circularity_score"]
        else:
            s_score = 50.0

        # G score (based on modules assessed)
        g_score = min(len(modules_assessed) * 20, 100)

        composite = e_score * 0.6 + s_score * 0.2 + g_score * 0.2
        risk_band = (
            "low" if composite >= 70
            else "medium" if composite >= 50
            else "high" if composite >= 30
            else "critical"
        )

        # CSRD E1 auto-population (energy + emissions datapoints)
        csrd_e1_datapoints = {
            "e1_6_scope2_location_tco2e": round(total_scope2_tco2e, 2),
            "e1_6_scope3_category1_tco2e": round(total_scope3_tco2e, 2),
            "e1_5_total_energy_mwh": round(sum(r.get("total_energy_mwh", 0) for r in dc_results), 1),
            "e1_5_renewable_share_pct": round(
                sum(dc.renewable_pct for dc in (data_centres or [])) / max(len(data_centres or []), 1), 1
            ),
            "e3_4_total_water_m3": round(total_water_m3, 1),
            "e5_5_ewaste_kg": round(total_ewaste_kg, 1),
        }

        # Deduplicate recommendations
        seen = set()
        unique_recs = []
        for r in recommendations:
            if r not in seen:
                seen.add(r)
                unique_recs.append(r)

        return {
            "entity_name": entity_name,
            "modules_assessed": modules_assessed,
            "total_scope2_tco2e": round(total_scope2_tco2e, 2),
            "total_scope3_tco2e": round(total_scope3_tco2e, 2),
            "total_carbon_tco2e": round(total_carbon, 2),
            "total_water_m3": round(total_water_m3, 1),
            "total_ewaste_kg_annual": round(total_ewaste_kg, 1),
            "esg_score": {
                "environmental": round(e_score, 1),
                "social": round(s_score, 1),
                "governance": round(g_score, 1),
                "composite": round(composite, 1),
                "risk_band": risk_band,
            },
            "csrd_e1_datapoints": csrd_e1_datapoints,
            "data_centres": dc_results,
            "cloud": cloud_result,
            "ai_models": ai_results,
            "semiconductor": semi_result,
            "ewaste": ewaste_result,
            "recommendations": unique_recs,
        }

    # ── Reference Data Accessors ────────────────────────────────────────────

    def get_grid_emission_factors(self) -> dict:
        return GRID_EMISSION_FACTORS

    def get_cloud_provider_benchmarks(self) -> dict:
        return {
            "pue": CLOUD_PROVIDER_PUE,
            "grid_factors": GRID_EMISSION_FACTORS,
        }

    def get_pue_benchmarks(self) -> dict:
        return PUE_BENCHMARKS

    def get_wue_benchmarks(self) -> dict:
        return WUE_BENCHMARKS

    def get_ai_training_benchmarks(self) -> dict:
        return AI_TRAINING_BENCHMARKS

    def get_semiconductor_water_data(self) -> dict:
        return {
            "water_intensity": SEMICONDUCTOR_WATER_INTENSITY,
            "rare_earth_concentration": RARE_EARTH_CONCENTRATION,
        }

    def get_ewaste_recycling_rates(self) -> dict:
        return EWASTE_RECYCLING_RATES
