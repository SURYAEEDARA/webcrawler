from fastapi import APIRouter, Depends
from sqlmodel import Session
from config.database import get_session
from models.user import User
from models.website import WebsiteRead
from controllers.scraper_controller import ScraperController
from config.dependencies import get_current_active_user
from sqlmodel import Session, select
from fastapi import Depends, HTTPException
from config.database import get_session
from config.dependencies import get_current_active_user
from models.user import User
from models.website import Website, WebsiteRead, WebPage, WebPageRead
from typing import List

router = APIRouter(prefix="/scraper", tags=["web-scraper"])

@router.post("/scrape", response_model=WebsiteRead)
def scrape_website(
    url: str,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user)
):
    return ScraperController.scrape_website(url, session, current_user)

@router.get("/websites", response_model=List[WebsiteRead])
def get_user_websites(
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user)
):
    statement = select(Website).where(Website.user_id == current_user.id)
    websites = session.exec(statement).all()
    return websites

@router.get("/websites/{website_id}", response_model=WebsiteRead)
def get_website(
    website_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user)
):
    website = session.get(Website, website_id)
    if not website or website.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Website not found")
    return website

@router.delete("/websites/{website_id}")
def delete_website(
    website_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user)
):
    website = session.get(Website, website_id)
    if not website or website.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Website not found")
    
    statement = select(WebPage).where(WebPage.website_id == website_id)
    pages = session.exec(statement).all()
    for page in pages:
        session.delete(page)
    
    session.delete(website)
    session.commit()
    
    return {"message": "Website deleted successfully"}