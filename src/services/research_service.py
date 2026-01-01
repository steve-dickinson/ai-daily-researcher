import asyncio
import time
from datetime import datetime, timedelta
from typing import List
from langchain_core.documents import Document
from src.ingestion.arxiv_client import ArxivClient
from src.ai.processor import ai_processor
from src.db.models import Paper, PaperEmbedding, DailyDigest, UserAnnotation
from src.db.postgres import AsyncSessionLocal
from sqlalchemy import select
from beanie.operators import In

from src.ingestion.rss_client import RSSClient

class ResearchService:
    def __init__(self):
        self.arxiv_client = ArxivClient()
        self.rss_client = RSSClient()

    async def run_daily_ingestion(self, max_papers: int = 5, on_progress=None) -> dict:
        """
        Orchestrates the daily ingestion workflow.
        Returns a dictionary of ingestion statistics.
        """
        def log(msg):
            print(msg)
            if on_progress:
                on_progress(msg)

        log("Starting daily ingestion...")
        stats = {"arxiv": 0}
        
        # Fetch from ArXiv
        log("Fetching papers from ArXiv...")
        arxiv_results = list(self.arxiv_client.fetch_recent_papers(days_back=2))
        stats["arxiv"] = len(arxiv_results)
        log(f"Fetched {len(arxiv_results)} ArXiv papers.")
        
        # Fetch from RSS
        rss_results = []
        cutoff_date = time.time() - (2 * 24 * 60 * 60)
        
        for source, url in self.rss_client.feeds.items():
            stats[source] = 0
            log(f"Fetching RSS feed: {source}...")
            try:
                feed_posts = list(self.rss_client.fetch_single_feed(source, url, cutoff_date))
                stats[source] = len(feed_posts)
                rss_results.extend(feed_posts)
            except Exception as e:
                log(f"Error fetching {source}: {e}")

        # Standardize and Combine
        all_items = []
        for res in arxiv_results[:max_papers]:
            meta = self.arxiv_client.get_paper_metadata(res)
            meta['unique_id'] = meta['arxiv_id']
            meta['source'] = 'arxiv'
            all_items.append(meta)
            
        all_items.extend(rss_results)
        
        processed_count = 0
        log(f"Processing {len(all_items)} unique items...")
        
        for item in all_items:
            if await self._process_item(item, log):
                processed_count += 1
            
        log(f"Ingestion complete. Added {processed_count} new items.")
        return stats

    async def _process_item(self, item: dict, log_fn) -> bool:
        """
        Handles deduplication, summarization, storage, and embedding for a single item.
        Returns True if item was new and added, False otherwise.
        """
        unique_id = item["unique_id"]
        
        if await Paper.find_one(Paper.unique_id == unique_id):
            return False
        
        paper = Paper(**item)
        
        # Pass 1 Summary
        if len(paper.abstract) > 50:
             paper.summary_pass_1 = await ai_processor.generate_summary(paper.abstract, pass_level=1)
        else:
             paper.summary_pass_1 = paper.abstract
        
        await paper.insert()
        log_fn(f"Saved: {paper.title[:30]}...")
        
        # Embeddings
        embedding_text = f"{paper.title} {paper.abstract}"
        embedding_vector = await ai_processor.get_embedding(embedding_text)
        
        async with AsyncSessionLocal() as session:
            existing_embedding = await session.execute(
                select(PaperEmbedding).where(PaperEmbedding.unique_id == unique_id)
            )
            if not existing_embedding.scalar_one_or_none():
                session.add(PaperEmbedding(unique_id=unique_id, embedding=embedding_vector))
                await session.commit()
                
        return True

    async def generate_daily_digest(self) -> DailyDigest:
        """Create a blog post from recent papers."""
        cutoff = datetime.now() - timedelta(days=1)
        papers = await Paper.find(Paper.published_date >= cutoff).to_list()
        
        if not papers:
            # Fallback for demo: use latest 5
            papers = await Paper.find_all().sort("-published_date").limit(5).to_list()
            
        if not papers:
            return None

        docs = [
            Document(page_content=p.summary_pass_1 or p.abstract, metadata={"title": p.title})
            for p in papers
        ]
        
        blog_content = await ai_processor.generate_blog_post(docs)
        
        digest = DailyDigest(
            date=datetime.now(),
            markdown_content=blog_content,
            paper_ids=[p.unique_id for p in papers]
        )
        await digest.insert()
        return digest

    async def search_papers(self, query: str, limit: int = 5) -> List[Paper]:
        """Semantic search using Postgres pgvector."""
        query_embedding = await ai_processor.get_embedding(query)
        
        async with AsyncSessionLocal() as session:
            stmt = select(PaperEmbedding.unique_id).order_by(
                PaperEmbedding.embedding.l2_distance(query_embedding)
            ).limit(limit)
            
            result = await session.execute(stmt)
            ids = result.scalars().all()
            
        papers = []
        for uid in ids:
            if p := await Paper.find_one(Paper.unique_id == uid):
                papers.append(p)
                
        return papers

    async def analyze_paper(self, unique_id: str) -> Paper:
        """Perform Pass 2 analysis on a specific paper."""
        paper = await Paper.find_one(Paper.unique_id == unique_id)
        if not paper or paper.summary_pass_2:
            return paper or None
            
        paper.summary_pass_2 = await ai_processor.generate_summary(paper.abstract, pass_level=2)
        await paper.save()
        
        return paper

    # --- Phase 3: Personalization & History ---

    async def toggle_bookmark(self, unique_id: str) -> bool:
        """Toggle bookmark status for a paper. Returns new status."""
        annotation = await UserAnnotation.find_one(UserAnnotation.unique_id == unique_id)
        if not annotation:
            annotation = UserAnnotation(unique_id=unique_id, is_bookmarked=True)
            await annotation.insert()
            return True
        else:
            annotation.is_bookmarked = not annotation.is_bookmarked
            annotation.updated_at = datetime.utcnow()
            await annotation.save()
            return annotation.is_bookmarked

    async def get_user_library(self) -> List[Paper]:
        """Fetch all bookmarked papers."""
        annotations = await UserAnnotation.find(UserAnnotation.is_bookmarked == True).sort("-updated_at").to_list()
        uids = [a.unique_id for a in annotations]
        
        # Papers logic: fetch all matching IDs using In operator
        papers = await Paper.find(In(Paper.unique_id, uids)).to_list()
        return papers

    async def get_bookmark_status(self, unique_id: str) -> bool:
        annotation = await UserAnnotation.find_one(UserAnnotation.unique_id == unique_id)
        return annotation.is_bookmarked if annotation else False
    
    # ... (rest unchanged)

    async def get_papers_by_date(self, date: datetime) -> List[Paper]:
        """Fetch papers published on a specific date (UTC)."""
        # Create 24h window for that date
        start = datetime(date.year, date.month, date.day)
        end = start + timedelta(days=1)
        # Assuming published_date is a datetime object in Mongo
        return await Paper.find(Paper.published_date >= start, Paper.published_date < end).sort("-published_date").to_list()

    async def get_digest_by_date(self, date: datetime) -> DailyDigest:
        """Fetch digest for a specific date."""
        # Because DailyDigest.date might not be exactly midnight, use range
        start = datetime(date.year, date.month, date.day)
        end = start + timedelta(days=1)
        return await DailyDigest.find_one(DailyDigest.date >= start, DailyDigest.date < end)
