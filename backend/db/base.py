"""SQLAlchemy Base and session management"""
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.pool import NullPool

# Load environment variables from .env file
load_dotenv()

# Get DATABASE_URL from environment
DATABASE_URL = os.environ.get("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError("DATABASE_URL environment variable is not set")

# Create engine with NullPool (Supabase handles connection pooling)
engine = create_engine(
    DATABASE_URL,
    poolclass=NullPool,
    echo=False,
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for declarative models
Base = declarative_base()


def get_db():
    """FastAPI dependency to get database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Initialize database - create all tables."""
    # Import all models to register them with Base.metadata
    from db.models.scenario import (
        Scenario,
        ScenarioVersion,
        ScenarioImpactPreview,
        NGFSDataSource,
    )
    from db.models.data_hub import (
        DataHubSource,
        DataHubScenario,
        DataHubTrajectory,
        DataHubComparison,
        DataHubSyncLog,
        DataHubFavorite,
        GapAnalysis,
        ConsistencyCheck,
        ScenarioAlert,
    )
    from db.models.ngfs_v2 import (
        NGFSScenario,
        NGFSScenarioParameter,
        NGFSScenarioTimeSeries,
    )
    from db.models.custom_builder import (
        CustomScenario,
        ParameterCustomization,
        SimulationRun,
    )
    Base.metadata.create_all(bind=engine)
    print("✅ PostgreSQL database tables created")
