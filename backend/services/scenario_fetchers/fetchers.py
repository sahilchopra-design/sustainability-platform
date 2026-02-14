"""
Scenario data fetchers — real data from IIASA Scenario Explorer for NGFS, IPCC AR6,
and IAM models (REMIND, GCAM, MESSAGEix, IMAGE, WITCH).
Synthetic data for sources without public APIs (IEA, IRENA, regional, sector, carbon pricing, physical risk).
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
import uuid
import logging

logger = logging.getLogger(__name__)

# Key variables we want to extract from IIASA databases
IIASA_KEY_VARIABLES = [
    "Price|Carbon",
    "Emissions|CO2",
    "Emissions|CO2|Energy",
    "Emissions|CO2|Energy and Industrial Processes",
    "GDP|PPP",
    "Primary Energy",
    "Primary Energy|Coal",
    "Primary Energy|Gas",
    "Primary Energy|Oil",
    "Primary Energy|Solar",
    "Primary Energy|Wind",
    "Primary Energy|Biomass",
    "Primary Energy|Nuclear",
    "Secondary Energy|Electricity",
    "Secondary Energy|Electricity|Solar",
    "Secondary Energy|Electricity|Wind",
    "Capacity|Electricity|Solar",
    "Capacity|Electricity|Wind",
    "Investment|Energy Supply",
    "AR6 climate diagnostics|Surface Temperature (GSAT)|MAGICCv7.5.3|50.0th Percentile",
]

IIASA_KEY_REGIONS = ["World", "R5.2OECD90+EU", "R5.2ASIA", "R5.2MAF", "R5.2LAM", "R5.2REF"]

NGFS_TEMPERATURE_MAP = {
    "Net Zero 2050": 1.5,
    "Below 2°C": 1.7,
    "Below 2?C": 1.7,
    "Delayed transition": 1.8,
    "Divergent Net Zero": 1.5,
    "Nationally Determined Contributions (NDCs)": 2.5,
    "Current Policies": 3.0,
    "Fragmented World": 2.8,
    "Low demand": 1.5,
    "Baseline": 3.2,
}

NGFS_CATEGORY_MAP = {
    "Net Zero 2050": "Orderly",
    "Below 2°C": "Orderly",
    "Below 2?C": "Orderly",
    "Delayed transition": "Disorderly",
    "Divergent Net Zero": "Disorderly",
    "Nationally Determined Contributions (NDCs)": "Hot House World",
    "Current Policies": "Hot House World",
    "Fragmented World": "Disorderly",
    "Low demand": "Orderly",
    "Baseline": "Hot House World",
}

NGFS_CARBON_NEUTRAL = {
    "Net Zero 2050": 2050,
    "Below 2°C": 2070,
    "Delayed transition": 2055,
    "Divergent Net Zero": 2050,
    "Low demand": 2050,
}


class BaseFetcher(ABC):
    """Base class for all scenario data fetchers."""
    source_short_name: str = ""

    @abstractmethod
    def fetch(self) -> Dict[str, Any]:
        """Returns {"scenarios": [...], "trajectories": [...]}"""
        ...


def _build_timeseries(years, values) -> Dict[str, float]:
    """Convert parallel arrays to {year_str: value} dict."""
    ts = {}
    for y, v in zip(years, values):
        if v is not None and str(v) != 'nan':
            ts[str(int(y))] = round(float(v), 6)
    return ts


class IIASAFetcher(BaseFetcher):
    """
    Generic fetcher for any IIASA Scenario Explorer database.
    Pulls REAL data via pyam library.
    """
    source_short_name = ""
    iiasa_database: str = ""
    model_filter: Optional[List[str]] = None
    scenario_filter: Optional[List[str]] = None
    variable_filter: List[str] = IIASA_KEY_VARIABLES
    region_filter: List[str] = IIASA_KEY_REGIONS
    category_map: Dict[str, str] = {}
    temperature_map: Dict[str, float] = {}
    carbon_neutral_map: Dict[str, int] = {}
    data_quality: int = 5

    def fetch(self) -> Dict[str, Any]:
        import pyam
        import warnings
        warnings.filterwarnings("ignore")

        logger.info(f"Connecting to IIASA database: {self.iiasa_database}")
        conn = pyam.iiasa.Connection(self.iiasa_database)

        # Get scenario properties
        props = conn.properties()
        all_models = props.index.get_level_values("model").unique().tolist()
        all_scenarios = props.index.get_level_values("scenario").unique().tolist()

        # Apply filters
        models = self.model_filter if self.model_filter else all_models
        scenarios_list = self.scenario_filter if self.scenario_filter else all_scenarios

        # Get available variables and regions to intersect with our desired lists
        available_vars = set(conn.variables())
        available_regions = set(conn.regions())
        vars_to_fetch = [v for v in self.variable_filter if v in available_vars]
        regions_to_fetch = [r for r in self.region_filter if r in available_regions]

        if not vars_to_fetch:
            # Fallback: take first 10 variables that look relevant
            vars_to_fetch = [v for v in available_vars
                            if any(k in v for k in ["Price|Carbon", "Emissions|CO2", "GDP", "Primary Energy", "Temperature"])][:10]

        if not regions_to_fetch:
            regions_to_fetch = ["World"] if "World" in available_regions else list(available_regions)[:5]

        logger.info(f"Fetching {len(models)} models, {len(scenarios_list)} scenarios, "
                    f"{len(vars_to_fetch)} vars, {len(regions_to_fetch)} regions")

        scenarios_out = []
        trajectories_out = []
        processed = set()

        for model in models:
            for scenario in scenarios_list:
                key = f"{model}|{scenario}"
                if key in processed:
                    continue
                processed.add(key)

                try:
                    df = conn.query(
                        model=model,
                        scenario=scenario,
                        variable=vars_to_fetch,
                        region=regions_to_fetch,
                    )
                    if df is None or len(df.data) == 0:
                        continue
                except Exception as e:
                    logger.warning(f"Failed to fetch {key}: {e}")
                    continue

                sc_id = str(uuid.uuid4())
                data = df.data
                sc_regions = data["region"].unique().tolist()
                sc_variables = data["variable"].unique().tolist()
                years = sorted(data["year"].unique().tolist())

                sc_name = scenario
                category = self.category_map.get(scenario, "")
                temp_target = self.temperature_map.get(scenario)
                cn_year = self.carbon_neutral_map.get(scenario)

                scenarios_out.append({
                    "id": sc_id,
                    "external_id": f"{model}|{scenario}",
                    "name": f"{scenario}",
                    "display_name": f"{scenario} [{model}]",
                    "category": category,
                    "description": f"{scenario} scenario from {model}",
                    "temperature_target": temp_target,
                    "carbon_neutral_year": cn_year,
                    "model": model,
                    "version": self.iiasa_database,
                    "tags": [category.lower()] if category else [],
                    "time_horizon_start": min(years) if years else None,
                    "time_horizon_end": max(years) if years else None,
                    "regions": sc_regions,
                    "variables": sc_variables,
                })

                # Build trajectories
                for var in sc_variables:
                    var_data = data[data["variable"] == var]
                    unit = var_data["unit"].iloc[0] if len(var_data) > 0 else ""
                    for region in var_data["region"].unique():
                        region_data = var_data[var_data["region"] == region].sort_values("year")
                        ts = _build_timeseries(region_data["year"].tolist(), region_data["value"].tolist())
                        if ts:
                            trajectories_out.append({
                                "scenario_id": sc_id,
                                "variable_name": var,
                                "variable_code": var,
                                "unit": unit,
                                "region": region,
                                "sector": _infer_sector(var),
                                "time_series": ts,
                                "data_quality_score": self.data_quality,
                                "interpolation_method": "none",
                                "metadata_info": {"model": model, "source_db": self.iiasa_database},
                            })

        logger.info(f"Fetched {len(scenarios_out)} scenarios, {len(trajectories_out)} trajectories from {self.iiasa_database}")
        return {"scenarios": scenarios_out, "trajectories": trajectories_out}


def _infer_sector(variable_name: str) -> Optional[str]:
    """Infer sector from variable name."""
    vl = variable_name.lower()
    if "electricity" in vl or "power" in vl:
        return "Power"
    if "transport" in vl:
        return "Transport"
    if "industry" in vl or "industrial" in vl:
        return "Industry"
    if "building" in vl or "residential" in vl:
        return "Buildings"
    if "agriculture" in vl or "afolu" in vl or "land" in vl:
        return "AFOLU"
    return None


# ============================================================================
# TIER 1 FETCHERS — REAL DATA
# ============================================================================

class NGFSFetcher(IIASAFetcher):
    """Fetches REAL NGFS Phase 5 data from IIASA."""
    source_short_name = "ngfs"
    iiasa_database = "ngfs_phase_5"
    model_filter = [
        "REMIND-MAgPIE 3.3-4.8",
        "GCAM 6.0 NGFS",
        "MESSAGEix-GLOBIOM 2.0-M-R12-NGFS",
    ]
    scenario_filter = [
        "Net Zero 2050",
        "Below 2°C",
        "Delayed transition",
        "Current Policies",
        "Nationally Determined Contributions (NDCs)",
        "Fragmented World",
        "Low demand",
    ]
    category_map = NGFS_CATEGORY_MAP
    temperature_map = NGFS_TEMPERATURE_MAP
    carbon_neutral_map = NGFS_CARBON_NEUTRAL
    data_quality = 5


class IPCCAR6Fetcher(IIASAFetcher):
    """Fetches REAL IPCC AR6 scenario data from IIASA."""
    source_short_name = "ipcc"
    iiasa_database = "ar6-public"
    model_filter = [
        "REMIND-MAgPIE 2.1-4.2",
        "MESSAGEix-GLOBIOM 1.1-M-R12",
        "IMAGE 3.0.1",
        "GCAM 5.3",
        "WITCH 5.0",
    ]
    scenario_filter = None  # Take all scenarios for these models
    category_map = {}
    temperature_map = {}
    carbon_neutral_map = {}
    data_quality = 5

    def fetch(self) -> Dict[str, Any]:
        # AR6 has thousands of scenarios; limit to 15 most relevant per model
        import pyam
        import warnings
        warnings.filterwarnings("ignore")

        logger.info("Connecting to IIASA AR6 public database")
        conn = pyam.iiasa.Connection(self.iiasa_database)
        props = conn.properties()

        available_vars = set(conn.variables())
        vars_to_fetch = [v for v in IIASA_KEY_VARIABLES if v in available_vars]
        if not vars_to_fetch:
            vars_to_fetch = [v for v in available_vars
                            if any(k in v for k in ["Emissions|CO2", "Price|Carbon", "Primary Energy"])][:8]

        available_regions = set(conn.regions())
        regions_to_fetch = [r for r in ["World"] if r in available_regions]

        scenarios_out = []
        trajectories_out = []

        for model in (self.model_filter or []):
            model_props = props.loc[props.index.get_level_values("model") == model]
            model_scenarios = model_props.index.get_level_values("scenario").unique().tolist()[:10]

            for scenario in model_scenarios:
                try:
                    df = conn.query(model=model, scenario=scenario, variable=vars_to_fetch, region=regions_to_fetch)
                    if df is None or len(df.data) == 0:
                        continue
                except Exception:
                    continue

                sc_id = str(uuid.uuid4())
                data = df.data
                years = sorted(data["year"].unique().tolist())
                sc_variables = data["variable"].unique().tolist()

                scenarios_out.append({
                    "id": sc_id,
                    "external_id": f"{model}|{scenario}",
                    "name": scenario,
                    "display_name": f"{scenario} [{model}]",
                    "category": "IPCC AR6",
                    "description": f"IPCC AR6 scenario: {scenario} from {model}",
                    "temperature_target": None,
                    "model": model,
                    "version": "AR6",
                    "tags": ["ipcc", "ar6"],
                    "time_horizon_start": min(years) if years else None,
                    "time_horizon_end": max(years) if years else None,
                    "regions": data["region"].unique().tolist(),
                    "variables": sc_variables,
                })

                for var in sc_variables:
                    var_data = data[data["variable"] == var]
                    unit = var_data["unit"].iloc[0] if len(var_data) > 0 else ""
                    for region in var_data["region"].unique():
                        rd = var_data[var_data["region"] == region].sort_values("year")
                        ts = _build_timeseries(rd["year"].tolist(), rd["value"].tolist())
                        if ts:
                            trajectories_out.append({
                                "scenario_id": sc_id,
                                "variable_name": var,
                                "variable_code": var,
                                "unit": unit,
                                "region": region,
                                "sector": _infer_sector(var),
                                "time_series": ts,
                                "data_quality_score": 5,
                                "metadata_info": {"model": model, "source_db": "ar6-public"},
                            })

        logger.info(f"AR6: {len(scenarios_out)} scenarios, {len(trajectories_out)} trajectories")
        return {"scenarios": scenarios_out, "trajectories": trajectories_out}


class IAMCFetcher(IIASAFetcher):
    """Fetches REAL data from IAMC 1.5°C database (REMIND, GCAM, MESSAGEix, IMAGE, WITCH)."""
    source_short_name = "iamc15"
    iiasa_database = "iamc15"
    model_filter = None  # All models
    scenario_filter = None
    data_quality = 4

    def fetch(self) -> Dict[str, Any]:
        import pyam
        import warnings
        warnings.filterwarnings("ignore")

        logger.info("Connecting to IAMC 1.5°C database")
        conn = pyam.iiasa.Connection(self.iiasa_database)
        props = conn.properties()

        available_vars = set(conn.variables())
        vars_to_fetch = [v for v in IIASA_KEY_VARIABLES if v in available_vars]
        if not vars_to_fetch:
            vars_to_fetch = [v for v in available_vars
                            if any(k in v for k in ["Emissions|CO2", "Price|Carbon", "Primary Energy"])][:8]

        available_regions = set(conn.regions())
        regions_to_fetch = [r for r in ["World"] if r in available_regions]

        scenarios_out = []
        trajectories_out = []

        # Take top 20 scenario entries
        all_entries = list(props.index)[:20]

        for model, scenario in all_entries:
            try:
                df = conn.query(model=model, scenario=scenario, variable=vars_to_fetch, region=regions_to_fetch)
                if df is None or len(df.data) == 0:
                    continue
            except Exception:
                continue

            sc_id = str(uuid.uuid4())
            data = df.data
            years = sorted(data["year"].unique().tolist())
            sc_variables = data["variable"].unique().tolist()

            scenarios_out.append({
                "id": sc_id,
                "external_id": f"{model}|{scenario}",
                "name": scenario,
                "display_name": f"{scenario} [{model}]",
                "category": "IAM 1.5C Pathways",
                "description": f"IAMC 1.5°C scenario: {scenario} from {model}",
                "temperature_target": 1.5,
                "model": model,
                "version": "SR1.5",
                "tags": ["iamc", "1.5c"],
                "time_horizon_start": min(years) if years else None,
                "time_horizon_end": max(years) if years else None,
                "regions": data["region"].unique().tolist(),
                "variables": sc_variables,
            })

            for var in sc_variables:
                var_data = data[data["variable"] == var]
                unit = var_data["unit"].iloc[0] if len(var_data) > 0 else ""
                for region in var_data["region"].unique():
                    rd = var_data[var_data["region"] == region].sort_values("year")
                    ts = _build_timeseries(rd["year"].tolist(), rd["value"].tolist())
                    if ts:
                        trajectories_out.append({
                            "scenario_id": sc_id,
                            "variable_name": var,
                            "variable_code": var,
                            "unit": unit,
                            "region": region,
                            "sector": _infer_sector(var),
                            "time_series": ts,
                            "data_quality_score": 4,
                            "metadata_info": {"model": model, "source_db": "iamc15"},
                        })

        logger.info(f"IAMC: {len(scenarios_out)} scenarios, {len(trajectories_out)} trajectories")
        return {"scenarios": scenarios_out, "trajectories": trajectories_out}


# ============================================================================
# TIER 1 SYNTHETIC FETCHERS (sources without public APIs)
# ============================================================================

class _SyntheticFetcher(BaseFetcher):
    """Base for synthetic data fetchers."""
    _scenarios: List[dict] = []
    _variables: List[tuple] = []
    _regions: List[str] = ["World"]
    _years: List[int] = list(range(2022, 2055, 3))

    def _gen_val(self, sc, var_name, region, year):
        import math
        seed = hash(f"{sc['external_id']}_{var_name}_{region}") % 1000
        base = (seed / 100.0) + 1
        temp = sc.get("temperature_target", 2.0) or 2.0
        t = (year - self._years[0]) / max(1, self._years[-1] - self._years[0])
        rfactor = {"World": 1.0, "Advanced Economies": 0.4, "Emerging Markets": 0.6,
                   "OECD": 0.45, "Non-OECD": 0.55, "EU": 0.18, "USA": 0.22,
                   "China": 0.3, "India": 0.08, "Japan": 0.05,
                   "Africa": 0.04, "Middle East": 0.06, "Southeast Asia": 0.07}.get(region, 1.0)
        vl = var_name.lower()
        if "carbon" in vl and "price" in vl:
            val = base * 30 * (1 + t * (4.0 - temp))
        elif "co2" in vl and "emission" in vl:
            val = base * 40 * max(0.05, 1 - t * (3.5 - temp) * 0.5)
        elif "temperature" in vl:
            val = 1.1 + temp * t * 0.8
        elif "gdp" in vl:
            val = base * 80000 * (1 + t * 0.3 * (1 - (temp - 1.5) * 0.1))
        elif "coal" in vl:
            val = base * 160 * max(0.01, 1 - t * (3.5 - temp) * 0.6)
        elif "oil" in vl:
            val = base * 190 * max(0.2, 1 - t * (2.5 - temp) * 0.3)
        elif "gas" in vl:
            val = base * 140 * max(0.2, 1 - t * (2.5 - temp) * 0.25)
        elif "renewable" in vl or "solar" in vl:
            val = base * 80 * (1 + t * (3.5 - temp) * 1.5)
        elif "wind" in vl:
            val = base * 60 * (1 + t * (3.5 - temp) * 1.3)
        elif "share" in vl:
            val = 28 + (90 - 28) * t * (3.0 - temp) * 0.7
        elif "investment" in vl:
            val = base * 400 * (1 + t * (3.0 - temp) * 1.5)
        elif "sea level" in vl:
            val = 0.2 + temp * t * 0.15
        elif "radiative" in vl:
            val = 2.6 + temp * t * 0.6
        elif "capacity" in vl:
            val = base * 1200 * (1 + t * (3.5 - temp) * 2)
        else:
            val = base * 100 * (1 + t * 0.2)
        return round(val * rfactor, 4)

    def fetch(self) -> Dict[str, Any]:
        scenarios = []
        trajectories = []
        for sc in self._scenarios:
            sc_id = str(uuid.uuid4())
            sc_out = {**sc, "id": sc_id, "regions": self._regions,
                      "variables": [v[0] for v in self._variables],
                      "time_horizon_start": self._years[0],
                      "time_horizon_end": self._years[-1]}
            scenarios.append(sc_out)
            for var_name, unit in self._variables:
                for region in self._regions:
                    ts = {}
                    for y in self._years:
                        ts[str(y)] = self._gen_val(sc, var_name, region, y)
                    trajectories.append({
                        "scenario_id": sc_id,
                        "variable_name": var_name,
                        "variable_code": var_name,
                        "unit": unit,
                        "region": region,
                        "sector": _infer_sector(var_name),
                        "time_series": ts,
                        "data_quality_score": 3,
                        "interpolation_method": "synthetic",
                        "metadata_info": {"source": self.source_short_name, "data_type": "synthetic"},
                    })
        return {"scenarios": scenarios, "trajectories": trajectories}


class IEAFetcher(_SyntheticFetcher):
    source_short_name = "iea"
    _scenarios = [
        {"external_id": "iea_nze", "name": "Net Zero Emissions by 2050", "display_name": "IEA NZE 2050",
         "category": "NZE", "description": "IEA pathway achieving global net-zero by 2050.",
         "temperature_target": 1.5, "carbon_neutral_year": 2050, "model": "IEA WEO 2024", "version": "WEO 2024",
         "tags": ["nze", "1.5C"]},
        {"external_id": "iea_aps", "name": "Announced Pledges Scenario", "display_name": "IEA APS",
         "category": "APS", "description": "Assumes all announced national pledges are met.",
         "temperature_target": 1.7, "model": "IEA WEO 2024", "version": "WEO 2024", "tags": ["aps"]},
        {"external_id": "iea_steps", "name": "Stated Policies Scenario", "display_name": "IEA STEPS",
         "category": "STEPS", "description": "Reflects current policy settings only.",
         "temperature_target": 2.5, "model": "IEA WEO 2024", "version": "WEO 2024", "tags": ["steps"]},
    ]
    _variables = [
        ("Primary Energy|Total", "EJ"), ("Primary Energy|Coal", "EJ"), ("Primary Energy|Oil", "EJ"),
        ("Primary Energy|Gas", "EJ"), ("Primary Energy|Renewables", "EJ"),
        ("Electricity Generation|Solar", "TWh"), ("Electricity Generation|Wind", "TWh"),
        ("Emissions|CO2|Energy", "Gt CO2"),
    ]
    _regions = ["World", "Advanced Economies", "Emerging Markets"]


class IRENAFetcher(_SyntheticFetcher):
    source_short_name = "irena"
    _scenarios = [
        {"external_id": "irena_15c", "name": "1.5C Pathway", "display_name": "IRENA 1.5C",
         "category": "Energy Transition", "description": "IRENA pathway for limiting warming to 1.5C.",
         "temperature_target": 1.5, "carbon_neutral_year": 2050, "model": "IRENA WETO 2023", "version": "WETO 2023",
         "tags": ["1.5C", "renewables"]},
        {"external_id": "irena_pes", "name": "Planned Energy Scenario", "display_name": "IRENA PES",
         "category": "Baseline", "description": "Based on current government plans.",
         "temperature_target": 2.6, "model": "IRENA WETO 2023", "version": "WETO 2023", "tags": ["baseline"]},
    ]
    _variables = [
        ("Renewable Energy Share", "%"), ("Installed Capacity|Solar PV", "GW"),
        ("Installed Capacity|Wind", "GW"), ("Investment|Renewables", "billion USD/yr"),
        ("Emissions|CO2|Energy", "Gt CO2"),
    ]


# ============================================================================
# TIER 2 — MODEL FRAMEWORKS (IAM models from IAMC already covered by IAMCFetcher above;
# these are additional synthetic variants)
# ============================================================================

class REMINDFetcher(_SyntheticFetcher):
    source_short_name = "remind"
    _scenarios = [
        {"external_id": "remind_ssp1_19", "name": "SSP1-1.9 (REMIND)", "display_name": "REMIND SSP1-1.9",
         "category": "Low Emissions", "description": "PIK REMIND SSP1-1.9 pathway.",
         "temperature_target": 1.5, "carbon_neutral_year": 2055, "model": "REMIND-MAgPIE 3.3", "version": "SSP",
         "tags": ["ssp1", "1.5c"]},
        {"external_id": "remind_ssp2_45", "name": "SSP2-4.5 (REMIND)", "display_name": "REMIND SSP2-4.5",
         "category": "Intermediate", "description": "PIK REMIND middle-of-the-road.",
         "temperature_target": 2.7, "model": "REMIND-MAgPIE 3.3", "version": "SSP", "tags": ["ssp2"]},
    ]
    _variables = [
        ("Price|Carbon", "USD/tCO2"), ("Emissions|CO2", "Gt CO2/yr"), ("GDP|PPP", "billion USD"),
        ("Primary Energy", "EJ/yr"), ("Primary Energy|Coal", "EJ/yr"), ("Primary Energy|Renewables", "EJ/yr"),
    ]


class GCAMFetcher(_SyntheticFetcher):
    source_short_name = "gcam"
    _scenarios = [
        {"external_id": "gcam_ref", "name": "Reference (GCAM)", "display_name": "GCAM Reference",
         "category": "Baseline", "description": "GCAM reference scenario.", "temperature_target": 3.0,
         "model": "GCAM 6.0", "version": "6.0", "tags": ["baseline"]},
        {"external_id": "gcam_2c", "name": "2C Target (GCAM)", "display_name": "GCAM 2C",
         "category": "Policy", "description": "GCAM 2°C policy scenario.",
         "temperature_target": 2.0, "carbon_neutral_year": 2070, "model": "GCAM 6.0", "version": "6.0",
         "tags": ["2c", "policy"]},
    ]
    _variables = [
        ("Price|Carbon", "USD/tCO2"), ("Emissions|CO2", "Gt CO2/yr"), ("Primary Energy", "EJ/yr"),
        ("Primary Energy|Coal", "EJ/yr"), ("Primary Energy|Gas", "EJ/yr"),
    ]


class MESSAGEixFetcher(_SyntheticFetcher):
    source_short_name = "messageix"
    _scenarios = [
        {"external_id": "msg_ssp2_26", "name": "SSP2-2.6 (MESSAGEix)", "display_name": "MESSAGEix SSP2-2.6",
         "category": "Low Emissions", "description": "IIASA MESSAGEix SSP2-2.6.",
         "temperature_target": 1.8, "model": "MESSAGEix-GLOBIOM 2.0", "version": "SSP", "tags": ["ssp2"]},
    ]
    _variables = [
        ("Price|Carbon", "USD/tCO2"), ("Emissions|CO2", "Gt CO2/yr"), ("GDP|PPP", "billion USD"),
        ("Primary Energy", "EJ/yr"),
    ]


class IMAGEFetcher(_SyntheticFetcher):
    source_short_name = "image"
    _scenarios = [
        {"external_id": "image_ssp1_26", "name": "SSP1-2.6 (IMAGE)", "display_name": "IMAGE SSP1-2.6",
         "category": "Low Emissions", "description": "PBL IMAGE SSP1-2.6.",
         "temperature_target": 1.8, "model": "IMAGE 3.2", "version": "SSP", "tags": ["ssp1"]},
    ]
    _variables = [
        ("Emissions|CO2", "Gt CO2/yr"), ("Primary Energy", "EJ/yr"), ("Primary Energy|Renewables", "EJ/yr"),
    ]


class WITCHFetcher(_SyntheticFetcher):
    source_short_name = "witch"
    _scenarios = [
        {"external_id": "witch_15c", "name": "1.5C (WITCH)", "display_name": "WITCH 1.5C",
         "category": "Low Emissions", "description": "FEEM/CMCC WITCH 1.5C pathway.",
         "temperature_target": 1.5, "model": "WITCH-GLOBIOM 4.2", "version": "4.2", "tags": ["1.5c"]},
    ]
    _variables = [
        ("Price|Carbon", "USD/tCO2"), ("Emissions|CO2", "Gt CO2/yr"), ("GDP|PPP", "billion USD"),
    ]


class TIAMFetcher(_SyntheticFetcher):
    source_short_name = "tiam"
    _scenarios = [
        {"external_id": "tiam_2c", "name": "2C Scenario (TIAM)", "display_name": "TIAM-ECN 2C",
         "category": "Policy", "description": "ETSAP TIAM-ECN 2°C optimization.",
         "temperature_target": 2.0, "model": "TIAM-ECN", "version": "2023", "tags": ["2c"]},
    ]
    _variables = [
        ("Primary Energy", "EJ/yr"), ("Primary Energy|Coal", "EJ/yr"),
        ("Emissions|CO2", "Gt CO2/yr"),
    ]


# ============================================================================
# TIER 3 — REGIONAL / NATIONAL
# ============================================================================

class EUReferenceScenarioFetcher(_SyntheticFetcher):
    source_short_name = "eu_ref"
    _scenarios = [
        {"external_id": "eu_ref_2023", "name": "EU Reference Scenario 2023", "display_name": "EU Ref 2023",
         "category": "Reference", "description": "European Commission Reference Scenario 2023.",
         "temperature_target": 2.0, "model": "PRIMES/GAINS", "version": "2023", "tags": ["eu", "reference"]},
        {"external_id": "eu_ff55", "name": "Fit for 55", "display_name": "EU Fit for 55",
         "category": "Policy", "description": "EU Fit for 55 package scenario.",
         "temperature_target": 1.5, "carbon_neutral_year": 2050, "model": "PRIMES/GAINS", "version": "2023",
         "tags": ["eu", "ff55"]},
    ]
    _variables = [
        ("Emissions|CO2", "Mt CO2/yr"), ("Primary Energy", "Mtoe"), ("Renewable Energy Share", "%"),
        ("Emissions|CO2|Transport", "Mt CO2/yr"), ("Emissions|CO2|Industry", "Mt CO2/yr"),
    ]
    _regions = ["EU"]


class UKCCCFetcher(_SyntheticFetcher):
    source_short_name = "uk_ccc"
    _scenarios = [
        {"external_id": "uk_6cb_balanced", "name": "Balanced Net Zero", "display_name": "UK 6CB Balanced",
         "category": "Net Zero", "description": "UK Climate Change Committee 6th Carbon Budget balanced pathway.",
         "temperature_target": 1.5, "carbon_neutral_year": 2050, "model": "CCC Model", "version": "6CB",
         "tags": ["uk", "net-zero"]},
    ]
    _variables = [
        ("Emissions|CO2", "MtCO2e/yr"), ("Emissions|CO2|Power", "MtCO2e/yr"),
        ("Emissions|CO2|Transport", "MtCO2e/yr"), ("Emissions|CO2|Buildings", "MtCO2e/yr"),
    ]
    _regions = ["United Kingdom"]


class USEIAFetcher(_SyntheticFetcher):
    source_short_name = "us_eia"
    _scenarios = [
        {"external_id": "eia_aeo_ref", "name": "AEO Reference Case", "display_name": "US AEO Reference",
         "category": "Reference", "description": "US EIA Annual Energy Outlook Reference Case.",
         "temperature_target": None, "model": "NEMS", "version": "AEO 2024", "tags": ["us", "reference"]},
        {"external_id": "eia_aeo_lowren", "name": "AEO Low Renewables Cost", "display_name": "US AEO Low Renew",
         "category": "Sensitivity", "description": "Low renewables cost sensitivity case.",
         "temperature_target": None, "model": "NEMS", "version": "AEO 2024", "tags": ["us", "renewables"]},
    ]
    _variables = [
        ("Primary Energy", "quad BTU"), ("Emissions|CO2|Energy", "MMt CO2"),
        ("Electricity Generation|Renewables", "billion kWh"), ("Price|Crude Oil", "USD/barrel"),
    ]
    _regions = ["USA"]


class ChinaFetcher(_SyntheticFetcher):
    source_short_name = "china_ndrc"
    _scenarios = [
        {"external_id": "cn_carbon_peak", "name": "China Carbon Peak 2030", "display_name": "China Peak 2030",
         "category": "Policy", "description": "China carbon peaking by 2030 pathway.",
         "temperature_target": None, "carbon_neutral_year": 2060, "model": "NDRC/IEA", "version": "2024",
         "tags": ["china", "carbon-peak"]},
    ]
    _variables = [
        ("Emissions|CO2", "Gt CO2/yr"), ("Primary Energy|Coal", "EJ/yr"),
        ("Primary Energy|Renewables", "EJ/yr"), ("Installed Capacity|Solar PV", "GW"),
    ]
    _regions = ["China"]


class JapanFetcher(_SyntheticFetcher):
    source_short_name = "japan_meti"
    _scenarios = [
        {"external_id": "jp_sep6", "name": "6th Strategic Energy Plan", "display_name": "Japan SEP 6th",
         "category": "Policy", "description": "Japan METI 6th Strategic Energy Plan.",
         "temperature_target": None, "carbon_neutral_year": 2050, "model": "METI", "version": "6th SEP",
         "tags": ["japan", "policy"]},
    ]
    _variables = [
        ("Primary Energy", "PJ"), ("Electricity Generation|Renewables", "TWh"),
        ("Emissions|CO2|Energy", "Mt CO2"),
    ]
    _regions = ["Japan"]


# ============================================================================
# TIER 4 — SECTOR-SPECIFIC
# ============================================================================

class IEASectorFetcher(_SyntheticFetcher):
    source_short_name = "iea_sectors"
    _scenarios = [
        {"external_id": "iea_nze_roadmap", "name": "Net Zero Roadmap (All Sectors)",
         "display_name": "IEA NZE Roadmap", "category": "NZE Roadmap",
         "description": "IEA Net Zero by 2050 sectoral roadmap.", "temperature_target": 1.5,
         "carbon_neutral_year": 2050, "model": "IEA NZE", "version": "2023", "tags": ["nze", "sectoral"]},
        {"external_id": "iea_steel", "name": "Iron & Steel Roadmap", "display_name": "IEA Steel Roadmap",
         "category": "Sector: Steel", "description": "IEA Iron & Steel Technology Roadmap.",
         "temperature_target": 1.5, "model": "IEA Sector", "version": "2023", "tags": ["steel", "industry"]},
        {"external_id": "iea_cement", "name": "Cement Technology Roadmap", "display_name": "IEA Cement Roadmap",
         "category": "Sector: Cement", "description": "IEA Cement Technology Roadmap.",
         "temperature_target": 1.5, "model": "IEA Sector", "version": "2023", "tags": ["cement", "industry"]},
        {"external_id": "iea_aviation", "name": "Aviation Decarbonization", "display_name": "IEA Aviation",
         "category": "Sector: Aviation", "description": "IEA aviation fuel and decarbonization pathway.",
         "temperature_target": 1.5, "model": "IEA Sector", "version": "2023", "tags": ["aviation", "transport"]},
        {"external_id": "iea_shipping", "name": "Shipping Decarbonization", "display_name": "IEA Shipping",
         "category": "Sector: Shipping", "description": "IEA shipping decarbonization pathway.",
         "temperature_target": 1.5, "model": "IEA Sector", "version": "2023", "tags": ["shipping", "transport"]},
    ]
    _variables = [
        ("Emissions|CO2|Industry", "Mt CO2"), ("Emissions|CO2|Transport", "Mt CO2"),
        ("Emissions|CO2|Power", "Mt CO2"), ("Energy Intensity", "MJ/USD"),
    ]


# ============================================================================
# TIER 5 — CARBON PRICING
# ============================================================================

class CarbonPriceFetcher(_SyntheticFetcher):
    source_short_name = "carbon_price"
    _scenarios = [
        {"external_id": "wb_high_price", "name": "High Carbon Price Pathway",
         "display_name": "WB High Carbon Price", "category": "Carbon Pricing",
         "description": "World Bank high carbon pricing scenario.",
         "temperature_target": 1.5, "model": "World Bank CPD", "version": "2024",
         "tags": ["carbon-price", "high"]},
        {"external_id": "wb_current_trend", "name": "Current Carbon Price Trends",
         "display_name": "WB Current Trend", "category": "Carbon Pricing",
         "description": "Extrapolation of current carbon pricing trends.",
         "temperature_target": 2.5, "model": "World Bank CPD", "version": "2024",
         "tags": ["carbon-price", "current"]},
        {"external_id": "icap_ets", "name": "ETS Price Trajectories",
         "display_name": "ICAP ETS Prices", "category": "Carbon Pricing",
         "description": "ICAP ETS price projections across major carbon markets.",
         "temperature_target": None, "model": "ICAP", "version": "2024", "tags": ["ets", "carbon-price"]},
    ]
    _variables = [
        ("Price|Carbon|EU ETS", "EUR/tCO2"), ("Price|Carbon|Global Average", "USD/tCO2"),
        ("Price|Carbon|China ETS", "CNY/tCO2"), ("Price|Carbon|UK ETS", "GBP/tCO2"),
    ]
    _regions = ["World", "EU", "China", "United Kingdom", "USA"]


# ============================================================================
# TIER 6 — PHYSICAL RISK
# ============================================================================

class PhysicalRiskFetcher(_SyntheticFetcher):
    source_short_name = "physical_risk"
    _scenarios = [
        {"external_id": "cmip6_ssp126", "name": "CMIP6 SSP1-2.6", "display_name": "CMIP6 SSP1-2.6",
         "category": "Physical Risk", "description": "CMIP6 low emissions physical risk projection.",
         "temperature_target": 1.8, "model": "CMIP6 Multi-Model", "version": "CMIP6",
         "tags": ["physical-risk", "ssp1"]},
        {"external_id": "cmip6_ssp245", "name": "CMIP6 SSP2-4.5", "display_name": "CMIP6 SSP2-4.5",
         "category": "Physical Risk", "description": "CMIP6 intermediate emissions projection.",
         "temperature_target": 2.7, "model": "CMIP6 Multi-Model", "version": "CMIP6",
         "tags": ["physical-risk", "ssp2"]},
        {"external_id": "cmip6_ssp585", "name": "CMIP6 SSP5-8.5", "display_name": "CMIP6 SSP5-8.5",
         "category": "Physical Risk", "description": "CMIP6 very high emissions projection.",
         "temperature_target": 4.4, "model": "CMIP6 Multi-Model", "version": "CMIP6",
         "tags": ["physical-risk", "ssp5"]},
        {"external_id": "isimip_flood", "name": "ISIMIP Flood Risk", "display_name": "ISIMIP Flood",
         "category": "Physical Risk", "description": "ISIMIP flood risk projections.",
         "temperature_target": None, "model": "ISIMIP3b", "version": "ISIMIP3b", "tags": ["physical-risk", "flood"]},
    ]
    _variables = [
        ("Temperature|Global Mean", "C above pre-industrial"),
        ("Sea Level Rise|Global Mean", "m"),
        ("Precipitation Change", "% change"),
        ("Extreme Heat Days", "days/yr above 35C"),
    ]
    _regions = ["World", "EU", "USA", "China", "India", "Africa", "Southeast Asia"]
    _years = list(range(2020, 2105, 5))


# ============================================================================
# REGISTRY
# ============================================================================

FETCHER_REGISTRY: Dict[str, type] = {
    # Tier 1 — Real data
    "ngfs": NGFSFetcher,
    "ipcc": IPCCAR6Fetcher,
    "iamc15": IAMCFetcher,
    # Tier 1 — Synthetic
    "iea": IEAFetcher,
    "irena": IRENAFetcher,
    # Tier 2 — Model frameworks (synthetic)
    "remind": REMINDFetcher,
    "gcam": GCAMFetcher,
    "messageix": MESSAGEixFetcher,
    "image": IMAGEFetcher,
    "witch": WITCHFetcher,
    "tiam": TIAMFetcher,
    # Tier 3 — Regional (synthetic)
    "eu_ref": EUReferenceScenarioFetcher,
    "uk_ccc": UKCCCFetcher,
    "us_eia": USEIAFetcher,
    "china_ndrc": ChinaFetcher,
    "japan_meti": JapanFetcher,
    # Tier 4 — Sector-specific (synthetic)
    "iea_sectors": IEASectorFetcher,
    # Tier 5 — Carbon pricing (synthetic)
    "carbon_price": CarbonPriceFetcher,
    # Tier 6 — Physical risk (synthetic)
    "physical_risk": PhysicalRiskFetcher,
}
