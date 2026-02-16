"""
Real Estate Valuation Engine
Implements three traditional valuation approaches:
- Income Approach (Direct Capitalization and DCF)
- Cost Approach (Replacement Cost)
- Sales Comparison Approach
"""

from decimal import Decimal, ROUND_HALF_UP
from typing import List, Dict, Optional, Any
from datetime import datetime, date
import statistics
import math

from schemas.real_estate_valuation import (
    PropertyType, QualityRating, ConditionRating, ConstructionType,
    DirectCapitalizationRequest, DirectCapitalizationResult,
    DCFRequest, DCFResult, DCFProjectionYear,
    ReplacementCostRequest, ReplacementCostResult,
    SubjectProperty, ComparableProperty,
    SalesComparisonRequest, SalesComparisonResult,
    AdjustedComparable, AdjustmentDetail,
    ComprehensiveValuationRequest, ComprehensiveValuationResult,
    ReconciliationResult, ApproachWeights,
)


class CostDataService:
    """
    Construction cost data service based on RS Means and Marshall & Swift.
    Provides base construction costs by type and quality.
    """
    
    # Base construction costs per SF (2024 national average USD)
    CONSTRUCTION_COSTS = {
        ConstructionType.STEEL_FRAME: {
            QualityRating.CLASS_A: Decimal("350"),
            QualityRating.CLASS_B: Decimal("280"),
            QualityRating.CLASS_C: Decimal("220"),
        },
        ConstructionType.CONCRETE: {
            QualityRating.CLASS_A: Decimal("380"),
            QualityRating.CLASS_B: Decimal("300"),
            QualityRating.CLASS_C: Decimal("240"),
        },
        ConstructionType.MASONRY: {
            QualityRating.CLASS_A: Decimal("300"),
            QualityRating.CLASS_B: Decimal("240"),
            QualityRating.CLASS_C: Decimal("190"),
        },
        ConstructionType.WOOD_FRAME: {
            QualityRating.CLASS_A: Decimal("250"),
            QualityRating.CLASS_B: Decimal("200"),
            QualityRating.CLASS_C: Decimal("160"),
        },
        ConstructionType.PREFABRICATED: {
            QualityRating.CLASS_A: Decimal("220"),
            QualityRating.CLASS_B: Decimal("175"),
            QualityRating.CLASS_C: Decimal("140"),
        },
        ConstructionType.MIXED: {
            QualityRating.CLASS_A: Decimal("320"),
            QualityRating.CLASS_B: Decimal("260"),
            QualityRating.CLASS_C: Decimal("200"),
        },
    }
    
    # Regional location factors (national average = 1.0)
    LOCATION_FACTORS = {
        "new_york": Decimal("1.35"),
        "san_francisco": Decimal("1.32"),
        "los_angeles": Decimal("1.20"),
        "chicago": Decimal("1.15"),
        "seattle": Decimal("1.18"),
        "boston": Decimal("1.25"),
        "miami": Decimal("1.05"),
        "houston": Decimal("0.95"),
        "dallas": Decimal("0.92"),
        "phoenix": Decimal("0.90"),
        "atlanta": Decimal("0.95"),
        "denver": Decimal("1.02"),
        "national_average": Decimal("1.00"),
    }
    
    def get_construction_cost(
        self, 
        construction_type: ConstructionType, 
        quality: QualityRating
    ) -> Decimal:
        """Get base construction cost per SF."""
        return self.CONSTRUCTION_COSTS.get(construction_type, {}).get(
            quality, Decimal("250")
        )
    
    def get_location_factor(self, location: str) -> Decimal:
        """Get location adjustment factor."""
        return self.LOCATION_FACTORS.get(
            location.lower().replace(" ", "_"), 
            Decimal("1.00")
        )


class MarketDataService:
    """
    Market data service for cap rates and market comparisons.
    """
    
    # Market cap rates by property type and quality
    MARKET_CAP_RATES = {
        PropertyType.OFFICE: {
            QualityRating.CLASS_A: {"low": Decimal("0.055"), "mid": Decimal("0.065"), "high": Decimal("0.075")},
            QualityRating.CLASS_B: {"low": Decimal("0.065"), "mid": Decimal("0.075"), "high": Decimal("0.090")},
            QualityRating.CLASS_C: {"low": Decimal("0.080"), "mid": Decimal("0.090"), "high": Decimal("0.110")},
        },
        PropertyType.RETAIL: {
            QualityRating.CLASS_A: {"low": Decimal("0.050"), "mid": Decimal("0.060"), "high": Decimal("0.070")},
            QualityRating.CLASS_B: {"low": Decimal("0.060"), "mid": Decimal("0.070"), "high": Decimal("0.085")},
            QualityRating.CLASS_C: {"low": Decimal("0.075"), "mid": Decimal("0.085"), "high": Decimal("0.100")},
        },
        PropertyType.INDUSTRIAL: {
            QualityRating.CLASS_A: {"low": Decimal("0.045"), "mid": Decimal("0.055"), "high": Decimal("0.065")},
            QualityRating.CLASS_B: {"low": Decimal("0.055"), "mid": Decimal("0.065"), "high": Decimal("0.075")},
            QualityRating.CLASS_C: {"low": Decimal("0.065"), "mid": Decimal("0.075"), "high": Decimal("0.090")},
        },
        PropertyType.MULTIFAMILY: {
            QualityRating.CLASS_A: {"low": Decimal("0.040"), "mid": Decimal("0.050"), "high": Decimal("0.060")},
            QualityRating.CLASS_B: {"low": Decimal("0.050"), "mid": Decimal("0.060"), "high": Decimal("0.070")},
            QualityRating.CLASS_C: {"low": Decimal("0.060"), "mid": Decimal("0.070"), "high": Decimal("0.085")},
        },
        PropertyType.HOTEL: {
            QualityRating.CLASS_A: {"low": Decimal("0.070"), "mid": Decimal("0.080"), "high": Decimal("0.095")},
            QualityRating.CLASS_B: {"low": Decimal("0.080"), "mid": Decimal("0.095"), "high": Decimal("0.110")},
            QualityRating.CLASS_C: {"low": Decimal("0.095"), "mid": Decimal("0.110"), "high": Decimal("0.130")},
        },
    }
    
    # Location quality adjustments
    LOCATION_ADJUSTMENTS = {
        "cbd_prime": Decimal("0.10"),
        "cbd": Decimal("0.05"),
        "urban": Decimal("0.0"),
        "suburban": Decimal("-0.03"),
        "rural": Decimal("-0.08"),
    }
    
    def get_cap_rate(
        self, 
        property_type: PropertyType, 
        quality: QualityRating,
        tier: str = "mid"
    ) -> Decimal:
        """Get market cap rate for property type and quality."""
        type_rates = self.MARKET_CAP_RATES.get(
            property_type, 
            self.MARKET_CAP_RATES[PropertyType.OFFICE]
        )
        quality_rates = type_rates.get(quality, type_rates[QualityRating.CLASS_B])
        return quality_rates.get(tier, quality_rates["mid"])
    
    def get_location_adjustment(
        self, 
        subject_location: str, 
        comp_location: str
    ) -> Decimal:
        """Calculate location adjustment between subject and comparable."""
        subject_adj = self.LOCATION_ADJUSTMENTS.get(
            subject_location.lower(), Decimal("0")
        )
        comp_adj = self.LOCATION_ADJUSTMENTS.get(
            comp_location.lower(), Decimal("0")
        )
        return subject_adj - comp_adj


class RealEstateValuationEngine:
    """
    Main valuation engine implementing all three approaches.
    """
    
    def __init__(self):
        self.cost_service = CostDataService()
        self.market_service = MarketDataService()
    
    def income_approach_direct_cap(
        self, 
        inputs: DirectCapitalizationRequest
    ) -> DirectCapitalizationResult:
        """
        Calculate property value using direct capitalization method.
        
        Formula: Value = NOI / Cap Rate
        
        Where NOI = EGI - Operating Expenses
        And EGI = PGI - Vacancy Loss - Collection Loss
        """
        # Calculate Potential Gross Income
        rental_income = inputs.rentable_area_sf * inputs.market_rent_per_sf
        pgi = rental_income + inputs.other_income
        
        # Calculate Vacancy and Collection Loss
        vacancy_loss = pgi * inputs.vacancy_rate
        collection_loss = pgi * inputs.collection_loss_rate
        
        # Calculate Effective Gross Income
        egi = pgi - vacancy_loss - collection_loss
        
        # Calculate Operating Expenses
        expense_breakdown = {}
        if inputs.expense_details:
            operating_expenses = (
                inputs.expense_details.property_taxes +
                inputs.expense_details.insurance +
                inputs.expense_details.utilities +
                inputs.expense_details.maintenance +
                inputs.expense_details.management +
                inputs.expense_details.reserves +
                inputs.expense_details.other
            )
            expense_breakdown = {
                "property_taxes": inputs.expense_details.property_taxes,
                "insurance": inputs.expense_details.insurance,
                "utilities": inputs.expense_details.utilities,
                "maintenance": inputs.expense_details.maintenance,
                "management": inputs.expense_details.management,
                "reserves": inputs.expense_details.reserves,
                "other": inputs.expense_details.other,
            }
        elif inputs.operating_expense_ratio:
            operating_expenses = egi * inputs.operating_expense_ratio
        else:
            # Default to 35% expense ratio
            operating_expenses = egi * Decimal("0.35")
        
        # Calculate Net Operating Income
        noi = egi - operating_expenses
        
        # Apply Capitalization Rate
        property_value = noi / inputs.cap_rate
        
        # Calculate derived metrics
        expense_ratio = operating_expenses / egi if egi > 0 else Decimal("0")
        gim = property_value / pgi if pgi > 0 else Decimal("0")
        nim = property_value / noi if noi > 0 else Decimal("0")
        
        return DirectCapitalizationResult(
            pgi=pgi.quantize(Decimal("0.01")),
            vacancy_loss=vacancy_loss.quantize(Decimal("0.01")),
            collection_loss=collection_loss.quantize(Decimal("0.01")),
            egi=egi.quantize(Decimal("0.01")),
            operating_expenses=operating_expenses.quantize(Decimal("0.01")),
            expense_breakdown=expense_breakdown if expense_breakdown else None,
            noi=noi.quantize(Decimal("0.01")),
            cap_rate=inputs.cap_rate,
            property_value=property_value.quantize(Decimal("0.01")),
            value_per_sf=(property_value / inputs.rentable_area_sf).quantize(Decimal("0.01")),
            expense_ratio=expense_ratio.quantize(Decimal("0.0001")),
            gross_income_multiplier=gim.quantize(Decimal("0.01")),
            net_income_multiplier=nim.quantize(Decimal("0.01")),
        )
    
    def income_approach_dcf(self, inputs: DCFRequest) -> DCFResult:
        """
        Calculate property value using Discounted Cash Flow analysis.
        
        Generates year-by-year projections and calculates NPV, IRR.
        """
        cash_flows = []
        cumulative = Decimal("0")
        
        # Convert all inputs to Decimal explicitly
        revenue_growth_rate = Decimal(str(inputs.revenue_growth_rate))
        expense_growth_rate = Decimal(str(inputs.expense_growth_rate))
        inflation_rate = Decimal(str(inputs.inflation_rate))
        current_noi = Decimal(str(inputs.current_noi))
        debt_service = Decimal(str(inputs.debt_service))
        terminal_growth_rate = Decimal(str(inputs.terminal_growth_rate))
        terminal_cap_rate = Decimal(str(inputs.terminal_cap_rate))
        selling_costs_pct = Decimal(str(inputs.selling_costs_percent))
        discount_rate = Decimal(str(inputs.discount_rate))
        equity_investment = Decimal(str(inputs.equity_investment))
        
        # Generate cash flow projections
        for year in range(1, inputs.projection_years + 1):
            # Revenue grows at specified rate
            revenue_growth = (Decimal("1") + revenue_growth_rate) ** year
            revenue = current_noi * Decimal("1.5") * revenue_growth  # Assume NOI is ~67% of revenue
            
            # Expenses grow with inflation
            expense_growth = (Decimal("1") + expense_growth_rate + inflation_rate) ** year
            expenses = current_noi * Decimal("0.5") * expense_growth
            
            # Calculate NOI
            noi = revenue - expenses
            
            # Cash Flow After Debt Service
            cfads = noi - debt_service
            cumulative += cfads
            
            cash_flows.append(DCFProjectionYear(
                year=year,
                revenue=revenue.quantize(Decimal("0.01")),
                expenses=expenses.quantize(Decimal("0.01")),
                noi=noi.quantize(Decimal("0.01")),
                debt_service=debt_service,
                cfads=cfads.quantize(Decimal("0.01")),
                cumulative_cash_flow=cumulative.quantize(Decimal("0.01")),
            ))
        
        # Calculate Terminal Value (Gordon Growth Model)
        final_noi = cash_flows[-1].noi
        terminal_noi = final_noi * (Decimal("1") + terminal_growth_rate)
        terminal_value = terminal_noi / terminal_cap_rate
        
        # Apply selling costs
        terminal_value_net = terminal_value * (Decimal("1") - selling_costs_pct)
        
        # Discount cash flows
        total_pv = Decimal("0")
        
        for cf in cash_flows:
            pv_factor = Decimal("1") / ((Decimal("1") + discount_rate) ** cf.year)
            total_pv += cf.cfads * pv_factor
        
        # Present value of terminal value
        terminal_pv_factor = Decimal("1") / ((Decimal("1") + discount_rate) ** inputs.projection_years)
        terminal_value_present = terminal_value_net * terminal_pv_factor
        
        # NPV
        npv = total_pv + terminal_value_present
        
        # Calculate IRR (using Newton-Raphson method)
        irr = self._calculate_irr(
            [-inputs.equity_investment] + 
            [cf.cfads for cf in cash_flows[:-1]] + 
            [cash_flows[-1].cfads + terminal_value_net]
        )
        
        # Equity Multiple
        total_return = sum(cf.cfads for cf in cash_flows) + terminal_value_net
        equity_multiple = total_return / inputs.equity_investment
        
        # Cash on Cash Returns
        cash_on_cash_year1 = cash_flows[0].cfads / inputs.equity_investment if inputs.equity_investment > 0 else Decimal("0")
        avg_annual_cfads = sum(cf.cfads for cf in cash_flows) / len(cash_flows)
        avg_cash_on_cash = avg_annual_cfads / inputs.equity_investment if inputs.equity_investment > 0 else Decimal("0")
        
        # Payback period
        payback_period = None
        cumulative_check = Decimal("0")
        for cf in cash_flows:
            cumulative_check += cf.cfads
            if cumulative_check >= inputs.equity_investment:
                payback_period = Decimal(str(cf.year))
                break
        
        # Sensitivity analysis
        sensitivity_cap = {}
        sensitivity_discount = {}
        
        for delta in [-0.01, -0.005, 0, 0.005, 0.01]:
            adj_cap = inputs.terminal_cap_rate + Decimal(str(delta))
            adj_terminal = terminal_noi / adj_cap if adj_cap > 0 else Decimal("0")
            adj_pv = adj_terminal * terminal_pv_factor
            sensitivity_cap[f"{float(adj_cap):.3f}"] = (total_pv + adj_pv).quantize(Decimal("0.01"))
            
            adj_disc = inputs.discount_rate + Decimal(str(delta))
            adj_pv_factor = Decimal("1") / ((Decimal("1") + adj_disc) ** inputs.projection_years)
            adj_npv = total_pv + terminal_value_net * adj_pv_factor
            sensitivity_discount[f"{float(adj_disc):.3f}"] = adj_npv.quantize(Decimal("0.01"))
        
        return DCFResult(
            cash_flows=cash_flows,
            terminal_value=terminal_value.quantize(Decimal("0.01")),
            terminal_value_present=terminal_value_present.quantize(Decimal("0.01")),
            total_pv_cash_flows=total_pv.quantize(Decimal("0.01")),
            npv=npv.quantize(Decimal("0.01")),
            irr=Decimal(str(irr)).quantize(Decimal("0.0001")) if irr else Decimal("0"),
            equity_multiple=equity_multiple.quantize(Decimal("0.01")),
            cash_on_cash_year1=cash_on_cash_year1.quantize(Decimal("0.0001")),
            average_cash_on_cash=avg_cash_on_cash.quantize(Decimal("0.0001")),
            payback_period_years=payback_period,
            sensitivity_cap_rate=sensitivity_cap,
            sensitivity_discount_rate=sensitivity_discount,
        )
    
    def cost_approach(self, inputs: ReplacementCostRequest) -> ReplacementCostResult:
        """
        Calculate property value using replacement cost method.
        
        Formula: Value = Land Value + (RCN - Total Depreciation)
        """
        # Calculate Land Value
        land_value = inputs.land_area_acres * inputs.land_value_per_acre
        
        # Get base construction cost
        base_cost_per_sf = self.cost_service.get_construction_cost(
            inputs.construction_type,
            inputs.quality
        )
        
        # Calculate Replacement Cost New (RCN)
        rcn_before_adj = inputs.building_area_sf * base_cost_per_sf
        rcn = rcn_before_adj * inputs.location_factor
        
        # Calculate Physical Depreciation (Age-Life Method)
        age_life_ratio = Decimal(str(inputs.effective_age)) / Decimal(str(inputs.total_economic_life))
        
        # Adjust for condition
        condition_factors = {
            ConditionRating.EXCELLENT: Decimal("0.85"),
            ConditionRating.GOOD: Decimal("1.0"),
            ConditionRating.FAIR: Decimal("1.15"),
            ConditionRating.POOR: Decimal("1.35"),
        }
        condition_factor = condition_factors.get(inputs.condition_rating, Decimal("1.0"))
        
        physical_depreciation = rcn * age_life_ratio * condition_factor
        physical_depreciation_pct = (physical_depreciation / rcn) if rcn > 0 else Decimal("0")
        
        # Calculate Functional Obsolescence
        deficiencies_total = sum((d.cost_to_cure for d in inputs.functional_deficiencies), Decimal("0"))
        superadequacies_total = sum((s.excess_cost for s in inputs.superadequacies), Decimal("0"))
        functional_obsolescence = deficiencies_total + superadequacies_total
        
        # Calculate External Obsolescence
        external_obsolescence = rcn * inputs.external_obsolescence_percent
        
        # Total Depreciation
        total_depreciation = physical_depreciation + functional_obsolescence + external_obsolescence
        total_depreciation_pct = (total_depreciation / rcn) if rcn > 0 else Decimal("0")
        
        # Depreciated Value of Improvements
        depreciated_improvements = rcn - total_depreciation
        depreciated_improvements = max(depreciated_improvements, Decimal("0"))
        
        # Total Property Value
        property_value = land_value + depreciated_improvements
        
        return ReplacementCostResult(
            land_value=land_value.quantize(Decimal("0.01")),
            base_cost_per_sf=base_cost_per_sf,
            rcn_before_adjustments=rcn_before_adj.quantize(Decimal("0.01")),
            location_factor=inputs.location_factor,
            rcn=rcn.quantize(Decimal("0.01")),
            age_life_ratio=age_life_ratio.quantize(Decimal("0.0001")),
            physical_depreciation=physical_depreciation.quantize(Decimal("0.01")),
            physical_depreciation_percent=physical_depreciation_pct.quantize(Decimal("0.0001")),
            functional_deficiencies_total=deficiencies_total.quantize(Decimal("0.01")),
            superadequacies_total=superadequacies_total.quantize(Decimal("0.01")),
            functional_obsolescence=functional_obsolescence.quantize(Decimal("0.01")),
            external_obsolescence=external_obsolescence.quantize(Decimal("0.01")),
            external_obsolescence_percent=inputs.external_obsolescence_percent,
            total_depreciation=total_depreciation.quantize(Decimal("0.01")),
            total_depreciation_percent=total_depreciation_pct.quantize(Decimal("0.0001")),
            depreciated_improvements=depreciated_improvements.quantize(Decimal("0.01")),
            property_value=property_value.quantize(Decimal("0.01")),
            value_per_sf=(property_value / inputs.building_area_sf).quantize(Decimal("0.01")),
        )
    
    def sales_comparison(
        self, 
        request: SalesComparisonRequest
    ) -> SalesComparisonResult:
        """
        Calculate property value using sales comparison approach.
        
        Adjusts comparable sales for differences with subject property.
        """
        subject = request.subject_property
        adjusted_comps = []
        
        today = date.today()
        
        for comp in request.comparables:
            adjustments = []
            
            # 1. Time Adjustment (market appreciation)
            days_since_sale = (today - comp.sale_date).days
            months_since_sale = days_since_sale / 30
            time_adj_pct = float(request.market_appreciation_rate) * months_since_sale
            time_adj = comp.sale_price * Decimal(str(time_adj_pct))
            adjustments.append(AdjustmentDetail(
                type="time",
                description=f"Market appreciation ({days_since_sale} days)",
                amount=time_adj.quantize(Decimal("0.01")),
                percentage=Decimal(str(time_adj_pct)).quantize(Decimal("0.0001")),
            ))
            
            # 2. Size Adjustment (larger properties typically have lower per-SF values)
            size_diff = float(subject.size_sf) - float(comp.size_sf)
            size_diff_pct = size_diff / float(comp.size_sf)
            # Apply diminishing returns factor (0.5)
            size_adj_pct = size_diff_pct * -0.3  # Negative because larger = lower per SF
            size_adj = comp.sale_price * Decimal(str(size_adj_pct))
            adjustments.append(AdjustmentDetail(
                type="size",
                description=f"Size differential ({size_diff:,.0f} SF)",
                amount=size_adj.quantize(Decimal("0.01")),
                percentage=Decimal(str(size_adj_pct)).quantize(Decimal("0.0001")),
            ))
            
            # 3. Age Adjustment
            age_diff = subject.year_built - comp.year_built
            age_adj_pct = age_diff * 0.005  # 0.5% per year of age difference
            age_adj = comp.sale_price * Decimal(str(age_adj_pct))
            adjustments.append(AdjustmentDetail(
                type="age",
                description=f"Age differential ({age_diff} years)",
                amount=age_adj.quantize(Decimal("0.01")),
                percentage=Decimal(str(age_adj_pct)).quantize(Decimal("0.0001")),
            ))
            
            # 4. Quality Adjustment
            quality_order = {
                QualityRating.CLASS_C: 1, 
                QualityRating.CLASS_B: 2, 
                QualityRating.CLASS_A: 3
            }
            qual_diff = quality_order.get(subject.quality, 2) - quality_order.get(comp.quality, 2)
            qual_adj_pct = qual_diff * 0.07  # 7% per quality class
            qual_adj = comp.sale_price * Decimal(str(qual_adj_pct))
            adjustments.append(AdjustmentDetail(
                type="quality",
                description=f"Quality differential ({qual_diff} classes)",
                amount=qual_adj.quantize(Decimal("0.01")),
                percentage=Decimal(str(qual_adj_pct)).quantize(Decimal("0.0001")),
            ))
            
            # 5. Condition Adjustment
            condition_order = {
                ConditionRating.POOR: 1,
                ConditionRating.FAIR: 2,
                ConditionRating.GOOD: 3,
                ConditionRating.EXCELLENT: 4,
            }
            cond_diff = condition_order.get(subject.condition, 3) - condition_order.get(comp.condition, 3)
            cond_adj_pct = cond_diff * 0.05  # 5% per condition level
            cond_adj = comp.sale_price * Decimal(str(cond_adj_pct))
            adjustments.append(AdjustmentDetail(
                type="condition",
                description=f"Condition differential ({cond_diff} levels)",
                amount=cond_adj.quantize(Decimal("0.01")),
                percentage=Decimal(str(cond_adj_pct)).quantize(Decimal("0.0001")),
            ))
            
            # 6. Location Adjustment
            loc_adj_pct = self.market_service.get_location_adjustment(
                subject.location, comp.location
            )
            loc_adj = comp.sale_price * loc_adj_pct
            adjustments.append(AdjustmentDetail(
                type="location",
                description=f"Location: {comp.location} → {subject.location}",
                amount=loc_adj.quantize(Decimal("0.01")),
                percentage=loc_adj_pct.quantize(Decimal("0.0001")),
            ))
            
            # Calculate totals
            total_adjustment = sum(adj.amount for adj in adjustments)
            total_adj_pct = sum(float(adj.percentage) for adj in adjustments)
            adjusted_price = comp.sale_price + total_adjustment
            
            # Weight based on how similar the comp is (lower adjustments = higher weight)
            abs_adj_pct = abs(total_adj_pct)
            weight = max(Decimal("0.1"), Decimal("1") - Decimal(str(abs_adj_pct)))
            
            adjusted_comps.append(AdjustedComparable(
                comp_id=comp.id,
                original_sale_price=comp.sale_price,
                sale_date=comp.sale_date,
                days_since_sale=days_since_sale,
                adjustments=adjustments,
                total_adjustment=total_adjustment.quantize(Decimal("0.01")),
                total_adjustment_percent=Decimal(str(total_adj_pct)).quantize(Decimal("0.0001")),
                adjusted_price=adjusted_price.quantize(Decimal("0.01")),
                adjusted_price_per_sf=(adjusted_price / comp.size_sf).quantize(Decimal("0.01")),
                weight=weight.quantize(Decimal("0.01")),
            ))
        
        # Statistical analysis
        prices = [float(c.adjusted_price) for c in adjusted_comps]
        weights = [float(c.weight) for c in adjusted_comps]
        
        mean_price = Decimal(str(statistics.mean(prices)))
        median_price = Decimal(str(statistics.median(prices)))
        std_dev = Decimal(str(statistics.stdev(prices))) if len(prices) > 1 else Decimal("0")
        cv = (std_dev / mean_price) if mean_price > 0 else Decimal("0")
        
        # Weighted average for reconciliation
        total_weight = sum(weights)
        weighted_sum = sum(p * w for p, w in zip(prices, weights))
        reconciled_value = Decimal(str(weighted_sum / total_weight))
        
        # Confidence range (95% CI)
        margin = Decimal("1.96") * std_dev
        conf_low = reconciled_value - margin
        conf_high = reconciled_value + margin
        
        # Determine confidence level
        if cv < Decimal("0.08"):
            confidence_level = "high"
        elif cv < Decimal("0.15"):
            confidence_level = "medium"
        else:
            confidence_level = "low"
        
        # Adjustment statistics
        gross_adj = [abs(float(c.total_adjustment_percent)) for c in adjusted_comps]
        net_adj = [float(c.total_adjustment_percent) for c in adjusted_comps]
        
        return SalesComparisonResult(
            adjusted_comparables=adjusted_comps,
            mean_adjusted_price=mean_price.quantize(Decimal("0.01")),
            median_adjusted_price=median_price.quantize(Decimal("0.01")),
            std_dev=std_dev.quantize(Decimal("0.01")),
            coefficient_of_variation=cv.quantize(Decimal("0.0001")),
            reconciled_value=reconciled_value.quantize(Decimal("0.01")),
            value_per_sf=(reconciled_value / subject.size_sf).quantize(Decimal("0.01")),
            confidence_range_low=conf_low.quantize(Decimal("0.01")),
            confidence_range_high=conf_high.quantize(Decimal("0.01")),
            confidence_level=confidence_level,
            avg_gross_adjustment_percent=Decimal(str(statistics.mean(gross_adj))).quantize(Decimal("0.0001")),
            avg_net_adjustment_percent=Decimal(str(statistics.mean(net_adj))).quantize(Decimal("0.0001")),
        )
    
    def comprehensive_valuation(
        self,
        property_data: Dict[str, Any],
        income_inputs: Optional[Dict[str, Any]] = None,
        cost_inputs: Optional[Dict[str, Any]] = None,
        comparables: Optional[List[Dict[str, Any]]] = None,
        weights: ApproachWeights = ApproachWeights(),
        include_income: bool = True,
        include_cost: bool = True,
        include_sales: bool = True,
        income_method: str = "direct_capitalization",
    ) -> ComprehensiveValuationResult:
        """
        Run comprehensive valuation using all three approaches and reconcile.
        """
        income_result = None
        dcf_result = None
        cost_result = None
        sales_result = None
        
        approach_reliability = {}
        reconciliation_notes = []
        
        # Income Approach
        if include_income and income_inputs:
            try:
                if income_method == "direct_capitalization":
                    request = DirectCapitalizationRequest(**income_inputs)
                    income_result = self.income_approach_direct_cap(request)
                    approach_reliability["income"] = "high" if income_result.noi > 0 else "low"
                else:
                    dcf_request = DCFRequest(**income_inputs)
                    dcf_result = self.income_approach_dcf(dcf_request)
                    approach_reliability["income"] = "high"
            except Exception as e:
                reconciliation_notes.append(f"Income approach error: {str(e)}")
                approach_reliability["income"] = "unavailable"
        
        # Cost Approach
        if include_cost and cost_inputs:
            try:
                request = ReplacementCostRequest(**cost_inputs)
                cost_result = self.cost_approach(request)
                # Cost approach is more reliable for newer properties
                effective_age = cost_inputs.get("effective_age", 20)
                approach_reliability["cost"] = "high" if effective_age < 10 else "medium" if effective_age < 30 else "low"
            except Exception as e:
                reconciliation_notes.append(f"Cost approach error: {str(e)}")
                approach_reliability["cost"] = "unavailable"
        
        # Sales Comparison
        if include_sales and comparables:
            try:
                subject = SubjectProperty(
                    size_sf=Decimal(str(property_data.get("rentable_area_sf", 10000))),
                    year_built=property_data.get("year_built", 2000),
                    quality=QualityRating(property_data.get("quality_rating", "class_b")),
                    condition=ConditionRating(property_data.get("condition_rating", "good")),
                    location=property_data.get("city", "urban"),
                )
                
                comp_objects = []
                from uuid import UUID
                for c in comparables:
                    comp_objects.append(ComparableProperty(
                        id=UUID(c["id"]) if isinstance(c["id"], str) else c["id"],
                        sale_price=Decimal(str(c["sale_price"])),
                        sale_date=c["sale_date"] if isinstance(c["sale_date"], date) else date.fromisoformat(c["sale_date"]),
                        size_sf=Decimal(str(c["size_sf"])),
                        year_built=c["year_built"],
                        quality=QualityRating(c.get("quality", "class_b")),
                        condition=ConditionRating(c.get("condition", "good")),
                        location=c.get("location", "urban"),
                    ))
                
                request = SalesComparisonRequest(
                    subject_property=subject,
                    comparables=comp_objects,
                )
                sales_result = self.sales_comparison(request)
                approach_reliability["sales"] = sales_result.confidence_level
            except Exception as e:
                reconciliation_notes.append(f"Sales comparison error: {str(e)}")
                approach_reliability["sales"] = "unavailable"
        
        # Reconciliation
        values = {}
        active_weights = {}
        
        if income_result:
            values["income"] = income_result.property_value
            active_weights["income"] = weights.income
        elif dcf_result:
            values["income"] = dcf_result.npv
            active_weights["income"] = weights.income
        
        if cost_result:
            values["cost"] = cost_result.property_value
            active_weights["cost"] = weights.cost
        
        if sales_result:
            values["sales"] = sales_result.reconciled_value
            active_weights["sales"] = weights.sales
        
        # Normalize weights if some approaches are missing
        total_weight = sum(active_weights.values())
        if total_weight > 0:
            for k in active_weights:
                active_weights[k] = active_weights[k] / total_weight
        
        # Calculate reconciled value
        reconciled_value = sum(
            values.get(k, Decimal("0")) * active_weights.get(k, Decimal("0"))
            for k in values
        )
        
        # Determine confidence level
        num_approaches = len([v for v in values.values() if v > 0])
        if num_approaches >= 3:
            overall_confidence = "high"
        elif num_approaches == 2:
            overall_confidence = "medium"
        else:
            overall_confidence = "low"
        
        # Value range
        if values:
            min_val = min(values.values())
            max_val = max(values.values())
            value_range = f"${float(min_val):,.0f} - ${float(max_val):,.0f}"
        else:
            value_range = "N/A"
        
        # Calculate value per SF
        rentable_sf = Decimal(str(property_data.get("rentable_area_sf", 10000)))
        value_per_sf = reconciled_value / rentable_sf if rentable_sf > 0 else Decimal("0")
        
        return ComprehensiveValuationResult(
            property_id=property_data.get("id"),
            valuation_date=date.today(),
            income_approach=income_result,
            dcf_analysis=dcf_result,
            cost_approach=cost_result,
            sales_comparison=sales_result,
            reconciliation=ReconciliationResult(
                income_value=values.get("income"),
                cost_value=values.get("cost"),
                sales_value=values.get("sales"),
                income_weight=active_weights.get("income", Decimal("0")),
                cost_weight=active_weights.get("cost", Decimal("0")),
                sales_weight=active_weights.get("sales", Decimal("0")),
                reconciled_value=reconciled_value.quantize(Decimal("0.01")),
                approach_reliability=approach_reliability,
                reconciliation_notes=reconciliation_notes,
            ),
            final_value=reconciled_value.quantize(Decimal("0.01")),
            value_per_sf=value_per_sf.quantize(Decimal("0.01")),
            value_range=value_range,
            confidence_level=overall_confidence,
        )
    
    def _calculate_irr(self, cash_flows: List[Decimal], max_iterations: int = 100) -> Optional[float]:
        """
        Calculate Internal Rate of Return using Newton-Raphson method.
        """
        if not cash_flows or len(cash_flows) < 2:
            return None
        
        flows = [float(cf) for cf in cash_flows]
        
        # Initial guess
        irr = 0.1
        
        for _ in range(max_iterations):
            npv = sum(cf / ((1 + irr) ** i) for i, cf in enumerate(flows))
            npv_derivative = sum(-i * cf / ((1 + irr) ** (i + 1)) for i, cf in enumerate(flows))
            
            if abs(npv_derivative) < 1e-10:
                break
            
            irr_new = irr - npv / npv_derivative
            
            if abs(irr_new - irr) < 1e-7:
                return irr_new
            
            irr = irr_new
            
            # Bounds check
            if irr < -0.99 or irr > 10:
                return None
        
        return irr if -0.99 < irr < 10 else None
