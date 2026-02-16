"""
Nature Risk Integration Calculation Engine
Based on TNFD LEAP methodology and NCORE framework

Provides:
- LEAPAssessmentCalculator: TNFD LEAP methodology calculations
- WaterRiskCalculator: Water risk analysis using Aqueduct data
- BiodiversityOverlapCalculator: Spatial overlap analysis
- PortfolioNatureRiskCalculator: Portfolio-level nature risk aggregation
"""

from decimal import Decimal
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum
import math


class LEAPPhase(str, Enum):
    LOCATE = "locate"
    EVALUATE = "evaluate"
    ASSESS = "assess"
    PREPARE = "prepare"


@dataclass
class LEAPScores:
    locate: float
    evaluate: float
    assess: float
    prepare: float
    overall: float


class LEAPAssessmentCalculator:
    """
    Calculates TNFD LEAP assessment scores for entities.
    Implements the full LEAP methodology: Locate, Evaluate, Assess, Prepare.
    """

    PHASE_WEIGHTS = {
        LEAPPhase.LOCATE: 0.20,
        LEAPPhase.EVALUATE: 0.25,
        LEAPPhase.ASSESS: 0.35,
        LEAPPhase.PREPARE: 0.20
    }

    RISK_THRESHOLDS = {
        "low": 1.0,
        "medium-low": 2.0,
        "medium": 3.0,
        "medium-high": 4.0,
        "high": 4.5,
        "critical": 5.0
    }

    def __init__(
        self,
        encore_data: Optional[Dict] = None,
        water_risk_data: Optional[Dict] = None,
        biodiversity_data: Optional[Dict] = None
    ):
        self.encore_data = encore_data or {}
        self.water_risk_data = water_risk_data or {}
        self.biodiversity_data = biodiversity_data or {}

    def calculate_leap_assessment(
        self,
        entity_data: Dict,
        scenario: Dict,
        include_water_risk: bool = True,
        include_biodiversity: bool = True
    ) -> Dict:
        """
        Calculate complete LEAP assessment for an entity.
        """
        locate_result = self._calculate_locate_phase(entity_data, include_biodiversity)
        evaluate_result = self._calculate_evaluate_phase(entity_data, locate_result)
        assess_result = self._calculate_assess_phase(
            entity_data, scenario, locate_result, evaluate_result, include_water_risk
        )
        prepare_result = self._calculate_prepare_phase(entity_data, assess_result)

        overall_score = self._calculate_overall_score(
            locate_result['score'],
            evaluate_result['score'],
            assess_result['score'],
            prepare_result['score']
        )

        return {
            "locate_score": round(locate_result['score'], 2),
            "locate_details": locate_result['details'],
            "evaluate_score": round(evaluate_result['score'], 2),
            "evaluate_details": evaluate_result['details'],
            "assess_score": round(assess_result['score'], 2),
            "assess_details": assess_result['details'],
            "prepare_score": round(prepare_result['score'], 2),
            "prepare_details": prepare_result['details'],
            "overall_score": round(overall_score, 2),
            "overall_risk_rating": self._score_to_rating(overall_score),
            "key_dependencies": evaluate_result.get('key_dependencies', []),
            "key_risks": assess_result.get('key_risks', []),
            "recommendations": prepare_result.get('recommendations', [])
        }

    def _calculate_locate_phase(self, entity_data: Dict, include_biodiversity: bool) -> Dict:
        """Calculate LOCATE phase score."""
        score_components = {}

        # Biome exposure (0-5 scale)
        biome_exposure = entity_data.get('biome_exposure', {})
        if isinstance(biome_exposure, dict):
            exposed_biomes = sum(1 for v in biome_exposure.values() if v)
        else:
            exposed_biomes = 0
        score_components['biome_exposure'] = min(exposed_biomes * 0.8, 5)

        # Geographic scope
        has_geographic_scope = entity_data.get('latitude') is not None
        score_components['geographic_scope'] = 5 if has_geographic_scope else 2

        # Value chain coverage
        value_chain = entity_data.get('value_chain_exposure', {})
        if value_chain and isinstance(value_chain, dict):
            value_chain_coverage = sum(1 for v in value_chain.values() if v) / max(len(value_chain), 1)
        else:
            value_chain_coverage = 0.5
        score_components['value_chain'] = value_chain_coverage * 5

        # Calculate weighted score
        locate_score = sum(score_components.values()) / len(score_components) if score_components else 2.5

        return {
            "score": locate_score,
            "details": score_components,
            "exposed_biomes": [k for k, v in biome_exposure.items() if v] if isinstance(biome_exposure, dict) else []
        }

    def _calculate_evaluate_phase(self, entity_data: Dict, locate_result: Dict) -> Dict:
        """Calculate EVALUATE phase score."""
        score_components = {}

        # Get ENCORE dependencies for sector
        sector_code = entity_data.get('sector_code', '')
        dependencies = self._get_encore_dependencies(sector_code)

        # Dependency ratings
        dependency_ratings = entity_data.get('dependency_ratings', [])
        if dependency_ratings:
            avg_dependency = sum(d.get('rating', 3) for d in dependency_ratings) / len(dependency_ratings)
            score_components['dependency_criticality'] = avg_dependency
        elif dependencies:
            avg_dependency = sum(d.get('dependency_score', 3) for d in dependencies) / len(dependencies)
            score_components['dependency_criticality'] = avg_dependency
        else:
            score_components['dependency_criticality'] = 3.0

        # Impact ratings
        impact_ratings = entity_data.get('impact_ratings', [])
        if impact_ratings:
            avg_impact = sum(i.get('rating', 3) for i in impact_ratings) / len(impact_ratings)
            score_components['impact_severity'] = avg_impact
        else:
            score_components['impact_severity'] = 3.0

        # Materiality assessment
        material_dependencies = [d for d in dependencies if d.get('dependency_score', 0) >= 4]
        score_components['materiality'] = min(len(material_dependencies) * 1.5, 5)

        evaluate_score = sum(score_components.values()) / len(score_components) if score_components else 3.0

        # Identify key dependencies
        key_dependencies = [
            d['ecosystem_service'] for d in dependencies
            if d.get('dependency_score', 0) >= 4
        ]

        return {
            "score": evaluate_score,
            "details": score_components,
            "key_dependencies": key_dependencies,
            "all_dependencies": dependencies
        }

    def _calculate_assess_phase(
        self,
        entity_data: Dict,
        scenario: Dict,
        locate_result: Dict,
        evaluate_result: Dict,
        include_water_risk: bool
    ) -> Dict:
        """Calculate ASSESS phase score."""
        score_components = {}
        key_risks = []

        # Physical risk scores
        physical_scores = entity_data.get('physical_risk_scores', {})
        if physical_scores and isinstance(physical_scores, dict):
            physical_avg = (
                physical_scores.get('acute', 2.5) + 
                physical_scores.get('chronic', 2.5)
            ) / 2
            score_components['physical_risk'] = physical_avg
        else:
            score_components['physical_risk'] = 2.5

        # Transition risk scores
        transition_scores = entity_data.get('transition_risk_scores', {})
        if transition_scores and isinstance(transition_scores, dict):
            transition_values = [
                transition_scores.get('policy', 2.5),
                transition_scores.get('legal', 2.5),
                transition_scores.get('technology', 2.5),
                transition_scores.get('market', 2.5),
                transition_scores.get('reputation', 2.5)
            ]
            transition_avg = sum(transition_values) / len(transition_values)
            score_components['transition_risk'] = transition_avg
        else:
            score_components['transition_risk'] = 2.5

        # Water risk (if applicable)
        key_dependencies = evaluate_result.get('key_dependencies', [])
        if include_water_risk and 'water' in key_dependencies:
            water_risk = self._calculate_water_risk_contribution(entity_data, scenario)
            score_components['water_risk'] = water_risk['score']
            if water_risk['score'] > 3:
                key_risks.append({
                    "type": "water_stress",
                    "severity": water_risk['score'],
                    "description": water_risk['description']
                })

        # Opportunity scores (inverted for risk)
        opportunity_scores = entity_data.get('opportunity_scores', {})
        if opportunity_scores and isinstance(opportunity_scores, dict):
            opportunity_avg = sum(opportunity_scores.values()) / len(opportunity_scores)
            score_components['opportunities'] = 5 - opportunity_avg
        else:
            score_components['opportunities'] = 2.5

        assess_score = sum(score_components.values()) / len(score_components) if score_components else 2.5

        # Add other key risks
        if score_components.get('physical_risk', 0) > 3.5:
            key_risks.append({
                "type": "physical",
                "severity": score_components['physical_risk'],
                "description": "High physical nature-related risks identified"
            })

        if score_components.get('transition_risk', 0) > 3.5:
            key_risks.append({
                "type": "transition",
                "severity": score_components['transition_risk'],
                "description": "Significant transition risks from nature policy changes"
            })

        return {
            "score": assess_score,
            "details": score_components,
            "key_risks": key_risks
        }

    def _calculate_prepare_phase(self, entity_data: Dict, assess_result: Dict) -> Dict:
        """Calculate PREPARE phase score."""
        score_components = {}
        recommendations = []

        # Strategy response
        strategy = entity_data.get('strategy_response', {})
        has_strategy = bool(strategy.get('goals') or strategy.get('actions')) if isinstance(strategy, dict) else bool(strategy)
        score_components['strategy_completeness'] = 4.0 if has_strategy else 2.0

        # Target setting
        targets = entity_data.get('target_setting', {})
        has_targets = bool(targets.get('gbf_targets') or targets.get('custom_targets')) if isinstance(targets, dict) else bool(targets)
        score_components['target_setting'] = 4.0 if has_targets else 1.5

        # Metrics disclosure
        metrics = entity_data.get('metrics_disclosure', {})
        has_metrics = bool(metrics.get('reported_metrics')) if isinstance(metrics, dict) else bool(metrics)
        score_components['disclosure_quality'] = 4.0 if has_metrics else 1.0

        prepare_score = sum(score_components.values()) / len(score_components) if score_components else 2.0

        # Generate recommendations
        if not has_strategy:
            recommendations.append("Develop comprehensive nature strategy with clear goals and actions")
        if not has_targets:
            recommendations.append("Set science-based targets aligned with GBF and TNFD guidance")
        if not has_metrics:
            recommendations.append("Implement nature-related metrics tracking and disclosure")

        for risk in assess_result.get('key_risks', []):
            if risk.get('type') == 'water_stress':
                recommendations.append("Implement water stewardship program at high-risk locations")
            elif risk.get('type') == 'biodiversity':
                recommendations.append("Conduct biodiversity impact assessment and develop mitigation plan")

        return {
            "score": prepare_score,
            "details": score_components,
            "recommendations": recommendations
        }

    def _calculate_overall_score(self, locate: float, evaluate: float, assess: float, prepare: float) -> float:
        """Calculate weighted overall LEAP score."""
        return (
            locate * self.PHASE_WEIGHTS[LEAPPhase.LOCATE] +
            evaluate * self.PHASE_WEIGHTS[LEAPPhase.EVALUATE] +
            assess * self.PHASE_WEIGHTS[LEAPPhase.ASSESS] +
            prepare * self.PHASE_WEIGHTS[LEAPPhase.PREPARE]
        )

    def _score_to_rating(self, score: float) -> str:
        """Convert numerical score to risk rating."""
        if score >= self.RISK_THRESHOLDS['critical']:
            return "critical"
        elif score >= self.RISK_THRESHOLDS['high']:
            return "high"
        elif score >= self.RISK_THRESHOLDS['medium-high']:
            return "medium-high"
        elif score >= self.RISK_THRESHOLDS['medium']:
            return "medium"
        elif score >= self.RISK_THRESHOLDS['medium-low']:
            return "medium-low"
        return "low"

    def _get_encore_dependencies(self, sector_code: Optional[str]) -> List[Dict]:
        """Get ENCORE dependencies for a sector."""
        if not sector_code or sector_code not in self.encore_data:
            return []
        return self.encore_data.get(sector_code, [])

    def _calculate_water_risk_contribution(self, entity_data: Dict, scenario: Dict) -> Dict:
        """Calculate water risk contribution to assessment."""
        water_stress = entity_data.get('baseline_water_stress', 3.0)
        return {
            "score": water_stress,
            "description": f"Water stress exposure level: {water_stress:.1f}/5"
        }


class WaterRiskCalculator:
    """
    Calculates water risk for locations using Aqueduct data and projections.
    Supports power plants, extraction sites, and facilities.
    """

    RISK_LEVELS = {
        "low": (0, 1),
        "low-medium": (1, 2),
        "medium": (2, 3),
        "medium-high": (3, 4),
        "high": (4, 5),
        "extremely-high": (5, 10)
    }

    BENCHMARKS = {
        "coal_mining": 2.5,
        "oil_extraction": 1.5,
        "gas_extraction": 0.5,
        "coal_power": 2.0,
        "gas_power": 1.0,
        "nuclear_power": 2.5,
        "solar_power": 0.05,
        "wind_power": 0.01,
    }

    def __init__(self, aqueduct_data: Optional[Dict] = None):
        self.aqueduct_data = aqueduct_data or {}

    def calculate_water_risk(
        self,
        location_data: Dict,
        scenario: Dict,
        include_projections: bool = True
    ) -> Dict:
        """Calculate comprehensive water risk for a location."""
        baseline_indicators = self._get_baseline_indicators(location_data)
        baseline_score = self._calculate_composite_score(baseline_indicators)
        baseline_level = self._score_to_level(baseline_score)

        projected_scores = {}
        if include_projections:
            for year in [2030, 2040, 2050]:
                projected_indicators = self._get_projected_indicators(location_data, year, scenario)
                projected_scores[year] = round(self._calculate_composite_score(projected_indicators), 2)

        key_risks = self._identify_key_risks(baseline_indicators)
        financial_impact = self._estimate_financial_impact(location_data, baseline_score, projected_scores, scenario)
        recommendations = self._generate_water_recommendations(baseline_indicators, key_risks)

        return {
            "baseline_risk_score": round(baseline_score, 2),
            "baseline_risk_level": baseline_level,
            "projected_risk_scores": projected_scores,
            "overall_risk_level": baseline_level,
            "key_risk_factors": key_risks,
            "financial_impact_estimate": financial_impact,
            "recommendations": recommendations,
            "indicators": {k: round(v, 2) if v else 0 for k, v in baseline_indicators.items()}
        }

    def _get_baseline_indicators(self, location_data: Dict) -> Dict:
        """Extract baseline water risk indicators."""
        return {
            "water_stress": location_data.get('baseline_water_stress', 0) or 0,
            "groundwater_decline": location_data.get('groundwater_table_decline', 0) or 0,
            "interannual_variability": location_data.get('interannual_variability', 0) or 0,
            "seasonal_variability": location_data.get('seasonal_variability', 0) or 0,
            "drought_risk": location_data.get('drought_risk', 0) or 0,
            "flood_risk": location_data.get('flood_risk', 0) or 0
        }

    def _get_projected_indicators(self, location_data: Dict, year: int, scenario: Dict) -> Dict:
        """Get projected indicators for a given year and scenario."""
        field_name = f'projected_water_stress_{year}'
        projected_stress = location_data.get(field_name) or location_data.get('baseline_water_stress', 0) or 0

        temp_increase = (scenario.get('temperature_c', 1.5) or 1.5) - 1.1
        stress_adjustment = temp_increase * 0.3

        return {
            "water_stress": min(projected_stress + stress_adjustment, 5),
            "groundwater_decline": location_data.get('groundwater_table_decline', 0) or 0,
            "interannual_variability": location_data.get('interannual_variability', 0) or 0,
            "seasonal_variability": location_data.get('seasonal_variability', 0) or 0,
            "drought_risk": min((location_data.get('drought_risk', 0) or 0) + temp_increase * 0.2, 5),
            "flood_risk": location_data.get('flood_risk', 0) or 0
        }

    def _calculate_composite_score(self, indicators: Dict) -> float:
        """Calculate composite water risk score from indicators."""
        weights = {
            "water_stress": 0.35,
            "groundwater_decline": 0.15,
            "interannual_variability": 0.10,
            "seasonal_variability": 0.10,
            "drought_risk": 0.20,
            "flood_risk": 0.10
        }

        weighted_sum = sum(
            (indicators.get(k, 0) or 0) * w
            for k, w in weights.items()
        )

        return min(weighted_sum, 5)

    def _score_to_level(self, score: float) -> str:
        """Convert score to risk level."""
        for level, (min_val, max_val) in self.RISK_LEVELS.items():
            if min_val <= score < max_val:
                return level
        return "extremely-high"

    def _identify_key_risks(self, indicators: Dict) -> List[Dict]:
        """Identify key water risk factors."""
        key_risks = []

        if (indicators.get('water_stress', 0) or 0) >= 3:
            key_risks.append({
                "factor": "water_stress",
                "level": self._score_to_level(indicators['water_stress']),
                "score": round(indicators['water_stress'], 2),
                "description": "High water stress may limit operational capacity"
            })

        if (indicators.get('drought_risk', 0) or 0) >= 3:
            key_risks.append({
                "factor": "drought_risk",
                "level": self._score_to_level(indicators['drought_risk']),
                "score": round(indicators['drought_risk'], 2),
                "description": "Drought risk threatens water supply reliability"
            })

        if (indicators.get('flood_risk', 0) or 0) >= 3:
            key_risks.append({
                "factor": "flood_risk",
                "level": self._score_to_level(indicators['flood_risk']),
                "score": round(indicators['flood_risk'], 2),
                "description": "Flood risk may damage infrastructure"
            })

        return key_risks

    def _estimate_financial_impact(
        self,
        location_data: Dict,
        baseline_score: float,
        projected_scores: Dict,
        scenario: Dict
    ) -> Dict:
        """Estimate financial impact of water risks."""
        annual_withdrawal = location_data.get('annual_water_withdrawal_m3', 0) or 0

        base_water_cost = 1.0
        cost_increase_factor = baseline_score * 0.1
        projected_cost = base_water_cost * (1 + cost_increase_factor)
        annual_water_cost = annual_withdrawal * projected_cost

        disruption_probability = min(baseline_score / 10, 0.5)
        disruption_impact = annual_water_cost * disruption_probability * 5

        mitigation_capex = annual_withdrawal * 0.5 if baseline_score > 3 else 0

        return {
            "annual_water_cost_increase_usd": round(annual_water_cost, 2),
            "operational_disruption_risk_usd": round(disruption_impact, 2),
            "mitigation_capex_estimate_usd": round(mitigation_capex, 2),
            "total_annual_impact_usd": round(annual_water_cost + disruption_impact, 2)
        }

    def _generate_water_recommendations(self, indicators: Dict, key_risks: List[Dict]) -> List[str]:
        """Generate water risk management recommendations."""
        recommendations = []

        if (indicators.get('water_stress', 0) or 0) >= 3:
            recommendations.append("Implement water efficiency measures and recycling systems")
            recommendations.append("Assess alternative water sources (recycled, desalinated)")

        if (indicators.get('drought_risk', 0) or 0) >= 3:
            recommendations.append("Develop drought contingency plans and water storage")
            recommendations.append("Engage in watershed stewardship programs")

        if (indicators.get('flood_risk', 0) or 0) >= 3:
            recommendations.append("Implement flood protection infrastructure")
            recommendations.append("Review insurance coverage for flood damage")

        if not recommendations:
            recommendations.append("Monitor water risk indicators and maintain current practices")

        return recommendations

    def calculate_portfolio_water_risk(self, locations: List[Dict], scenario: Dict) -> Dict:
        """Calculate aggregated water risk for a portfolio of locations."""
        location_risks = []

        for location in locations:
            risk = self.calculate_water_risk(location, scenario)
            location_risks.append({
                "location_id": location.get('id'),
                "location_name": location.get('location_name'),
                **risk
            })

        if not location_risks:
            return {
                "location_count": 0,
                "average_baseline_risk": 0,
                "high_risk_locations": 0,
                "high_risk_percent": 0,
                "total_financial_impact_usd": 0,
                "location_details": []
            }

        avg_baseline = sum(r['baseline_risk_score'] for r in location_risks) / len(location_risks)
        high_risk_count = sum(1 for r in location_risks if r['baseline_risk_level'] in ['high', 'extremely-high'])

        total_financial_impact = sum(
            r['financial_impact_estimate']['total_annual_impact_usd']
            for r in location_risks
        )

        return {
            "location_count": len(locations),
            "average_baseline_risk": round(avg_baseline, 2),
            "high_risk_locations": high_risk_count,
            "high_risk_percent": round((high_risk_count / len(locations) * 100), 2),
            "total_financial_impact_usd": round(total_financial_impact, 2),
            "location_details": location_risks
        }


class BiodiversityOverlapCalculator:
    """
    Calculates overlaps between assets and biodiversity sites.
    Uses coordinate-based distance calculations.
    """

    IMPACT_SEVERITY = {
        "direct_overlap": 1.0,
        "buffer_5km": 0.7,
        "buffer_10km": 0.4,
        "buffer_25km": 0.2
    }

    SITE_SENSITIVITY = {
        "world_heritage": 1.0,
        "ramsar": 0.9,
        "key_biodiversity_area": 0.85,
        "protected_area": 0.8,
        "iba": 0.75
    }

    def __init__(self, biodiversity_sites: Optional[List[Dict]] = None):
        self.biodiversity_sites = biodiversity_sites or []

    def calculate_overlaps(
        self,
        asset_data: Dict,
        asset_type: str,
        buffer_distances: List[float] = None
    ) -> Dict:
        """Calculate overlaps between asset and biodiversity sites."""
        if buffer_distances is None:
            buffer_distances = [5, 10, 25]

        overlaps = {
            "direct_overlaps": [],
            "buffer_overlaps": [],
            "total_overlap_area_km2": 0,
            "impact_score": 0,
            "key_sites_affected": [],
            "mitigation_requirements": []
        }

        asset_lat = asset_data.get('latitude')
        asset_lng = asset_data.get('longitude')

        if asset_lat is None or asset_lng is None:
            overlaps['mitigation_requirements'].append("Asset location required for spatial analysis")
            return overlaps

        for site in self.biodiversity_sites:
            site_lat = site.get('latitude')
            site_lng = site.get('longitude')

            if site_lat is None or site_lng is None:
                continue

            distance = self._haversine_distance(asset_lat, asset_lng, site_lat, site_lng)
            site_sensitivity = self.SITE_SENSITIVITY.get(site.get('site_type', ''), 0.5)

            # Direct overlap (within 1km)
            if distance < 1:
                overlap_info = {
                    "site_id": site.get('id'),
                    "site_name": site.get('site_name'),
                    "site_type": site.get('site_type'),
                    "distance_km": round(distance, 2),
                    "overlap_area_km2": site.get('area_km2', 0),
                    "sensitivity": site_sensitivity
                }
                overlaps['direct_overlaps'].append(overlap_info)
                overlaps['key_sites_affected'].append(site.get('site_name'))

            # Buffer overlaps
            else:
                for buffer_km in buffer_distances:
                    if distance <= buffer_km:
                        overlap_info = {
                            "site_id": site.get('id'),
                            "site_name": site.get('site_name'),
                            "site_type": site.get('site_type'),
                            "distance_km": round(distance, 2),
                            "buffer_distance_km": buffer_km,
                            "sensitivity": site_sensitivity
                        }
                        overlaps['buffer_overlaps'].append(overlap_info)
                        if site.get('site_name') not in overlaps['key_sites_affected']:
                            overlaps['key_sites_affected'].append(site.get('site_name'))
                        break

        overlaps['impact_score'] = round(self._calculate_impact_score(overlaps), 2)
        overlaps['mitigation_requirements'] = self._determine_mitigation(overlaps)

        return overlaps

    def _haversine_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calculate distance between two points using Haversine formula."""
        R = 6371  # Earth's radius in km

        lat1_rad = math.radians(lat1)
        lat2_rad = math.radians(lat2)
        delta_lat = math.radians(lat2 - lat1)
        delta_lon = math.radians(lon2 - lon1)

        a = math.sin(delta_lat / 2) ** 2 + \
            math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lon / 2) ** 2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

        return R * c

    def _calculate_impact_score(self, overlaps: Dict) -> float:
        """Calculate overall biodiversity impact score."""
        score = 0.0

        for overlap in overlaps['direct_overlaps']:
            score += self.IMPACT_SEVERITY['direct_overlap'] * overlap['sensitivity']

        for overlap in overlaps['buffer_overlaps']:
            buffer_km = overlap.get('buffer_distance_km', 10)
            buffer_key = f"buffer_{int(buffer_km)}km"
            buffer_severity = self.IMPACT_SEVERITY.get(buffer_key, 0.2)
            score += buffer_severity * overlap['sensitivity']

        return min(score, 5)

    def _determine_mitigation(self, overlaps: Dict) -> List[str]:
        """Determine required mitigation measures."""
        requirements = []

        if overlaps['direct_overlaps']:
            critical_sites = [o for o in overlaps['direct_overlaps'] if o['sensitivity'] >= 0.8]

            if critical_sites:
                requirements.append("CRITICAL: Immediate biodiversity impact assessment required")
                requirements.append("Consider project redesign to avoid critical habitats")
            else:
                requirements.append("Conduct biodiversity baseline survey")
                requirements.append("Implement biodiversity management plan")

        if overlaps['buffer_overlaps']:
            high_sensitivity_buffers = [o for o in overlaps['buffer_overlaps'] if o['sensitivity'] >= 0.7]

            if high_sensitivity_buffers:
                requirements.append("Implement buffer zone management measures")
                requirements.append("Monitor indirect impacts on protected areas")

        if not requirements:
            requirements.append("No significant biodiversity overlaps detected")
            requirements.append("Maintain standard environmental management practices")

        return requirements


class PortfolioNatureRiskCalculator:
    """
    Calculates portfolio-level nature risk for financial institutions.
    Aggregates LEAP scores, water risk, and biodiversity exposure.
    """

    def __init__(self):
        self.leap_calculator = LEAPAssessmentCalculator()
        self.water_calculator = WaterRiskCalculator()
        self.biodiversity_calculator = BiodiversityOverlapCalculator()

    def calculate_portfolio_nature_risk(
        self,
        holdings: List[Dict],
        scenarios: List[Dict],
        include_collateral_impact: bool = True
    ) -> Dict:
        """Calculate comprehensive nature risk for a portfolio."""
        holding_results = []

        for holding in holdings:
            for scenario in scenarios:
                # Calculate LEAP assessment
                leap_result = self.leap_calculator.calculate_leap_assessment(
                    holding,
                    scenario,
                    include_water_risk=True,
                    include_biodiversity=True
                )

                # Calculate financial impact
                financial_impact = self._calculate_nature_financial_impact(
                    holding, leap_result, scenario, include_collateral_impact
                )

                holding_results.append({
                    "holding_id": holding.get('id'),
                    "entity_name": holding.get('entity_name', holding.get('name', 'Unknown')),
                    "sector": holding.get('sector', 'Unknown'),
                    "exposure_usd": holding.get('exposure_usd', 0),
                    "scenario_id": scenario.get('id'),
                    "scenario_name": scenario.get('name'),
                    "leap_scores": {
                        "locate": leap_result['locate_score'],
                        "evaluate": leap_result['evaluate_score'],
                        "assess": leap_result['assess_score'],
                        "prepare": leap_result['prepare_score'],
                        "overall": leap_result['overall_score']
                    },
                    "risk_rating": leap_result['overall_risk_rating'],
                    "key_dependencies": leap_result['key_dependencies'],
                    "key_risks": leap_result['key_risks'],
                    "financial_impact": financial_impact,
                    "recommendations": leap_result['recommendations']
                })

        aggregate = self._aggregate_portfolio_results(holding_results)

        return {
            "holding_count": len(holdings),
            "scenario_count": len(scenarios),
            "aggregate_metrics": aggregate,
            "holding_results": holding_results
        }

    def _calculate_nature_financial_impact(
        self,
        holding: Dict,
        leap_result: Dict,
        scenario: Dict,
        include_collateral: bool
    ) -> Dict:
        """Calculate financial impact of nature risks on a holding."""
        exposure = holding.get('exposure_usd', 0)
        risk_score = leap_result.get('overall_score', 2.5)

        # Calculate risk-adjusted impacts
        capex_increase = risk_score * 2  # 2% per risk point
        opex_increase = risk_score * 1.5  # 1.5% per risk point
        revenue_at_risk = risk_score * 3  # 3% per risk point

        impact = {
            "capex_increase_percent": round(capex_increase, 2),
            "opex_increase_percent": round(opex_increase, 2),
            "revenue_at_risk_percent": round(revenue_at_risk, 2),
            "estimated_impact_usd": round(exposure * (revenue_at_risk / 100), 2)
        }

        if include_collateral:
            collateral_impact = risk_score * 2.5  # 2.5% per risk point
            haircut_recommendation = min(risk_score * 5, 50)  # Max 50%
            impact['collateral_impact'] = {
                "value_impact_percent": round(collateral_impact, 2),
                "haircut_recommendation_percent": round(haircut_recommendation, 2)
            }

        return impact

    def _aggregate_portfolio_results(self, holding_results: List[Dict]) -> Dict:
        """Aggregate portfolio-level metrics."""
        if not holding_results:
            return {
                "average_leap_score": 0,
                "avg_locate_score": 0,
                "avg_evaluate_score": 0,
                "avg_assess_score": 0,
                "avg_prepare_score": 0,
                "high_risk_count": 0,
                "critical_risk_count": 0,
                "total_exposure_at_risk_usd": 0,
                "dependency_breakdown": {}
            }

        leap_scores = [r['leap_scores']['overall'] for r in holding_results]
        locate_scores = [r['leap_scores']['locate'] for r in holding_results]
        evaluate_scores = [r['leap_scores']['evaluate'] for r in holding_results]
        assess_scores = [r['leap_scores']['assess'] for r in holding_results]
        prepare_scores = [r['leap_scores']['prepare'] for r in holding_results]

        high_risk = sum(1 for r in holding_results if r['risk_rating'] in ['high', 'medium-high'])
        critical_risk = sum(1 for r in holding_results if r['risk_rating'] == 'critical')

        total_exposure_at_risk = sum(
            r['financial_impact'].get('estimated_impact_usd', 0)
            for r in holding_results
        )

        # Count dependencies
        dependency_counts = {}
        for r in holding_results:
            for dep in r.get('key_dependencies', []):
                dependency_counts[dep] = dependency_counts.get(dep, 0) + 1

        return {
            "average_leap_score": round(sum(leap_scores) / len(leap_scores), 2),
            "avg_locate_score": round(sum(locate_scores) / len(locate_scores), 2),
            "avg_evaluate_score": round(sum(evaluate_scores) / len(evaluate_scores), 2),
            "avg_assess_score": round(sum(assess_scores) / len(assess_scores), 2),
            "avg_prepare_score": round(sum(prepare_scores) / len(prepare_scores), 2),
            "high_risk_count": high_risk,
            "critical_risk_count": critical_risk,
            "total_exposure_at_risk_usd": round(total_exposure_at_risk, 2),
            "dependency_breakdown": dependency_counts
        }
