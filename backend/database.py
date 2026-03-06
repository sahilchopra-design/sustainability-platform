"""
database.py — MongoDB stub kept for import compatibility.
All persistent storage is now handled by PostgreSQL (Supabase) via db/base.py.
"""


def get_database():
    """Legacy stub — returns None. Use db/base.py get_db() for PostgreSQL sessions."""
    return None


async def init_db():
    """No-op — MongoDB removed. PostgreSQL initialised via db/base.py."""
    print("[INFO] All data stored in Supabase PostgreSQL (MongoDB removed)")


async def close_db():
    """No-op — PostgreSQL connections managed by SQLAlchemy session factory."""
    pass
