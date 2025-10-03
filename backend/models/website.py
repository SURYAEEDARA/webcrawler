from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime

class Website(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    url: str = Field(index=True)
    title: Optional[str] = Field(default=None)
    scraped_content: Optional[str] = Field(default=None)
    word_count: Optional[int] = Field(default=0)
    grammar_score: Optional[int] = Field(default=None)
    improvement_suggestions: Optional[str] = Field(default=None)
    analysis_result: Optional[str] = Field(default=None)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    user_id: Optional[int] = Field(default=None, foreign_key="user.id")
    
    class Config:
        schema_extra = {
            "example": {
                "url": "https://example.com",
                "title": "Example Domain",
                "scraped_content": "This domain is for use in illustrative examples...",
                "word_count": 150,
                "grammar_score": 85,
                "improvement_suggestions": "Consider using more active voice...",
                "analysis_result": "Grammar: 85% - Good overall with minor improvements needed"
            }
        }

class WebsiteCreate(SQLModel):
    url: str

class WebsiteRead(SQLModel):
    id: int
    url: str
    title: Optional[str]
    word_count: Optional[int]
    grammar_score: Optional[int]
    created_at: datetime
    user_id: Optional[int]