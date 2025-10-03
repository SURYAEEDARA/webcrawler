from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session
from config.database import get_session
from models.website import Website
from controllers.ai_controller import AIController

router = APIRouter(prefix="/ai", tags=["ai-analysis"])

@router.post("/analyze/{website_id}", response_model=Website)
def analyze_website(website_id: int, session: Session = Depends(get_session)):
    """Analyze website content using AI"""
    return AIController.analyze_website(website_id, session)

@router.post("/analyze-text")
def analyze_text(text: str):
    """Analyze custom text using AI (without saving to database)"""
    analysis_result = AIController.analyze_grammar(text)
    return {
        "text_preview": text[:200] + "..." if len(text) > 200 else text,
        "analysis": analysis_result
    }