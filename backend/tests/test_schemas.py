"""Tests for Pydantic v2 schemas"""
import pytest
from decimal import Decimal
from datetime import datetime, timedelta
from pydantic import ValidationError

from schemas.common import (
    Sector, AssetType, ScenarioType, CurrencyCode,
    PaginationParams, DateRangeFilter, MonetaryAmount
)
from schemas.portfolio import (
    PortfolioCreate, PortfolioUpdate, HoldingCreate,
    PortfolioFilter, PortfolioMetrics
)
from schemas.counterparty import (
    CounterpartyCreate, CounterpartyUpdate, CounterpartyFilter
)
from schemas.scenario import (
    ScenarioCreate, ScenarioUpdate, ScenarioVariable,
    ScenarioDataRefreshRequest
)
from schemas.analysis import (
    RunScenarioAnalysisRequest, PortfolioMetrics as AnalysisPortfolioMetrics,
    RatingMigration, SectorExposure, CounterpartyScenarioDetail,
    ScenarioComparisonRequest
)


class TestCommonSchemas:
    """Test common/shared schemas"""
    
    def test_pagination_params_valid(self):
        """Test pagination params with valid values"""
        params = PaginationParams(page=2, page_size=50)
        assert params.page == 2
        assert params.page_size == 50
        assert params.skip == 50
        assert params.limit == 50
    
    def test_pagination_params_defaults(self):
        """Test default pagination values"""
        params = PaginationParams()
        assert params.page == 1
        assert params.page_size == 20
        assert params.skip == 0
    
    def test_pagination_params_invalid(self):
        """Test pagination validation"""
        with pytest.raises(ValidationError):
            PaginationParams(page=0)  # Must be >= 1
        
        with pytest.raises(ValidationError):
            PaginationParams(page_size=150)  # Must be <= 100
    
    def test_date_range_filter_valid(self):
        """Test valid date range"""
        start = datetime(2024, 1, 1)
        end = datetime(2024, 12, 31)
        date_range = DateRangeFilter(start_date=start, end_date=end)
        assert date_range.start_date == start
        assert date_range.end_date == end
    
    def test_date_range_filter_invalid(self):
        """Test invalid date range (end before start)"""
        with pytest.raises(ValidationError) as exc_info:
            DateRangeFilter(
                start_date=datetime(2024, 12, 31),
                end_date=datetime(2024, 1, 1)
            )
        assert "end_date must be after start_date" in str(exc_info.value)
    
    def test_monetary_amount(self):
        """Test monetary amount schema"""
        amount = MonetaryAmount(amount=Decimal("1000000.50"), currency=CurrencyCode.EUR)
        assert amount.amount == Decimal("1000000.50")
        assert amount.currency == CurrencyCode.EUR


class TestPortfolioSchemas:
    """Test portfolio-related schemas"""
    
    def test_portfolio_create_valid(self):
        """Test creating valid portfolio"""
        portfolio = PortfolioCreate(
            name="Test Portfolio",
            description="Test description",
            currency=CurrencyCode.USD
        )
        assert portfolio.name == "Test Portfolio"
        assert portfolio.currency == CurrencyCode.USD
    
    def test_portfolio_create_minimal(self):
        """Test portfolio with minimal required fields"""
        portfolio = PortfolioCreate(name="Minimal Portfolio")
        assert portfolio.name == "Minimal Portfolio"
        assert portfolio.currency == CurrencyCode.USD  # Default
        assert portfolio.description is None
    
    def test_portfolio_create_invalid_name(self):
        """Test portfolio with invalid name"""
        with pytest.raises(ValidationError):
            PortfolioCreate(name="")  # Empty name
    
    def test_holding_create_valid(self):
        """Test creating valid holding"""
        holding = HoldingCreate(
            asset_type=AssetType.BOND,
            company_name="Orsted A/S",
            sector=Sector.POWER,
            subsector="Offshore Wind",
            country_code="dk",  # Should be uppercased
            exposure=Decimal("5000000.00"),
            market_value=Decimal("4850000.00"),
            base_pd=Decimal("0.0150"),
            base_lgd=Decimal("0.4500"),
            rating="BBB+",
            maturity_years=7
        )
        assert holding.country_code == "DK"  # Uppercased
        assert holding.exposure == Decimal("5000000.00")
        assert holding.base_pd == Decimal("0.0150")
    
    def test_holding_create_invalid_pd(self):
        """Test holding with invalid PD (must be 0-1)"""
        with pytest.raises(ValidationError):
            HoldingCreate(
                asset_type=AssetType.BOND,
                company_name="Test Co",
                sector=Sector.POWER,
                exposure=Decimal("1000000"),
                market_value=Decimal("1000000"),
                base_pd=Decimal("1.5"),  # Invalid: > 1
                base_lgd=Decimal("0.45")
            )
    
    def test_holding_create_invalid_exposure(self):
        """Test holding with negative exposure"""
        with pytest.raises(ValidationError):
            HoldingCreate(
                asset_type=AssetType.BOND,
                company_name="Test Co",
                sector=Sector.POWER,
                exposure=Decimal("-1000000"),  # Must be > 0
                market_value=Decimal("1000000"),
                base_pd=Decimal("0.02"),
                base_lgd=Decimal("0.45")
            )
    
    def test_portfolio_filter_valid(self):
        """Test portfolio filter with valid parameters"""
        portfolio_filter = PortfolioFilter(
            name_contains="Energy",
            currency=CurrencyCode.EUR,
            min_exposure=Decimal("1000000"),
            max_exposure=Decimal("100000000"),
            sector=Sector.POWER
        )
        assert portfolio_filter.name_contains == "Energy"
        assert portfolio_filter.min_exposure == Decimal("1000000")
    
    def test_portfolio_filter_invalid_range(self):
        """Test portfolio filter with invalid exposure range"""
        with pytest.raises(ValidationError) as exc_info:
            PortfolioFilter(
                min_exposure=Decimal("100000000"),
                max_exposure=Decimal("1000000")  # Less than min
            )
        assert "max_exposure must be >= min_exposure" in str(exc_info.value)
    
    def test_portfolio_metrics(self):
        """Test portfolio metrics schema"""
        metrics = PortfolioMetrics(
            total_exposure=Decimal("150000000.00"),
            total_market_value=Decimal("148500000.00"),
            num_holdings=45,
            weighted_avg_pd=Decimal("0.0235"),
            weighted_avg_lgd=Decimal("0.4250"),
            expected_loss_baseline=Decimal("1498125.00"),
            sector_concentration={
                "Power Generation": Decimal("0.35"),
                "Oil & Gas": Decimal("0.25")
            },
            geographic_concentration={
                "US": Decimal("0.40"),
                "EU": Decimal("0.35")
            },
            hhi_sector=Decimal("0.2450"),
            hhi_geographic=Decimal("0.3025")
        )
        assert metrics.num_holdings == 45
        assert metrics.hhi_sector == Decimal("0.2450")


class TestCounterpartySchemas:
    """Test counterparty schemas"""
    
    def test_counterparty_create_valid(self):
        """Test creating valid counterparty"""
        counterparty = CounterpartyCreate(
            name="Orsted A/S",
            lei="529900MTJPDPE4MHJ122",
            sector=Sector.POWER,
            country_code="dk",  # Should be uppercased
            emissions_intensity=Decimal("0.1250"),
            baseline_pd=Decimal("0.0150"),
            baseline_lgd=Decimal("0.4500"),
            transition_plan_score=5,
            physical_risk_score=2
        )
        assert counterparty.lei == "529900MTJPDPE4MHJ122"  # Uppercased
        assert counterparty.country_code == "DK"
        assert counterparty.transition_plan_score == 5
    
    def test_counterparty_create_invalid_lei_length(self):
        """Test counterparty with invalid LEI length"""
        with pytest.raises(ValidationError):
            CounterpartyCreate(
                name="Test Co",
                lei="SHORT",  # Must be 20 chars
                sector=Sector.POWER,
                country_code="US",
                baseline_pd=Decimal("0.02"),
                baseline_lgd=Decimal("0.45")
            )
    
    def test_counterparty_create_invalid_score(self):
        """Test counterparty with invalid transition score"""
        with pytest.raises(ValidationError):
            CounterpartyCreate(
                name="Test Co",
                sector=Sector.POWER,
                country_code="US",
                baseline_pd=Decimal("0.02"),
                baseline_lgd=Decimal("0.45"),
                transition_plan_score=6  # Must be 1-5
            )
    
    def test_counterparty_filter(self):
        """Test counterparty filter"""
        cp_filter = CounterpartyFilter(
            sector=Sector.POWER,
            country_code="DK",
            min_pd=Decimal("0.01"),
            max_pd=Decimal("0.05"),
            min_transition_score=4
        )
        assert cp_filter.sector == Sector.POWER
        assert cp_filter.min_transition_score == 4


class TestScenarioSchemas:
    """Test scenario schemas"""
    
    def test_scenario_create_valid(self):
        """Test creating valid scenario"""
        scenario = ScenarioCreate(
            name="Net Zero 2050",
            scenario_type=ScenarioType.ORDERLY,
            description="Immediate policy action",
            temperature_target=Decimal("1.5"),
            carbon_price_trajectory={
                2030: Decimal("100.00"),
                2040: Decimal("250.00"),
                2050: Decimal("500.00")
            },
            is_active=True
        )
        assert scenario.name == "Net Zero 2050"
        assert scenario.temperature_target == Decimal("1.5")
        assert scenario.carbon_price_trajectory[2050] == Decimal("500.00")
    
    def test_scenario_create_invalid_temperature(self):
        """Test scenario with invalid temperature target"""
        with pytest.raises(ValidationError):
            ScenarioCreate(
                name="Test Scenario",
                scenario_type=ScenarioType.ORDERLY,
                temperature_target=Decimal("6.0")  # Must be <= 5.0
            )
    
    def test_scenario_variable(self):
        """Test scenario variable schema"""
        variable = ScenarioVariable(
            variable_name="Price|Carbon",
            region="World",
            unit="USD/tCO2",
            values={
                2030: Decimal("100.00"),
                2040: Decimal("250.00"),
                2050: Decimal("500.00")
            }
        )
        assert variable.variable_name == "Price|Carbon"
        assert variable.values[2030] == Decimal("100.00")
    
    def test_scenario_data_refresh_request(self):
        """Test scenario data refresh request"""
        request = ScenarioDataRefreshRequest(
            force=True,
            source="NGFS_Phase5",
            variables=["Price|Carbon", "Emissions|CO2"]
        )
        assert request.force is True
        assert len(request.variables) == 2


class TestAnalysisSchemas:
    """Test analysis schemas"""
    
    def test_run_scenario_analysis_request_valid(self):
        """Test valid analysis request"""
        request = RunScenarioAnalysisRequest(
            portfolio_id="550e8400-e29b-41d4-a716-446655440000",
            scenario_ids=["660e8400-e29b-41d4-a716-446655440001"],
            time_horizons=[2030, 2040, 2050],
            include_counterparty_detail=True
        )
        assert len(request.scenario_ids) == 1
        assert request.time_horizons == [2030, 2040, 2050]  # Sorted
    
    def test_run_scenario_analysis_unsorted_horizons(self):
        """Test that horizons are automatically sorted"""
        request = RunScenarioAnalysisRequest(
            portfolio_id="550e8400-e29b-41d4-a716-446655440000",
            scenario_ids=["660e8400-e29b-41d4-a716-446655440001"],
            time_horizons=[2050, 2030, 2040]  # Unsorted
        )
        assert request.time_horizons == [2030, 2040, 2050]  # Auto-sorted
    
    def test_run_scenario_analysis_invalid_horizon(self):
        """Test analysis request with invalid time horizon"""
        with pytest.raises(ValidationError) as exc_info:
            RunScenarioAnalysisRequest(
                portfolio_id="550e8400-e29b-41d4-a716-446655440000",
                scenario_ids=["660e8400-e29b-41d4-a716-446655440001"],
                time_horizons=[2020, 2030]  # 2020 is < 2025
            )
        assert "between 2025 and 2100" in str(exc_info.value)
    
    def test_rating_migration(self):
        """Test rating migration schema"""
        migration = RatingMigration(
            upgrades=3,
            downgrades=12,
            stable=30
        )
        assert migration.upgrades == 3
        assert migration.downgrades == 12
    
    def test_sector_exposure(self):
        """Test sector exposure schema"""
        exposure = SectorExposure(
            sector=Sector.POWER,
            exposure_amount=Decimal("52500000.00"),
            exposure_pct=Decimal("35.00"),
            num_holdings=18,
            avg_adjusted_pd=Decimal("0.0285"),
            expected_loss=Decimal("750000.00"),
            climate_risk_score=Decimal("72.5")
        )
        assert exposure.sector == Sector.POWER
        assert exposure.climate_risk_score == Decimal("72.5")
    
    def test_counterparty_scenario_detail(self):
        """Test counterparty scenario detail"""
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
            alert_triggered=False
        )
        assert detail.pd_change_pct == Decimal("23.33")
        assert detail.alert_triggered is False
    
    def test_scenario_comparison_request_valid(self):
        """Test scenario comparison request"""
        request = ScenarioComparisonRequest(
            portfolio_id="550e8400-e29b-41d4-a716-446655440000",
            scenario_ids=[
                "660e8400-e29b-41d4-a716-446655440001",
                "770e8400-e29b-41d4-a716-446655440002"
            ],
            time_horizon=2050
        )
        assert len(request.scenario_ids) == 2
        assert request.time_horizon == 2050
    
    def test_scenario_comparison_request_invalid(self):
        """Test comparison request with too few scenarios"""
        with pytest.raises(ValidationError):
            ScenarioComparisonRequest(
                portfolio_id="550e8400-e29b-41d4-a716-446655440000",
                scenario_ids=["660e8400-e29b-41d4-a716-446655440001"],  # Need >= 2
                time_horizon=2050
            )


class TestSchemaExamples:
    """Test that examples in json_schema_extra are valid"""
    
    def test_portfolio_create_example(self):
        """Test PortfolioCreate example is valid"""
        example = PortfolioCreate.model_config["json_schema_extra"]["example"]
        portfolio = PortfolioCreate(**example)
        assert portfolio.name == "European Green Energy Portfolio"
    
    def test_holding_create_example(self):
        """Test HoldingCreate example is valid"""
        example = HoldingCreate.model_config["json_schema_extra"]["example"]
        holding = HoldingCreate(**example)
        assert holding.company_name == "Orsted A/S"
    
    def test_counterparty_create_example(self):
        """Test CounterpartyCreate example is valid"""
        example = CounterpartyCreate.model_config["json_schema_extra"]["example"]
        counterparty = CounterpartyCreate(**example)
        assert counterparty.name == "Orsted A/S"
    
    def test_scenario_create_example(self):
        """Test ScenarioCreate example is valid"""
        example = ScenarioCreate.model_config["json_schema_extra"]["example"]
        scenario = ScenarioCreate(**example)
        assert scenario.name == "Net Zero 2050"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
