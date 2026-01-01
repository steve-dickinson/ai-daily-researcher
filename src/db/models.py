from datetime import datetime
from typing import List, Optional
from uuid import UUID, uuid4

# MongoDB / Beanie
from beanie import Document
from pydantic import Field

# Postgres / SQLAlchemy
from pgvector.sqlalchemy import Vector
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

# --- MongoDB Models ---

class Paper(Document):
    """
    Main Paper/Article document.
    Generalized to support ArXiv papers and Blog posts.
    """
    # Unique identifier: use URL for blogs, arxiv_id for papers (or just URL for everything?)
    # We'll use a calculated 'unique_id' which is arxiv_id OR the url for blogs.
    unique_id: str = Field(unique=True, index=True) 
    
    arxiv_id: Optional[str] = None # Optional now
    source: str = "arxiv" # arxiv, openai, etc.
    title: str
    authors: List[str] = []
    abstract: str
    published_date: datetime
    updated_date: datetime
    pdf_url: str # Serves as the main URL for blogs too
    
    # Generated content
    summary_pass_1: Optional[str] = None
    summary_pass_2: Optional[str] = None
    
    # Category tags
    categories: List[str] = []
    
    class Settings:
        name = "papers"

class DailyDigest(Document):
    """
    Stores generated daily digests/blogs.
    """
    date: datetime = Field(unique=True) # One digest per day
    markdown_content: str
    paper_ids: List[str] # List of unique_ids included
    
    class Settings:
        name = "daily_digests"

class UserAnnotation(Document):
    """
    Stores user interactions.
    """
    # Key linked to Paper.unique_id
    unique_id: str = Field(unique=True, index=True) 
    is_bookmarked: bool = False
    rating: Optional[int] = None
    notes: Optional[str] = None
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "user_annotations"

# --- Postgres Models ---

class Base(DeclarativeBase):
    pass

class PaperEmbedding(Base):
    """
    Stores vector embeddings.
    """
    __tablename__ = "paper_embeddings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    # Linked to Paper.unique_id
    unique_id: Mapped[str] = mapped_column(String, unique=True, index=True)
    
    # Embedding vector
    embedding = mapped_column(Vector(1536))
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
