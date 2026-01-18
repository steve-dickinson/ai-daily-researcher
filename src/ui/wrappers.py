import asyncio
import datetime
from src.db.mongo import init_mongo
from src.db.postgres import init_postgres
from src.db.models import Paper
from src.services.research_service import ResearchService

# Initialize Service
service = ResearchService()

# --- Async Helper ---
def run_async(coro):
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    return loop.run_until_complete(coro)

# --- Core Wrappers ---
async def main_ingestion_wrapper(max_papers=5, on_progress=None):
    await init_mongo()
    await init_postgres()
    return await service.run_daily_ingestion(max_papers=max_papers, on_progress=on_progress)

async def get_recent_papers_wrapper():
    await init_mongo()
    await init_postgres()
    return await Paper.find_all().sort("-published_date").limit(20).to_list()

async def search_wrapper(query: str):
    await init_mongo()
    await init_postgres()
    return await service.search_papers(query, limit=5)

async def digest_wrapper(date=None):
    await init_mongo()
    await init_postgres()
    return await service.generate_daily_digest(date)

async def analyze_wrapper(arxiv_id: str):
    await init_mongo()
    await init_postgres()
    return await service.analyze_paper(arxiv_id)

async def toggle_bookmark_wrapper(arxiv_id: str):
    await init_mongo()
    await init_postgres()
    return await service.toggle_bookmark(arxiv_id)

async def get_library_wrapper():
    await init_mongo()
    await init_postgres()
    return await service.get_user_library()

async def get_bookmark_status_wrapper(arxiv_id: str):
    await init_mongo()
    await init_postgres()
    return await service.get_bookmark_status(arxiv_id)

async def get_papers_by_date_wrapper(date):
    await init_mongo()
    await init_postgres()
    return await service.get_papers_by_date(date)

async def get_digest_by_date_wrapper(date):
    await init_mongo()
    await init_postgres()
    return await service.get_digest_by_date(date)

async def get_all_papers_wrapper():
    await init_mongo()
    return await service.get_all_papers_sorted()

# --- RSS Wrappers ---
async def get_feeds_wrapper():
    await init_mongo()
    return await service.get_all_feeds()

async def add_feed_wrapper(name, url):
    await init_mongo()
    await service.add_rss_feed(name, url)

async def delete_feed_wrapper(name):
    await init_mongo()
    await service.delete_rss_feed(name)

from src.seed_db import seed_data
async def seed_data_wrapper(log_fn):
    return await seed_data(days_back=30, log_fn=log_fn)

async def get_changelogs_wrapper():
    await init_mongo()
    return await service.get_latest_changelogs()
