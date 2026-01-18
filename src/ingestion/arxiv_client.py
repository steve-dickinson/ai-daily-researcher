import arxiv
from datetime import datetime, timedelta, timezone
from typing import List, Generator

class ArxivClient:
    def __init__(self, max_results: int = 50):
        self.client = arxiv.Client(
            page_size=max_results,
            delay_seconds=3.0,
            num_retries=3
        )

    def fetch_recent_papers(
        self, 
        query: str = "cat:cs.AI OR cat:cs.LG OR cat:cs.CL", 
        days_back: int = 1,
        max_results: int = 100
    ) -> Generator[arxiv.Result, None, None]:
        search = arxiv.Search(
            query=query,
            max_results=max_results, 
            sort_by=arxiv.SortCriterion.SubmittedDate,
            sort_order=arxiv.SortOrder.Descending
        )
        
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days_back)
        
        for result in self.client.results(search):
            if result.published >= cutoff_date:
                yield result
            else:
                break

    def get_paper_metadata(self, paper: arxiv.Result) -> dict:
        return {
            "arxiv_id": paper.get_short_id(), # e.g. 2101.12345v1 -> 2101.12345
            "title": paper.title,
            "authors": [a.name for a in paper.authors],
            "abstract": paper.summary,
            "published_date": paper.published,
            "updated_date": paper.updated,
            "pdf_url": paper.pdf_url,
            "categories": paper.categories
        }
