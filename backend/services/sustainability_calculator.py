"""
Sustainability Frameworks Calculation Engine
Analyzes value impact of green building certifications: GRESB, LEED, BREEAM, etc.

Data sources:
- GRESB Real Estate Assessment Reference Guide
- USGBC LEED Rating System documentation
- BRE Global BREEAM Technical Standards
- Academic research: Eichholtz et al. (2010, 2013), Fuerst & McAllister (2011)
- Industry reports: JLL, CBRE, Cushman & Wakefield
"""

from decimal import Decimal
from typing import Dict, List, Optional, Any
from datetime import date
from uuid import UUID, uuid4

from schemas.sustainability import (
    CertificationType, LEEDLevel, BREEAMLevel, GRESBRating,
    PropertySector, Region,
    GRESBAssessmentRequest, GRESBAssessmentResult, GRESBBenchmark, GRESBComponentScore,
    LEEDAssessmentRequest, LEEDAssessmentResult, LEEDCategoryScore,
    BREEAMAssessmentRequest, BREEAMAssessmentResult, BREEAMCategoryScore, BREEAMWeights,
    CertificationValueImpactRequest, CertificationValueImpactResult,
    PortfolioSustainabilityRequest, PortfolioSustainabilityResult,
    CertificationBenchmarkData,
)


# ============ Benchmark Data (from research) ============

# Rent premium percentages by certification type and level
# Sources: Eichholtz et al., Fuerst & McAllister, JLL Green Building Research
RENT_PREMIUMS = {
    CertificationType.LEED: {
        LEEDLevel.CERTIFIED: {"low": Decimal("2.0"), "mid": Decimal("4.0"), "high": Decimal("6.0")},
        LEEDLevel.SILVER: {"low": Decimal("4.0"), "mid": Decimal("6.0"), "high": Decimal("8.0")},
        LEEDLevel.GOLD: {"low": Decimal("6.0"), "mid": Decimal("9.0"), "high": Decimal("12.0")},
        LEEDLevel.PLATINUM: {"low": Decimal("10.0"), "mid": Decimal("15.0"), "high": Decimal("20.0")},
    },
    CertificationType.BREEAM: {
        BREEAMLevel.PASS: {"low": Decimal("1.0"), "mid": Decimal("2.5"), "high": Decimal("4.0")},
        BREEAMLevel.GOOD: {"low": Decimal("3.0"), "mid": Decimal("5.0"), "high": Decimal("7.0")},
        BREEAMLevel.VERY_GOOD: {"low": Decimal("5.0"), "mid": Decimal("7.5"), "high": Decimal("10.0")},
        BREEAMLevel.EXCELLENT: {"low": Decimal("8.0"), "mid": Decimal("11.0"), "high": Decimal("14.0")},
        BREEAMLevel.OUTSTANDING: {"low": Decimal("12.0"), "mid": Decimal("16.0"), "high": Decimal("20.0")},
    },
    CertificationType.ENERGY_STAR: {
        "certified": {"low": Decimal("3.0"), "mid": Decimal("5.0"), "high": Decimal("7.0")},
    },
    CertificationType.WELL: {
        "silver": {"low": Decimal("4.0"), "mid": Decimal("6.0"), "high": Decimal("8.0")},
        "gold": {"low": Decimal("6.0"), "mid": Decimal("8.0"), "high": Decimal("11.0")},
        "platinum": {"low": Decimal("8.0"), "mid": Decimal("12.0"), "high": Decimal("16.0")},
    },
}

# Value premiums (typically 1.5-2x rent premiums due to cap rate compression)
VALUE_PREMIUM_MULTIPLIER = Decimal("1.7")

# Cap rate compression by certification (basis points)
CAP_RATE_COMPRESSION = {
    CertificationType.LEED: {
        LEEDLevel.CERTIFIED: 15,
        LEEDLevel.SILVER: 25,
        LEEDLevel.GOLD: 40,
        LEEDLevel.PLATINUM: 60,
    },
    CertificationType.BREEAM: {
        BREEAMLevel.PASS: 10,
        BREEAMLevel.GOOD: 20,
        BREEAMLevel.VERY_GOOD: 35,
        BREEAMLevel.EXCELLENT: 50,
        BREEAMLevel.OUTSTANDING: 70,
    },
}

# Operating cost savings percentages
OPERATING_COST_SAVINGS = {
    CertificationType.LEED: Decimal("8.0"),  # avg 8-15% energy savings
    CertificationType.BREEAM: Decimal("7.0"),
    CertificationType.ENERGY_STAR: Decimal("10.0"),
    CertificationType.WELL: Decimal("3.0"),  # Focused on health, less on energy
}

# GRESB benchmark data by region (2024 data)
GRESB_BENCHMARKS = {
    Region.NORTH_AMERICA: {
        "peer_avg_score": Decimal("72"),
        "top_quartile_threshold": Decimal("82"),
        "bottom_quartile_threshold": Decimal("60"),
        "num_peers": 450,
    },
    Region.EUROPE: {
        "peer_avg_score": Decimal("76"),
        "top_quartile_threshold": Decimal("86"),
        "bottom_quartile_threshold": Decimal("65"),
        "num_peers": 680,
    },
    Region.ASIA_PACIFIC: {
        "peer_avg_score": Decimal("68"),
        "top_quartile_threshold": Decimal("78"),
        "bottom_quartile_threshold": Decimal("55"),
        "num_peers": 520,
    },
}

# GRESB rating thresholds
GRESB_RATING_THRESHOLDS = {
    GRESBRating.FIVE_STAR: 80,
    GRESBRating.FOUR_STAR: 60,
    GRESBRating.THREE_STAR: 40,
    GRESBRating.TWO_STAR: 20,
    GRESBRating.ONE_STAR: 0,
}

# LEED point thresholds
LEED_LEVEL_THRESHOLDS = {
    LEEDLevel.PLATINUM: 80,
    LEEDLevel.GOLD: 60,
    LEEDLevel.SILVER: 50,
    LEEDLevel.CERTIFIED: 40,
}

# BREEAM score thresholds
BREEAM_LEVEL_THRESHOLDS = {
    BREEAMLevel.OUTSTANDING: Decimal("85"),
    BREEAMLevel.EXCELLENT: Decimal("70"),
    BREEAMLevel.VERY_GOOD: Decimal("55"),
    BREEAMLevel.GOOD: Decimal("45"),
    BREEAMLevel.PASS: Decimal("30"),
}

# Regional adjustment factors for premiums
REGIONAL_ADJUSTMENTS = {
    Region.NORTH_AMERICA: Decimal("1.0"),
    Region.EUROPE: Decimal("1.1"),  # Higher premiums in Europe
    Region.ASIA_PACIFIC: Decimal("0.9"),
    Region.MIDDLE_EAST: Decimal("0.85"),
    Region.LATIN_AMERICA: Decimal("0.75"),
    Region.AFRICA: Decimal("0.7"),
}

# Sector adjustments (office typically sees highest premiums)
SECTOR_ADJUSTMENTS = {
    PropertySector.OFFICE: Decimal("1.0"),
    PropertySector.RETAIL: Decimal("0.85"),
    PropertySector.INDUSTRIAL: Decimal("0.7"),
    PropertySector.MULTIFAMILY: Decimal("0.9"),
    PropertySector.HOTEL: Decimal("0.8"),
    PropertySector.HEALTHCARE: Decimal("0.95"),
    PropertySector.DATA_CENTER: Decimal("0.6"),
    PropertySector.MIXED_USE: Decimal("0.9"),
}


class GRESBCalculator:
    """Calculator for GRESB Real Estate Assessment."""
    
    def calculate_assessment(self, request: GRESBAssessmentRequest) -> GRESBAssessmentResult:
        """Calculate GRESB score and value impact."""
        
        # Calculate total score from components
        scores = request.component_scores
        total_score = (
            scores.management +
            scores.policy +
            scores.risk_management +
            scores.stakeholder_engagement +
            scores.performance_indicators
        )
        
        # Separate management and performance scores
        management_score = scores.management + scores.policy + scores.risk_management
        performance_score = scores.stakeholder_engagement + scores.performance_indicators
        
        # Determine star rating
        star_rating = self._get_star_rating(total_score)
        
        # Get benchmark data
        benchmark_data = GRESB_BENCHMARKS.get(
            request.region, 
            GRESB_BENCHMARKS[Region.NORTH_AMERICA]
        )
        
        # Calculate percentile rank
        percentile_rank = self._calculate_percentile(total_score, benchmark_data)
        
        # Calculate value impact
        rent_premium = self._calculate_gresb_rent_premium(star_rating, request.region)
        value_premium = rent_premium * VALUE_PREMIUM_MULTIPLIER
        cap_rate_compression = self._calculate_gresb_cap_compression(star_rating)
        
        estimated_value_impact = request.total_aum * (value_premium / Decimal("100"))
        
        # Improvement analysis
        score_to_next = self._score_to_next_star(total_score, star_rating)
        recommendations = self._generate_gresb_recommendations(scores, total_score)
        priority_areas = self._identify_priority_areas(scores)
        
        # YoY change if prior data available
        yoy_change = None
        yoy_rating_change = None
        if request.prior_year_score:
            yoy_change = total_score - request.prior_year_score
            if request.prior_year_rating:
                yoy_rating_change = f"{request.prior_year_rating.value} -> {star_rating.value}"
        
        return GRESBAssessmentResult(
            total_score=total_score,
            star_rating=star_rating,
            component_scores=scores,
            management_score=management_score,
            performance_score=performance_score,
            benchmark=GRESBBenchmark(
                peer_group=f"Global {request.entity_type.replace('_', ' ').title()}",
                peer_avg_score=benchmark_data["peer_avg_score"],
                percentile_rank=percentile_rank,
                num_peers=benchmark_data["num_peers"],
                top_quartile_threshold=benchmark_data["top_quartile_threshold"],
                bottom_quartile_threshold=benchmark_data["bottom_quartile_threshold"],
            ),
            percentile_rank=percentile_rank,
            estimated_rent_premium_percent=rent_premium,
            estimated_value_premium_percent=value_premium,
            estimated_value_impact=estimated_value_impact,
            cap_rate_compression_bps=cap_rate_compression,
            score_to_next_star=score_to_next,
            improvement_recommendations=recommendations,
            priority_areas=priority_areas,
            yoy_score_change=yoy_change,
            yoy_rating_change=yoy_rating_change,
        )
    
    def _get_star_rating(self, score: Decimal) -> GRESBRating:
        """Determine GRESB star rating from score."""
        score_float = float(score)
        if score_float >= 80:
            return GRESBRating.FIVE_STAR
        elif score_float >= 60:
            return GRESBRating.FOUR_STAR
        elif score_float >= 40:
            return GRESBRating.THREE_STAR
        elif score_float >= 20:
            return GRESBRating.TWO_STAR
        else:
            return GRESBRating.ONE_STAR
    
    def _calculate_percentile(self, score: Decimal, benchmark: Dict) -> int:
        """Estimate percentile rank based on benchmark data."""
        avg = float(benchmark["peer_avg_score"])
        top_q = float(benchmark["top_quartile_threshold"])
        bottom_q = float(benchmark["bottom_quartile_threshold"])
        score_f = float(score)
        
        if score_f >= top_q:
            # Top quartile: 75-100
            return min(99, 75 + int((score_f - top_q) / (100 - top_q) * 25))
        elif score_f >= avg:
            # Above average: 50-75
            return 50 + int((score_f - avg) / (top_q - avg) * 25)
        elif score_f >= bottom_q:
            # Below average: 25-50
            return 25 + int((score_f - bottom_q) / (avg - bottom_q) * 25)
        else:
            # Bottom quartile: 0-25
            return max(1, int((score_f / bottom_q) * 25))
    
    def _calculate_gresb_rent_premium(self, rating: GRESBRating, region: Region) -> Decimal:
        """Calculate rent premium based on GRESB rating."""
        base_premiums = {
            GRESBRating.FIVE_STAR: Decimal("8.0"),
            GRESBRating.FOUR_STAR: Decimal("5.5"),
            GRESBRating.THREE_STAR: Decimal("3.5"),
            GRESBRating.TWO_STAR: Decimal("2.0"),
            GRESBRating.ONE_STAR: Decimal("0.5"),
        }
        base = base_premiums.get(rating, Decimal("0"))
        return base * REGIONAL_ADJUSTMENTS.get(region, Decimal("1.0"))
    
    def _calculate_gresb_cap_compression(self, rating: GRESBRating) -> Decimal:
        """Calculate cap rate compression in basis points."""
        compression_map = {
            GRESBRating.FIVE_STAR: Decimal("50"),
            GRESBRating.FOUR_STAR: Decimal("35"),
            GRESBRating.THREE_STAR: Decimal("20"),
            GRESBRating.TWO_STAR: Decimal("10"),
            GRESBRating.ONE_STAR: Decimal("5"),
        }
        return compression_map.get(rating, Decimal("0"))
    
    def _score_to_next_star(self, current_score: Decimal, current_rating: GRESBRating) -> Optional[Decimal]:
        """Calculate points needed for next star rating."""
        next_thresholds = {
            GRESBRating.FOUR_STAR: Decimal("80"),
            GRESBRating.THREE_STAR: Decimal("60"),
            GRESBRating.TWO_STAR: Decimal("40"),
            GRESBRating.ONE_STAR: Decimal("20"),
        }
        if current_rating == GRESBRating.FIVE_STAR:
            return None
        target = next_thresholds.get(current_rating)
        if target:
            return target - current_score
        return None
    
    def _generate_gresb_recommendations(self, scores: GRESBComponentScore, total: Decimal) -> List[str]:
        """Generate improvement recommendations."""
        recommendations = []
        
        # Check each component against targets
        if scores.management < 24:  # Target 80% of max (30)
            recommendations.append("Strengthen management systems including sustainability policies and governance structures")
        if scores.policy < 10:  # Target ~80% of max (12)
            recommendations.append("Enhance ESG policy coverage including climate risk and biodiversity commitments")
        if scores.risk_management < 11:  # Target ~80% of max (14)
            recommendations.append("Improve risk assessment processes including physical and transition climate risks")
        if scores.stakeholder_engagement < 11:  # Target ~80% of max (14)
            recommendations.append("Increase tenant and community engagement programs")
        if scores.performance_indicators < 24:  # Target 80% of max (30)
            recommendations.append("Improve data collection and reporting on energy, water, waste, and GHG emissions")
        
        if float(total) < 60:
            recommendations.append("Consider GRESB training programs to improve overall assessment approach")
        
        return recommendations[:5]  # Return top 5
    
    def _identify_priority_areas(self, scores: GRESBComponentScore) -> List[Dict[str, Any]]:
        """Identify priority improvement areas with potential points."""
        max_scores = {
            "management": 30, "policy": 12, "risk_management": 14,
            "stakeholder_engagement": 14, "performance_indicators": 30
        }
        
        areas = []
        for field, max_val in max_scores.items():
            current = float(getattr(scores, field))
            potential = max_val - current
            if potential > 3:  # Only show if significant improvement possible
                areas.append({
                    "area": field.replace("_", " ").title(),
                    "current_score": current,
                    "max_score": max_val,
                    "potential_improvement": potential,
                    "priority": "high" if potential > max_val * 0.3 else "medium",
                })
        
        return sorted(areas, key=lambda x: x["potential_improvement"], reverse=True)[:5]


class LEEDCalculator:
    """Calculator for LEED certification assessment."""
    
    def calculate_assessment(self, request: LEEDAssessmentRequest) -> LEEDAssessmentResult:
        """Calculate LEED points and value impact."""
        
        scores = request.category_scores
        total_points = (
            scores.integrative_process +
            scores.location_transportation +
            scores.sustainable_sites +
            scores.water_efficiency +
            scores.energy_atmosphere +
            scores.materials_resources +
            scores.indoor_environmental_quality +
            scores.innovation +
            scores.regional_priority
        )
        
        # Determine certification level
        cert_level = self._get_certification_level(total_points)
        
        # Points to next level
        points_to_next = self._points_to_next_level(total_points, cert_level)
        
        # Get premiums
        premiums = RENT_PREMIUMS.get(CertificationType.LEED, {}).get(cert_level, {})
        rent_premium = premiums.get("mid", Decimal("0"))
        value_premium = rent_premium * VALUE_PREMIUM_MULTIPLIER
        
        # Apply regional and sector adjustments
        regional_adj = REGIONAL_ADJUSTMENTS.get(request.region, Decimal("1.0"))
        sector_adj = SECTOR_ADJUSTMENTS.get(request.property_sector, Decimal("1.0"))
        
        rent_premium = rent_premium * regional_adj * sector_adj
        value_premium = value_premium * regional_adj * sector_adj
        
        # Calculate value impact if property value provided
        value_impact = None
        rent_impact = None
        if request.current_value:
            value_impact = request.current_value * (value_premium / Decimal("100"))
        if request.annual_rent_income:
            rent_impact = request.annual_rent_income * (rent_premium / Decimal("100"))
        
        # Category analysis
        category_analysis = self._analyze_categories(scores)
        
        return LEEDAssessmentResult(
            total_points=total_points,
            certification_level=cert_level,
            category_breakdown=scores,
            points_to_next_level=points_to_next,
            max_achievable_points=110,
            estimated_rent_premium_percent=rent_premium,
            estimated_value_premium_percent=value_premium,
            estimated_value_impact=value_impact,
            estimated_rent_premium=rent_impact,
            strongest_categories=category_analysis["strongest"],
            weakest_categories=category_analysis["weakest"],
            improvement_potential=category_analysis["potential"],
            market_avg_points=55,  # Typical market average
            percentile_in_market=self._calculate_market_percentile(total_points),
        )
    
    def _get_certification_level(self, points: int) -> LEEDLevel:
        """Determine LEED certification level from points."""
        if points >= 80:
            return LEEDLevel.PLATINUM
        elif points >= 60:
            return LEEDLevel.GOLD
        elif points >= 50:
            return LEEDLevel.SILVER
        else:
            return LEEDLevel.CERTIFIED
    
    def _points_to_next_level(self, current: int, level: LEEDLevel) -> Optional[int]:
        """Calculate points needed for next certification level."""
        next_thresholds = {
            LEEDLevel.CERTIFIED: 50,
            LEEDLevel.SILVER: 60,
            LEEDLevel.GOLD: 80,
        }
        if level == LEEDLevel.PLATINUM:
            return None
        target = next_thresholds.get(level)
        return target - current if target else None
    
    def _analyze_categories(self, scores: LEEDCategoryScore) -> Dict[str, Any]:
        """Analyze category performance."""
        max_scores = {
            "energy_atmosphere": 33,
            "location_transportation": 16,
            "indoor_environmental_quality": 16,
            "materials_resources": 13,
            "water_efficiency": 11,
            "sustainable_sites": 10,
            "innovation": 6,
            "regional_priority": 4,
            "integrative_process": 1,
        }
        
        percentages = {}
        for cat, max_val in max_scores.items():
            current = getattr(scores, cat)
            percentages[cat] = (current / max_val) * 100 if max_val > 0 else 0
        
        sorted_cats = sorted(percentages.items(), key=lambda x: x[1], reverse=True)
        
        strongest = [cat for cat, pct in sorted_cats[:3]]
        weakest = [cat for cat, pct in sorted_cats[-3:] if pct < 70]
        
        potential = {}
        for cat, max_val in max_scores.items():
            current = getattr(scores, cat)
            remaining = max_val - current
            if remaining > 2:
                potential[cat] = remaining
        
        return {
            "strongest": strongest,
            "weakest": weakest,
            "potential": potential,
        }
    
    def _calculate_market_percentile(self, points: int) -> int:
        """Estimate market percentile based on points."""
        # Distribution approximation based on USGBC data
        if points >= 80:
            return 95
        elif points >= 70:
            return 85
        elif points >= 60:
            return 70
        elif points >= 50:
            return 50
        elif points >= 40:
            return 30
        else:
            return 15


class BREEAMCalculator:
    """Calculator for BREEAM certification assessment."""
    
    def calculate_assessment(self, request: BREEAMAssessmentRequest) -> BREEAMAssessmentResult:
        """Calculate BREEAM score and value impact."""
        
        scores = request.category_scores
        weights = request.weights
        
        # Calculate weighted score
        weighted_components = {
            "management": scores.management * weights.management,
            "health_wellbeing": scores.health_wellbeing * weights.health_wellbeing,
            "energy": scores.energy * weights.energy,
            "transport": scores.transport * weights.transport,
            "water": scores.water * weights.water,
            "materials": scores.materials * weights.materials,
            "waste": scores.waste * weights.waste,
            "land_use_ecology": scores.land_use_ecology * weights.land_use_ecology,
            "pollution": scores.pollution * weights.pollution,
            "innovation": min(scores.innovation * weights.innovation, Decimal("10")),  # Innovation capped
        }
        
        weighted_score = sum(weighted_components.values())
        
        # Determine rating
        rating = self._get_rating(weighted_score)
        
        # Points to next level
        points_to_next = self._points_to_next_level(weighted_score, rating)
        
        # Get premiums
        premiums = RENT_PREMIUMS.get(CertificationType.BREEAM, {}).get(rating, {})
        rent_premium = premiums.get("mid", Decimal("0"))
        value_premium = rent_premium * VALUE_PREMIUM_MULTIPLIER
        
        # Apply adjustments
        regional_adj = REGIONAL_ADJUSTMENTS.get(request.region, Decimal("1.0"))
        sector_adj = SECTOR_ADJUSTMENTS.get(request.property_sector, Decimal("1.0"))
        
        rent_premium = rent_premium * regional_adj * sector_adj
        value_premium = value_premium * regional_adj * sector_adj
        
        # Value impact
        value_impact = None
        if request.current_value:
            value_impact = request.current_value * (value_premium / Decimal("100"))
        
        # Category analysis
        highest_performing = self._identify_highest_performing(scores)
        improvement_priorities = self._identify_improvements(scores, weights)
        
        # Regional benchmark
        regional_avg = GRESB_BENCHMARKS.get(request.region, {}).get("peer_avg_score", Decimal("55"))
        percentile = self._calculate_percentile(weighted_score, regional_avg)
        
        return BREEAMAssessmentResult(
            weighted_score=weighted_score.quantize(Decimal("0.1")),
            rating=rating,
            category_weighted_scores={k: v.quantize(Decimal("0.1")) for k, v in weighted_components.items()},
            points_to_next_level=points_to_next,
            estimated_rent_premium_percent=rent_premium,
            estimated_value_premium_percent=value_premium,
            estimated_value_impact=value_impact,
            highest_performing=highest_performing,
            improvement_priorities=improvement_priorities,
            percentile_rank=percentile,
            regional_avg_score=regional_avg,
        )
    
    def _get_rating(self, score: Decimal) -> BREEAMLevel:
        """Determine BREEAM rating from weighted score."""
        score_f = float(score)
        if score_f >= 85:
            return BREEAMLevel.OUTSTANDING
        elif score_f >= 70:
            return BREEAMLevel.EXCELLENT
        elif score_f >= 55:
            return BREEAMLevel.VERY_GOOD
        elif score_f >= 45:
            return BREEAMLevel.GOOD
        else:
            return BREEAMLevel.PASS
    
    def _points_to_next_level(self, current: Decimal, level: BREEAMLevel) -> Optional[Decimal]:
        """Calculate points to next BREEAM level."""
        next_thresholds = {
            BREEAMLevel.PASS: Decimal("45"),
            BREEAMLevel.GOOD: Decimal("55"),
            BREEAMLevel.VERY_GOOD: Decimal("70"),
            BREEAMLevel.EXCELLENT: Decimal("85"),
        }
        if level == BREEAMLevel.OUTSTANDING:
            return None
        target = next_thresholds.get(level)
        return (target - current).quantize(Decimal("0.1")) if target else None
    
    def _identify_highest_performing(self, scores: BREEAMCategoryScore) -> List[str]:
        """Identify top performing categories."""
        score_dict = {
            "management": scores.management,
            "health_wellbeing": scores.health_wellbeing,
            "energy": scores.energy,
            "transport": scores.transport,
            "water": scores.water,
            "materials": scores.materials,
            "waste": scores.waste,
            "land_use_ecology": scores.land_use_ecology,
            "pollution": scores.pollution,
        }
        sorted_scores = sorted(score_dict.items(), key=lambda x: x[1], reverse=True)
        return [cat for cat, _ in sorted_scores[:3]]
    
    def _identify_improvements(self, scores: BREEAMCategoryScore, weights: BREEAMWeights) -> List[Dict[str, Any]]:
        """Identify improvement priorities with impact analysis."""
        improvements = []
        
        score_dict = {
            "management": (scores.management, weights.management),
            "health_wellbeing": (scores.health_wellbeing, weights.health_wellbeing),
            "energy": (scores.energy, weights.energy),
            "transport": (scores.transport, weights.transport),
            "water": (scores.water, weights.water),
            "materials": (scores.materials, weights.materials),
            "waste": (scores.waste, weights.waste),
            "land_use_ecology": (scores.land_use_ecology, weights.land_use_ecology),
            "pollution": (scores.pollution, weights.pollution),
        }
        
        for cat, (score, weight) in score_dict.items():
            if score < 70:  # Room for improvement
                potential_gain = (Decimal("80") - score) * weight
                improvements.append({
                    "category": cat.replace("_", " ").title(),
                    "current_score": float(score),
                    "target_score": 80,
                    "weight": float(weight),
                    "potential_weighted_gain": float(potential_gain.quantize(Decimal("0.1"))),
                    "priority": "high" if potential_gain > 5 else "medium",
                })
        
        return sorted(improvements, key=lambda x: x["potential_weighted_gain"], reverse=True)[:5]
    
    def _calculate_percentile(self, score: Decimal, regional_avg: Decimal) -> int:
        """Estimate percentile based on score."""
        score_f = float(score)
        avg_f = float(regional_avg)
        
        # Simple linear approximation
        if score_f >= 85:
            return 95
        elif score_f >= 70:
            return 80
        elif score_f >= avg_f:
            return 50 + int((score_f - avg_f) / (70 - avg_f) * 30)
        elif score_f >= 45:
            return 25 + int((score_f - 45) / (avg_f - 45) * 25)
        else:
            return max(5, int(score_f / 45 * 25))


class ValueImpactCalculator:
    """Calculator for certification value impact analysis."""
    
    def calculate_value_impact(self, request: CertificationValueImpactRequest) -> CertificationValueImpactResult:
        """Calculate value impact of certification."""
        
        # Get base premiums for certification type and level
        cert_premiums = RENT_PREMIUMS.get(request.certification_type, {})
        
        # Handle level lookup
        level_premiums = {}
        if request.certification_type == CertificationType.LEED:
            try:
                level = LEEDLevel(request.certification_level)
                level_premiums = cert_premiums.get(level, {})
            except ValueError:
                level_premiums = cert_premiums.get(LEEDLevel.CERTIFIED, {})
        elif request.certification_type == CertificationType.BREEAM:
            try:
                level = BREEAMLevel(request.certification_level)
                level_premiums = cert_premiums.get(level, {})
            except ValueError:
                level_premiums = cert_premiums.get(BREEAMLevel.GOOD, {})
        else:
            level_premiums = cert_premiums.get(request.certification_level, 
                                               {"low": Decimal("2"), "mid": Decimal("4"), "high": Decimal("6")})
        
        # Get rent premium range
        rent_low = level_premiums.get("low", Decimal("2"))
        rent_mid = level_premiums.get("mid", Decimal("4"))
        rent_high = level_premiums.get("high", Decimal("6"))
        
        # Apply adjustments
        regional_adj = REGIONAL_ADJUSTMENTS.get(request.region, Decimal("1.0"))
        sector_adj = SECTOR_ADJUSTMENTS.get(request.property_sector, Decimal("1.0"))
        
        rent_premium = rent_mid * regional_adj * sector_adj
        
        # Value premium (typically higher due to cap rate compression)
        value_premium = rent_premium * VALUE_PREMIUM_MULTIPLIER
        
        # Calculate cap rate compression
        cap_compression = self._get_cap_rate_compression(
            request.certification_type, 
            request.certification_level
        )
        
        # Operating cost savings
        op_savings = OPERATING_COST_SAVINGS.get(request.certification_type, Decimal("5"))
        
        # Calculate impacts
        value_increase = request.current_value * (value_premium / Decimal("100"))
        
        rent_premium_psf = None
        annual_rent_increase = None
        annual_cost_savings = None
        
        if request.current_rent_psf and request.gross_floor_area_sf:
            rent_premium_psf = request.current_rent_psf * (rent_premium / Decimal("100"))
            annual_rent_increase = rent_premium_psf * request.gross_floor_area_sf
        
        if request.current_noi:
            # Estimate operating expenses as % of NOI (typically NOI is ~60-70% of revenue)
            estimated_expenses = request.current_noi * Decimal("0.5")  # Rough estimate
            annual_cost_savings = estimated_expenses * (op_savings / Decimal("100"))
        
        # Source studies for credibility
        sources = self._get_source_studies(request.certification_type)
        
        return CertificationValueImpactResult(
            certification_type=request.certification_type,
            certification_level=request.certification_level,
            rent_premium_percent=rent_premium,
            rent_premium_range={
                "low": rent_low * regional_adj * sector_adj,
                "mid": rent_mid * regional_adj * sector_adj,
                "high": rent_high * regional_adj * sector_adj,
            },
            value_premium_percent=value_premium,
            value_premium_range={
                "low": rent_low * VALUE_PREMIUM_MULTIPLIER * regional_adj * sector_adj,
                "mid": rent_mid * VALUE_PREMIUM_MULTIPLIER * regional_adj * sector_adj,
                "high": rent_high * VALUE_PREMIUM_MULTIPLIER * regional_adj * sector_adj,
            },
            estimated_rent_premium_psf=rent_premium_psf,
            estimated_annual_rent_increase=annual_rent_increase,
            estimated_value_increase=value_increase,
            cap_rate_compression_bps=cap_compression,
            estimated_operating_cost_savings_percent=op_savings,
            estimated_annual_cost_savings=annual_cost_savings,
            source_studies=sources,
            data_reliability="high" if request.certification_type in [CertificationType.LEED, CertificationType.BREEAM] else "medium",
            regional_adjustment=regional_adj,
        )
    
    def _get_cap_rate_compression(self, cert_type: CertificationType, level: str) -> Decimal:
        """Get cap rate compression for certification."""
        if cert_type == CertificationType.LEED:
            try:
                leed_level = LEEDLevel(level)
                return Decimal(str(CAP_RATE_COMPRESSION.get(cert_type, {}).get(leed_level, 20)))
            except ValueError:
                return Decimal("20")
        elif cert_type == CertificationType.BREEAM:
            try:
                breeam_level = BREEAMLevel(level)
                return Decimal(str(CAP_RATE_COMPRESSION.get(cert_type, {}).get(breeam_level, 20)))
            except ValueError:
                return Decimal("20")
        return Decimal("25")  # Default
    
    def _get_source_studies(self, cert_type: CertificationType) -> List[str]:
        """Get academic/industry source studies for premiums."""
        base_sources = [
            "Eichholtz, Kok, Quigley (2010) - Energy Efficiency & Economic Value",
            "Fuerst & McAllister (2011) - Green Building Premiums in the UK",
        ]
        
        if cert_type == CertificationType.LEED:
            base_sources.extend([
                "Miller, Spivey, Florance (2008) - LEED Rent Premiums",
                "Wiley, Benefield, Johnson (2010) - Green Building Value",
            ])
        elif cert_type == CertificationType.BREEAM:
            base_sources.extend([
                "RICS Research (2013) - Sustainability & Value",
                "BRE Global Impact Studies (2020)",
            ])
        elif cert_type == CertificationType.GRESB:
            base_sources.extend([
                "GRESB Foundation Research (2023)",
                "UNEP FI - Sustainable Real Estate Investment",
            ])
        
        return base_sources


class PortfolioSustainabilityCalculator:
    """Calculator for portfolio-level sustainability analysis."""
    
    def analyze_portfolio(self, request: PortfolioSustainabilityRequest) -> PortfolioSustainabilityResult:
        """Analyze portfolio sustainability metrics."""
        
        total_assets = len(request.assets)
        certified_assets = [a for a in request.assets if a.get("certification_type")]
        uncertified_assets = [a for a in request.assets if not a.get("certification_type")]
        
        # Count by certification type
        by_type = {}
        scores_by_type = {}
        
        for asset in certified_assets:
            cert_type = asset.get("certification_type", "unknown")
            by_type[cert_type] = by_type.get(cert_type, 0) + 1
            
            if asset.get("score"):
                if cert_type not in scores_by_type:
                    scores_by_type[cert_type] = []
                scores_by_type[cert_type].append(float(asset["score"]))
        
        avg_scores = {
            cert: Decimal(str(sum(scores) / len(scores))).quantize(Decimal("0.1"))
            for cert, scores in scores_by_type.items()
            if scores
        }
        
        # Calculate value premiums
        value_calc = ValueImpactCalculator()
        total_value_premium = Decimal("0")
        total_rent_premium = Decimal("0")
        
        for asset in certified_assets:
            cert_type = asset.get("certification_type")
            cert_level = asset.get("certification_level", "certified")
            value = Decimal(str(asset.get("value", 0)))
            
            if cert_type and value > 0:
                try:
                    impact = value_calc.calculate_value_impact(
                        CertificationValueImpactRequest(
                            certification_type=CertificationType(cert_type),
                            certification_level=cert_level,
                            property_sector=PropertySector(asset.get("sector", "office")),
                            region=Region(asset.get("region", "north_america")),
                            current_value=value,
                        )
                    )
                    total_value_premium += impact.estimated_value_increase
                    if impact.estimated_annual_rent_increase:
                        total_rent_premium += impact.estimated_annual_rent_increase
                except (ValueError, KeyError):
                    pass
        
        # Certified value and uncertified opportunity
        certified_value = sum(Decimal(str(a.get("value", 0))) for a in certified_assets)
        uncertified_value = sum(Decimal(str(a.get("value", 0))) for a in uncertified_assets)
        
        # Potential uplift if uncertified get certified (assuming avg 5% premium)
        potential_uplift = uncertified_value * Decimal("0.05")
        
        # Portfolio sustainability score (weighted by AUM)
        if certified_assets and request.total_aum > 0:
            weighted_scores = []
            for asset in certified_assets:
                score = asset.get("score", 50)
                weight = Decimal(str(asset.get("value", 0))) / request.total_aum
                weighted_scores.append(Decimal(str(score)) * weight)
            portfolio_score = sum(weighted_scores) if weighted_scores else Decimal("0")
        else:
            portfolio_score = Decimal("0")
        
        # Portfolio rating
        coverage = (len(certified_assets) / total_assets * 100) if total_assets > 0 else 0
        if coverage >= 80 and float(portfolio_score) >= 70:
            rating = "Leader"
        elif coverage >= 60 and float(portfolio_score) >= 55:
            rating = "Advanced"
        elif coverage >= 40:
            rating = "Developing"
        else:
            rating = "Starting"
        
        # Recommendations
        recommendations = self._generate_recommendations(
            coverage, float(portfolio_score), by_type, uncertified_assets
        )
        
        return PortfolioSustainabilityResult(
            portfolio_name=request.portfolio_name,
            total_assets=total_assets,
            certified_assets=len(certified_assets),
            certified_percentage=Decimal(str(coverage)).quantize(Decimal("0.1")),
            uncertified_assets=len(uncertified_assets),
            certifications_by_type=by_type,
            avg_scores_by_type=avg_scores,
            total_estimated_value_premium=total_value_premium,
            avg_value_premium_percent=Decimal(str(
                (float(total_value_premium) / float(certified_value) * 100) if certified_value > 0 else 0
            )).quantize(Decimal("0.1")),
            total_estimated_rent_premium=total_rent_premium,
            portfolio_sustainability_score=portfolio_score.quantize(Decimal("0.1")),
            portfolio_rating=rating,
            uncertified_value=uncertified_value,
            potential_value_uplift=potential_uplift,
            recommendations=recommendations,
        )
    
    def _generate_recommendations(
        self, coverage: float, score: float, by_type: Dict, uncertified: List
    ) -> List[str]:
        """Generate portfolio improvement recommendations."""
        recommendations = []
        
        if coverage < 50:
            recommendations.append(
                f"Certification coverage is low ({coverage:.0f}%). Prioritize certifying high-value uncertified assets."
            )
        
        if CertificationType.GRESB.value not in by_type:
            recommendations.append(
                "Consider GRESB participation for portfolio-level ESG benchmarking and investor reporting."
            )
        
        if score < 60 and score > 0:
            recommendations.append(
                f"Portfolio sustainability score ({score:.0f}) is below industry average. Focus on performance improvements."
            )
        
        if uncertified:
            uncert_value = sum(float(a.get("value", 0)) for a in uncertified)
            recommendations.append(
                f"${uncert_value/1e6:.1f}M in uncertified assets represent significant value uplift opportunity."
            )
        
        recommendations.append(
            "Implement energy management systems across portfolio to improve operational performance metrics."
        )
        
        return recommendations[:5]


# ============ Main Engine Class ============

class SustainabilityEngine:
    """Main engine for sustainability framework calculations."""
    
    def __init__(self):
        self.gresb_calc = GRESBCalculator()
        self.leed_calc = LEEDCalculator()
        self.breeam_calc = BREEAMCalculator()
        self.value_calc = ValueImpactCalculator()
        self.portfolio_calc = PortfolioSustainabilityCalculator()
    
    def calculate_gresb(self, request: GRESBAssessmentRequest) -> GRESBAssessmentResult:
        return self.gresb_calc.calculate_assessment(request)
    
    def calculate_leed(self, request: LEEDAssessmentRequest) -> LEEDAssessmentResult:
        return self.leed_calc.calculate_assessment(request)
    
    def calculate_breeam(self, request: BREEAMAssessmentRequest) -> BREEAMAssessmentResult:
        return self.breeam_calc.calculate_assessment(request)
    
    def calculate_value_impact(self, request: CertificationValueImpactRequest) -> CertificationValueImpactResult:
        return self.value_calc.calculate_value_impact(request)
    
    def analyze_portfolio(self, request: PortfolioSustainabilityRequest) -> PortfolioSustainabilityResult:
        return self.portfolio_calc.analyze_portfolio(request)
