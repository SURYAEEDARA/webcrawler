from sqlmodel import SQLModel, Field
from typing import Optional
from typing import List
from datetime import datetime

class BulkAnalysisRequest(SQLModel):
    page_ids: List[int]

class LinkCheckRequest(SQLModel):
    url: str
    links: List[str]

class ImageCheckRequest(SQLModel):
    url: str
    image_urls: List[str]

class AnalysisSummary(SQLModel):
    website_id: int
    total_pages: int
    broken_links_count: int
    image_issues_count: int
    average_grammar_score: Optional[float]
    overall_health_score: Optional[float]
    seo_score: Optional[float]
    accessibility_score: Optional[float]

class AuditLog(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    level: str 
    user_id: Optional[int] = Field(default=None, foreign_key="user.id")
    action: str 
    message: str
    url: Optional[str] = Field(default=None)
    details: Optional[str] = Field(default=None)
    website_id: Optional[int] = Field(default=None, foreign_key="website.id")