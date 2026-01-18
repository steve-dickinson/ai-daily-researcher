import asyncio
import sys
import os
from sqlalchemy import select

# Add the project root to the python path to ensure imports work correctly
sys.path.append(os.getcwd())

from src.db.mongo import init_mongo
from src.db.postgres import init_postgres, AsyncSessionLocal
from src.db.models import Paper, PaperEmbedding
from src.ingestion.arxiv_client import ArxivClient
from src.ingestion.rss_client import RSSClient
from src.core.config import settings
from src.ai.processor import ai_processor

async def ensure_embedding(paper):
    """Generates and saves embedding if it doesn't exist."""
    try:
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(PaperEmbedding).where(PaperEmbedding.unique_id == paper.unique_id)
            )
            if result.scalar_one_or_none():
                return False # Already exists

            # Generate
            text = f"{paper.title} {paper.abstract}"
            vector = await ai_processor.get_embedding(text)
            
            # Insert
            session.add(PaperEmbedding(unique_id=paper.unique_id, embedding=vector))
            await session.commit()
            return True
    except Exception as e:
        print(f"Embedding error for {paper.unique_id}: {e}")
        return False

async def seed_data(days_back=30, log_fn=print):
    log_fn(f"Initializing MongoDB...")
    await init_mongo()
    log_fn(f"Initializing Postgres...")
    await init_postgres()
    
    stats = {"arxiv_new": 0, "arxiv_skipped": 0, "rss_new": 0, "rss_skipped": 0, "embeddings_created": 0}
    
    # 1. Seed ArXiv Papers
    log_fn(f"\n--- Seeding ArXiv Papers (Past {days_back} days) ---")
    arxiv_client = ArxivClient()
    
    # Fetch a good amount to ensure we cover the days (arxiv search limit)
    max_results = 500
    
    try:
        # returns generator of arxiv.Result
        results = arxiv_client.fetch_recent_papers(days_back=days_back, max_results=max_results)
        
        for result in results:
            meta = arxiv_client.get_paper_metadata(result)
            
            # Prepare Paper document data
            paper_data = meta.copy()
            paper_data["source"] = "arxiv"
            paper_data["unique_id"] = meta["arxiv_id"] # Use arxiv_id as unique_id for papers
            
            # Check existence
            existing = await Paper.find_one(Paper.unique_id == paper_data["unique_id"])
            if existing:
                stats["arxiv_skipped"] += 1
                # Check embedding even if paper exists
                if await ensure_embedding(existing):
                     stats["embeddings_created"] += 1
            else:
                new_paper = Paper(**paper_data)
                await new_paper.insert()
                stats["arxiv_new"] += 1
                log_fn(f"Inserted: {paper_data['title'][:50]}...")
                if await ensure_embedding(new_paper):
                     stats["embeddings_created"] += 1
                
    except Exception as e:
        log_fn(f"\nError fetching ArXiv: {e}")

    log_fn(f"ArXiv Summary: {stats['arxiv_new']} new, {stats['arxiv_skipped']} skipped.")

    # 2. Seed RSS Feeds
    log_fn(f"\n--- Seeding RSS Feeds (Past {days_back} days) ---")
    rss_client = RSSClient()
    
    try:
        # returns async generator
        async for post in rss_client.fetch_recent_posts(days_back=days_back):
            # Check existence
            existing = await Paper.find_one(Paper.unique_id == post["unique_id"])
            if existing:
                stats["rss_skipped"] += 1
                if await ensure_embedding(existing):
                     stats["embeddings_created"] += 1
            else:
                new_paper = Paper(**post)
                await new_paper.insert()
                stats["rss_new"] += 1
                log_fn(f"Inserted: {post['title'][:50]}...")
                if await ensure_embedding(new_paper):
                     stats["embeddings_created"] += 1

    except Exception as e:
        log_fn(f"\nError fetching RSS: {e}")

    log_fn(f"RSS Summary: {stats['rss_new']} new, {stats['rss_skipped']} skipped.")
    log_fn(f"\nTotal Embeddings Created: {stats['embeddings_created']}")
    log_fn("\n--- Seeding Complete ---")
    return stats

if __name__ == "__main__":
    asyncio.run(seed_data())
