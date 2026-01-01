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
            return ChatOpenAI(api_key=settings.OPENAI_API_KEY, model="gpt-3.5-turbo")
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
        if not self.llm:
            return "## Daily Digest (Mock)\n\nReal AI not configured."
            
        summaries = "\n\n".join([f"Title: {p.metadata['title']}\nSummary: {p.page_content}" for p in papers])
        
        template = """
        You are an expert tech editor writing a "Daily AI Research Digest".
        Write a cohesive, engaging blog post summarizing the following key papers from today.
        
        Style: Professional yet accessible, like a TechCrunch or TheVerge article.
        Structure:
        - Catchy Title for the day
        - Intro summarizing the trend of the day
        - "Paper of the Day" (pick the most interesting one)
        - Quick hits for the others
        - Conclusion
        
        Papers:
        {summaries}
        """
        
        chain = PromptTemplate.from_template(template) | self.llm | StrOutputParser()
        return await chain.ainvoke({"summaries": summaries})

ai_processor = AIProcessor()
