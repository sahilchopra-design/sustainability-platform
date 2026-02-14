"""
Proof of Concept Script for Climate Risk Calculation Engine

This script tests the calculation engine in isolation by:
1. Loading sample portfolio data from MongoDB
2. Running the new calculation engine for multiple scenarios and horizons
3. Comparing results with the legacy risk_engine.py
4. Printing performance statistics and validation results
"""
import sys
import os
import time
import json
from decimal import Decimal

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
import numpy as np
from motor.motor_asyncio import AsyncIOMotorClient

from services.calculation_engine import ClimateRiskCalculationEngine, AssetInput
from risk_engine import RiskEngine, SECTOR_MULTIPLIERS
from models import Portfolio, Asset


async def load_sample_portfolio():
    """Load sample portfolio from MongoDB"""
    mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
    client = AsyncIOMotorClient(mongo_url)
    db = client['climate_risk']
    
    # Find sample portfolio
    portfolio_doc = await db.portfolios.find_one({'name': 'Sample Climate Risk Portfolio'})
    
    if not portfolio_doc:
        print("❌ Sample portfolio not found. Run /api/sample-data/generate first")
        return None
    
    # Parse portfolio
    assets = []
    for asset_doc in portfolio_doc.get('assets', []):
        assets.append(Asset(**asset_doc))
    
    print(f"✓ Loaded portfolio: {portfolio_doc['name']}")
    print(f"  - Total assets: {len(assets)}")
    print(f"  - Total exposure: ${sum(a.exposure for a in assets):,.0f}")
    
    await client.close()
    return assets


async def load_scenario_data():
    """Load scenario parameters from MongoDB"""
    mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
    client = AsyncIOMotorClient(mongo_url)
    db = client['climate_risk']
    
    scenarios = ['Orderly', 'Disorderly', 'Hot house world']
    horizons = [2030, 2040, 2050]
    
    scenario_params = {}
    
    for scenario in scenarios:
        scenario_params[scenario] = {}
        for year in horizons:
            # Get carbon price and GDP index
            carbon_doc = await db.scenario_series.find_one({
                'scenario': scenario,
                'year': year,
                'region': 'World',
                'variable': 'Price|Carbon'
            })
            
            gdp_doc = await db.scenario_series.find_one({
                'scenario': scenario,
                'year': year,
                'region': 'World',
                'variable': 'GDP|PPP'
            })
            
            scenario_params[scenario][year] = {
                'carbon_price': carbon_doc['value'] if carbon_doc else 50,
                'gdp_index': gdp_doc['value'] if gdp_doc else 100
            }
    
    await client.close()
    return scenario_params


def prepare_assets_for_engine(assets: list) -> list:
    """Convert Asset objects to AssetInput for the calculation engine"""
    asset_inputs = []
    
    for asset in assets:
        # Map subsector to emissions characteristics
        subsector = asset.company.subsector or ''
        
        # Assign emissions intensity based on subsector
        if 'Coal' in subsector:
            emissions_intensity = 1.8
            emissions_trend = 'Deteriorating'
        elif 'Renewables' in subsector or 'EV' in subsector:
            emissions_intensity = 0.2
            emissions_trend = 'Improving'
        elif 'Oil' in subsector or 'Gas' in subsector:
            emissions_intensity = 1.2
            emissions_trend = 'Stable'
        else:
            emissions_intensity = 0.8
            emissions_trend = 'Stable'
        
        # Assign transition plan score (1-5)
        if 'Renewables' in subsector or 'EV' in subsector or 'Green' in asset.company.name:
            transition_plan_score = 5
        elif 'Coal' in subsector or 'Petro' in asset.company.name:
            transition_plan_score = 2
        else:
            transition_plan_score = 3
        
        # Assign physical risk score (1-5)
        sector = asset.company.sector.value
        if sector in ['Real Estate', 'Airlines']:
            physical_risk_score = 4
        elif sector in ['Power Generation', 'Metals & Mining']:
            physical_risk_score = 3
        else:
            physical_risk_score = 2
        
        asset_inputs.append(AssetInput(
            id=asset.id,
            exposure=asset.exposure,
            baseline_pd=asset.base_pd,
            baseline_lgd=asset.base_lgd,
            sector=sector,
            country='World',
            emissions_intensity=emissions_intensity,
            emissions_trend=emissions_trend,
            transition_plan_score=transition_plan_score,
            physical_risk_score=physical_risk_score,
            collateral_type='Unsecured'
        ))
    
    return asset_inputs


def run_legacy_engine(assets: list, scenario_params: dict, scenarios: list, horizons: list):
    """Run the legacy risk engine for comparison"""
    print("\n" + "="*60)
    print("LEGACY ENGINE (risk_engine.py)")
    print("="*60)
    
    engine = RiskEngine(scenario_params)
    results = {}
    
    start_time = time.time()
    
    for scenario in scenarios:
        results[scenario] = {}
        for horizon in horizons:
            result = engine.calculate_scenario_impact(assets, scenario, horizon)
            results[scenario][horizon] = result
            
            print(f"\n{scenario} @ {horizon}:")
            print(f"  Expected Loss: ${result.expected_loss:,.0f} ({result.expected_loss_pct:.2f}%)")
            print(f"  VaR 95: ${result.var_95:,.0f}")
            print(f"  Avg PD Change: {result.avg_pd_change_pct:+.1f}%")
            print(f"  HHI: {result.concentration_hhi:.0f}")
    
    elapsed = time.time() - start_time
    print(f"\n⏱ Legacy Engine Runtime: {elapsed:.3f}s")
    
    return results


def run_new_engine(asset_inputs: list, scenarios: list, horizons: list):
    """Run the new calculation engine"""
    print("\n" + "="*60)
    print("NEW ENGINE (calculation_engine.py)")
    print("="*60)
    
    engine = ClimateRiskCalculationEngine(
        n_simulations=10000,
        correlation=0.3,
        var_method='monte_carlo',
        random_seed=42
    )
    
    results = {}
    
    start_time = time.time()
    
    for scenario in scenarios:
        results[scenario] = {}
        for horizon in horizons:
            result = engine.calculate_scenario(
                assets=asset_inputs,
                scenario=scenario,
                horizon=horizon,
                include_sector_breakdown=True
            )
            results[scenario][horizon] = result
            
            print(f"\n{scenario} @ {horizon}:")
            print(f"  Expected Loss: ${result.expected_loss:,.0f} ({result.expected_loss_pct:.2f}%)")
            print(f"  VaR 95: ${result.var_95:,.0f}")
            print(f"  VaR 99: ${result.var_99:,.0f}")
            print(f"  Expected Shortfall 95: ${result.expected_shortfall_95:,.0f}")
            print(f"  Avg PD Change: {result.avg_pd_change_pct:+.1f}%")
            print(f"  Weighted Avg PD: {result.weighted_avg_pd:.4f}")
            print(f"  Sector HHI: {result.sector_hhi:.0f}")
            print(f"  Rating Migrations: ↑{result.rating_migrations['upgrades']} "
                  f"={result.rating_migrations['stable']} "
                  f"↓{result.rating_migrations['downgrades']}")
    
    elapsed = time.time() - start_time
    print(f"\n⏱ New Engine Runtime: {elapsed:.3f}s")
    
    return results


def compare_results(legacy_results: dict, new_results: dict, scenarios: list, horizons: list):
    """Compare outputs from both engines"""
    print("\n" + "="*60)
    print("COMPARISON & VALIDATION")
    print("="*60)
    
    comparison = []
    
    for scenario in scenarios:
        for horizon in horizons:
            legacy = legacy_results[scenario][horizon]
            new = new_results[scenario][horizon]
            
            # Calculate relative differences
            el_diff = abs(new.expected_loss - legacy.expected_loss) / legacy.expected_loss * 100 if legacy.expected_loss > 0 else 0
            var_diff = abs(new.var_95 - legacy.var_95) / legacy.var_95 * 100 if legacy.var_95 > 0 else 0
            
            comparison.append({
                'scenario': scenario,
                'horizon': horizon,
                'el_legacy': legacy.expected_loss,
                'el_new': new.expected_loss,
                'el_diff_pct': el_diff,
                'var_legacy': legacy.var_95,
                'var_new': new.var_95,
                'var_diff_pct': var_diff,
            })
            
            print(f"\n{scenario} @ {horizon}:")
            print(f"  Expected Loss: ${legacy.expected_loss:,.0f} → ${new.expected_loss:,.0f} ({el_diff:+.1f}%)")
            print(f"  VaR 95: ${legacy.var_95:,.0f} → ${new.var_95:,.0f} ({var_diff:+.1f}%)")
    
    return comparison


def validate_outputs(new_results: dict, scenarios: list, horizons: list):
    """Validate that outputs are bounded and consistent"""
    print("\n" + "="*60)
    print("OUTPUT VALIDATION")
    print("="*60)
    
    all_valid = True
    
    for scenario in scenarios:
        for horizon in horizons:
            result = new_results[scenario][horizon]
            
            checks = {
                'Expected Loss >= 0': result.expected_loss >= 0,
                'Expected Loss % in [0, 100]': 0 <= result.expected_loss_pct <= 100,
                'VaR 95 >= EL': result.var_95 >= result.expected_loss,
                'VaR 99 >= VaR 95': result.var_99 >= result.var_95,
                'ES 95 >= VaR 95': result.expected_shortfall_95 >= result.var_95,
                'Weighted Avg PD in [0, 1]': 0 <= result.weighted_avg_pd <= 1,
                'Sector HHI in [0, 10000]': 0 <= result.sector_hhi <= 10000,
                'Total Exposure > 0': result.total_exposure > 0,
                'No NaN values': not (
                    np.isnan(result.expected_loss) or
                    np.isnan(result.var_95) or
                    np.isnan(result.var_99) or
                    np.isnan(result.weighted_avg_pd)
                )
            }
            
            failed_checks = [name for name, passed in checks.items() if not passed]
            
            if failed_checks:
                print(f"\n❌ {scenario} @ {horizon}: FAILED")
                for check_name in failed_checks:
                    print(f"  - {check_name}")
                all_valid = False
            else:
                print(f"✓ {scenario} @ {horizon}: All checks passed")
    
    return all_valid


async def main():
    """Main POC execution"""
    print("="*60)
    print("CLIMATE RISK CALCULATION ENGINE - PROOF OF CONCEPT")
    print("="*60)
    
    # Load data
    print("\n📊 Loading data from MongoDB...")
    assets = await load_sample_portfolio()
    
    if not assets:
        return
    
    scenario_params = await load_scenario_data()
    print("✓ Loaded scenario data")
    
    # Prepare assets for new engine
    asset_inputs = prepare_assets_for_engine(assets)
    
    scenarios = ['Orderly', 'Disorderly', 'Hot house world']
    horizons = [2030, 2050]  # Test with 2 horizons for speed
    
    # Run legacy engine
    legacy_results = run_legacy_engine(assets, scenario_params, scenarios, horizons)
    
    # Run new engine
    new_results = run_new_engine(asset_inputs, scenarios, horizons)
    
    # Compare
    comparison = compare_results(legacy_results, new_results, scenarios, horizons)
    
    # Validate
    all_valid = validate_outputs(new_results, scenarios, horizons)
    
    # Summary
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    
    if all_valid:
        print("✅ All output validation checks passed")
        print("✅ New engine produces bounded, consistent results")
        print("✅ Ready for integration into /api/analysis/run")
    else:
        print("❌ Some validation checks failed - review output above")
    
    # Save results for inspection
    output_file = '/app/backend/scripts/engine_poc_results.json'
    with open(output_file, 'w') as f:
        # Convert results to serializable format
        serializable_results = {}
        for scenario in scenarios:
            serializable_results[scenario] = {}
            for horizon in horizons:
                result = new_results[scenario][horizon]
                serializable_results[scenario][horizon] = {
                    'expected_loss': result.expected_loss,
                    'expected_loss_pct': result.expected_loss_pct,
                    'var_95': result.var_95,
                    'var_99': result.var_99,
                    'expected_shortfall_95': result.expected_shortfall_95,
                    'expected_shortfall_99': result.expected_shortfall_99,
                    'risk_adjusted_return': result.risk_adjusted_return,
                    'weighted_avg_pd': result.weighted_avg_pd,
                    'avg_pd_change_pct': result.avg_pd_change_pct,
                    'sector_hhi': result.sector_hhi,
                    'geographic_hhi': result.geographic_hhi,
                    'rating_migrations': result.rating_migrations,
                    'total_exposure': result.total_exposure
                }
        
        json.dump(serializable_results, f, indent=2)
    
    print(f"\n📄 Detailed results saved to: {output_file}")


if __name__ == '__main__':
    asyncio.run(main())
