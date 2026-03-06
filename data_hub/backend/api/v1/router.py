from fastapi import APIRouter
from api.v1.routes import sources, kpis, mappings, queries, sync, analytics

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(sources.router)
api_router.include_router(kpis.router)
api_router.include_router(mappings.router)
api_router.include_router(queries.router)
api_router.include_router(sync.router)
api_router.include_router(analytics.router)
