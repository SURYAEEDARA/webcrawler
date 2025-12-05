from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, List
from datetime import datetime

class WebPage(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    url: str = Field(index=True)
    title: Optional[str] = Field(default=None)
    scraped_content: Optional[str] = Field(default=None)
    word_count: Optional[int] = Field(default=0)
    grammar_score: Optional[int] = Field(default=None)
    improvement_suggestions: Optional[str] = Field(default=None)
    analysis_result: Optional[str] = Field(default=None)
    status_code: Optional[int] = Field(default=None)
    load_time: Optional[float] = Field(default=None)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    website_id: Optional[int] = Field(default=None, foreign_key="website.id")
    
    broken_links_data: Optional[str] = Field(default=None)
    large_images_data: Optional[str] = Field(default=None)
   
    website: Optional["Website"] = Relationship(back_populates="pages")

class Website(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    base_url: str = Field(index=True)
    title: Optional[str] = Field(default=None)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    user_id: Optional[int] = Field(default=None, foreign_key="user.id")
   
    pages: List[WebPage] = Relationship(back_populates="website")

class WebsiteCreate(SQLModel):
    base_url: str
    max_pages: int = Field(default=50, ge=1, le=1000)

class WebsiteRead(SQLModel):
    id: int
    base_url: str
    title: Optional[str]
    created_at: datetime
    user_id: Optional[int]
    page_count: int = 0

class WebPageRead(SQLModel):
    id: int
    url: str
    title: Optional[str]
    scraped_content: Optional[str]
    word_count: Optional[int]
    grammar_score: Optional[int]
    status_code: Optional[int]
    load_time: Optional[float]
    created_at: datetime

class WebsiteWithPagesResponse(SQLModel):
    id: int
    base_url: str
    title: Optional[str] = None
    created_at: str
    user_id: int
    page_count: int
    pages: List[WebPageRead] = []