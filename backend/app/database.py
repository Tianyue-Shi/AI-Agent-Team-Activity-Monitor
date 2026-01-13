from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase

from app.config import get_settings

settings = get_settings()

# Create async engine
# echo=True logs all SQL statements (useful for debugging)
engine = create_async_engine(
    settings.database_url,
    echo=settings.debug,  # Log SQL in debug mode
)

# Session factory - creates new sessions for each request
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,  # Keep objects usable after commit
)


class Base(DeclarativeBase):
    """
    Base class for all ORM models.
    
    All our database tables will inherit from this.
    SQLAlchemy uses this to track all models and create tables.
    """
    pass


async def get_db() -> AsyncSession:
    """
    Dependency that provides a database session.
    
    Usage in FastAPI:
        @app.get("/items")
        async def get_items(db: AsyncSession = Depends(get_db)):
            ...
    
    The 'yield' makes this a generator - FastAPI will:
    1. Call next() to get the session (before your endpoint runs)
    2. Run your endpoint code
    3. Continue past yield to close the session (cleanup)
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def init_db():
    """
    Create all database tables.
    
    Called once at application startup.
    In production, use Alembic migrations instead.
    """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
