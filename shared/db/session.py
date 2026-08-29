import os
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from dotenv import load_dotenv

load_dotenv()

# We use asyncpg for fast, asynchronous PostgreSQL access
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://shilpsetu:shilpsetu123@localhost:5432/shilpsetu")

engine = create_async_engine(DATABASE_URL, echo=False)
AsyncSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

async def get_db():
    """
    Dependency to provide a database session for FastAPI routes.
    """
    async with AsyncSessionLocal() as session:
        yield session
