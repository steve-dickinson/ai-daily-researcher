import asyncio
import feedparser
import httpx
from datetime import datetime
from bs4 import BeautifulSoup
from typing import List, Dict, Optional
import re

class ChangelogClient:
    """
    Fetches changelogs/release notes from:
    1. GitHub Copilot (via GitHub Blog RSS)
    2. OpenAI API (via OpenAI News RSS + Python SDK Releases)
    3. ChatGPT (via Scraping Help Center)
    """
    
    def __init__(self):
        self.headers = {
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }

    async def fetch_all(self) -> Dict[str, List[Dict]]:
        """Returns a dict with keys: 'copilot', 'openai', 'chatgpt'."""
        results = {
            "copilot": [],
            "openai": [],
            "chatgpt": []
        }
        
        # Parallel fetch
        copilot, openai, chatgpt = await asyncio.gather(
            self.fetch_copilot(),
            self.fetch_openai(),
            self.fetch_chatgpt()
        )
        
        results["copilot"] = copilot
        results["openai"] = openai
        results["chatgpt"] = chatgpt
        
        return results

    async def fetch_copilot(self) -> List[Dict]:
        """Scrapes GitHub RSS for Copilot news."""
        try:
            feed = feedparser.parse("https://github.blog/changelog/feed/")
            items = []
            for entry in feed.entries:
                # Filter for Copilot
                if "copilot" in entry.title.lower() or "copilot" in entry.summary.lower():
                    items.append({
                        "date": self._parse_date(entry.published),
                        "title": entry.title,
                        "url": entry.link,
                        "content": self._clean_html(entry.summary)[:500] + "...",
                        "source": "GitHub Copilot"
                    })
            return items
        except Exception as e:
            print(f"Error fetching Copilot changelog: {e}")
            return []

    async def fetch_openai(self) -> List[Dict]:
        """Fetches OpenAI News + Python SDK releases."""
        items = []
        try:
            # 1. Official News (looking for API/Product announcements)
            # OpenAI news feed might differ. Handle AttributeError.
            try:
                feed = feedparser.parse("https://openai.com/news/rss.xml")
                for entry in feed.entries:
                    content = entry.get("summary", entry.get("description", ""))
                    items.append({
                        "date": self._parse_date(entry.published),
                        "title": entry.title,
                        "url": entry.link,
                        "content": self._clean_html(content)[:300] + "...",
                        "source": "OpenAI News"
                    })
            except Exception as e:
                print(f"OpenAI News Error: {e}")
            
            # 2. Python SDK (Proxy for API updates)
            try:
                feed_sdk = feedparser.parse("https://github.com/openai/openai-python/releases.atom")
                for entry in feed_sdk.entries:
                     # Atom feeds often have 'content' list
                     body = ""
                     if "content" in entry:
                         body = entry.content[0].value
                     elif "summary" in entry:
                         body = entry.summary
                     
                     items.append({
                        "date": self._parse_date(entry.updated),
                        "title": f"Python SDK {entry.title}",
                        "url": entry.link,
                        "content": self._clean_html(body)[:300] + "...",
                        "source": "OpenAI API (SDK)"
                    })
            except Exception as e:
                 print(f"OpenAI SDK Error: {e}")
                 
            # Sort combined
            items.sort(key=lambda x: x["date"], reverse=True)
            return items
            
        except Exception as e:
            print(f"Error fetching OpenAI changelog: {e}")
            return []

    async def fetch_chatgpt(self) -> List[Dict]:
        """Scrapes ChatGPT Release Notes page."""
        url = "https://help.openai.com/en/articles/6825453-chatgpt-release-notes"
    async def fetch_chatgpt(self) -> List[Dict]:
        """Scrapes ChatGPT Release Notes page."""
        url = "https://help.openai.com/en/articles/6825453-chatgpt-release-notes"
        items = []
        try:
            async with httpx.AsyncClient(follow_redirects=True) as client:
                resp = await client.get(url, headers=self.headers)
                
                if resp.status_code == 200:
                    soup = BeautifulSoup(resp.text, 'html.parser')
                    
                    # Strategy: Find all bold tags <strong> or <b>
                    candidates = soup.find_all(['strong', 'b'])
                    date_pattern = re.compile(r'(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]* ([\d]{1,2})', re.IGNORECASE)
                    
                    for tag in candidates:
                        text = tag.get_text().strip()
                        match = date_pattern.search(text)
                        if match:
                            date_str = match.group(0)
                            parent = tag.parent
                            full_text = parent.get_text().strip()
                            content = full_text.replace(text, "").strip()
                            if not content and parent.next_sibling:
                                content = parent.next_sibling.get_text().strip()[:200]
                            
                            items.append({
                                "date": datetime.now(), 
                                "title": f"Update - {date_str}",
                                "url": url,
                                "content": content[:300] + "..." if content else "See release notes.",
                                "source": "ChatGPT"
                            })

        except Exception as e:
            print(f"Error scraping ChatGPT: {e}")
        
        # Always return fallback if empty
        if not items:
             items.append({
                 "date": datetime.now(),
                 "title": "Recent Updates (View Page)",
                 "url": url,
                 "content": "Refer to official release notes for latest details.",
                 "source": "ChatGPT"
             })
        
        return items[:15]

    def _parse_date(self, date_str: str) -> datetime:
        # Feedparser usually gives struct_time, but sometimes raw string
        # If struct_time:
        try:
             import time
             if isinstance(date_str, time.struct_time):
                 return datetime(*date_str[:6])
             # string parsing fallback...
             return datetime.now() 
        except:
            return datetime.now()

    def _clean_html(self, raw_html: str) -> str:
        clean = re.sub(r'<[^>]+>', '', raw_html)
        return clean.strip()
