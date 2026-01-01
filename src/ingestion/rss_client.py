import feedparser
from datetime import datetime, timezone
import time
from typing import List, Generator

class RSSClient:
    def __init__(self):
        self.feeds = {
            "openai": "https://openai.com/blog/rss.xml",
            "google_deepmind": "https://deepmind.google/blog/rss.xml",
            "anthropic": "https://www.anthropic.com/rss",
            "huggingface": "https://huggingface.co/blog/feed.xml",
        }

    def fetch_recent_posts(self, days_back: int = 1) -> Generator[dict, None, None]:
        """
        Fetch posts from all configured RSS feeds from the last N days.
        """
        cutoff_date = time.time() - (days_back * 24 * 60 * 60)
        
        for source, url in self.feeds.items():
            yield from self.fetch_single_feed(source, url, cutoff_date)

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
