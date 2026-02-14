# Pydantic v2 Schema Documentation

Comprehensive type-safe schemas for the Climate Credit Risk Intelligence Platform API.

## Overview

This schema system provides:
- **Type Safety**: Full Pydantic v2 type validation
- **API Documentation**: Automatic OpenAPI/Swagger generation
- **Data Validation**: Field-level constraints and custom validators
- **Examples**: JSON schema examples for all request/response types
- **Reusability**: Shared base models and mixins

## Schema Organization

```
schemas/
├── common.py          # Shared enums, mixins, and utilities
├── portfolio.py       # Portfolio and holding schemas
├── counterparty.py    # Counterparty/company schemas
├── scenario.py        # NGFS scenario schemas
└── analysis.py        # Risk analysis request/response schemas
```

## Key Features

### 1. Enums for Type Safety

```python
from schemas.common import Sector, AssetType, ScenarioType

sector = Sector.POWER  # Power Generation
asset = AssetType.BOND
scenario = ScenarioType.ORDERLY
```

### 2. Financial Precision

All monetary amounts use `Decimal` with proper precision:
- Currency amounts: 2 decimal places
- Probabilities (PD, LGD): 4 decimal places
- Percentages: 2 decimal places

### 3. Automatic Validation

```python
from schemas.portfolio import HoldingCreate

# Valid
holding = HoldingCreate(
    asset_type="Bond",
    company_name="Orsted A/S",
    sector="Power Generation",
    exposure="5000000.00",
    base_pd="0.0150",  # Validated: 0 <= PD <= 1
    base_lgd="0.4500"
)

# Invalid - raises ValidationError
holding = HoldingCreate(
    exposure="-1000000",  # Must be > 0
    base_pd="1.5"  # Must be <= 1
)
```

### 4. Pagination & Filtering

```python
from schemas.common import PaginationParams
from schemas.portfolio import PortfolioFilter

# Pagination
params = PaginationParams(page=2, page_size=50)
skip = params.skip  # 50
limit = params.limit  # 50

# Filtering
filters = PortfolioFilter(
    name_contains="Energy",
    min_exposure="1000000",
    sector="Power Generation"
)
```

### 5. Request Schemas

#### Create Portfolio
```python
from schemas.portfolio import PortfolioCreate

request = PortfolioCreate(
    name="European Green Energy Portfolio",
    description="Focused on renewable energy",
    currency="EUR"
)
```

#### Run Analysis
```python
from schemas.analysis import RunScenarioAnalysisRequest

request = RunScenarioAnalysisRequest(
    portfolio_id="550e8400-e29b-41d4-a716-446655440000",
    scenario_ids=["660e...", "770e..."],
    time_horizons=[2030, 2040, 2050],
    include_counterparty_detail=True
)
```

### 6. Response Schemas

#### Portfolio Response
```python
from schemas.portfolio import PortfolioResponse

{
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "name": "European Green Energy Portfolio",
    "holdings": [...],
    "metrics": {
        "total_exposure": "150000000.00",
        "weighted_avg_pd": "0.0235",
        "hhi_sector": "0.2450"
    },
    "created_at": "2024-01-15T10:30:00Z"
}
```

#### Analysis Results
```python
from schemas.analysis import ScenarioResultResponse

{
    "analysis_id": "...",
    "portfolio_id": "...",
    "portfolio_metrics": [
        {
            "scenario_name": "Net Zero 2050",
            "time_horizon": 2050,
            "expected_loss": "2250000.00",
            "value_at_risk_95": "3500000.00",
            "climate_risk_contribution_pct": "65.50"
        }
    ],
    "sector_breakdown": [...],
    "counterparty_details": [...]
}
```

## Common Patterns

### Create/Update Pattern
```python
# Create: All required fields
PortfolioCreate(name="...", ...)

# Update: All fields optional
PortfolioUpdate(name="New Name")  # Only update name
```

### Base/Response Pattern
```python
# Base: Shared fields
class PortfolioBase(BaseModel):
    name: str
    description: Optional[str]

# Response: Adds ID, timestamps
class PortfolioResponse(PortfolioBase, TimestampMixin):
    id: str
    created_at: datetime
```

### Summary/Detail Pattern
```python
# Summary: Lightweight for lists
PortfolioSummary(id, name, num_holdings, total_exposure)

# Response: Full details with relationships
PortfolioResponse(id, name, holdings=[...], metrics={...})
```

## Field Validators

### Custom Validation
```python
from pydantic import field_validator

class DateRangeFilter(BaseModel):
    start_date: Optional[datetime]
    end_date: Optional[datetime]
    
    @field_validator('end_date')
    @classmethod
    def validate_date_range(cls, v, info):
        if v and info.data.get('start_date'):
            if v < info.data['start_date']:
                raise ValueError('end_date must be after start_date')
        return v
```

### String Normalization
```python
@field_validator('country_code')
@classmethod
def validate_country_code(cls, v: str) -> str:
    return v.upper()  # DK, US, etc.
```

### Range Validation
```python
transition_plan_score: Optional[int] = Field(
    default=None,
    ge=1,  # Greater than or equal to 1
    le=5,  # Less than or equal to 5
    description="Quality of climate transition plan (1-5)"
)
```

## Testing

Run schema tests:
```bash
cd /app/backend
pytest tests/test_schemas.py -v
```

All schemas include:
- Validation tests for valid data
- Validation tests for invalid data
- Example validation (ensures documentation examples work)
- Edge case testing

## Integration with FastAPI

```python
from fastapi import FastAPI
from schemas.portfolio import PortfolioCreate, PortfolioResponse

app = FastAPI()

@app.post("/portfolios", response_model=PortfolioResponse)
async def create_portfolio(data: PortfolioCreate):
    # Pydantic validates incoming data
    # FastAPI serializes response with PortfolioResponse schema
    ...
```

Benefits:
- Automatic request validation
- Type hints in IDE
- OpenAPI documentation generation
- Consistent error messages

## Best Practices

1. **Use Enums**: Define fixed sets of values as enums
2. **Decimal for Money**: Never use float for financial amounts
3. **Optional Carefully**: Make fields optional only if truly optional
4. **Examples**: Always include json_schema_extra examples
5. **Validators**: Add custom validators for complex business rules
6. **Descriptive Fields**: Use Field() with descriptions for API docs

## Schema Hierarchy

```
Common (Base Models & Enums)
    ↓
Portfolio ← Counterparty → Scenario
    ↓           ↓              ↓
    └─────── Analysis ─────────┘
```

## Future Enhancements

Potential additions:
- [ ] CSV import/export schemas
- [ ] Batch operation schemas
- [ ] Webhook event schemas
- [ ] Audit log schemas
- [ ] Report generation schemas

## References

- [Pydantic v2 Documentation](https://docs.pydantic.dev/latest/)
- [FastAPI with Pydantic](https://fastapi.tiangolo.com/tutorial/body/)
- [JSON Schema](https://json-schema.org/)
