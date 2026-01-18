from typing import List, Optional
from langchain_core.documents import Document
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from src.core.config import settings

class AIProcessor:
    def __init__(self):
        self.provider = settings.AI_PROVIDER
        self.llm = self._get_llm()
        self.embeddings = self._get_embeddings()

    def _get_llm(self):
        if self.provider == "openai" and settings.OPENAI_API_KEY:
            return ChatOpenAI(api_key=settings.OPENAI_API_KEY, model=settings.OPENAI_MODEL)
        elif self.provider == "gemini" and settings.GEMINI_API_KEY:
            return ChatGoogleGenerativeAI(google_api_key=settings.GEMINI_API_KEY, model="gemini-pro")
        return None # Mock fallback handled in methods

    def _get_embeddings(self):
        if self.provider == "openai" and settings.OPENAI_API_KEY:
            return OpenAIEmbeddings(api_key=settings.OPENAI_API_KEY)
        elif self.provider == "gemini" and settings.GEMINI_API_KEY:
            return GoogleGenerativeAIEmbeddings(google_api_key=settings.GEMINI_API_KEY, model="models/embedding-001")
        return None

    async def generate_summary(self, text: str, pass_level: int = 1) -> str:
        if not self.llm:
            return f"[Mock Summary Pass {pass_level}] Configure AI_PROVIDER to enable real AI. Text: {text[:50]}..."

        template = """
        You are a research assistant. Summarize the following paper abstract into a "Pass 1" summary.
        Requirements:
        1. One engaging "hook" sentence.
        2. Three bullet points highlighting the key contributions.
        
        Abstract: {text}
        """ if pass_level == 1 else """
        You are a research assistant. Analyze the following text (abstract) for a "Pass 2" deep dive.
        Extract:
        - Key Claims
        - Methodology insights
        - Potential limitations inferred from the abstract
        
        Text: {text}
        """
            
        try:
            chain = PromptTemplate.from_template(template) | self.llm | StrOutputParser()
            return await chain.ainvoke({"text": text})
        except Exception as e:
            return f"Error generating summary: {e}"

    async def get_embedding(self, text: str) -> List[float]:
        if not self.embeddings:
            return [0.0] * 1536
            
        try:
            return await self.embeddings.aembed_query(text)
        except Exception as e:
            print(f"Embedding error: {e}")
            return [0.0] * 1536

    async def generate_blog_post(self, papers: List[Document]) -> str:
        # Legacy method kept for compatibility if needed, or redirect to new logic
        # For now, we update it to use the new logic if papers are mixed?
        # Simpler: just keep it as legacy fallback.
        if not self.llm:
            return "## Daily Digest (Mock)\n\nReal AI not configured."
            
        summaries = "\n\n".join([f"Title: {p.metadata['title']}\nSummary: {p.page_content}" for p in papers])
        
        template = """
        You are an expert tech editor writing a "Daily AI Research Digest".
        Write a cohesive, engaging blog post summarizing the following key research papers, engineering blogs, and industry news from today.
        
        Style: Professional yet accessible, like a TechCrunch or TheVerge article.
        Structure:
        - Catchy Title for the day
        - Intro summarizing the trend of the day
        - "Highlight of the Day" (pick the most interesting paper or blog post)
        - Quick hits for the others
        - Conclusion
        
        Papers:
        {summaries}
        """
        
        chain = PromptTemplate.from_template(template) | self.llm | StrOutputParser()
        return await chain.ainvoke({"summaries": summaries})

    async def generate_structured_digest(self, news_items: List[str], research_papers: List[str]) -> str:
        if not self.llm:
            return "## Daily Digest (Mock)\n\nReal AI not configured."
            
        news_text = "\n---\n".join(news_items)
        research_text = "\n---\n".join(research_papers)
        
        template = """
        You are an expert tech editor writing a "Daily AI Research Digest".
        You have been provided with two sources of information:
        1. **Industry News & Blogs**: High-level updates, product launches, and company news.
        2. **Research Papers**: Academic pre-prints (ArXiv).
        
        **Goal**: Write a comprehensive, structured blog post that covers the most important developments.
        
        **Requirements**:
        - **Don't miss the News**: The 'Industry News' section often contains the "gold" (major announcements). Ensure these are highlighted if significant.
        - **Group by Topic**: Do not just list the research papers. Group them by topic (e.g., "LLM Architectures", "Computer Vision", "Robotics", "Safety").
        - **Links are Critical**: You MUST link to the sources. Use Markdown format: `[Title](URL)`.
        - **Formatting**: Use Markdown with clear headers.
        
        **Structure**:
        # [Catchy Headline for the Day]
        
        ## 🚨 Top Stories
        (Synthesize the biggest news from the Industry News section. ALWAYS link to the source: `[Article Title](URL)`.)
        
        ## 🧠 Research Deep Dive
        (Group the research papers by topic. For each topic, provide a summary of the key advancements. Cite papers using `[Paper Title](URL)`.)
        
        ## ⚡ Quick Hits
        (Bullet points for other interesting items that didn't fit above, mixed news and research. Link them!)
        
        ---
        **Input Data**:
        
        ### SECTION 1: INDUSTRY NEWS & BLOGS
        {news_text}
        
        ### SECTION 2: RESEARCH PAPERS
        {research_text}
        """
        
        try:
            chain = PromptTemplate.from_template(template) | self.llm | StrOutputParser()
            return await chain.ainvoke({"news_text": news_text, "research_text": research_text})
        except Exception as e:
            return f"Error generating digest: {e}"

ai_processor = AIProcessor()
