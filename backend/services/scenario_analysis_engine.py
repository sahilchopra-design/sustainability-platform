"""
Interactive Scenario Builder and Sensitivity Analysis Engine
Enables real-time what-if analysis, scenario comparison, and sensitivity testing
"""

from decimal import Decimal
from typing import Dict, List, Optional, Any, Tuple
from uuid import uuid4, UUID
from datetime import datetime, timezone
import copy
import os
import json

from sqlalchemy import create_engine, text
from sqlalchemy.pool import NullPool

from schemas.scenario_analysis import (
    ModificationType, ChangeType,
    ScenarioModification, ComponentImpact,
    ScenarioBuildRequest, ScenarioBuildResult,
    SensitivityVariable, SensitivityDataPoint,
    TornadoDataPoint, SpiderChartData, SpiderChartScenario,
    SensitivityAnalyzeResult,
    WhatIfChange, ChangeBreakdown, WhatIfResult,
    ScenarioComparisonRow, ScenarioComparisonResult,
    ScenarioTemplate,
)


# ============ Sample Property Data ============

# Use consistent UUIDs for sample properties
SAMPLE_PROPERTY_UUIDS = {
    "office": "00000000-0000-0000-0000-000000000001",
    "retail": "00000000-0000-0000-0000-000000000002",
    "industrial": "00000000-0000-0000-0000-000000000003",
}

def get_sample_properties() -> Dict[str, Dict]:
    """Sample properties for scenario analysis."""
    return {
        SAMPLE_PROPERTY_UUIDS["office"]: {
            "id": SAMPLE_PROPERTY_UUIDS["office"],
            "name": "Downtown Office Tower",
            "property_type": "office",
            "gross_floor_area_sf": 450000,
            "noi": Decimal("23940000"),
            "cap_rate": Decimal("0.055"),
            "market_rent_psf": Decimal("65"),
            "vacancy_rate": Decimal("0.05"),
            "expense_ratio": Decimal("0.35"),
            "rent_growth_rate": Decimal("0.025"),
            "discount_rate": Decimal("0.08"),
            "exit_cap_rate": Decimal("0.06"),
            "holding_period_years": 10,
            "current_value": Decimal("435000000"),
            "certifications": ["LEED Gold"],
            "epc_rating": "B",
        },
        SAMPLE_PROPERTY_UUIDS["retail"]: {
            "id": SAMPLE_PROPERTY_UUIDS["retail"],
            "name": "Suburban Retail Center",
            "property_type": "retail",
            "gross_floor_area_sf": 125000,
            "noi": Decimal("4860000"),
            "cap_rate": Decimal("0.065"),
            "market_rent_psf": Decimal("42"),
            "vacancy_rate": Decimal("0.08"),
            "expense_ratio": Decimal("0.28"),
            "rent_growth_rate": Decimal("0.02"),
            "discount_rate": Decimal("0.09"),
            "exit_cap_rate": Decimal("0.07"),
            "holding_period_years": 10,
            "current_value": Decimal("74770000"),
            "certifications": [],
            "epc_rating": "C",
        },
        SAMPLE_PROPERTY_UUIDS["industrial"]: {
            "id": SAMPLE_PROPERTY_UUIDS["industrial"],
            "name": "Industrial Distribution Hub",
            "property_type": "industrial",
            "gross_floor_area_sf": 800000,
            "noi": Decimal("14480000"),
            "cap_rate": Decimal("0.048"),
            "market_rent_psf": Decimal("22"),
            "vacancy_rate": Decimal("0.03"),
            "expense_ratio": Decimal("0.18"),
            "rent_growth_rate": Decimal("0.035"),
            "discount_rate": Decimal("0.075"),
            "exit_cap_rate": Decimal("0.055"),
            "holding_period_years": 10,
            "current_value": Decimal("301670000"),
            "certifications": ["BREEAM Very Good"],
            "epc_rating": "B",
        },
    }


# ============ Scenario Storage (PostgreSQL with In-Memory Fallback) ============

_db_engine = None

def _get_db_engine():
    """Get or create database engine."""
    global _db_engine
    if _db_engine is None:
        DATABASE_URL = os.environ.get("DATABASE_URL")
        if DATABASE_URL:
            try:
                _db_engine = create_engine(DATABASE_URL, poolclass=NullPool)
                with _db_engine.connect() as conn:
                    conn.execute(text("SELECT 1"))
            except Exception as e:
                print(f"Warning: Could not connect to PostgreSQL for scenarios: {e}")
                _db_engine = None
    return _db_engine


def save_scenario(scenario_id: str, scenario_data: Dict) -> None:
    """Save scenario to PostgreSQL."""
    engine = _get_db_engine()
    if not engine:
        return
    
    try:
        with engine.connect() as conn:
            # Prepare parameters as JSON
            parameters = {
                "property_id": scenario_data.get("property_id"),
                "modifications": scenario_data.get("modifications", []),
                "base_value": str(scenario_data.get("base_value", 0)),
                "modified_value": str(scenario_data.get("modified_value", 0)),
                "value_change_amount": str(scenario_data.get("value_change_amount", 0)),
                "value_change_percent": str(scenario_data.get("value_change_percent", 0)),
                "component_impacts": scenario_data.get("component_impacts", []),
            }
            
            conn.execute(text("""
                INSERT INTO scenarios (id, name, description, source, parameters, created_at, updated_at)
                VALUES (:id, :name, :description, 'custom', :parameters, :created_at, :updated_at)
                ON CONFLICT (id) DO UPDATE SET
                    name = EXCLUDED.name,
                    description = EXCLUDED.description,
                    parameters = EXCLUDED.parameters,
                    updated_at = EXCLUDED.updated_at
            """), {
                "id": scenario_id,
                "name": scenario_data.get("name", f"Scenario {scenario_id[:8]}"),
                "description": scenario_data.get("description"),
                "parameters": json.dumps(parameters),
                "created_at": scenario_data.get("created_at", datetime.now(timezone.utc)),
                "updated_at": datetime.now(timezone.utc),
            })
            conn.commit()
    except Exception as e:
        print(f"Error saving scenario: {e}")


def get_scenario(scenario_id: str) -> Optional[Dict]:
    """Get scenario from PostgreSQL."""
    engine = _get_db_engine()
    if not engine:
        return None
    
    try:
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT id, name, description, parameters, created_at, updated_at
                FROM scenarios WHERE id = :id
            """), {"id": scenario_id})
            row = result.fetchone()
            
            if row:
                params = row[3] if isinstance(row[3], dict) else json.loads(row[3]) if row[3] else {}
                return {
                    "id": str(row[0]),
                    "name": row[1],
                    "description": row[2],
                    "property_id": params.get("property_id"),
                    "modifications": params.get("modifications", []),
                    "base_value": Decimal(params.get("base_value", "0")),
                    "modified_value": Decimal(params.get("modified_value", "0")),
                    "value_change_amount": Decimal(params.get("value_change_amount", "0")),
                    "value_change_percent": Decimal(params.get("value_change_percent", "0")),
                    "component_impacts": params.get("component_impacts", []),
                    "created_at": row[4],
                    "updated_at": row[5],
                }
    except Exception as e:
        print(f"Error getting scenario: {e}")
    return None


def list_scenarios() -> List[Dict]:
    """List all scenarios from PostgreSQL."""
    engine = _get_db_engine()
    if not engine:
        return []
    
    try:
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT id, name, description, parameters, created_at, updated_at
                FROM scenarios WHERE source = 'custom'
                ORDER BY updated_at DESC
                LIMIT 100
            """))
            
            scenarios = []
            for row in result:
                params = row[3] if isinstance(row[3], dict) else json.loads(row[3]) if row[3] else {}
                scenarios.append({
                    "id": str(row[0]),
                    "name": row[1],
                    "description": row[2],
                    "property_id": params.get("property_id"),
                    "base_value": Decimal(params.get("base_value", "0")),
                    "modified_value": Decimal(params.get("modified_value", "0")),
                    "value_change_percent": Decimal(params.get("value_change_percent", "0")),
                    "created_at": row[4],
                    "updated_at": row[5],
                })
            return scenarios
    except Exception as e:
        print(f"Error listing scenarios: {e}")
    return []


def delete_scenario(scenario_id: str) -> bool:
    """Delete scenario from PostgreSQL."""
    engine = _get_db_engine()
    if not engine:
        return False
    
    try:
        with engine.connect() as conn:
            result = conn.execute(text("DELETE FROM scenarios WHERE id = :id"), {"id": scenario_id})
            conn.commit()
            return result.rowcount > 0
    except Exception as e:
        print(f"Error deleting scenario: {e}")
    return False


# ============ Core Calculation Functions ============

def calculate_value_direct_cap(noi: Decimal, cap_rate: Decimal) -> Decimal:
    """Calculate property value using direct capitalization."""
    if cap_rate <= 0:
        return Decimal("0")
    return (noi / cap_rate).quantize(Decimal("0.01"))


def calculate_noi(
    gross_floor_area: float,
    rent_psf: Decimal,
    vacancy_rate: Decimal,
    expense_ratio: Decimal
) -> Decimal:
    """Calculate Net Operating Income."""
    pgi = Decimal(str(gross_floor_area)) * rent_psf
    egi = pgi * (1 - vacancy_rate)
    expenses = egi * expense_ratio
    return (egi - expenses).quantize(Decimal("0.01"))


def calculate_dcf_value(
    noi: Decimal,
    rent_growth: Decimal,
    discount_rate: Decimal,
    exit_cap: Decimal,
    holding_years: int = 10
) -> Tuple[Decimal, Decimal]:
    """
    Calculate DCF value and IRR.
    Returns (NPV, IRR estimate)
    """
    cash_flows = []
    current_noi = float(noi)
    growth = float(rent_growth)
    disc = float(discount_rate)
    
    # Annual cash flows
    for year in range(1, holding_years + 1):
        current_noi *= (1 + growth)
        cash_flows.append(current_noi)
    
    # Terminal value at exit
    terminal_value = current_noi / float(exit_cap)
    cash_flows[-1] += terminal_value
    
    # NPV calculation
    npv = sum(cf / ((1 + disc) ** (i + 1)) for i, cf in enumerate(cash_flows))
    
    # Simple IRR estimate (Newton-Raphson would be more accurate)
    # Using approximation based on growth and cap rate spread
    irr_estimate = disc + (growth * 0.5) + ((float(exit_cap) - disc) * 0.1)
    
    return Decimal(str(npv)).quantize(Decimal("0.01")), Decimal(str(irr_estimate)).quantize(Decimal("0.0001"))


# ============ Scenario Builder Engine ============

class ScenarioBuilderEngine:
    """Engine for building and analyzing scenarios."""
    
    def __init__(self):
        self.properties = get_sample_properties()
    
    def get_property(self, property_id: str) -> Optional[Dict]:
        """Get property by ID."""
        # Try UUID format
        prop_id_str = str(property_id)
        
        # Check sample properties
        for key, prop in self.properties.items():
            if key == prop_id_str or prop.get("id") == prop_id_str:
                return copy.deepcopy(prop)
        
        # Default to first property for demo
        return copy.deepcopy(list(self.properties.values())[0])
    
    def calculate_property_value(self, property_data: Dict) -> Dict[str, Decimal]:
        """Calculate comprehensive property valuation."""
        noi = property_data.get("noi")
        
        if not noi:
            noi = calculate_noi(
                property_data.get("gross_floor_area_sf", 100000),
                property_data.get("market_rent_psf", Decimal("50")),
                property_data.get("vacancy_rate", Decimal("0.05")),
                property_data.get("expense_ratio", Decimal("0.35")),
            )
            property_data["noi"] = noi
        
        cap_rate = property_data.get("cap_rate", Decimal("0.06"))
        direct_cap_value = calculate_value_direct_cap(noi, cap_rate)
        
        dcf_value, irr = calculate_dcf_value(
            noi,
            property_data.get("rent_growth_rate", Decimal("0.025")),
            property_data.get("discount_rate", Decimal("0.08")),
            property_data.get("exit_cap_rate", Decimal("0.06")),
            property_data.get("holding_period_years", 10),
        )
        
        # Weighted average (60% DCF, 40% Direct Cap)
        final_value = (dcf_value * Decimal("0.6") + direct_cap_value * Decimal("0.4")).quantize(Decimal("0.01"))
        
        return {
            "direct_cap_value": direct_cap_value,
            "dcf_value": dcf_value,
            "final_value": final_value,
            "noi": noi,
            "cap_rate": cap_rate,
            "irr": irr,
            "expense_ratio": property_data.get("expense_ratio", Decimal("0.35")),
        }
    
    def apply_modification(
        self, 
        property_data: Dict, 
        mod: ScenarioModification
    ) -> Tuple[Dict, float]:
        """Apply a single modification to property data."""
        old_value = None
        
        if mod.type == ModificationType.RENT_GROWTH:
            old_value = float(property_data.get("rent_growth_rate", 0.025))
            property_data["rent_growth_rate"] = Decimal(str(mod.new_value))
            
        elif mod.type == ModificationType.VACANCY:
            old_value = float(property_data.get("vacancy_rate", 0.05))
            property_data["vacancy_rate"] = Decimal(str(mod.new_value))
            # Recalculate NOI with new vacancy
            property_data["noi"] = calculate_noi(
                property_data.get("gross_floor_area_sf", 100000),
                property_data.get("market_rent_psf", Decimal("50")),
                Decimal(str(mod.new_value)),
                property_data.get("expense_ratio", Decimal("0.35")),
            )
            
        elif mod.type == ModificationType.EXPENSES:
            old_value = float(property_data.get("expense_ratio", 0.35))
            property_data["expense_ratio"] = Decimal(str(mod.new_value))
            # Recalculate NOI
            property_data["noi"] = calculate_noi(
                property_data.get("gross_floor_area_sf", 100000),
                property_data.get("market_rent_psf", Decimal("50")),
                property_data.get("vacancy_rate", Decimal("0.05")),
                Decimal(str(mod.new_value)),
            )
            
        elif mod.type == ModificationType.CAP_RATE:
            old_value = float(property_data.get("cap_rate", 0.06))
            property_data["cap_rate"] = Decimal(str(mod.new_value))
            
        elif mod.type == ModificationType.EXIT_CAP_RATE:
            old_value = float(property_data.get("exit_cap_rate", 0.065))
            property_data["exit_cap_rate"] = Decimal(str(mod.new_value))
            
        elif mod.type == ModificationType.DISCOUNT_RATE:
            old_value = float(property_data.get("discount_rate", 0.08))
            property_data["discount_rate"] = Decimal(str(mod.new_value))
            
        elif mod.type == ModificationType.NOI:
            old_value = float(property_data.get("noi", 0))
            property_data["noi"] = Decimal(str(mod.new_value))
            
        elif mod.type == ModificationType.RENT_PSF:
            old_value = float(property_data.get("market_rent_psf", 50))
            property_data["market_rent_psf"] = Decimal(str(mod.new_value))
            # Recalculate NOI
            property_data["noi"] = calculate_noi(
                property_data.get("gross_floor_area_sf", 100000),
                Decimal(str(mod.new_value)),
                property_data.get("vacancy_rate", Decimal("0.05")),
                property_data.get("expense_ratio", Decimal("0.35")),
            )
            
        elif mod.type == ModificationType.CERTIFICATION:
            old_value = 0
            certs = property_data.get("certifications", [])
            certs.append(str(mod.new_value))
            property_data["certifications"] = certs
            # Certification premium (simplified)
            property_data["cap_rate"] = property_data.get("cap_rate", Decimal("0.06")) * Decimal("0.98")
            
        elif mod.type == ModificationType.RETROFIT:
            old_value = 0
            # Retrofit reduces expenses and may improve cap rate
            property_data["expense_ratio"] = property_data.get("expense_ratio", Decimal("0.35")) * Decimal("0.95")
            property_data["cap_rate"] = property_data.get("cap_rate", Decimal("0.06")) * Decimal("0.99")
            
        elif mod.type == ModificationType.CLIMATE:
            old_value = 0
            # Climate scenario adjustment
            if mod.new_value == "high_risk":
                property_data["cap_rate"] = property_data.get("cap_rate", Decimal("0.06")) * Decimal("1.05")
            elif mod.new_value == "low_risk":
                property_data["cap_rate"] = property_data.get("cap_rate", Decimal("0.06")) * Decimal("0.98")
        
        return property_data, old_value
    
    def build_scenario(self, request: ScenarioBuildRequest) -> ScenarioBuildResult:
        """Build a custom scenario with modifications."""
        # Get base property
        base_property = self.get_property(str(request.base_property_id))
        
        # Calculate base valuation
        base_metrics = self.calculate_property_value(base_property)
        base_value = base_metrics["final_value"]
        
        # Apply modifications incrementally to track impacts
        modified_property = copy.deepcopy(base_property)
        component_impacts = []
        running_value = base_value
        
        for mod in request.modifications:
            # Apply modification
            modified_property, old_val = self.apply_modification(modified_property, mod)
            
            # Calculate new value
            new_metrics = self.calculate_property_value(copy.deepcopy(modified_property))
            new_value = new_metrics["final_value"]
            
            impact = new_value - running_value
            impact_pct = (impact / running_value * Decimal("100")).quantize(Decimal("0.01")) if running_value else Decimal("0")
            
            component_impacts.append(ComponentImpact(
                modification=mod.description or f"{mod.type.value} change",
                parameter=mod.parameter,
                old_value=old_val,
                new_value=mod.new_value,
                impact=impact,
                impact_pct=impact_pct,
            ))
            
            running_value = new_value
        
        # Final adjusted value
        final_metrics = self.calculate_property_value(modified_property)
        adjusted_value = final_metrics["final_value"]
        value_change = adjusted_value - base_value
        value_change_pct = (value_change / base_value * Decimal("100")).quantize(Decimal("0.01")) if base_value else Decimal("0")
        
        scenario_id = uuid4()
        
        # Store scenario
        save_scenario(str(scenario_id), {
            "id": str(scenario_id),
            "scenario_name": request.scenario_name,
            "description": request.description,
            "base_property_id": str(request.base_property_id),
            "modifications": [m.model_dump() for m in request.modifications],
            "base_value": float(base_value),
            "adjusted_value": float(adjusted_value),
            "value_change_pct": float(value_change_pct),
            "metrics": {k: float(v) for k, v in final_metrics.items()},
            "created_at": datetime.now(timezone.utc).isoformat(),
        })
        
        return ScenarioBuildResult(
            scenario_id=scenario_id,
            scenario_name=request.scenario_name,
            base_value=base_value,
            adjusted_value=adjusted_value,
            value_change=value_change,
            value_change_pct=value_change_pct,
            component_impacts=component_impacts,
            modifications_applied=len(request.modifications),
        )
    
    def compare_scenarios(
        self, 
        base_property_id: str, 
        scenario_ids: List[str],
        metrics: List[str]
    ) -> ScenarioComparisonResult:
        """Compare multiple scenarios."""
        base_property = self.get_property(base_property_id)
        base_metrics = self.calculate_property_value(base_property)
        base_value = base_metrics["final_value"]
        
        comparison_rows = []
        
        # Add base case
        comparison_rows.append(ScenarioComparisonRow(
            scenario_id=UUID(int=0),
            scenario_name="Base Case",
            value=base_value,
            value_change_pct=Decimal("0"),
            noi=base_metrics["noi"],
            cap_rate=base_metrics["cap_rate"],
            irr=base_metrics["irr"],
            expense_ratio=base_metrics["expense_ratio"],
        ))
        
        # Add each scenario
        for sid in scenario_ids:
            scenario = get_scenario(str(sid))
            if scenario:
                adjusted_value = Decimal(str(scenario["adjusted_value"]))
                value_change_pct = Decimal(str(scenario["value_change_pct"]))
                scenario_metrics = scenario.get("metrics", {})
                
                comparison_rows.append(ScenarioComparisonRow(
                    scenario_id=UUID(str(sid)),
                    scenario_name=scenario["scenario_name"],
                    value=adjusted_value,
                    value_change_pct=value_change_pct,
                    noi=Decimal(str(scenario_metrics.get("noi", 0))),
                    cap_rate=Decimal(str(scenario_metrics.get("cap_rate", 0))),
                    irr=Decimal(str(scenario_metrics.get("irr", 0))),
                    expense_ratio=Decimal(str(scenario_metrics.get("expense_ratio", 0))),
                ))
        
        # Find best/worst
        if len(comparison_rows) > 1:
            sorted_rows = sorted(comparison_rows, key=lambda x: x.value, reverse=True)
            best_scenario = sorted_rows[0].scenario_name
            worst_scenario = sorted_rows[-1].scenario_name
        else:
            best_scenario = "Base Case"
            worst_scenario = "Base Case"
        
        # Key differentiators
        differentiators = []
        if len(comparison_rows) > 1:
            value_spread = max(r.value for r in comparison_rows) - min(r.value for r in comparison_rows)
            differentiators.append(f"Value spread: ${float(value_spread)/1e6:,.1f}M")
            
            cap_rates = [r.cap_rate for r in comparison_rows if r.cap_rate]
            if cap_rates:
                differentiators.append(f"Cap rate range: {float(min(cap_rates))*100:.2f}% - {float(max(cap_rates))*100:.2f}%")
        
        return ScenarioComparisonResult(
            comparison_table=comparison_rows,
            best_scenario=best_scenario,
            worst_scenario=worst_scenario,
            key_differentiators=differentiators,
            base_value=base_value,
        )


# ============ Sensitivity Analysis Engine ============

class SensitivityAnalysisEngine:
    """Engine for sensitivity analysis and tornado/spider charts."""
    
    def __init__(self):
        self.scenario_engine = ScenarioBuilderEngine()
    
    def analyze(
        self,
        property_id: str,
        base_valuation: Optional[Decimal],
        variables: List[SensitivityVariable]
    ) -> SensitivityAnalyzeResult:
        """Perform comprehensive sensitivity analysis."""
        property_data = self.scenario_engine.get_property(property_id)
        
        if not base_valuation:
            base_metrics = self.scenario_engine.calculate_property_value(property_data)
            base_valuation = base_metrics["final_value"]
        
        sensitivities = {}
        
        for var in variables:
            var_results = []
            step_size = (var.range.max - var.range.min) / (var.steps - 1)
            
            for i in range(var.steps):
                current_value = var.range.min + (i * step_size)
                
                # Create modified property
                modified = copy.deepcopy(property_data)
                self._apply_variable_change(modified, var.name, current_value)
                
                # Calculate new valuation
                new_metrics = self.scenario_engine.calculate_property_value(modified)
                new_value = new_metrics["final_value"]
                
                change_from_base = new_value - base_valuation
                change_pct = (change_from_base / base_valuation * Decimal("100")).quantize(Decimal("0.01"))
                
                var_results.append(SensitivityDataPoint(
                    variable_value=round(current_value, 4),
                    valuation=new_value,
                    change_from_base=change_from_base,
                    change_pct=change_pct,
                ))
            
            sensitivities[var.name] = var_results
        
        # Generate tornado data
        tornado_data = self._generate_tornado_data(sensitivities, base_valuation, variables)
        
        # Generate spider chart data
        spider_data = self._generate_spider_data(property_data, variables)
        
        return SensitivityAnalyzeResult(
            property_id=UUID(property_id) if len(property_id) == 36 else UUID(int=0),
            base_valuation=base_valuation,
            sensitivities=sensitivities,
            tornado_data=tornado_data,
            spider_chart_data=spider_data,
        )
    
    def _apply_variable_change(self, property_data: Dict, var_name: str, value: float) -> None:
        """Apply variable change to property data."""
        var_mapping = {
            "cap_rate": "cap_rate",
            "rent_growth": "rent_growth_rate",
            "rent_growth_rate": "rent_growth_rate",
            "vacancy_rate": "vacancy_rate",
            "vacancy": "vacancy_rate",
            "expense_ratio": "expense_ratio",
            "expenses": "expense_ratio",
            "exit_cap_rate": "exit_cap_rate",
            "exit_cap": "exit_cap_rate",
            "discount_rate": "discount_rate",
            "noi": "noi",
            "rent_psf": "market_rent_psf",
        }
        
        mapped_var = var_mapping.get(var_name.lower(), var_name)
        property_data[mapped_var] = Decimal(str(value))
        
        # Recalculate NOI if relevant variables changed
        if mapped_var in ["vacancy_rate", "expense_ratio", "market_rent_psf"]:
            property_data["noi"] = calculate_noi(
                property_data.get("gross_floor_area_sf", 100000),
                property_data.get("market_rent_psf", Decimal("50")),
                property_data.get("vacancy_rate", Decimal("0.05")),
                property_data.get("expense_ratio", Decimal("0.35")),
            )
    
    def _generate_tornado_data(
        self,
        sensitivities: Dict[str, List[SensitivityDataPoint]],
        base_value: Decimal,
        variables: List[SensitivityVariable]
    ) -> List[TornadoDataPoint]:
        """Generate tornado chart data."""
        tornado_data = []
        
        var_bases = {v.name: v.base_value for v in variables}
        
        for var_name, data_points in sensitivities.items():
            valuations = [dp.valuation for dp in data_points]
            var_values = [dp.variable_value for dp in data_points]
            
            min_val = min(valuations)
            max_val = max(valuations)
            
            low_impact = ((min_val - base_value) / base_value * Decimal("100")).quantize(Decimal("0.01"))
            high_impact = ((max_val - base_value) / base_value * Decimal("100")).quantize(Decimal("0.01"))
            swing = high_impact - low_impact
            
            tornado_data.append(TornadoDataPoint(
                variable=var_name.replace("_", " ").title(),
                low_impact=low_impact,
                high_impact=high_impact,
                swing=abs(swing),
                low_value=min(var_values),
                high_value=max(var_values),
                base_value=var_bases.get(var_name),
            ))
        
        # Sort by swing (largest impact first)
        tornado_data.sort(key=lambda x: abs(x.swing), reverse=True)
        
        return tornado_data
    
    def _generate_spider_data(
        self,
        property_data: Dict,
        variables: List[SensitivityVariable]
    ) -> SpiderChartData:
        """Generate spider chart data."""
        var_names = [v.name.replace("_", " ").title() for v in variables]
        
        # Base case values
        base_values = [v.base_value * 100 if v.base_value < 1 else v.base_value for v in variables]
        
        # Optimistic scenario (favorable direction)
        optimistic_values = []
        for v in variables:
            if v.name in ["cap_rate", "vacancy_rate", "expense_ratio", "exit_cap_rate", "discount_rate"]:
                optimistic_values.append(v.range.min * 100 if v.range.min < 1 else v.range.min)
            else:
                optimistic_values.append(v.range.max * 100 if v.range.max < 1 else v.range.max)
        
        # Pessimistic scenario (unfavorable direction)
        pessimistic_values = []
        for v in variables:
            if v.name in ["cap_rate", "vacancy_rate", "expense_ratio", "exit_cap_rate", "discount_rate"]:
                pessimistic_values.append(v.range.max * 100 if v.range.max < 1 else v.range.max)
            else:
                pessimistic_values.append(v.range.min * 100 if v.range.min < 1 else v.range.min)
        
        return SpiderChartData(
            variables=var_names,
            scenarios=[
                SpiderChartScenario(name="Base Case", values=base_values),
                SpiderChartScenario(name="Optimistic", values=optimistic_values),
                SpiderChartScenario(name="Pessimistic", values=pessimistic_values),
            ]
        )


# ============ What-If Analysis Engine ============

class WhatIfAnalysisEngine:
    """Engine for what-if analysis with cascading effects."""
    
    def __init__(self):
        self.scenario_engine = ScenarioBuilderEngine()
    
    def analyze(self, request) -> WhatIfResult:
        """Perform what-if analysis."""
        property_data = self.scenario_engine.get_property(str(request.property_id))
        
        # Base valuation
        base_metrics = self.scenario_engine.calculate_property_value(copy.deepcopy(property_data))
        base_value = base_metrics["final_value"]
        
        modified = copy.deepcopy(property_data)
        change_breakdown = []
        
        for change in request.changes:
            old_value = self._get_parameter_value(modified, change.parameter)
            
            if change.change_type == ChangeType.ABSOLUTE:
                new_value = old_value + change.change_value
            else:  # percentage
                new_value = old_value * (1 + change.change_value)
            
            # Apply change
            self._set_parameter_value(modified, change.parameter, new_value)
            
            # Calculate cascading effects
            cascading_impact = Decimal("0")
            if request.cascade_effects:
                cascading_impact = self._apply_cascading_effects(
                    modified, change.parameter, old_value, new_value
                )
            
            # Calculate impact
            temp_metrics = self.scenario_engine.calculate_property_value(copy.deepcopy(modified))
            temp_value = temp_metrics["final_value"]
            direct_impact = temp_value - base_value - cascading_impact
            
            change_breakdown.append(ChangeBreakdown(
                parameter=change.parameter,
                old_value=old_value,
                new_value=new_value,
                direct_impact=direct_impact,
                cascading_impacts=cascading_impact,
                total_impact=direct_impact + cascading_impact,
            ))
        
        # Final valuation
        final_metrics = self.scenario_engine.calculate_property_value(modified)
        final_value = final_metrics["final_value"]
        
        total_change = final_value - base_value
        total_change_pct = (total_change / base_value * Decimal("100")).quantize(Decimal("0.01"))
        
        return WhatIfResult(
            property_id=request.property_id,
            base_valuation=base_value,
            adjusted_valuation=final_value,
            total_change=total_change,
            total_change_pct=total_change_pct,
            change_breakdown=change_breakdown,
            cascade_effects_applied=request.cascade_effects,
        )
    
    def _get_parameter_value(self, prop: Dict, parameter: str) -> float:
        """Get parameter value from property."""
        mapping = {
            "cap_rate": "cap_rate",
            "vacancy_rate": "vacancy_rate",
            "expense_ratio": "expense_ratio",
            "rent_growth": "rent_growth_rate",
            "discount_rate": "discount_rate",
            "exit_cap_rate": "exit_cap_rate",
            "noi": "noi",
            "rent_psf": "market_rent_psf",
        }
        key = mapping.get(parameter, parameter)
        return float(prop.get(key, 0))
    
    def _set_parameter_value(self, prop: Dict, parameter: str, value: float) -> None:
        """Set parameter value in property."""
        mapping = {
            "cap_rate": "cap_rate",
            "vacancy_rate": "vacancy_rate",
            "expense_ratio": "expense_ratio",
            "rent_growth": "rent_growth_rate",
            "discount_rate": "discount_rate",
            "exit_cap_rate": "exit_cap_rate",
            "noi": "noi",
            "rent_psf": "market_rent_psf",
        }
        key = mapping.get(parameter, parameter)
        prop[key] = Decimal(str(value))
        
        # Recalculate NOI if needed
        if key in ["vacancy_rate", "expense_ratio", "market_rent_psf"]:
            prop["noi"] = calculate_noi(
                prop.get("gross_floor_area_sf", 100000),
                prop.get("market_rent_psf", Decimal("50")),
                prop.get("vacancy_rate", Decimal("0.05")),
                prop.get("expense_ratio", Decimal("0.35")),
            )
    
    def _apply_cascading_effects(
        self,
        prop: Dict,
        parameter: str,
        old_value: float,
        new_value: float
    ) -> Decimal:
        """Apply cascading effects and return the impact."""
        cascading_impact = Decimal("0")
        
        if parameter == "vacancy_rate":
            # Higher vacancy → higher collection loss
            vacancy_change = new_value - old_value
            if vacancy_change > 0:
                # Cascading effect: collection loss increases proportionally
                cascading_impact += Decimal(str(vacancy_change * 0.3))
        
        elif parameter == "expense_ratio":
            # Higher expenses might reduce rent competitiveness
            expense_change = new_value - old_value
            if expense_change > 0.05:  # Significant increase
                prop["vacancy_rate"] = prop.get("vacancy_rate", Decimal("0.05")) * Decimal("1.02")
        
        elif parameter == "rent_psf":
            # Higher rent might increase vacancy
            rent_change_pct = (new_value - old_value) / old_value if old_value > 0 else 0
            if rent_change_pct > 0.1:  # >10% rent increase
                prop["vacancy_rate"] = prop.get("vacancy_rate", Decimal("0.05")) * Decimal("1.05")
        
        return cascading_impact


# ============ Scenario Templates ============

def get_scenario_templates() -> List[ScenarioTemplate]:
    """Get predefined scenario templates."""
    return [
        ScenarioTemplate(
            name="Optimistic Growth",
            description="Strong rent growth, declining vacancy, cap rate compression",
            category="optimistic",
            modifications=[
                ScenarioModification(type=ModificationType.RENT_GROWTH, parameter="rent_growth_rate", new_value=0.04, description="Strong rent growth (4%)"),
                ScenarioModification(type=ModificationType.VACANCY, parameter="vacancy_rate", new_value=0.03, description="Low vacancy (3%)"),
                ScenarioModification(type=ModificationType.CAP_RATE, parameter="cap_rate", new_value=0.05, description="Cap rate compression (5%)"),
            ]
        ),
        ScenarioTemplate(
            name="Recession Stress Test",
            description="Economic downturn with rising vacancy and cap rates",
            category="stress_test",
            modifications=[
                ScenarioModification(type=ModificationType.RENT_GROWTH, parameter="rent_growth_rate", new_value=0.0, description="Flat rent growth (0%)"),
                ScenarioModification(type=ModificationType.VACANCY, parameter="vacancy_rate", new_value=0.12, description="High vacancy (12%)"),
                ScenarioModification(type=ModificationType.CAP_RATE, parameter="cap_rate", new_value=0.075, description="Cap rate expansion (7.5%)"),
                ScenarioModification(type=ModificationType.EXPENSES, parameter="expense_ratio", new_value=0.40, description="Higher expenses (40%)"),
            ]
        ),
        ScenarioTemplate(
            name="Green Building Upgrade",
            description="LEED certification with efficiency improvements",
            category="green_upgrade",
            modifications=[
                ScenarioModification(type=ModificationType.CERTIFICATION, parameter="certification", new_value="LEED Gold", description="LEED Gold certification"),
                ScenarioModification(type=ModificationType.EXPENSES, parameter="expense_ratio", new_value=0.30, description="Reduced expenses (30%)"),
                ScenarioModification(type=ModificationType.RENT_PSF, parameter="rent_psf", new_value=70, description="Green rent premium ($70/SF)"),
            ]
        ),
        ScenarioTemplate(
            name="Rising Interest Rates",
            description="Higher discount and exit cap rates scenario",
            category="pessimistic",
            modifications=[
                ScenarioModification(type=ModificationType.DISCOUNT_RATE, parameter="discount_rate", new_value=0.095, description="Higher discount rate (9.5%)"),
                ScenarioModification(type=ModificationType.EXIT_CAP_RATE, parameter="exit_cap_rate", new_value=0.07, description="Higher exit cap (7%)"),
            ]
        ),
        ScenarioTemplate(
            name="Value-Add Repositioning",
            description="Property upgrade with higher rents and reduced vacancy",
            category="optimistic",
            modifications=[
                ScenarioModification(type=ModificationType.RENT_PSF, parameter="rent_psf", new_value=75, description="Premium rents post-renovation ($75/SF)"),
                ScenarioModification(type=ModificationType.VACANCY, parameter="vacancy_rate", new_value=0.04, description="Reduced vacancy (4%)"),
                ScenarioModification(type=ModificationType.EXPENSES, parameter="expense_ratio", new_value=0.32, description="Efficient operations (32%)"),
                ScenarioModification(type=ModificationType.CAP_RATE, parameter="cap_rate", new_value=0.052, description="Cap rate compression (5.2%)"),
            ]
        ),
    ]


# ============ Main Engine Class ============

class InteractiveScenarioEngine:
    """Main engine combining all scenario analysis capabilities."""
    
    def __init__(self):
        self.scenario_builder = ScenarioBuilderEngine()
        self.sensitivity_analyzer = SensitivityAnalysisEngine()
        self.whatif_analyzer = WhatIfAnalysisEngine()
    
    def build_scenario(self, request: ScenarioBuildRequest) -> ScenarioBuildResult:
        return self.scenario_builder.build_scenario(request)
    
    def compare_scenarios(self, base_property_id: str, scenario_ids: List[str], metrics: List[str]) -> ScenarioComparisonResult:
        return self.scenario_builder.compare_scenarios(base_property_id, scenario_ids, metrics)
    
    def analyze_sensitivity(self, property_id: str, base_valuation: Optional[Decimal], variables: List[SensitivityVariable]) -> SensitivityAnalyzeResult:
        return self.sensitivity_analyzer.analyze(property_id, base_valuation, variables)
    
    def what_if_analysis(self, request) -> WhatIfResult:
        return self.whatif_analyzer.analyze(request)
    
    def get_templates(self) -> List[ScenarioTemplate]:
        return get_scenario_templates()
    
    def list_scenarios(self) -> List[Dict]:
        return list_scenarios()
