import feedparser
from datetime import datetime, timezone
import time
from typing import List, Generator

from src.db.models import RSSFeedConfig

class RSSClient:
    def __init__(self):
        # Default feeds to seed if DB is empty
        self.default_feeds = {
            "openai": "https://openai.com/blog/rss.xml",
            "google_deepmind": "https://deepmind.google/blog/rss.xml",
            "anthropic": "https://www.anthropic.com/rss",
            "huggingface": "https://huggingface.co/blog/feed.xml",
        }

    async def get_active_feeds(self) -> List[RSSFeedConfig]:
        """Fetch active feeds from DB, seeding defaults if empty."""
        # Check if any feeds exist
        count = await RSSFeedConfig.count()
        if count == 0:
            print("Seeding default RSS feeds...")
            for name, url in self.default_feeds.items():
                await RSSFeedConfig(name=name, url=url).insert()
        
        return await RSSFeedConfig.find(RSSFeedConfig.is_active == True).to_list()

    async def fetch_recent_posts(self, days_back: int = 1) -> Generator[dict, None, None]:
        """
        Fetch posts from all configured RSS feeds from the last N days.
        """
        cutoff_date = time.time() - (days_back * 24 * 60 * 60)
        
        feeds = await self.get_active_feeds()
        
        for feed in feeds:
            # Yield from sub-generator
            for item in self.fetch_single_feed(feed.name, feed.url, cutoff_date):
                yield item

    def fetch_single_feed(self, source: str, url: str, cutoff_date: float) -> Generator[dict, None, None]:
        try:
            feed = feedparser.parse(url)
            # print(f"Fetching RSS: {source} ({len(feed.entries)} entries)")
            
            for entry in feed.entries:
                # Parse published date
                published_ts = 0
                if hasattr(entry, 'published_parsed') and entry.published_parsed:
                        published_ts = time.mktime(entry.published_parsed)
                elif hasattr(entry, 'updated_parsed') and entry.updated_parsed:
                        published_ts = time.mktime(entry.updated_parsed)
                
                if published_ts >= cutoff_date:
                    # Convert abstract/summary
                    summary = getattr(entry, 'summary', '') or getattr(entry, 'description', '')
                    
                    yield {
                        "unique_id": entry.link, 
                        "arxiv_id": None,
                        "source": source,
                        "title": entry.title,
                        "authors": [getattr(entry, 'author', source)],
                        "abstract": summary,
                        "published_date": datetime.fromtimestamp(published_ts, timezone.utc),
                        "updated_date": datetime.now(timezone.utc),
                        "pdf_url": entry.link,
                        "categories": ["blog", "industry"]
                    }
        except Exception as e:
            print(f"Error fetching {source}: {e}")
