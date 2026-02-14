from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie
import os
from models import Portfolio, ScenarioSeries, AnalysisRun


MONGO_URL = os.getenv("MONGO_URL", "mongodb://localhost:27017")
DB_NAME = "climate_risk_platform"

_client = None


def get_database():
    """Get raw MongoDB database instance for direct queries."""
    global _client
    if _client is None:
        _client = AsyncIOMotorClient(MONGO_URL)
    return _client[DB_NAME]


async def init_db():
    """Initialize database connection and Beanie ODM"""
    client = AsyncIOMotorClient(MONGO_URL)
    
    await init_beanie(
        database=client[DB_NAME],
        document_models=[
            Portfolio,
            ScenarioSeries,
            AnalysisRun
        ]
    )
    
    print(f"✅ Database initialized: {DB_NAME}")


async def close_db():
    """Close database connection"""
    pass  # Motor handles connection pooling automatically
