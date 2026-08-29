import asyncio
import os
from shared.db.models import Base
from shared.db.session import engine

async def init_models():
    print("Creating database tables...")
    async with engine.begin() as conn:
        # Create all tables (Product, etc.)
        await conn.run_sync(Base.metadata.create_all)
    print("Database tables created successfully!")

if __name__ == "__main__":
    asyncio.run(init_models())
