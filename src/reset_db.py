import asyncio
import sys
import os

# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.db.mongo import init_mongo
from src.db.postgres import init_postgres, AsyncSessionLocal
from src.db.models import Paper, DailyDigest, PaperEmbedding, UserAnnotation
from sqlalchemy import delete, text

async def reset_databases():
    print("Initializing databases...")
    await init_mongo()
    await init_postgres()
    
    print("Clearing MongoDB collections...")
    await Paper.delete_all()
    print("  - Papers cleared.")
    await DailyDigest.delete_all()
    print("  - Daily Digests cleared.")
    await UserAnnotation.delete_all()
    print("  - User Annotations cleared.")
    
    print("Clearing Postgres tables...")
    async with AsyncSessionLocal() as session:
        # Drop the table so it gets recreated with new schema
        await session.execute(text("DROP TABLE IF EXISTS paper_embeddings CASCADE"))
        await session.commit()
    print("  - Paper Embeddings table dropped.")
    
    print("Reset complete! You can now ingest fresh data.")

if __name__ == "__main__":
    # Always run without prompt for now to ensure it works from agent
    asyncio.run(reset_databases())
