"""Main API v1 router"""
from fastapi import APIRouter

from api.v1.routes import portfolios, counterparties, scenarios, analysis, exports

# Create main v1 router
api_router = APIRouter(prefix="/api/v1")

# Include all route modules
api_router.include_router(portfolios.router)
api_router.include_router(counterparties.router)
api_router.include_router(scenarios.router)
api_router.include_router(analysis.router)
api_router.include_router(exports.router)
