"""
Carbon Credits Calculation Engine
Handles carbon credit calculations, risk adjustments, and projections.
"""

import numpy as np
from typing import List, Dict, Optional, Any
from datetime import datetime, timezone


class CarbonCalculationEngine:
    """Engine for calculating carbon credit metrics and projections."""
    
    # Quality rating to score mapping
    QUALITY_SCORES = {
        "AAA": 5.0, "AA": 4.5, "A": 4.0,
        "BBB": 3.0, "BB": 2.5, "B": 2.0, "CCC": 1.0
    }
    
    # Score to rating mapping
    SCORE_TO_RATING = [
        (4.5, "AAA"), (4.0, "AA"), (3.5, "A"),
        (2.5, "BBB"), (2.0, "BB"), (1.5, "B"), (0, "CCC")
    ]
    
    # Project type risk factors
    PROJECT_TYPE_RISKS = {
        "RENEWABLE_ENERGY": {"permanence": 0.05, "delivery": 0.05, "additionality": 0.10},
        "FOREST_CONSERVATION": {"permanence": 0.20, "delivery": 0.10, "additionality": 0.05},
        "AFFORESTATION": {"permanence": 0.15, "delivery": 0.08, "additionality": 0.08},
        "METHANE_CAPTURE": {"permanence": 0.05, "delivery": 0.10, "additionality": 0.05},
        "COOKSTOVES": {"permanence": 0.02, "delivery": 0.15, "additionality": 0.10},
        "BLUE_CARBON": {"permanence": 0.18, "delivery": 0.12, "additionality": 0.05},
        "SOIL_CARBON": {"permanence": 0.25, "delivery": 0.10, "additionality": 0.08},
        "DIRECT_AIR_CAPTURE": {"permanence": 0.02, "delivery": 0.20, "additionality": 0.02},
        "BIOCHAR": {"permanence": 0.08, "delivery": 0.12, "additionality": 0.05},
        "OTHER": {"permanence": 0.15, "delivery": 0.15, "additionality": 0.10}
    }
    
    # Country risk factors (sample - would be more comprehensive in production)
    COUNTRY_RISKS = {
        "US": 0.02, "CA": 0.02, "GB": 0.03, "DE": 0.03, "FR": 0.03,
        "AU": 0.04, "JP": 0.03, "CN": 0.08, "IN": 0.10, "BR": 0.12,
        "ID": 0.12, "KE": 0.15, "NG": 0.18, "DEFAULT": 0.10
    }
    
    def __init__(
        self,
        n_simulations: int = 10000,
        random_seed: Optional[int] = None
    ):
        self.n_simulations = n_simulations
        if random_seed:
            np.random.seed(random_seed)
    
    def calculate_project_risk(
        self,
        project_type: str,
        country_code: str,
        quality_rating: Optional[str] = None,
        custom_risks: Optional[Dict[str, float]] = None
    ) -> Dict[str, float]:
        """Calculate risk factors for a single project."""
        
        # Get base risks from project type
        type_risks = self.PROJECT_TYPE_RISKS.get(
            project_type, 
            self.PROJECT_TYPE_RISKS["OTHER"]
        )
        
        # Get country risk
        country_risk = self.COUNTRY_RISKS.get(
            country_code, 
            self.COUNTRY_RISKS["DEFAULT"]
        )
        
        # Quality adjustment (better quality = lower risk)
        quality_score = self.QUALITY_SCORES.get(quality_rating, 3.0) if quality_rating else 3.0
        quality_multiplier = 1.0 + (3.0 - quality_score) * 0.05  # Higher quality = lower risk
        
        # Calculate individual risks
        permanence_risk = type_risks["permanence"] * quality_multiplier
        delivery_risk = type_risks["delivery"] * quality_multiplier + country_risk * 0.5
        regulatory_risk = country_risk
        market_risk = 0.10  # Base market volatility
        
        # Apply custom overrides if provided
        if custom_risks:
            permanence_risk = custom_risks.get("permanence_risk", permanence_risk)
            delivery_risk = custom_risks.get("delivery_risk", delivery_risk)
            regulatory_risk = custom_risks.get("regulatory_risk", regulatory_risk)
            market_risk = custom_risks.get("market_risk", market_risk)
        
        total_risk = permanence_risk + delivery_risk + regulatory_risk + market_risk
        
        return {
            "permanence_risk": round(permanence_risk * 100, 2),
            "delivery_risk": round(delivery_risk * 100, 2),
            "regulatory_risk": round(regulatory_risk * 100, 2),
            "market_risk": round(market_risk * 100, 2),
            "total_risk_pct": round(total_risk * 100, 2)
        }
    
    def calculate_risk_adjusted_credits(
        self,
        annual_credits: float,
        risk_breakdown: Dict[str, float]
    ) -> float:
        """Calculate risk-adjusted credit amount."""
        total_risk_pct = risk_breakdown["total_risk_pct"]
        risk_discount = total_risk_pct / 100
        return annual_credits * (1 - risk_discount)
    
    def calculate_npv(
        self,
        annual_credits: float,
        price_per_credit: float,
        years: int = 10,
        discount_rate: float = 0.08,
        price_growth_rate: float = 0.05
    ) -> float:
        """Calculate Net Present Value of carbon credits over time."""
        # Handle None values with defaults
        if price_per_credit is None:
            price_per_credit = 15.0  # Default carbon price
        if annual_credits is None:
            annual_credits = 0
        
        npv = 0.0
        for year in range(1, years + 1):
            future_price = price_per_credit * ((1 + price_growth_rate) ** year)
            annual_value = annual_credits * future_price
            discounted_value = annual_value / ((1 + discount_rate) ** year)
            npv += discounted_value
        return round(npv, 2)
    
    def calculate_quality_score(
        self,
        additionality_score: Optional[float] = None,
        permanence_score: Optional[float] = None,
        co_benefits_score: Optional[float] = None,
        verification_status: str = "unverified"
    ) -> tuple[float, str]:
        """Calculate overall quality score and rating for a project."""
        
        # Default scores if not provided
        additionality = additionality_score if additionality_score is not None else 3.0
        permanence = permanence_score if permanence_score is not None else 3.0
        co_benefits = co_benefits_score if co_benefits_score is not None else 3.0
        
        # Verification bonus
        verification_bonus = 0.5 if verification_status == "verified" else 0
        
        # Weighted average
        score = (additionality * 0.4 + permanence * 0.35 + co_benefits * 0.25) + verification_bonus
        score = min(5.0, max(1.0, score))
        
        # Get rating from score
        rating = "CCC"
        for threshold, r in self.SCORE_TO_RATING:
            if score >= threshold:
                rating = r
                break
        
        return round(score, 2), rating
    
    def generate_yearly_projections(
        self,
        total_annual_credits: float,
        risk_adjusted_credits: float,
        years: int = 10,
        optimistic_factor: float = 1.15,
        pessimistic_factor: float = 0.85
    ) -> List[Dict[str, Any]]:
        """Generate yearly credit projections."""
        projections = []
        current_year = datetime.now().year
        
        for i in range(years):
            year = current_year + i
            # Add some variance over time
            time_factor = 1.0 + (i * 0.02)  # Slight increase over time
            
            base = total_annual_credits * time_factor
            optimistic = base * optimistic_factor
            pessimistic = base * pessimistic_factor
            risk_adj = risk_adjusted_credits * time_factor
            
            projections.append({
                "year": year,
                "base_case": round(base, 0),
                "optimistic": round(optimistic, 0),
                "pessimistic": round(pessimistic, 0),
                "risk_adjusted": round(risk_adj, 0)
            })
        
        return projections
    
    def run_monte_carlo(
        self,
        projects: List[Dict[str, Any]],
        scenario: Dict[str, Any],
        n_runs: Optional[int] = None
    ) -> Dict[str, Any]:
        """Run Monte Carlo simulation for portfolio."""
        n = n_runs or self.n_simulations
        
        # Extract parameters
        permanence_risk = scenario.get("permanence_risk_pct", 10) / 100
        delivery_risk = scenario.get("delivery_risk_pct", 5) / 100
        price_volatility = scenario.get("price_volatility_pct", 20) / 100
        base_price = scenario.get("base_carbon_price_usd", 15)
        
        # Calculate base portfolio credits
        total_credits = sum(p.get("annual_credits", 0) for p in projects)
        
        # Run simulations
        results = []
        for _ in range(n):
            # Random risk adjustments
            perm_adj = np.random.normal(1 - permanence_risk, permanence_risk * 0.5)
            del_adj = np.random.normal(1 - delivery_risk, delivery_risk * 0.5)
            price_adj = np.random.normal(1, price_volatility)
            
            # Clip to reasonable bounds
            perm_adj = np.clip(perm_adj, 0.5, 1.2)
            del_adj = np.clip(del_adj, 0.5, 1.2)
            price_adj = np.clip(price_adj, 0.5, 1.5)
            
            simulated_credits = total_credits * perm_adj * del_adj
            simulated_value = simulated_credits * base_price * price_adj
            results.append(simulated_value)
        
        results = np.array(results)
        
        return {
            "mean": round(float(np.mean(results)), 2),
            "std": round(float(np.std(results)), 2),
            "confidence_interval_low": round(float(np.percentile(results, 5)), 2),
            "confidence_interval_high": round(float(np.percentile(results, 95)), 2),
            "median": round(float(np.median(results)), 2),
            "min": round(float(np.min(results)), 2),
            "max": round(float(np.max(results)), 2)
        }
    
    def calculate_portfolio(
        self,
        projects: List[Dict[str, Any]],
        scenario: Optional[Dict[str, Any]] = None,
        run_monte_carlo: bool = False
    ) -> Dict[str, Any]:
        """Calculate portfolio-level metrics."""
        
        if not projects:
            return {
                "total_annual_credits": 0,
                "total_risk_adjusted_credits": 0,
                "portfolio_quality_score": 0,
                "portfolio_quality_rating": "N/A",
                "portfolio_npv_10yr_usd": 0,
                "project_results": [],
                "risk_breakdown": {
                    "permanence_risk": 0,
                    "delivery_risk": 0,
                    "regulatory_risk": 0,
                    "market_risk": 0,
                    "total_risk_pct": 0
                },
                "yearly_projections": self.generate_yearly_projections(0, 0, years=10)
            }
        
        # Default scenario if not provided
        if not scenario:
            scenario = {
                "permanence_risk_pct": 10,
                "delivery_risk_pct": 5,
                "regulatory_risk_pct": 5,
                "market_risk_pct": 10,
                "base_carbon_price_usd": 15,
                "price_growth_rate_pct": 5,
                "discount_rate_pct": 8,
                "projection_years": 10
            }
        
        project_results = []
        total_credits = 0
        total_risk_adjusted = 0
        total_quality_weighted = 0
        total_npv = 0
        
        agg_risks = {"permanence": 0, "delivery": 0, "regulatory": 0, "market": 0}
        
        for proj in projects:
            annual_credits = proj.get("annual_credits", 0)
            
            # Calculate project-level risk
            risk_breakdown = self.calculate_project_risk(
                project_type=proj.get("project_type", "OTHER"),
                country_code=proj.get("country_code", "DEFAULT"),
                quality_rating=proj.get("quality_rating"),
                custom_risks=proj.get("custom_risk_adjustments")
            )
            
            # Risk-adjusted credits
            risk_adjusted = self.calculate_risk_adjusted_credits(
                annual_credits, risk_breakdown
            )
            
            # Quality score
            quality_score, quality_rating = self.calculate_quality_score(
                additionality_score=proj.get("additionality_score"),
                permanence_score=proj.get("permanence_score"),
                co_benefits_score=proj.get("co_benefits_score"),
                verification_status=proj.get("verification_status", "unverified")
            )
            
            # NPV
            price_per_credit = proj.get("price_per_credit_usd", scenario["base_carbon_price_usd"])
            npv = self.calculate_npv(
                annual_credits=risk_adjusted,
                price_per_credit=price_per_credit,
                years=scenario.get("projection_years", 10),
                discount_rate=scenario.get("discount_rate_pct", 8) / 100,
                price_growth_rate=scenario.get("price_growth_rate_pct", 5) / 100
            )
            
            project_results.append({
                "project_id": proj.get("id", ""),
                "project_name": proj.get("name", "Unknown"),
                "annual_credits": annual_credits,
                "risk_adjusted_credits": round(risk_adjusted, 2),
                "risk_discount_pct": risk_breakdown["total_risk_pct"],
                "quality_score": quality_score,
                "quality_rating": quality_rating,
                "npv_usd": npv
            })
            
            total_credits += annual_credits
            total_risk_adjusted += risk_adjusted
            total_quality_weighted += quality_score * annual_credits
            total_npv += npv
            
            # Aggregate risks (weighted by credits)
            if annual_credits > 0:
                weight = annual_credits
                agg_risks["permanence"] += risk_breakdown["permanence_risk"] * weight
                agg_risks["delivery"] += risk_breakdown["delivery_risk"] * weight
                agg_risks["regulatory"] += risk_breakdown["regulatory_risk"] * weight
                agg_risks["market"] += risk_breakdown["market_risk"] * weight
        
        # Calculate portfolio averages
        if total_credits > 0:
            avg_quality = total_quality_weighted / total_credits
            portfolio_risk = {
                "permanence_risk": round(agg_risks["permanence"] / total_credits, 2),
                "delivery_risk": round(agg_risks["delivery"] / total_credits, 2),
                "regulatory_risk": round(agg_risks["regulatory"] / total_credits, 2),
                "market_risk": round(agg_risks["market"] / total_credits, 2),
            }
            portfolio_risk["total_risk_pct"] = round(
                portfolio_risk["permanence_risk"] + portfolio_risk["delivery_risk"] +
                portfolio_risk["regulatory_risk"] + portfolio_risk["market_risk"], 2
            )
        else:
            avg_quality = 0
            portfolio_risk = {
                "permanence_risk": 0, "delivery_risk": 0, "regulatory_risk": 0,
                "market_risk": 0, "total_risk_pct": 0
            }
        
        _, portfolio_rating = self.calculate_quality_score(
            additionality_score=avg_quality,
            permanence_score=avg_quality,
            co_benefits_score=avg_quality
        )
        
        result = {
            "total_annual_credits": round(total_credits, 2),
            "total_risk_adjusted_credits": round(total_risk_adjusted, 2),
            "portfolio_quality_score": round(avg_quality, 2),
            "portfolio_quality_rating": portfolio_rating,
            "portfolio_npv_10yr_usd": round(total_npv, 2),
            "project_results": project_results,
            "risk_breakdown": portfolio_risk,
            "yearly_projections": self.generate_yearly_projections(
                total_credits, total_risk_adjusted,
                years=scenario.get("projection_years", 10)
            )
        }
        
        # Add Monte Carlo results if requested
        if run_monte_carlo:
            mc_results = self.run_monte_carlo(projects, scenario)
            result["monte_carlo"] = mc_results
            result["confidence_interval_low"] = mc_results["confidence_interval_low"]
            result["confidence_interval_high"] = mc_results["confidence_interval_high"]
        
        return result
