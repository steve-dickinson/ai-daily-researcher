from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie
from src.core.config import settings
from src.db.models import Paper, DailyDigest, UserAnnotation, RSSFeedConfig

async def init_mongo():
    """
    Initialize MongoDB connection and Beanie ODM.
    """
    client = AsyncIOMotorClient(settings.MONGODB_URL)
    # Default database name 'researcher' if not specified in URL
    await init_beanie(database=client.researcher, document_models=[Paper, DailyDigest, UserAnnotation, RSSFeedConfig])
