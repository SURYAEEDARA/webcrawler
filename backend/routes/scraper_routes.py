from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session
from typing import List
from config.database import get_session
from models.website import Website
from models.user import User
from controllers.scraper_controller import ScraperController
from config.dependencies import get_current_active_user

router = APIRouter(prefix="/scraper", tags=["web-scraper"])

@router.post("/scrape", response_model=Website)
def scrape_website(
    url: str, 
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user)
):
    """Scrape a website and store its content"""
    return ScraperController.scrape_website(url, session, current_user)

@router.get("/websites", response_model=List[Website])
def get_websites(
    offset: int = 0,
    limit: int = Query(default=100, le=100),
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user)
):
    """Get all scraped websites for current user"""
    return ScraperController.get_websites(session, current_user, offset, limit)

@router.get("/websites/{website_id}", response_model=Website)
def get_website(
    website_id: int, 
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user)
):
    """Get a specific website analysis"""
    return ScraperController.get_website(website_id, session, current_user)

@router.delete("/websites/{website_id}")
def delete_website(
    website_id: int, 
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user)
):
    """Delete a website record"""
    return ScraperController.delete_website(website_id, session, current_user)