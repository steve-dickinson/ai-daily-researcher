from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.pool import NullPool
from src.core.config import settings
from src.db.models import Base

# Create async engine with NullPool to allow use across multiple asyncio.run() loops in Streamlit
engine = create_async_engine(settings.POSTGRES_URL, echo=False, poolclass=NullPool)

# Session factory
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False
)

async def init_postgres():
    """
    Initialize Postgres tables.
    Also ensures pgvector extension is created.
    """
    async with engine.begin() as conn:
        # Create extension if not exists (needs superuser usually, 
        # but docker pgvector image has it enabled or user has rights)
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        await conn.run_sync(Base.metadata.create_all)

from sqlalchemy import text
