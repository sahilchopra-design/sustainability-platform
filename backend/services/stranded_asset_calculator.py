"""
Stranded Asset Calculation Engine
Calculates reserve impairment, power plant valuations, and technology disruption metrics
for climate transition risk assessment.
"""

from decimal import Decimal
from typing import Dict, List, Optional, Tuple, Any
from datetime import date, datetime, timezone
from uuid import UUID
import uuid
import math

from schemas.stranded_assets import (
    ReserveType, ReserveCategory, PlantTechnology, InfrastructureType,
    RiskCategory, AssetType, OfftakeType, RepurposingType,
    YearlyImpairment, YearlyValuation, RepurposingOption,
    ReserveImpairmentResult, PowerPlantValuationResult, InfrastructureValuationResult,
    TechnologyDisruptionSummary, CriticalAssetAlert
)


# ==================== RESERVE IMPAIRMENT CALCULATOR ====================

class ReserveImpairmentCalculator:
    """Calculate reserve impairment under climate scenarios."""
    
    CO2_FACTOR = Decimal("3.664")  # kg CO2 per kg carbon
    
    # Default commodity prices by type (USD)
    DEFAULT_PRICES = {
        "oil": Decimal("75"),      # per barrel
        "gas": Decimal("4"),       # per MMBtu
        "coal": Decimal("80")      # per tonne
    }
    
    # Default carbon intensities (kgCO2 per unit)
    DEFAULT_CARBON_INTENSITY = {
        "oil": Decimal("430"),     # per barrel
        "gas": Decimal("53"),      # per MMBtu
        "coal": Decimal("2400")    # per tonne
    }
    
    def __init__(self, db_session=None, cache_client=None):
        self.db = db_session
        self.cache = cache_client
    
    async def calculate_impairment(
        self,
        reserve_id: UUID,
        reserve_data: Dict,
        scenario_data: Dict,
        target_years: List[int],
        discount_rate: Decimal = Decimal("0.08"),
        commodity_price_forecast: Optional[Dict[int, Decimal]] = None,
        carbon_price_forecast: Optional[Dict[int, Decimal]] = None
    ) -> ReserveImpairmentResult:
        """
        Calculate reserve impairment under climate scenario.
        
        Formula:
        Stranded_Volume = Recoverable_Reserves - Economic_Reserves_under_Scenario
        Stranded_Value = NPV(Stranded_Volume × Commodity_Price - Production_Cost - Carbon_Cost)
        
        Args:
            reserve_id: UUID of the reserve
            reserve_data: Reserve details (from DB or API input)
            scenario_data: Scenario parameters
            target_years: List of years to calculate impairment for
            discount_rate: Discount rate for NPV calculation
            commodity_price_forecast: Optional price forecasts by year
            carbon_price_forecast: Optional carbon price forecasts by year
        
        Returns:
            ReserveImpairmentResult with yearly impairments and risk assessment
        """
        # Extract reserve properties
        reserve_type = reserve_data.get("reserve_type", "oil")
        asset_name = reserve_data.get("asset_name", "Unknown Reserve")
        
        proven = Decimal(str(reserve_data.get("proven_reserves_mmBOE", 0) or 0))
        probable = Decimal(str(reserve_data.get("probable_reserves_mmBOE", 0) or 0))
        total_reserves = proven + probable
        
        breakeven = Decimal(str(reserve_data.get("breakeven_price_USD", 0) or 0))
        lifting_cost = Decimal(str(reserve_data.get("lifting_cost_USD", 20) or 20))
        remaining_capex = Decimal(str(reserve_data.get("remaining_capex_USD", 0) or 0))
        carbon_intensity = Decimal(str(
            reserve_data.get("carbon_intensity_kgCO2_per_unit") or 
            self.DEFAULT_CARBON_INTENSITY.get(reserve_type, Decimal("500"))
        ))
        
        expected_depletion = reserve_data.get("expected_depletion_year", 2045)
        
        # Get pathway data from scenario
        pathway_data = scenario_data.get("demand_trajectory", {})
        base_year = scenario_data.get("base_year", 2025)
        
        yearly_impairments = []
        current_year = date.today().year
        
        for year in target_years:
            # Get demand reduction for year
            demand_reduction = self._get_demand_reduction(pathway_data, base_year, year)
            
            # Get commodity price
            if commodity_price_forecast and year in commodity_price_forecast:
                commodity_price = Decimal(str(commodity_price_forecast[year]))
            else:
                commodity_price = self._get_default_commodity_price(reserve_type, year, scenario_data)
            
            # Get carbon price
            if carbon_price_forecast and year in carbon_price_forecast:
                carbon_price = Decimal(str(carbon_price_forecast[year]))
            else:
                carbon_price = self._get_default_carbon_price(year, scenario_data)
            
            # Calculate carbon cost per unit
            carbon_cost_per_unit = carbon_intensity * carbon_price / Decimal("1000")
            
            # Calculate total cost per unit
            capex_per_unit = remaining_capex / total_reserves if total_reserves > 0 else Decimal("0")
            total_cost = lifting_cost + carbon_cost_per_unit + capex_per_unit
            
            # Calculate economic reserves
            if commodity_price > total_cost:
                economic_reserves = total_reserves * (Decimal("1") - demand_reduction)
            else:
                economic_reserves = Decimal("0")
            
            stranded_volume = total_reserves - economic_reserves
            stranded_percent = (stranded_volume / total_reserves * 100) if total_reserves > 0 else Decimal("0")
            
            # Calculate NPV for this year
            years_to_horizon = max(year - current_year, 1)
            npv = self._calculate_npv(
                economic_reserves, commodity_price, total_cost,
                years_to_horizon, discount_rate
            )
            
            yearly_impairments.append(YearlyImpairment(
                year=year,
                demand_reduction_percent=round(demand_reduction * 100, 2),
                commodity_price_usd=round(commodity_price, 2),
                carbon_price_usd_tco2=round(carbon_price, 2),
                economic_reserves_mmBOE=round(economic_reserves, 4),
                stranded_volume_mmBOE=round(stranded_volume, 4),
                stranded_volume_percent=round(stranded_percent, 2),
                npv_usd=round(npv, 2)
            ))
        
        # Calculate baseline NPV (no climate impact)
        baseline_npv = self._calculate_baseline_npv(
            total_reserves, breakeven, lifting_cost,
            expected_depletion, current_year, discount_rate
        )
        
        # Get final year results
        final_year = yearly_impairments[-1] if yearly_impairments else None
        scenario_npv = Decimal(str(final_year.npv_usd)) if final_year else Decimal("0")
        
        npv_impact = (
            (scenario_npv - baseline_npv) / baseline_npv * 100
            if baseline_npv > 0 else Decimal("0")
        )
        
        total_stranded = Decimal(str(final_year.stranded_volume_percent)) if final_year else Decimal("0")
        stranded_value = max(baseline_npv - scenario_npv, Decimal("0"))
        
        # Calculate risk score
        last_price = Decimal(str(final_year.commodity_price_usd)) if final_year else self.DEFAULT_PRICES.get(reserve_type, Decimal("50"))
        risk_score = self._calculate_risk_score(
            total_stranded, npv_impact, breakeven, last_price
        )
        
        return ReserveImpairmentResult(
            reserve_id=reserve_id,
            asset_name=asset_name,
            reserve_type=reserve_type,
            total_reserves_mmBOE=round(total_reserves, 4),
            baseline_npv_usd=round(baseline_npv, 2),
            scenario_npv_usd=round(scenario_npv, 2),
            npv_impact_percent=round(npv_impact, 2),
            total_stranded_percent=round(total_stranded, 2),
            total_stranded_value_usd=round(stranded_value, 2),
            yearly_impairments=yearly_impairments,
            stranding_risk_score=round(risk_score, 2),
            risk_category=self._get_risk_category(risk_score),
            key_drivers=self._identify_key_drivers(reserve_data, scenario_data),
            recommendations=self._generate_recommendations(risk_score, reserve_data)
        )
    
    def _calculate_npv(
        self, reserves: Decimal, price: Decimal, cost: Decimal,
        years: int, discount_rate: Decimal
    ) -> Decimal:
        """Calculate NPV of remaining reserves."""
        if years <= 0 or reserves <= 0:
            return Decimal("0")
        
        annual_production = reserves / Decimal(str(years))
        annual_cash_flow = annual_production * (price - cost)
        
        npv = Decimal("0")
        for t in range(1, years + 1):
            discount_factor = (Decimal("1") + discount_rate) ** t
            npv += annual_cash_flow / discount_factor
        
        return max(npv, Decimal("0"))
    
    def _calculate_baseline_npv(
        self, total_reserves: Decimal, breakeven: Decimal, lifting_cost: Decimal,
        expected_depletion: int, current_year: int, discount_rate: Decimal
    ) -> Decimal:
        """Calculate baseline NPV without climate impact."""
        if total_reserves <= 0:
            return Decimal("0")
        
        # Assume price at 20% above breakeven
        commodity_price = breakeven * Decimal("1.2") if breakeven > 0 else Decimal("60")
        
        remaining_years = max(expected_depletion - current_year, 10)
        
        return self._calculate_npv(
            total_reserves, commodity_price, lifting_cost,
            remaining_years, discount_rate
        )
    
    def _get_demand_reduction(
        self, pathway_data: Dict, base_year: int, year: int
    ) -> Decimal:
        """Get demand reduction percentage for year from pathway."""
        if not pathway_data:
            # Default demand reduction trajectory
            years_from_base = year - base_year
            reduction = min(Decimal("0.05") * years_from_base, Decimal("0.6"))
            return reduction
        
        base_demand = Decimal(str(pathway_data.get(str(base_year), 100)))
        year_demand = Decimal(str(pathway_data.get(str(year), base_demand)))
        
        if base_demand > 0:
            return max(Decimal("1") - (year_demand / base_demand), Decimal("0"))
        return Decimal("0")
    
    def _get_default_commodity_price(
        self, reserve_type: str, year: int, scenario_data: Dict
    ) -> Decimal:
        """Get default commodity price for year."""
        base_price = self.DEFAULT_PRICES.get(reserve_type, Decimal("50"))
        
        # Price decline under transition scenario
        decline_rate = Decimal("0.02")  # 2% annual decline
        years_from_now = year - date.today().year
        
        return base_price * ((Decimal("1") - decline_rate) ** years_from_now)
    
    def _get_default_carbon_price(self, year: int, scenario_data: Dict) -> Decimal:
        """Get default carbon price for year."""
        # EU ETS style trajectory
        base_price = Decimal("85")  # 2025 baseline
        annual_increase = Decimal("8")
        
        price_trajectory = scenario_data.get("carbon_price_trajectory", {})
        if price_trajectory and str(year) in price_trajectory:
            return Decimal(str(price_trajectory[str(year)]))
        
        return base_price + (annual_increase * (year - 2025))
    
    def _calculate_risk_score(
        self, stranded_percent: Decimal, npv_impact: Decimal,
        breakeven: Decimal, current_price: Decimal
    ) -> Decimal:
        """Calculate stranding risk score (0-1)."""
        # Weighted combination of factors
        stranded_weight = Decimal("0.4")
        npv_weight = Decimal("0.4")
        margin_weight = Decimal("0.2")
        
        # Normalize each factor
        stranded_normalized = min(stranded_percent / Decimal("100"), Decimal("1"))
        npv_normalized = min(abs(npv_impact) / Decimal("100"), Decimal("1"))
        
        margin_ratio = (breakeven / current_price) if current_price > 0 else Decimal("1")
        margin_normalized = min(margin_ratio, Decimal("1"))
        
        return (
            stranded_weight * stranded_normalized +
            npv_weight * npv_normalized +
            margin_weight * margin_normalized
        )
    
    def _get_risk_category(self, risk_score: Decimal) -> RiskCategory:
        """Convert risk score to category."""
        if risk_score < Decimal("0.25"):
            return RiskCategory.LOW
        elif risk_score < Decimal("0.5"):
            return RiskCategory.MEDIUM
        elif risk_score < Decimal("0.75"):
            return RiskCategory.HIGH
        else:
            return RiskCategory.CRITICAL
    
    def _identify_key_drivers(self, reserve_data: Dict, scenario_data: Dict) -> List[str]:
        """Identify key risk drivers."""
        drivers = []
        
        breakeven = Decimal(str(reserve_data.get("breakeven_price_USD", 0) or 0))
        if breakeven > Decimal("60"):
            drivers.append("High breakeven price increases stranding risk")
        
        carbon_intensity = Decimal(str(reserve_data.get("carbon_intensity_kgCO2_per_unit", 0) or 0))
        if carbon_intensity > Decimal("500"):
            drivers.append("High carbon intensity increases carbon cost exposure")
        
        methane_rate = Decimal(str(reserve_data.get("methane_leakage_rate", 0) or 0))
        if methane_rate > Decimal("0.02"):
            drivers.append("Methane leakage adds to emissions profile")
        
        peak_year = scenario_data.get("peak_demand_year")
        if peak_year and peak_year < 2035:
            drivers.append("Early peak demand significantly reduces economic reserves")
        
        reserve_type = reserve_data.get("reserve_type", "")
        if reserve_type == "coal":
            drivers.append("Coal faces fastest demand decline in transition scenarios")
        
        return drivers if drivers else ["Standard transition risk exposure"]
    
    def _generate_recommendations(self, risk_score: Decimal, reserve_data: Dict) -> List[str]:
        """Generate action recommendations."""
        recommendations = []
        
        if risk_score >= Decimal("0.75"):
            recommendations.append("URGENT: Consider divestment or accelerated production")
            recommendations.append("Review portfolio concentration in this asset class")
        elif risk_score >= Decimal("0.5"):
            recommendations.append("HIGH: Evaluate hedging strategies for carbon exposure")
            recommendations.append("Consider strategic partnerships for cost reduction")
        elif risk_score >= Decimal("0.25"):
            recommendations.append("MEDIUM: Monitor scenario developments and update forecasts")
            recommendations.append("Prepare contingency plans for accelerated transition")
        else:
            recommendations.append("LOW: Continue standard monitoring procedures")
        
        methane_rate = Decimal(str(reserve_data.get("methane_leakage_rate", 0) or 0))
        if methane_rate > Decimal("0.02"):
            recommendations.append("Address methane leakage to reduce carbon intensity")
        
        return recommendations


# ==================== POWER PLANT VALUATOR ====================

class PowerPlantValuator:
    """Value power plants under different transition scenarios."""
    
    # Default capacity factors by technology
    DEFAULT_CAPACITY_FACTORS = {
        "coal": Decimal("0.50"),
        "gas_ccgt": Decimal("0.55"),
        "gas_ocgt": Decimal("0.20"),
        "nuclear": Decimal("0.90"),
        "hydro": Decimal("0.40"),
        "wind_onshore": Decimal("0.35"),
        "wind_offshore": Decimal("0.45"),
        "solar_pv": Decimal("0.25"),
        "solar_csp": Decimal("0.30"),
        "biomass": Decimal("0.60"),
        "geothermal": Decimal("0.85"),
        "battery_storage": Decimal("0.15"),
        "pumped_hydro": Decimal("0.25")
    }
    
    # Default CO2 intensity by technology (tCO2/MWh)
    DEFAULT_CO2_INTENSITY = {
        "coal": Decimal("0.95"),
        "gas_ccgt": Decimal("0.40"),
        "gas_ocgt": Decimal("0.55"),
        "nuclear": Decimal("0.012"),
        "hydro": Decimal("0.024"),
        "wind_onshore": Decimal("0.011"),
        "wind_offshore": Decimal("0.012"),
        "solar_pv": Decimal("0.041"),
        "solar_csp": Decimal("0.022"),
        "biomass": Decimal("0.23"),
        "geothermal": Decimal("0.038"),
        "battery_storage": Decimal("0"),
        "pumped_hydro": Decimal("0")
    }
    
    def __init__(self, db_session=None, cache_client=None):
        self.db = db_session
        self.cache = cache_client
    
    async def value_plant(
        self,
        plant_id: UUID,
        plant_data: Dict,
        scenario_data: Dict,
        target_years: List[int],
        discount_rate: Decimal = Decimal("0.06"),
        include_repurposing: bool = True,
        wholesale_price_forecast: Optional[Dict[int, Decimal]] = None,
        carbon_price_forecast: Optional[Dict[int, Decimal]] = None
    ) -> PowerPlantValuationResult:
        """
        Calculate power plant NPV under climate scenario.
        
        Args:
            plant_id: UUID of the plant
            plant_data: Plant details
            scenario_data: Scenario parameters
            target_years: List of years to calculate
            discount_rate: Discount rate for NPV
            include_repurposing: Whether to include repurposing options
            wholesale_price_forecast: Optional price forecasts
            carbon_price_forecast: Optional carbon price forecasts
        
        Returns:
            PowerPlantValuationResult with NPV and recommendations
        """
        # Extract plant properties
        plant_name = plant_data.get("plant_name", "Unknown Plant")
        technology_type = plant_data.get("technology_type", "coal")
        capacity_mw = Decimal(str(plant_data.get("capacity_mw", 100)))
        
        commissioning_year = plant_data.get("commissioning_year", 2000)
        retirement_year = plant_data.get("original_retirement_year", 2050)
        technical_lifetime = plant_data.get("technical_lifetime_years", 40)
        
        capacity_factor_baseline = Decimal(str(
            plant_data.get("capacity_factor_baseline") or 
            self.DEFAULT_CAPACITY_FACTORS.get(technology_type, Decimal("0.5"))
        ))
        
        co2_intensity = Decimal(str(
            plant_data.get("co2_intensity_tco2_mwh") or
            self.DEFAULT_CO2_INTENSITY.get(technology_type, Decimal("0.5"))
        ))
        
        fixed_om = Decimal(str(plant_data.get("fixed_om_cost_usd_kw_year", 25) or 25))
        variable_om = Decimal(str(plant_data.get("variable_om_cost_usd_mwh", 3) or 3))
        fuel_cost_mmbtu = Decimal(str(plant_data.get("fuel_cost_usd_mmbtu", 4) or 0))
        heat_rate = Decimal(str(plant_data.get("heat_rate_btu_kwh", 7000) or 7000))
        
        has_ccs = plant_data.get("has_ccs", False)
        
        current_year = date.today().year
        remaining_life = self._calculate_remaining_life(
            retirement_year, commissioning_year, technical_lifetime, current_year
        )
        
        # Calculate baseline NPV
        baseline_npv = await self._calculate_plant_npv(
            plant_data, scenario_data,
            use_baseline=True,
            discount_rate=discount_rate,
            wholesale_price_forecast=wholesale_price_forecast,
            carbon_price_forecast=None  # No carbon cost in baseline
        )
        
        # Calculate scenario NPV
        scenario_npv = await self._calculate_plant_npv(
            plant_data, scenario_data,
            use_baseline=False,
            discount_rate=discount_rate,
            wholesale_price_forecast=wholesale_price_forecast,
            carbon_price_forecast=carbon_price_forecast
        )
        
        npv_impact = (
            (scenario_npv - baseline_npv) / baseline_npv * 100
            if baseline_npv != 0 else Decimal("0")
        )
        
        # Find optimal retirement year
        optimal_retirement = await self._find_optimal_retirement(
            plant_data, scenario_data, discount_rate, carbon_price_forecast
        )
        
        # Calculate yearly valuations
        yearly_valuations = await self._calculate_yearly_valuations(
            plant_data, scenario_data, target_years,
            wholesale_price_forecast, carbon_price_forecast
        )
        
        # Get repurposing options
        repurposing_options = []
        if include_repurposing:
            repurposing_options = self._get_repurposing_options(plant_data)
        
        # Calculate risk score
        risk_score = self._calculate_plant_risk_score(
            npv_impact, technology_type, remaining_life, co2_intensity
        )
        
        # Generate recommendation
        recommended_action = self._generate_plant_recommendation(
            plant_data, npv_impact, optimal_retirement, repurposing_options, risk_score
        )
        
        return PowerPlantValuationResult(
            plant_id=plant_id,
            plant_name=plant_name,
            technology_type=technology_type,
            capacity_mw=capacity_mw,
            remaining_life_years=remaining_life,
            baseline_npv_usd=round(baseline_npv, 2),
            scenario_npv_usd=round(scenario_npv, 2),
            npv_impact_percent=round(npv_impact, 2),
            optimal_retirement_year=optimal_retirement.get("year"),
            early_retirement_npv_usd=optimal_retirement.get("npv"),
            yearly_valuations=yearly_valuations,
            repurposing_options=repurposing_options,
            stranding_risk_score=round(risk_score, 2),
            risk_category=self._get_risk_category(risk_score),
            recommended_action=recommended_action
        )
    
    async def _calculate_plant_npv(
        self, plant_data: Dict, scenario_data: Dict,
        use_baseline: bool, discount_rate: Decimal,
        wholesale_price_forecast: Optional[Dict[int, Decimal]] = None,
        carbon_price_forecast: Optional[Dict[int, Decimal]] = None
    ) -> Decimal:
        """Calculate plant NPV over remaining life."""
        technology_type = plant_data.get("technology_type", "coal")
        capacity_mw = Decimal(str(plant_data.get("capacity_mw", 100)))
        
        retirement_year = plant_data.get("original_retirement_year", 2050)
        commissioning_year = plant_data.get("commissioning_year", 2000)
        technical_lifetime = plant_data.get("technical_lifetime_years", 40)
        
        current_year = date.today().year
        remaining_years = self._calculate_remaining_life(
            retirement_year, commissioning_year, technical_lifetime, current_year
        )
        
        capacity_factor = Decimal(str(
            plant_data.get("capacity_factor_baseline") or
            self.DEFAULT_CAPACITY_FACTORS.get(technology_type, Decimal("0.5"))
        ))
        
        co2_intensity = Decimal(str(
            plant_data.get("co2_intensity_tco2_mwh") or
            self.DEFAULT_CO2_INTENSITY.get(technology_type, Decimal("0.5"))
        ))
        
        fixed_om = Decimal(str(plant_data.get("fixed_om_cost_usd_kw_year", 25) or 25))
        variable_om = Decimal(str(plant_data.get("variable_om_cost_usd_mwh", 3) or 3))
        fuel_cost_mmbtu = Decimal(str(plant_data.get("fuel_cost_usd_mmbtu", 4) or 0))
        heat_rate = Decimal(str(plant_data.get("heat_rate_btu_kwh", 7000) or 7000))
        
        npv = Decimal("0")
        
        for year_offset in range(remaining_years):
            year = current_year + year_offset
            
            # Adjust capacity factor under scenario
            if not use_baseline:
                cf_decline = Decimal("0.01") * year_offset  # 1% annual decline
                capacity_factor = max(capacity_factor - cf_decline, Decimal("0.1"))
            
            # Get wholesale price
            if wholesale_price_forecast and year in wholesale_price_forecast:
                price = Decimal(str(wholesale_price_forecast[year]))
            else:
                price = self._get_default_wholesale_price(year, use_baseline)
            
            # Get carbon cost
            carbon_cost = Decimal("0")
            if not use_baseline:
                if carbon_price_forecast and year in carbon_price_forecast:
                    carbon_price = Decimal(str(carbon_price_forecast[year]))
                else:
                    carbon_price = self._get_default_carbon_price(year)
                carbon_cost = co2_intensity * carbon_price
            
            # Calculate annual generation (MWh)
            hours_per_year = Decimal("8760")
            generation_mwh = capacity_mw * hours_per_year * capacity_factor
            
            # Calculate revenue
            revenue = generation_mwh * price
            
            # Calculate costs
            fixed_cost = fixed_om * capacity_mw * Decimal("1000")  # Convert MW to kW
            variable_cost = variable_om * generation_mwh
            fuel_cost = self._calculate_fuel_cost(
                generation_mwh, fuel_cost_mmbtu, heat_rate, technology_type
            )
            carbon_total = carbon_cost * generation_mwh
            
            total_cost = fixed_cost + variable_cost + fuel_cost + carbon_total
            
            cash_flow = revenue - total_cost
            discount_factor = (Decimal("1") + discount_rate) ** (year_offset + 1)
            npv += cash_flow / discount_factor
        
        return npv
    
    async def _calculate_yearly_valuations(
        self, plant_data: Dict, scenario_data: Dict,
        target_years: List[int],
        wholesale_price_forecast: Optional[Dict[int, Decimal]] = None,
        carbon_price_forecast: Optional[Dict[int, Decimal]] = None
    ) -> List[YearlyValuation]:
        """Calculate yearly valuation breakdown."""
        valuations = []
        
        technology_type = plant_data.get("technology_type", "coal")
        capacity_mw = Decimal(str(plant_data.get("capacity_mw", 100)))
        
        capacity_factor = Decimal(str(
            plant_data.get("capacity_factor_baseline") or
            self.DEFAULT_CAPACITY_FACTORS.get(technology_type, Decimal("0.5"))
        ))
        
        co2_intensity = Decimal(str(
            plant_data.get("co2_intensity_tco2_mwh") or
            self.DEFAULT_CO2_INTENSITY.get(technology_type, Decimal("0.5"))
        ))
        
        fixed_om = Decimal(str(plant_data.get("fixed_om_cost_usd_kw_year", 25) or 25))
        variable_om = Decimal(str(plant_data.get("variable_om_cost_usd_mwh", 3) or 3))
        fuel_cost_mmbtu = Decimal(str(plant_data.get("fuel_cost_usd_mmbtu", 4) or 0))
        heat_rate = Decimal(str(plant_data.get("heat_rate_btu_kwh", 7000) or 7000))
        
        current_year = date.today().year
        
        for year in target_years:
            year_offset = year - current_year
            cf_decline = Decimal("0.01") * year_offset
            adj_cf = max(capacity_factor - cf_decline, Decimal("0.1"))
            
            # Get prices
            if wholesale_price_forecast and year in wholesale_price_forecast:
                price = Decimal(str(wholesale_price_forecast[year]))
            else:
                price = self._get_default_wholesale_price(year, False)
            
            if carbon_price_forecast and year in carbon_price_forecast:
                carbon_price = Decimal(str(carbon_price_forecast[year]))
            else:
                carbon_price = self._get_default_carbon_price(year)
            
            carbon_cost_mwh = co2_intensity * carbon_price
            
            # Calculate generation
            hours_per_year = Decimal("8760")
            generation_mwh = capacity_mw * hours_per_year * adj_cf
            
            # Calculate components
            revenue = generation_mwh * price
            opex = (fixed_om * capacity_mw * Decimal("1000")) + (variable_om * generation_mwh)
            fuel = self._calculate_fuel_cost(generation_mwh, fuel_cost_mmbtu, heat_rate, technology_type)
            ebitda = revenue - opex - fuel - (carbon_cost_mwh * generation_mwh)
            
            valuations.append(YearlyValuation(
                year=year,
                capacity_factor=round(adj_cf, 4),
                wholesale_price_usd_mwh=round(price, 2),
                carbon_cost_usd_mwh=round(carbon_cost_mwh, 2),
                revenue_usd=round(revenue, 2),
                opex_usd=round(opex, 2),
                fuel_cost_usd=round(fuel, 2),
                ebitda_usd=round(ebitda, 2)
            ))
        
        return valuations
    
    async def _find_optimal_retirement(
        self, plant_data: Dict, scenario_data: Dict,
        discount_rate: Decimal,
        carbon_price_forecast: Optional[Dict[int, Decimal]] = None
    ) -> Dict:
        """Find optimal retirement year."""
        retirement_year = plant_data.get("original_retirement_year", 2050)
        current_year = date.today().year
        
        best_npv = Decimal("-999999999999")
        best_year = retirement_year
        
        for test_year in range(current_year + 1, retirement_year + 1):
            # Temporarily adjust retirement year
            test_data = plant_data.copy()
            test_data["original_retirement_year"] = test_year
            
            npv = await self._calculate_plant_npv(
                test_data, scenario_data,
                use_baseline=False,
                discount_rate=discount_rate,
                carbon_price_forecast=carbon_price_forecast
            )
            
            if npv > best_npv:
                best_npv = npv
                best_year = test_year
        
        return {"year": best_year, "npv": round(best_npv, 2)}
    
    def _calculate_remaining_life(
        self, retirement_year: int, commissioning_year: int,
        technical_lifetime: int, current_year: int
    ) -> int:
        """Calculate remaining operational years."""
        if retirement_year:
            return max(0, retirement_year - current_year)
        elif commissioning_year and technical_lifetime:
            expected_retirement = commissioning_year + technical_lifetime
            return max(0, expected_retirement - current_year)
        return 20  # Default
    
    def _calculate_fuel_cost(
        self, generation_mwh: Decimal, fuel_cost_mmbtu: Decimal,
        heat_rate: Decimal, technology_type: str
    ) -> Decimal:
        """Calculate annual fuel cost."""
        # Only thermal plants have fuel costs
        thermal_types = ["coal", "gas_ccgt", "gas_ocgt", "biomass"]
        if technology_type not in thermal_types:
            return Decimal("0")
        
        if fuel_cost_mmbtu and heat_rate:
            # Convert heat rate from Btu/kWh to MMBtu/MWh
            mmbtu_per_mwh = heat_rate / Decimal("1000")
            return generation_mwh * mmbtu_per_mwh * fuel_cost_mmbtu
        return Decimal("0")
    
    def _get_default_wholesale_price(self, year: int, use_baseline: bool) -> Decimal:
        """Get default wholesale electricity price."""
        base_price = Decimal("50")  # USD/MWh
        
        if use_baseline:
            # Slight increase
            annual_increase = Decimal("0.01")
        else:
            # Price pressure from renewables
            annual_decrease = Decimal("0.005")
            return base_price * ((Decimal("1") - annual_decrease) ** (year - 2025))
        
        return base_price * ((Decimal("1") + annual_increase) ** (year - 2025))
    
    def _get_default_carbon_price(self, year: int) -> Decimal:
        """Get default carbon price."""
        base_price = Decimal("85")
        annual_increase = Decimal("8")
        return base_price + (annual_increase * (year - 2025))
    
    def _get_repurposing_options(self, plant_data: Dict) -> List[RepurposingOption]:
        """Get repurposing options for plant."""
        options = []
        technology_type = plant_data.get("technology_type", "")
        capacity_mw = Decimal(str(plant_data.get("capacity_mw", 100)))
        
        # CCS option for fossil plants
        if technology_type in ["coal", "gas_ccgt", "gas_ocgt"]:
            options.append(RepurposingOption(
                option_type="ccs",
                capital_cost_usd=capacity_mw * Decimal("1000000"),  # ~$1M/MW
                annual_savings_usd=capacity_mw * Decimal("50000"),
                payback_years=Decimal("20"),
                npv_impact_usd=capacity_mw * Decimal("200000"),
                feasibility_score=Decimal("0.7")
            ))
        
        # Hydrogen blending for gas plants
        if technology_type in ["gas_ccgt", "gas_ocgt"]:
            options.append(RepurposingOption(
                option_type="hydrogen",
                capital_cost_usd=capacity_mw * Decimal("200000"),
                annual_savings_usd=capacity_mw * Decimal("30000"),
                payback_years=Decimal("6.7"),
                npv_impact_usd=capacity_mw * Decimal("100000"),
                feasibility_score=Decimal("0.8")
            ))
        
        # Battery storage for any plant site
        options.append(RepurposingOption(
            option_type="storage",
            capital_cost_usd=capacity_mw * Decimal("300000"),
            annual_savings_usd=capacity_mw * Decimal("40000"),
            payback_years=Decimal("7.5"),
            npv_impact_usd=capacity_mw * Decimal("150000"),
            feasibility_score=Decimal("0.9")
        ))
        
        # Retirement option
        options.append(RepurposingOption(
            option_type="retirement",
            capital_cost_usd=capacity_mw * Decimal("50000"),  # Decommissioning cost
            annual_savings_usd=Decimal("0"),
            payback_years=Decimal("0"),
            npv_impact_usd=Decimal("0") - (capacity_mw * Decimal("50000")),
            feasibility_score=Decimal("1.0")
        ))
        
        return options
    
    def _calculate_plant_risk_score(
        self, npv_impact: Decimal, technology_type: str,
        remaining_life: int, co2_intensity: Decimal
    ) -> Decimal:
        """Calculate plant stranding risk score."""
        # Technology risk weights
        tech_risk = {
            "coal": Decimal("0.9"),
            "gas_ocgt": Decimal("0.6"),
            "gas_ccgt": Decimal("0.5"),
            "nuclear": Decimal("0.3"),
            "biomass": Decimal("0.4"),
            "geothermal": Decimal("0.2"),
            "hydro": Decimal("0.1"),
            "wind_onshore": Decimal("0.1"),
            "wind_offshore": Decimal("0.1"),
            "solar_pv": Decimal("0.1"),
            "solar_csp": Decimal("0.15"),
            "battery_storage": Decimal("0.05"),
            "pumped_hydro": Decimal("0.05")
        }.get(technology_type, Decimal("0.5"))
        
        # NPV impact factor
        npv_factor = min(abs(npv_impact) / Decimal("100"), Decimal("1"))
        
        # Remaining life factor (longer life = higher risk)
        life_factor = min(Decimal(str(remaining_life)) / Decimal("30"), Decimal("1"))
        
        # CO2 intensity factor
        co2_factor = min(co2_intensity / Decimal("1"), Decimal("1"))
        
        # Weighted combination
        score = (
            Decimal("0.3") * tech_risk +
            Decimal("0.3") * npv_factor +
            Decimal("0.2") * life_factor +
            Decimal("0.2") * co2_factor
        )
        
        return min(score, Decimal("1"))
    
    def _get_risk_category(self, risk_score: Decimal) -> RiskCategory:
        """Convert risk score to category."""
        if risk_score < Decimal("0.25"):
            return RiskCategory.LOW
        elif risk_score < Decimal("0.5"):
            return RiskCategory.MEDIUM
        elif risk_score < Decimal("0.75"):
            return RiskCategory.HIGH
        else:
            return RiskCategory.CRITICAL
    
    def _generate_plant_recommendation(
        self, plant_data: Dict, npv_impact: Decimal,
        optimal_retirement: Dict, repurposing_options: List[RepurposingOption],
        risk_score: Decimal
    ) -> str:
        """Generate recommended action."""
        technology_type = plant_data.get("technology_type", "")
        
        if risk_score >= Decimal("0.75"):
            return f"CRITICAL: Accelerate retirement to {optimal_retirement.get('year')}"
        elif npv_impact < Decimal("-50"):
            return f"Consider early retirement by {optimal_retirement.get('year')}"
        elif npv_impact < Decimal("-20"):
            # Find best repurposing option
            if repurposing_options:
                best_option = max(repurposing_options, key=lambda x: float(x.feasibility_score))
                return f"Evaluate {best_option.option_type} repurposing (feasibility: {best_option.feasibility_score})"
            return "Evaluate repurposing options"
        elif technology_type in ["coal"]:
            return "Plan phase-out strategy with timeline"
        else:
            return "Continue operations with enhanced monitoring"


# ==================== INFRASTRUCTURE VALUATOR ====================

class InfrastructureValuator:
    """Value infrastructure assets under transition scenarios."""
    
    def __init__(self, db_session=None, cache_client=None):
        self.db = db_session
        self.cache = cache_client
    
    async def value_infrastructure(
        self,
        asset_id: UUID,
        asset_data: Dict,
        scenario_data: Dict,
        target_years: List[int],
        discount_rate: Decimal = Decimal("0.07"),
        demand_forecast: Optional[Dict[int, Decimal]] = None
    ) -> InfrastructureValuationResult:
        """
        Calculate infrastructure asset valuation under climate scenario.
        """
        asset_name = asset_data.get("asset_name", "Unknown Asset")
        asset_type = asset_data.get("asset_type", "pipeline_gas")
        
        utilization_rate = Decimal(str(asset_data.get("utilization_rate_percent", 80) or 80))
        book_value = Decimal(str(asset_data.get("remaining_book_value_usd", 0) or 0))
        replacement_cost = Decimal(str(asset_data.get("replacement_cost_usd", 0) or 0))
        take_or_pay = Decimal(str(asset_data.get("take_or_pay_exposure_usd", 0) or 0))
        
        hydrogen_ready = asset_data.get("hydrogen_ready", False)
        ammonia_ready = asset_data.get("ammonia_ready", False)
        ccs_compatible = asset_data.get("ccs_compatible", False)
        
        retirement_year = asset_data.get("expected_retirement_year", 2050)
        current_year = date.today().year
        remaining_years = max(retirement_year - current_year, 1)
        
        # Calculate baseline NPV
        baseline_npv = self._calculate_baseline_npv(
            utilization_rate, book_value, remaining_years, discount_rate
        )
        
        # Calculate scenario NPV with utilization decline
        utilization_decline = self._calculate_utilization_decline(
            asset_type, scenario_data, target_years[-1] if target_years else 2040
        )
        
        scenario_npv = self._calculate_scenario_npv(
            utilization_rate, utilization_decline, book_value,
            remaining_years, discount_rate
        )
        
        npv_impact = (
            (scenario_npv - baseline_npv) / baseline_npv * 100
            if baseline_npv > 0 else Decimal("0")
        )
        
        stranded_value = max(baseline_npv - scenario_npv, Decimal("0"))
        
        # Calculate contract exposure at risk
        contract_at_risk = take_or_pay * (utilization_decline / Decimal("100"))
        
        # Calculate risk score
        risk_score = self._calculate_infra_risk_score(
            asset_type, utilization_decline, npv_impact,
            hydrogen_ready, ammonia_ready, ccs_compatible
        )
        
        return InfrastructureValuationResult(
            asset_id=asset_id,
            asset_name=asset_name,
            asset_type=asset_type,
            baseline_npv_usd=round(baseline_npv, 2),
            scenario_npv_usd=round(scenario_npv, 2),
            npv_impact_percent=round(npv_impact, 2),
            stranded_value_usd=round(stranded_value, 2),
            utilization_decline_percent=round(utilization_decline, 2),
            contract_exposure_at_risk_usd=round(contract_at_risk, 2),
            stranding_risk_score=round(risk_score, 2),
            risk_category=self._get_risk_category(risk_score),
            transition_readiness={
                "hydrogen_ready": hydrogen_ready,
                "ammonia_ready": ammonia_ready,
                "ccs_compatible": ccs_compatible
            },
            recommended_action=self._generate_infra_recommendation(
                asset_type, risk_score, hydrogen_ready, ammonia_ready, ccs_compatible
            )
        )
    
    def _calculate_baseline_npv(
        self, utilization: Decimal, book_value: Decimal,
        years: int, discount_rate: Decimal
    ) -> Decimal:
        """Calculate baseline NPV from current operations."""
        if book_value <= 0 or years <= 0:
            return Decimal("0")
        
        # Assume annual revenue proportional to book value and utilization
        annual_revenue = book_value * Decimal("0.15") * (utilization / Decimal("100"))
        
        npv = Decimal("0")
        for t in range(1, years + 1):
            npv += annual_revenue / ((Decimal("1") + discount_rate) ** t)
        
        return npv
    
    def _calculate_utilization_decline(
        self, asset_type: str, scenario_data: Dict, target_year: int
    ) -> Decimal:
        """Calculate utilization decline under scenario."""
        # Default decline rates by asset type
        decline_rates = {
            "pipeline_oil": Decimal("40"),
            "pipeline_gas": Decimal("30"),
            "lng_terminal": Decimal("25"),
            "refinery": Decimal("45"),
            "storage_facility": Decimal("20"),
            "petrochemical_plant": Decimal("35")
        }
        
        base_decline = decline_rates.get(asset_type, Decimal("30"))
        
        # Adjust for scenario severity
        scenario_factor = Decimal(str(scenario_data.get("transition_severity", 1.0)))
        
        return min(base_decline * scenario_factor, Decimal("80"))
    
    def _calculate_scenario_npv(
        self, current_util: Decimal, decline: Decimal,
        book_value: Decimal, years: int, discount_rate: Decimal
    ) -> Decimal:
        """Calculate NPV under transition scenario."""
        if book_value <= 0 or years <= 0:
            return Decimal("0")
        
        npv = Decimal("0")
        for t in range(1, years + 1):
            # Linear decline in utilization
            year_util = current_util - (decline * t / years)
            year_util = max(year_util, Decimal("10"))  # Minimum 10%
            
            annual_revenue = book_value * Decimal("0.15") * (year_util / Decimal("100"))
            npv += annual_revenue / ((Decimal("1") + discount_rate) ** t)
        
        return npv
    
    def _calculate_infra_risk_score(
        self, asset_type: str, utilization_decline: Decimal, npv_impact: Decimal,
        hydrogen_ready: bool, ammonia_ready: bool, ccs_compatible: bool
    ) -> Decimal:
        """Calculate infrastructure risk score."""
        # Base risk by type
        type_risk = {
            "pipeline_oil": Decimal("0.7"),
            "pipeline_gas": Decimal("0.5"),
            "lng_terminal": Decimal("0.45"),
            "refinery": Decimal("0.75"),
            "storage_facility": Decimal("0.4"),
            "petrochemical_plant": Decimal("0.6")
        }.get(asset_type, Decimal("0.5"))
        
        # Utilization impact
        util_factor = utilization_decline / Decimal("100")
        
        # NPV impact
        npv_factor = min(abs(npv_impact) / Decimal("100"), Decimal("1"))
        
        # Transition readiness reduces risk
        readiness_factor = Decimal("1")
        if hydrogen_ready:
            readiness_factor -= Decimal("0.15")
        if ammonia_ready:
            readiness_factor -= Decimal("0.1")
        if ccs_compatible:
            readiness_factor -= Decimal("0.1")
        
        score = (
            Decimal("0.3") * type_risk +
            Decimal("0.3") * util_factor +
            Decimal("0.2") * npv_factor
        ) * readiness_factor + Decimal("0.2") * (Decimal("1") - readiness_factor)
        
        return min(max(score, Decimal("0")), Decimal("1"))
    
    def _get_risk_category(self, risk_score: Decimal) -> RiskCategory:
        """Convert risk score to category."""
        if risk_score < Decimal("0.25"):
            return RiskCategory.LOW
        elif risk_score < Decimal("0.5"):
            return RiskCategory.MEDIUM
        elif risk_score < Decimal("0.75"):
            return RiskCategory.HIGH
        else:
            return RiskCategory.CRITICAL
    
    def _generate_infra_recommendation(
        self, asset_type: str, risk_score: Decimal,
        hydrogen_ready: bool, ammonia_ready: bool, ccs_compatible: bool
    ) -> str:
        """Generate recommendation for infrastructure."""
        if risk_score >= Decimal("0.75"):
            return "CRITICAL: Evaluate divestment or accelerated depreciation"
        elif risk_score >= Decimal("0.5"):
            if not hydrogen_ready and asset_type in ["pipeline_gas", "lng_terminal"]:
                return "HIGH: Invest in hydrogen readiness conversion"
            return "HIGH: Develop transition strategy with timeline"
        elif risk_score >= Decimal("0.25"):
            if not any([hydrogen_ready, ammonia_ready, ccs_compatible]):
                return "MEDIUM: Assess feasibility of future-fuel compatibility"
            return "MEDIUM: Monitor utilization trends and contract renewals"
        else:
            return "LOW: Continue standard asset management"


# ==================== TECHNOLOGY DISRUPTION TRACKER ====================

class TechnologyDisruptionTracker:
    """Track technology disruption metrics (EVs, heat pumps, hydrogen)."""
    
    # Regional EV saturation levels
    REGIONAL_EV_SATURATION = {
        "global": Decimal("0.8"),
        "europe": Decimal("0.95"),
        "china": Decimal("0.9"),
        "us": Decimal("0.75"),
        "india": Decimal("0.6"),
        "japan": Decimal("0.8"),
        "korea": Decimal("0.85")
    }
    
    # Regional vehicle stock (millions)
    VEHICLE_STOCK = {
        "global": Decimal("1400"),
        "europe": Decimal("250"),
        "china": Decimal("300"),
        "us": Decimal("280"),
        "india": Decimal("50"),
        "japan": Decimal("78")
    }
    
    # Building stock (millions)
    BUILDING_STOCK = {
        "global": Decimal("2000"),
        "europe": Decimal("220"),
        "china": Decimal("600"),
        "us": Decimal("140"),
        "japan": Decimal("60")
    }
    
    def __init__(self, db_session=None, cache_client=None):
        self.db = db_session
        self.cache = cache_client
    
    def ev_adoption_s_curve(
        self, year: int, region: str = "global",
        saturation: Optional[Decimal] = None,
        midpoint: int = 2030,
        steepness: Decimal = Decimal("0.3")
    ) -> Decimal:
        """
        Logistic S-curve for EV adoption.
        
        Formula: saturation / (1 + exp(-steepness * (year - midpoint)))
        
        Args:
            year: Target year
            region: Geographic region
            saturation: Maximum adoption rate (defaults to regional value)
            midpoint: Year of 50% adoption
            steepness: Curve steepness parameter
        
        Returns:
            Adoption rate as decimal (0-1)
        """
        if saturation is None:
            saturation = self.REGIONAL_EV_SATURATION.get(
                region.lower(), Decimal("0.8")
            )
        
        exponent = float(-steepness * (year - midpoint))
        
        # Handle extreme values to avoid overflow
        if exponent > 100:
            adoption = Decimal("0")
        elif exponent < -100:
            adoption = saturation
        else:
            adoption = saturation / (Decimal("1") + Decimal(str(math.exp(exponent))))
        
        return min(adoption, saturation)
    
    def calculate_oil_displacement(
        self, year: int, region: str = "global"
    ) -> Dict:
        """
        Calculate oil displacement from EV adoption.
        
        Returns:
            Dict with ev_sales_share, oil_displacement_kbpd, vehicle_stock
        """
        ev_share = self.ev_adoption_s_curve(year, region)
        
        # Get regional vehicle stock (in millions)
        vehicle_stock = self.VEHICLE_STOCK.get(region.lower(), Decimal("1400"))
        
        # Average ICE vehicle uses ~15 barrels/year = ~0.041 barrels/day
        # EV penetration displaces this consumption
        barrels_per_vehicle_day = Decimal("0.041")
        
        # Oil displacement in kbpd (thousand barrels per day)
        ev_vehicles_millions = vehicle_stock * ev_share
        oil_displacement_kbpd = ev_vehicles_millions * barrels_per_vehicle_day * Decimal("1000") / Decimal("1000")
        
        return {
            "year": year,
            "region": region,
            "ev_sales_share_percent": round(ev_share * 100, 2),
            "ev_stock_millions": round(ev_vehicles_millions, 2),
            "oil_displacement_kbpd": round(oil_displacement_kbpd, 2),
            "total_vehicle_stock_millions": round(vehicle_stock, 2)
        }
    
    def heat_pump_adoption_curve(
        self, year: int, region: str = "global",
        saturation: Decimal = Decimal("0.7"),
        midpoint: int = 2035,
        steepness: Decimal = Decimal("0.25")
    ) -> Decimal:
        """
        S-curve for heat pump adoption in buildings.
        
        Args:
            year: Target year
            region: Geographic region
            saturation: Maximum adoption (70% default)
            midpoint: Year of 50% adoption
            steepness: Curve steepness
        
        Returns:
            Adoption rate as decimal
        """
        return self.ev_adoption_s_curve(year, region, saturation, midpoint, steepness)
    
    def calculate_gas_displacement(
        self, year: int, region: str = "global"
    ) -> Dict:
        """
        Calculate gas displacement from heat pump adoption.
        
        Returns:
            Dict with heat_pump_share, gas_displacement_bcm
        """
        hp_share = self.heat_pump_adoption_curve(year, region)
        
        # Get building stock (in millions)
        building_stock = self.BUILDING_STOCK.get(region.lower(), Decimal("2000"))
        
        # Average gas heating: ~1000 m3/year per building
        # Heat pumps displace this
        gas_per_building_m3 = Decimal("1000")
        
        # Gas displacement in BCM (billion cubic meters)
        hp_buildings = building_stock * hp_share
        gas_displacement_bcm = hp_buildings * gas_per_building_m3 / Decimal("1000000000") * Decimal("1000000")
        
        return {
            "year": year,
            "region": region,
            "heat_pump_share_percent": round(hp_share * 100, 2),
            "heat_pump_buildings_millions": round(hp_buildings, 2),
            "gas_displacement_bcm": round(gas_displacement_bcm, 4),
            "total_building_stock_millions": round(building_stock, 2)
        }
    
    def green_hydrogen_cost_curve(
        self, year: int, region: str = "global"
    ) -> Dict:
        """
        Project green hydrogen cost trajectory.
        
        Uses learning curve: 15% cost reduction per doubling of capacity.
        
        Returns:
            Dict with costs, premium, and competitive timeline
        """
        # Base parameters (2025)
        base_year = 2025
        base_cost = Decimal("6.0")  # $/kg
        base_capacity_gw = Decimal("1")
        learning_rate = Decimal("0.15")  # 15% reduction per doubling
        
        # Projected capacity growth (doubling every 3 years)
        years_from_base = year - base_year
        doublings = Decimal(str(years_from_base / 3))
        
        projected_capacity_gw = base_capacity_gw * (Decimal("2") ** doublings)
        
        # Cost reduction from learning
        cost_factor = (Decimal("1") - learning_rate) ** doublings
        projected_cost = base_cost * cost_factor
        
        # Grey hydrogen benchmark (natural gas + SMR)
        grey_hydrogen_cost = Decimal("2.0")  # $/kg
        
        # Blue hydrogen (grey + CCS)
        blue_hydrogen_cost = Decimal("3.0")  # $/kg
        
        # Calculate competitiveness
        premium_vs_grey = ((projected_cost / grey_hydrogen_cost) - 1) * 100
        premium_vs_blue = ((projected_cost / blue_hydrogen_cost) - 1) * 100
        
        # Find competitive year (when green < blue * 1.1)
        competitive_year = base_year
        test_cost = base_cost
        for test_year in range(base_year, 2060):
            test_doublings = Decimal(str((test_year - base_year) / 3))
            test_cost = base_cost * ((Decimal("1") - learning_rate) ** test_doublings)
            if test_cost <= blue_hydrogen_cost * Decimal("1.1"):
                competitive_year = test_year
                break
        
        return {
            "year": year,
            "region": region,
            "green_hydrogen_cost_usd_kg": round(projected_cost, 2),
            "grey_hydrogen_cost_usd_kg": grey_hydrogen_cost,
            "blue_hydrogen_cost_usd_kg": blue_hydrogen_cost,
            "cost_premium_vs_grey_percent": round(premium_vs_grey, 1),
            "cost_premium_vs_blue_percent": round(premium_vs_blue, 1),
            "projected_capacity_gw": round(projected_capacity_gw, 1),
            "competitive_with_blue_year": competitive_year,
            "is_competitive_with_blue": projected_cost <= blue_hydrogen_cost * Decimal("1.1")
        }
    
    def battery_cost_curve(
        self, year: int, chemistry: str = "lithium_ion"
    ) -> Dict:
        """
        Project battery cost trajectory.
        
        Uses learning curve with ~18% reduction per doubling.
        """
        base_year = 2025
        base_costs = {
            "lithium_ion": Decimal("140"),  # $/kWh
            "sodium_ion": Decimal("100"),
            "solid_state": Decimal("300")
        }
        
        base_cost = base_costs.get(chemistry, Decimal("140"))
        learning_rate = Decimal("0.18")
        
        years_from_base = year - base_year
        doublings = Decimal(str(years_from_base / 2.5))  # Faster doubling for batteries
        
        projected_cost = base_cost * ((Decimal("1") - learning_rate) ** doublings)
        
        # Grid parity benchmark
        grid_parity_cost = Decimal("80")  # $/kWh
        
        return {
            "year": year,
            "chemistry": chemistry,
            "battery_cost_usd_kwh": round(projected_cost, 2),
            "grid_parity_cost_usd_kwh": grid_parity_cost,
            "at_grid_parity": projected_cost <= grid_parity_cost,
            "cost_decline_percent": round((1 - projected_cost / base_cost) * 100, 1)
        }
    
    def get_disruption_summary(
        self, year: int, region: str = "global"
    ) -> TechnologyDisruptionSummary:
        """
        Get comprehensive technology disruption summary for a year.
        """
        ev_data = self.calculate_oil_displacement(year, region)
        hp_data = self.calculate_gas_displacement(year, region)
        h2_data = self.green_hydrogen_cost_curve(year, region)
        battery_data = self.battery_cost_curve(year)
        
        # Build chart data for visualization
        chart_data = []
        for y in range(2025, 2051, 5):
            ev = self.calculate_oil_displacement(y, region)
            hp = self.calculate_gas_displacement(y, region)
            h2 = self.green_hydrogen_cost_curve(y, region)
            
            chart_data.append({
                "year": y,
                "ev_share": ev["ev_sales_share_percent"],
                "heat_pump_share": hp["heat_pump_share_percent"],
                "green_h2_cost": float(h2["green_hydrogen_cost_usd_kg"]),
                "oil_displacement_kbpd": float(ev["oil_displacement_kbpd"]),
                "gas_displacement_bcm": float(hp["gas_displacement_bcm"])
            })
        
        return TechnologyDisruptionSummary(
            metric_type="technology_disruption_composite",
            region=region,
            scenario_name="central",
            current_value=Decimal(str(ev_data["ev_sales_share_percent"])),
            current_year=year,
            projected_2030=self.ev_adoption_s_curve(2030, region) * 100,
            projected_2040=self.ev_adoption_s_curve(2040, region) * 100,
            projected_2050=self.ev_adoption_s_curve(2050, region) * 100,
            unit="percent",
            growth_rate_cagr=self._calculate_cagr(
                self.ev_adoption_s_curve(2025, region),
                self.ev_adoption_s_curve(2050, region),
                25
            ),
            chart_data=chart_data
        )
    
    def _calculate_cagr(
        self, start_value: Decimal, end_value: Decimal, years: int
    ) -> Decimal:
        """Calculate Compound Annual Growth Rate."""
        if start_value <= 0 or years <= 0:
            return Decimal("0")
        
        ratio = end_value / start_value
        cagr = (Decimal(str(float(ratio) ** (1 / years))) - 1) * 100
        return round(cagr, 2)


# ==================== PORTFOLIO STRANDING ANALYZER ====================

class PortfolioStrandingAnalyzer:
    """Analyze portfolio-level stranding risk."""
    
    def __init__(self, db_session=None):
        self.db = db_session
        self.reserve_calculator = ReserveImpairmentCalculator(db_session)
        self.plant_valuator = PowerPlantValuator(db_session)
        self.infra_valuator = InfrastructureValuator(db_session)
    
    async def analyze_portfolio(
        self,
        portfolio_id: UUID,
        portfolio_name: str,
        reserves: List[Dict],
        plants: List[Dict],
        infrastructure: List[Dict],
        scenario_data: Dict,
        target_year: int = 2040
    ) -> Dict:
        """
        Comprehensive portfolio stranding analysis.
        """
        target_years = [2030, target_year, 2050]
        
        # Analyze reserves
        reserve_results = []
        for reserve in reserves:
            result = await self.reserve_calculator.calculate_impairment(
                reserve_id=reserve.get("id", uuid.uuid4()),
                reserve_data=reserve,
                scenario_data=scenario_data,
                target_years=target_years
            )
            reserve_results.append(result)
        
        # Analyze plants
        plant_results = []
        for plant in plants:
            result = await self.plant_valuator.value_plant(
                plant_id=plant.get("id", uuid.uuid4()),
                plant_data=plant,
                scenario_data=scenario_data,
                target_years=target_years
            )
            plant_results.append(result)
        
        # Analyze infrastructure
        infra_results = []
        for asset in infrastructure:
            result = await self.infra_valuator.value_infrastructure(
                asset_id=asset.get("id", uuid.uuid4()),
                asset_data=asset,
                scenario_data=scenario_data,
                target_years=target_years
            )
            infra_results.append(result)
        
        # Aggregate results
        total_baseline = sum(
            [Decimal(str(r.baseline_npv_usd)) for r in reserve_results] +
            [Decimal(str(p.baseline_npv_usd)) for p in plant_results] +
            [Decimal(str(i.baseline_npv_usd)) for i in infra_results]
        )
        
        total_scenario = sum(
            [Decimal(str(r.scenario_npv_usd)) for r in reserve_results] +
            [Decimal(str(p.scenario_npv_usd)) for p in plant_results] +
            [Decimal(str(i.scenario_npv_usd)) for i in infra_results]
        )
        
        total_stranded = sum(
            [Decimal(str(r.total_stranded_value_usd)) for r in reserve_results] +
            [max(Decimal(str(p.baseline_npv_usd)) - Decimal(str(p.scenario_npv_usd)), Decimal("0")) for p in plant_results] +
            [Decimal(str(i.stranded_value_usd)) for i in infra_results]
        )
        
        # Risk distribution
        all_scores = (
            [r.stranding_risk_score for r in reserve_results] +
            [p.stranding_risk_score for p in plant_results] +
            [i.stranding_risk_score for i in infra_results]
        )
        
        risk_distribution = {
            "low": sum(1 for s in all_scores if s < Decimal("0.25")),
            "medium": sum(1 for s in all_scores if Decimal("0.25") <= s < Decimal("0.5")),
            "high": sum(1 for s in all_scores if Decimal("0.5") <= s < Decimal("0.75")),
            "critical": sum(1 for s in all_scores if s >= Decimal("0.75"))
        }
        
        avg_risk = sum(all_scores) / len(all_scores) if all_scores else Decimal("0")
        
        # Top risk assets
        all_results = (
            [(r, "reserve", r.stranding_risk_score) for r in reserve_results] +
            [(p, "plant", p.stranding_risk_score) for p in plant_results] +
            [(i, "infrastructure", i.stranding_risk_score) for i in infra_results]
        )
        
        top_risks = sorted(all_results, key=lambda x: x[2], reverse=True)[:5]
        top_risk_assets = [
            {
                "asset_name": r[0].asset_name if hasattr(r[0], 'asset_name') else r[0].plant_name,
                "asset_type": r[1],
                "risk_score": float(r[2]),
                "risk_category": str(r[0].risk_category.value)
            }
            for r in top_risks
        ]
        
        return {
            "portfolio_id": str(portfolio_id),
            "portfolio_name": portfolio_name,
            "scenario_id": str(scenario_data.get("id", "")),
            "scenario_name": scenario_data.get("name", "Unknown"),
            "target_year": target_year,
            "total_assets_analyzed": len(reserves) + len(plants) + len(infrastructure),
            "total_baseline_npv_usd": round(total_baseline, 2),
            "total_scenario_npv_usd": round(total_scenario, 2),
            "total_npv_impact_usd": round(total_scenario - total_baseline, 2),
            "total_npv_impact_percent": round(
                (total_scenario - total_baseline) / total_baseline * 100 if total_baseline > 0 else Decimal("0"), 2
            ),
            "total_stranded_value_usd": round(total_stranded, 2),
            "avg_stranding_risk_score": round(avg_risk, 2),
            "risk_distribution": risk_distribution,
            "asset_breakdown": {
                "reserves": {
                    "count": len(reserves),
                    "total_stranded_usd": round(sum(Decimal(str(r.total_stranded_value_usd)) for r in reserve_results), 2)
                },
                "plants": {
                    "count": len(plants),
                    "total_capacity_mw": sum(Decimal(str(p.capacity_mw)) for p in plant_results)
                },
                "infrastructure": {
                    "count": len(infrastructure),
                    "total_stranded_usd": round(sum(Decimal(str(i.stranded_value_usd)) for i in infra_results), 2)
                }
            },
            "top_risk_assets": top_risk_assets,
            "recommendations": self._generate_portfolio_recommendations(
                avg_risk, risk_distribution, top_risk_assets
            )
        }
    
    def _generate_portfolio_recommendations(
        self, avg_risk: Decimal, risk_distribution: Dict, top_risks: List[Dict]
    ) -> List[str]:
        """Generate portfolio-level recommendations."""
        recommendations = []
        
        critical_count = risk_distribution.get("critical", 0)
        high_count = risk_distribution.get("high", 0)
        
        if critical_count > 0:
            recommendations.append(
                f"URGENT: {critical_count} assets at critical stranding risk - prioritize immediate review"
            )
        
        if high_count > 0:
            recommendations.append(
                f"HIGH PRIORITY: {high_count} assets at high stranding risk - develop transition plans"
            )
        
        if avg_risk >= Decimal("0.5"):
            recommendations.append(
                "Portfolio-wide: Consider strategic reallocation to lower-carbon assets"
            )
        
        # Asset-specific recommendations
        for asset in top_risks[:3]:
            recommendations.append(
                f"Review {asset['asset_name']} ({asset['asset_type']}): {asset['risk_category']} risk"
            )
        
        if not recommendations:
            recommendations.append("Portfolio risk profile within acceptable bounds - continue monitoring")
        
        return recommendations
