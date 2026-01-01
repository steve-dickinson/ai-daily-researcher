import asyncio
from src.db.mongo import init_mongo
from src.db.postgres import init_postgres
from src.services.research_service import ResearchService

async def main():
    print("Initializing databases...")
    await init_mongo()
    await init_postgres()
    
    service = ResearchService()
    await service.run_daily_ingestion()

if __name__ == "__main__":
    asyncio.run(main())
