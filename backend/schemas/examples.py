"""
Example usage of Pydantic v2 schemas for Climate Risk API

This script demonstrates:
1. Creating portfolios with validation
2. Adding holdings to portfolios
3. Running scenario analysis
4. Handling validation errors
5. Using filters and pagination
"""

from decimal import Decimal
from datetime import datetime
from pydantic import ValidationError

# Import schemas
from schemas import (
    # Portfolio schemas
    PortfolioCreate, HoldingCreate, PortfolioFilter,
    # Counterparty schemas
    CounterpartyCreate, CounterpartyFilter,
    # Scenario schemas
    ScenarioCreate, ScenarioVariable,
    # Analysis schemas
    RunScenarioAnalysisRequest, RatingMigration,
    SectorExposure, CounterpartyScenarioDetail,
    # Common utilities
    PaginationParams, DateRangeFilter,
    Sector, AssetType, ScenarioType, CurrencyCode
)


def example_create_portfolio():
    """Example: Create a new portfolio"""
    print("\n=== Example 1: Create Portfolio ===")
    
    portfolio = PortfolioCreate(
        name="European Renewable Energy Fund",
        description="Focus on wind, solar, and hydro across EU",
        currency=CurrencyCode.EUR,
        metadata={
            "fund_manager": "GreenCapital Partners",
            "inception_date": "2020-01-15",
            "target_return": 8.5
        }
    )
    
    print(f"Portfolio Name: {portfolio.name}")
    print(f"Currency: {portfolio.currency}")
    print(f"Metadata: {portfolio.metadata}")
    print(f"\nJSON representation:")
    print(portfolio.model_dump_json(indent=2))


def example_add_holdings():
    """Example: Add holdings to portfolio"""
    print("\n=== Example 2: Add Holdings ===")
    
    # Valid holding
    holding = HoldingCreate(
        asset_type=AssetType.BOND,
        company_name="Orsted A/S",
        sector=Sector.POWER,
        subsector="Offshore Wind",
        country_code="dk",  # Will be auto-uppercased to "DK"
        exposure=Decimal("5000000.00"),
        market_value=Decimal("4850000.00"),
        base_pd=Decimal("0.0150"),
        base_lgd=Decimal("0.4500"),
        rating="BBB+",
        maturity_years=7
    )
    
    print(f"Company: {holding.company_name}")
    print(f"Sector: {holding.sector}")
    print(f"Country: {holding.country_code}")  # DK (uppercased)
    print(f"Exposure: ${holding.exposure:,.2f}")
    print(f"Base PD: {holding.base_pd:.4f}")
    
    # Try creating invalid holding
    try:
        invalid_holding = HoldingCreate(
            asset_type=AssetType.BOND,
            company_name="Test Company",
            sector=Sector.POWER,
            exposure=Decimal("-1000000"),  # Invalid: negative
            market_value=Decimal("1000000"),
            base_pd=Decimal("1.5"),  # Invalid: > 1
            base_lgd=Decimal("0.45")
        )
    except ValidationError as e:
        print("\n⚠️  Validation Error (expected):")
        for error in e.errors():
            print(f"  - Field: {error['loc']}, Error: {error['msg']}")


def example_create_counterparty():
    """Example: Create counterparty with climate data"""
    print("\n=== Example 3: Create Counterparty ===")
    
    counterparty = CounterpartyCreate(
        name="Orsted A/S",
        lei="529900MTJPDPE4MHJ122",  # Legal Entity Identifier
        sector=Sector.POWER,
        country_code="DK",
        emissions_intensity=Decimal("0.1250"),  # tCO2e per revenue unit
        emissions_trend="Improving",
        transition_plan_score=5,  # 1-5 scale (5 = best)
        physical_risk_score=2,    # 1-5 scale (1 = lowest risk)
        baseline_pd=Decimal("0.0150"),
        baseline_lgd=Decimal("0.4500"),
        metadata={
            "renewable_capacity_mw": 15000,
            "offshore_wind_share": 0.85,
            "net_zero_target_year": 2040
        }
    )
    
    print(f"Counterparty: {counterparty.name}")
    print(f"LEI: {counterparty.lei}")
    print(f"Transition Plan Score: {counterparty.transition_plan_score}/5")
    print(f"Emissions Trend: {counterparty.emissions_trend}")
    print(f"Baseline PD: {counterparty.baseline_pd:.4f}")


def example_create_scenario():
    """Example: Create NGFS climate scenario"""
    print("\n=== Example 4: Create Scenario ===")
    
    scenario = ScenarioCreate(
        name="Net Zero 2050",
        scenario_type=ScenarioType.ORDERLY,
        description="Immediate policy action with net zero emissions by 2050",
        temperature_target=Decimal("1.5"),
        carbon_price_trajectory={
            2030: Decimal("100.00"),
            2040: Decimal("250.00"),
            2050: Decimal("500.00")
        },
        is_active=True,
        metadata={
            "ngfs_version": "Phase 5",
            "model": "REMIND-MAgPIE 3.0",
            "policy_stringency": "high",
            "renewable_share_2050": 0.85
        }
    )
    
    print(f"Scenario: {scenario.name}")
    print(f"Type: {scenario.scenario_type}")
    print(f"Temperature Target: {scenario.temperature_target}°C")
    print(f"Carbon Price Trajectory:")
    for year, price in scenario.carbon_price_trajectory.items():
        print(f"  {year}: ${price}/tCO2")


def example_run_analysis():
    """Example: Run scenario analysis"""
    print("\n=== Example 5: Run Scenario Analysis ===")
    
    request = RunScenarioAnalysisRequest(
        portfolio_id="550e8400-e29b-41d4-a716-446655440000",
        scenario_ids=[
            "660e8400-e29b-41d4-a716-446655440001",  # Net Zero 2050
            "770e8400-e29b-41d4-a716-446655440002",  # Delayed Transition
            "880e8400-e29b-41d4-a716-446655440003"   # Current Policies
        ],
        time_horizons=[2050, 2030, 2040],  # Will be auto-sorted to [2030, 2040, 2050]
        include_counterparty_detail=True,
        include_sector_breakdown=True,
        include_geographic_breakdown=True
    )
    
    print(f"Portfolio ID: {request.portfolio_id}")
    print(f"Scenarios: {len(request.scenario_ids)} scenarios")
    print(f"Time Horizons: {request.time_horizons}")  # [2030, 2040, 2050]
    print(f"Include Details: Counterparty={request.include_counterparty_detail}, Sector={request.include_sector_breakdown}")


def example_analysis_results():
    """Example: Analysis result structures"""
    print("\n=== Example 6: Analysis Results ===")
    
    # Rating migration
    migration = RatingMigration(
        upgrades=3,
        downgrades=12,
        stable=30
    )
    print(f"Rating Migrations: ↑{migration.upgrades} ={migration.stable} ↓{migration.downgrades}")
    
    # Sector exposure
    sector = SectorExposure(
        sector=Sector.POWER,
        exposure_amount=Decimal("52500000.00"),
        exposure_pct=Decimal("35.00"),
        num_holdings=18,
        avg_adjusted_pd=Decimal("0.0285"),
        expected_loss=Decimal("750000.00"),
        climate_risk_score=Decimal("72.5")
    )
    print(f"\nSector: {sector.sector}")
    print(f"Exposure: ${sector.exposure_amount:,.2f} ({sector.exposure_pct}%)")
    print(f"Climate Risk Score: {sector.climate_risk_score}/100")
    
    # Counterparty detail
    detail = CounterpartyScenarioDetail(
        counterparty_id="880e8400-e29b-41d4-a716-446655440003",
        counterparty_name="Orsted A/S",
        sector=Sector.POWER,
        exposure_amount=Decimal("5000000.00"),
        baseline_pd=Decimal("0.0150"),
        adjusted_pd=Decimal("0.0185"),
        pd_change_pct=Decimal("23.33"),
        expected_loss=Decimal("41625.00"),
        velocity_score=Decimal("1.25"),
        velocity_trajectory="Converging",
        alert_triggered=False
    )
    print(f"\nCounterparty: {detail.counterparty_name}")
    print(f"PD Change: {detail.pd_change_pct:.2f}%")
    print(f"Alert Triggered: {detail.alert_triggered}")


def example_filtering():
    """Example: Using filters"""
    print("\n=== Example 7: Filtering and Pagination ===")
    
    # Portfolio filter
    portfolio_filter = PortfolioFilter(
        name_contains="Energy",
        currency=CurrencyCode.EUR,
        min_exposure=Decimal("1000000.00"),
        max_exposure=Decimal("100000000.00"),
        sector=Sector.POWER,
        created_after=datetime(2023, 1, 1)
    )
    print("Portfolio Filter:")
    print(f"  Name contains: '{portfolio_filter.name_contains}'")
    print(f"  Currency: {portfolio_filter.currency}")
    print(f"  Exposure range: ${portfolio_filter.min_exposure:,.0f} - ${portfolio_filter.max_exposure:,.0f}")
    
    # Counterparty filter
    cp_filter = CounterpartyFilter(
        sector=Sector.POWER,
        country_code="DK",
        emissions_trend="Improving",
        min_transition_score=4,
        has_lei=True
    )
    print("\nCounterparty Filter:")
    print(f"  Sector: {cp_filter.sector}")
    print(f"  Country: {cp_filter.country_code}")
    print(f"  Min Transition Score: {cp_filter.min_transition_score}/5")
    
    # Pagination
    pagination = PaginationParams(page=2, page_size=50)
    print(f"\nPagination:")
    print(f"  Page: {pagination.page}")
    print(f"  Page Size: {pagination.page_size}")
    print(f"  Skip: {pagination.skip} records")
    print(f"  Limit: {pagination.limit} records")


def example_date_range_validation():
    """Example: Date range validation"""
    print("\n=== Example 8: Date Range Validation ===")
    
    # Valid date range
    valid_range = DateRangeFilter(
        start_date=datetime(2024, 1, 1),
        end_date=datetime(2024, 12, 31)
    )
    print(f"Valid range: {valid_range.start_date.date()} to {valid_range.end_date.date()}")
    
    # Invalid date range (end before start)
    try:
        invalid_range = DateRangeFilter(
            start_date=datetime(2024, 12, 31),
            end_date=datetime(2024, 1, 1)
        )
    except ValidationError as e:
        print("\n⚠️  Validation Error (expected):")
        print(f"  {e.errors()[0]['msg']}")


def example_serialization():
    """Example: JSON serialization"""
    print("\n=== Example 9: JSON Serialization ===")
    
    holding = HoldingCreate(
        asset_type=AssetType.BOND,
        company_name="Orsted A/S",
        sector=Sector.POWER,
        exposure=Decimal("5000000.00"),
        market_value=Decimal("4850000.00"),
        base_pd=Decimal("0.0150"),
        base_lgd=Decimal("0.4500")
    )
    
    # To dict
    data_dict = holding.model_dump()
    print("As dictionary:")
    print(f"  Type: {data_dict['asset_type']}")
    print(f"  Exposure: {data_dict['exposure']}")
    
    # To JSON
    json_str = holding.model_dump_json(indent=2)
    print("\nAs JSON:")
    print(json_str[:200] + "...")


if __name__ == "__main__":
    print("=" * 70)
    print("PYDANTIC V2 SCHEMA EXAMPLES")
    print("Climate Credit Risk Intelligence Platform")
    print("=" * 70)
    
    example_create_portfolio()
    example_add_holdings()
    example_create_counterparty()
    example_create_scenario()
    example_run_analysis()
    example_analysis_results()
    example_filtering()
    example_date_range_validation()
    example_serialization()
    
    print("\n" + "=" * 70)
    print("✅ All examples completed successfully!")
    print("=" * 70)
