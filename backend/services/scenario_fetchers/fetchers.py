"""
Scenario data fetcher base class and Tier 1 fetcher implementations.

Each fetcher produces a standardized list of scenarios + trajectories
that can be persisted via DataHubService.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any
import uuid


class BaseFetcher(ABC):
    """Base class for all scenario data fetchers."""

    source_short_name: str = ""

    @abstractmethod
    def fetch(self) -> Dict[str, Any]:
        """
        Fetch scenarios and trajectories from the source.
        Returns: {"scenarios": [...], "trajectories": [...]}
        """
        ...


class NGFSFetcher(BaseFetcher):
    """Fetcher for NGFS Phase V scenarios (synthetic data for now)."""

    source_short_name = "ngfs"

    SCENARIOS = [
        {
            "external_id": "ngfs_net_zero_2050",
            "name": "Net Zero 2050",
            "category": "Orderly",
            "description": "Global net zero CO2 emissions around 2050, limiting warming to 1.5C.",
            "temperature_target": 1.5,
            "model": "REMIND-MAgPIE 3.0",
            "version": "Phase V",
            "tags": ["orderly", "1.5C", "net-zero"],
        },
        {
            "external_id": "ngfs_below_2c",
            "name": "Below 2C",
            "category": "Orderly",
            "description": "Gradually increasing climate policies to limit warming to below 2C.",
            "temperature_target": 1.8,
            "model": "REMIND-MAgPIE 3.0",
            "version": "Phase V",
            "tags": ["orderly", "2C"],
        },
        {
            "external_id": "ngfs_delayed_transition",
            "name": "Delayed Transition",
            "category": "Disorderly",
            "description": "Annual emissions do not decrease until 2030. Strong policies needed afterward.",
            "temperature_target": 1.8,
            "model": "REMIND-MAgPIE 3.0",
            "version": "Phase V",
            "tags": ["disorderly", "delayed"],
        },
        {
            "external_id": "ngfs_divergent_net_zero",
            "name": "Divergent Net Zero",
            "category": "Disorderly",
            "description": "Reach net zero around 2050 but with higher costs due to divergent policies.",
            "temperature_target": 1.5,
            "model": "REMIND-MAgPIE 3.0",
            "version": "Phase V",
            "tags": ["disorderly", "divergent"],
        },
        {
            "external_id": "ngfs_ndc",
            "name": "Nationally Determined Contributions (NDCs)",
            "category": "Hot House World",
            "description": "Policies as pledged through NDCs, insufficient to limit warming to 2C.",
            "temperature_target": 2.5,
            "model": "REMIND-MAgPIE 3.0",
            "version": "Phase V",
            "tags": ["hot-house", "ndc"],
        },
        {
            "external_id": "ngfs_current_policies",
            "name": "Current Policies",
            "category": "Hot House World",
            "description": "Only currently implemented policies, leading to over 3C warming by 2100.",
            "temperature_target": 3.2,
            "model": "REMIND-MAgPIE 3.0",
            "version": "Phase V",
            "tags": ["hot-house", "current-policies"],
        },
    ]

    VARIABLES = [
        ("Price|Carbon", "USD/tCO2"),
        ("Emissions|CO2", "Gt CO2/yr"),
        ("Temperature|Global Mean", "C above pre-industrial"),
        ("GDP|PPP", "billion USD 2010"),
        ("Primary Energy|Coal", "EJ/yr"),
        ("Primary Energy|Gas", "EJ/yr"),
        ("Primary Energy|Solar", "EJ/yr"),
        ("Primary Energy|Wind", "EJ/yr"),
    ]

    REGIONS = ["World", "United States", "European Union", "China", "India"]

    YEARS = list(range(2025, 2105, 5))

    def _generate_trajectory(self, scenario: dict, var_name: str, region: str) -> dict:
        """Generate synthetic trajectory values."""
        import math
        temp = scenario["temperature_target"]
        seed_val = hash(f"{scenario['external_id']}_{var_name}_{region}") % 1000
        base = (seed_val / 100.0) + 1

        ts = {}
        for y in self.YEARS:
            t = (y - 2025) / 80.0
            if "Carbon" in var_name:
                val = base * 30 * (1 + t * (4.0 - temp))
            elif "CO2" in var_name:
                val = base * 40 * max(0.05, 1 - t * (3.5 - temp) * 0.5)
            elif "Temperature" in var_name:
                val = 1.1 + temp * t * 0.8
            elif "GDP" in var_name:
                val = base * 80000 * (1 + t * 0.3 * (1 - (temp - 1.5) * 0.1))
            elif "Coal" in var_name:
                val = base * 160 * max(0.01, 1 - t * (3.5 - temp) * 0.6)
            elif "Gas" in var_name:
                val = base * 140 * max(0.1, 1 - t * (3.0 - temp) * 0.3)
            elif "Solar" in var_name:
                val = base * 5 * (1 + t * (4.0 - temp) * 2)
            elif "Wind" in var_name:
                val = base * 6 * (1 + t * (4.0 - temp) * 1.5)
            else:
                val = base * (1 + t)
            # regional factor
            rfactor = {"World": 1.0, "United States": 0.22, "European Union": 0.18,
                       "China": 0.3, "India": 0.08}.get(region, 1.0)
            ts[str(y)] = round(val * rfactor, 4)
        return ts

    def fetch(self) -> Dict[str, Any]:
        scenarios = []
        trajectories = []
        for sc in self.SCENARIOS:
            sc_id = str(uuid.uuid4())
            scenarios.append({
                "id": sc_id,
                "external_id": sc["external_id"],
                "name": sc["name"],
                "category": sc["category"],
                "description": sc["description"],
                "temperature_target": sc["temperature_target"],
                "model": sc["model"],
                "version": sc["version"],
                "tags": sc["tags"],
                "time_horizon_start": 2025,
                "time_horizon_end": 2100,
                "regions": self.REGIONS,
                "variables": [v[0] for v in self.VARIABLES],
            })
            for var_name, unit in self.VARIABLES:
                for region in self.REGIONS:
                    ts = self._generate_trajectory(sc, var_name, region)
                    trajectories.append({
                        "scenario_id": sc_id,
                        "variable_name": var_name,
                        "unit": unit,
                        "region": region,
                        "time_series": ts,
                        "metadata": {"model": sc["model"]},
                    })
        return {"scenarios": scenarios, "trajectories": trajectories}


class IPCCFetcher(BaseFetcher):
    """Fetcher for IPCC AR6 representative pathways (synthetic)."""

    source_short_name = "ipcc"

    SCENARIOS = [
        {"external_id": "ipcc_ssp119", "name": "SSP1-1.9", "category": "Very Low GHG",
         "description": "Sustainability pathway, very low greenhouse-gas emissions.", "temperature_target": 1.4,
         "tags": ["ssp1", "1.5C"]},
        {"external_id": "ipcc_ssp126", "name": "SSP1-2.6", "category": "Low GHG",
         "description": "Sustainability pathway, CO2 emissions declining to net zero around 2075.", "temperature_target": 1.8,
         "tags": ["ssp1", "2C"]},
        {"external_id": "ipcc_ssp245", "name": "SSP2-4.5", "category": "Intermediate GHG",
         "description": "Middle-of-the-road pathway, emissions around current levels until 2050.", "temperature_target": 2.7,
         "tags": ["ssp2", "middle"]},
        {"external_id": "ipcc_ssp370", "name": "SSP3-7.0", "category": "High GHG",
         "description": "Regional rivalry pathway, emissions rise substantially.", "temperature_target": 3.6,
         "tags": ["ssp3", "high"]},
        {"external_id": "ipcc_ssp585", "name": "SSP5-8.5", "category": "Very High GHG",
         "description": "Fossil-fueled development, highest emissions.", "temperature_target": 4.4,
         "tags": ["ssp5", "very-high"]},
    ]

    VARIABLES = [
        ("Emissions|CO2", "Gt CO2/yr"),
        ("Temperature|Global Mean", "C"),
        ("Sea Level Rise", "m"),
        ("Radiative Forcing", "W/m2"),
    ]

    REGIONS = ["World"]
    YEARS = list(range(2020, 2105, 5))

    def fetch(self) -> Dict[str, Any]:
        scenarios = []
        trajectories = []
        for sc in self.SCENARIOS:
            sc_id = str(uuid.uuid4())
            scenarios.append({
                "id": sc_id,
                "external_id": sc["external_id"],
                "name": sc["name"],
                "category": sc["category"],
                "description": sc["description"],
                "temperature_target": sc["temperature_target"],
                "model": "IPCC AR6 WGIII",
                "version": "AR6",
                "tags": sc["tags"],
                "time_horizon_start": 2020,
                "time_horizon_end": 2100,
                "regions": self.REGIONS,
                "variables": [v[0] for v in self.VARIABLES],
            })
            temp = sc["temperature_target"]
            for var_name, unit in self.VARIABLES:
                for region in self.REGIONS:
                    ts = {}
                    for y in self.YEARS:
                        t = (y - 2020) / 80.0
                        if "CO2" in var_name:
                            val = 40 * max(0.01, 1 - t * (4.5 - temp) * 0.4)
                        elif "Temperature" in var_name:
                            val = 1.1 + temp * t * 0.85
                        elif "Sea Level" in var_name:
                            val = 0.2 + temp * t * 0.15
                        else:
                            val = 2.6 + temp * t * 0.6
                        ts[str(y)] = round(val, 4)
                    trajectories.append({
                        "scenario_id": sc_id,
                        "variable_name": var_name,
                        "unit": unit,
                        "region": region,
                        "time_series": ts,
                        "metadata": {"model": "IPCC AR6 WGIII"},
                    })
        return {"scenarios": scenarios, "trajectories": trajectories}


class IEAFetcher(BaseFetcher):
    """Fetcher for IEA World Energy Outlook scenarios (synthetic)."""

    source_short_name = "iea"

    SCENARIOS = [
        {"external_id": "iea_nze", "name": "Net Zero Emissions by 2050",
         "category": "NZE", "description": "Aggressive pathway achieving net-zero globally by 2050.",
         "temperature_target": 1.5, "tags": ["nze", "1.5C"]},
        {"external_id": "iea_aps", "name": "Announced Pledges Scenario",
         "category": "APS", "description": "Assumes all announced pledges are met in full and on time.",
         "temperature_target": 1.7, "tags": ["aps", "pledges"]},
        {"external_id": "iea_steps", "name": "Stated Policies Scenario",
         "category": "STEPS", "description": "Reflects current policy settings and firm commitments only.",
         "temperature_target": 2.5, "tags": ["steps", "current"]},
    ]

    VARIABLES = [
        ("Primary Energy|Total", "EJ"),
        ("Primary Energy|Coal", "EJ"),
        ("Primary Energy|Oil", "EJ"),
        ("Primary Energy|Gas", "EJ"),
        ("Primary Energy|Renewables", "EJ"),
        ("Electricity Generation|Solar", "TWh"),
        ("Electricity Generation|Wind", "TWh"),
        ("Emissions|CO2|Energy", "Gt CO2"),
    ]

    REGIONS = ["World", "Advanced Economies", "Emerging Markets"]
    YEARS = list(range(2022, 2055, 3))

    def fetch(self) -> Dict[str, Any]:
        scenarios = []
        trajectories = []
        for sc in self.SCENARIOS:
            sc_id = str(uuid.uuid4())
            scenarios.append({
                "id": sc_id,
                "external_id": sc["external_id"],
                "name": sc["name"],
                "category": sc["category"],
                "description": sc["description"],
                "temperature_target": sc["temperature_target"],
                "model": "IEA WEO 2024",
                "version": "WEO 2024",
                "tags": sc["tags"],
                "time_horizon_start": 2022,
                "time_horizon_end": 2050,
                "regions": self.REGIONS,
                "variables": [v[0] for v in self.VARIABLES],
            })
            temp = sc["temperature_target"]
            for var_name, unit in self.VARIABLES:
                for region in self.REGIONS:
                    ts = {}
                    rfactor = {"World": 1.0, "Advanced Economies": 0.4, "Emerging Markets": 0.6}.get(region, 1.0)
                    for y in self.YEARS:
                        t = (y - 2022) / 28.0
                        if "Coal" in var_name:
                            val = 160 * max(0.05, 1 - t * (3.0 - temp) * 0.5) * rfactor
                        elif "Oil" in var_name:
                            val = 190 * max(0.2, 1 - t * (2.5 - temp) * 0.3) * rfactor
                        elif "Gas" in var_name:
                            val = 140 * max(0.2, 1 - t * (2.5 - temp) * 0.25) * rfactor
                        elif "Renewables" in var_name:
                            val = 80 * (1 + t * (3.5 - temp) * 1.5) * rfactor
                        elif "Solar" in var_name:
                            val = 1200 * (1 + t * (3.5 - temp) * 2) * rfactor
                        elif "Wind" in var_name:
                            val = 1800 * (1 + t * (3.5 - temp) * 1.3) * rfactor
                        elif "CO2" in var_name:
                            val = 37 * max(0.01, 1 - t * (3.5 - temp) * 0.5) * rfactor
                        else:
                            val = 600 * (1 + t * 0.1) * rfactor
                        ts[str(y)] = round(val, 4)
                    trajectories.append({
                        "scenario_id": sc_id,
                        "variable_name": var_name,
                        "unit": unit,
                        "region": region,
                        "time_series": ts,
                        "metadata": {"model": "IEA WEO 2024"},
                    })
        return {"scenarios": scenarios, "trajectories": trajectories}


class IRENAFetcher(BaseFetcher):
    """Fetcher for IRENA energy transition scenarios (synthetic)."""

    source_short_name = "irena"

    SCENARIOS = [
        {"external_id": "irena_15c", "name": "1.5C Pathway",
         "category": "Energy Transition", "description": "IRENA pathway for limiting warming to 1.5C through rapid renewables deployment.",
         "temperature_target": 1.5, "tags": ["1.5C", "renewables"]},
        {"external_id": "irena_pes", "name": "Planned Energy Scenario",
         "category": "Baseline", "description": "Based on current government plans and policies.",
         "temperature_target": 2.6, "tags": ["baseline", "planned"]},
    ]

    VARIABLES = [
        ("Renewable Energy Share", "%"),
        ("Installed Capacity|Solar PV", "GW"),
        ("Installed Capacity|Wind", "GW"),
        ("Investment|Renewables", "billion USD/yr"),
        ("Emissions|CO2|Energy", "Gt CO2"),
    ]

    REGIONS = ["World"]
    YEARS = list(range(2022, 2055, 3))

    def fetch(self) -> Dict[str, Any]:
        scenarios = []
        trajectories = []
        for sc in self.SCENARIOS:
            sc_id = str(uuid.uuid4())
            scenarios.append({
                "id": sc_id,
                "external_id": sc["external_id"],
                "name": sc["name"],
                "category": sc["category"],
                "description": sc["description"],
                "temperature_target": sc["temperature_target"],
                "model": "IRENA World Energy Transitions Outlook",
                "version": "WETO 2023",
                "tags": sc["tags"],
                "time_horizon_start": 2022,
                "time_horizon_end": 2050,
                "regions": self.REGIONS,
                "variables": [v[0] for v in self.VARIABLES],
            })
            temp = sc["temperature_target"]
            for var_name, unit in self.VARIABLES:
                for region in self.REGIONS:
                    ts = {}
                    for y in self.YEARS:
                        t = (y - 2022) / 28.0
                        if "Share" in var_name:
                            val = 28 + (90 - 28) * t * (3.0 - temp) * 0.7
                        elif "Solar" in var_name:
                            val = 1200 * (1 + t * (3.5 - temp) * 3)
                        elif "Wind" in var_name:
                            val = 900 * (1 + t * (3.5 - temp) * 2)
                        elif "Investment" in var_name:
                            val = 400 * (1 + t * (3.0 - temp) * 1.5)
                        elif "CO2" in var_name:
                            val = 37 * max(0.01, 1 - t * (3.5 - temp) * 0.5)
                        else:
                            val = 100 * (1 + t)
                        ts[str(y)] = round(val, 4)
                    trajectories.append({
                        "scenario_id": sc_id,
                        "variable_name": var_name,
                        "unit": unit,
                        "region": region,
                        "time_series": ts,
                        "metadata": {"model": "IRENA WETO 2023"},
                    })
        return {"scenarios": scenarios, "trajectories": trajectories}


# Registry
FETCHER_REGISTRY: Dict[str, type] = {
    "ngfs": NGFSFetcher,
    "ipcc": IPCCFetcher,
    "iea": IEAFetcher,
    "irena": IRENAFetcher,
}
