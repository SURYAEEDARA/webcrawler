from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from config.database import get_session
from config.dependencies import get_current_active_user
from models.user import User
from models.website import Website, WebPage, WebsiteCreate 
from controllers.recursive_crawler import RecursiveCrawlerController
from controllers.logger import AppLogger
from sqlmodel import Session, select
from fastapi import Depends, HTTPException
from config.database import get_session
from config.dependencies import get_current_active_user
from models.user import User
from models.website import Website, WebsiteWithPagesResponse, WebPage
from typing import List
from models.website import WebPageRead 

router = APIRouter(prefix="/crawl", tags=["recursive-crawling"])

@router.post("/website")
def crawl_website_recursive(
    website_data: WebsiteCreate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user)
):
    logger = AppLogger(session)
    
    try:
        logger.log_analysis_start(website_data.base_url, current_user.id)
        
        result = RecursiveCrawlerController.crawl_website_recursive(website_data, session, current_user)
        
        logger.log_analysis_complete(website_data.base_url, current_user.id, {
            "total_pages": result.get("page_count", 0),
            "crawl_mode": "recursive",
            "max_pages": website_data.max_pages
        }, website_id=result.get("id"))
        
        return result
        
    except Exception as e:
        logger.log_error("recursive_crawl_error", str(e), current_user.id, website_data.base_url)
        raise HTTPException(status_code=500, detail=f"Recursive crawling failed: {str(e)}")

@router.get("/websites/{website_id}/pages")
def get_website_pages(
    website_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user)
):
    logger = AppLogger(session)
    
    try:
        website = session.get(Website, website_id)
        if not website or website.user_id != current_user.id:
            raise HTTPException(status_code=404, detail="Website not found")
        
        statement = select(WebPage).where(WebPage.website_id == website_id)
        pages = session.exec(statement).all()
        
        logger._create_log(
            level="info",
            action="pages_retrieved",
            message=f"User retrieved {len(pages)} pages for website {website_id}",
            user_id=current_user.id,
            website_id=website_id
        )
        
        return pages
        
    except HTTPException:
        raise
    except Exception as e:
        logger.log_error("pages_retrieval_error", str(e), current_user.id)
        raise HTTPException(status_code=500, detail=f"Failed to get website pages: {str(e)}")
    
@router.get("/websites", response_model=List[WebsiteWithPagesResponse])
def get_crawled_websites(
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user)
):
    statement = select(Website).where(Website.user_id == current_user.id)
    websites = session.exec(statement).all()

    result = []
    for website in websites:
        pages_statement = select(WebPage).where(WebPage.website_id == website.id)
        pages = session.exec(pages_statement).all()

        page_data = []
        for page in pages:
            page_data.append(WebPageRead(
                id=page.id,
                url=page.url,
                title=page.title,
                scraped_content=page.scraped_content,
                word_count=page.word_count,
                grammar_score=page.grammar_score,
                status_code=page.status_code,
                load_time=page.load_time,
                created_at=page.created_at
            ))

        result.append(WebsiteWithPagesResponse(
            id=website.id,
            base_url=website.base_url,
            title=website.title,
            created_at=website.created_at.isoformat(),
            user_id=website.user_id,
            page_count=len(pages),
            pages=page_data
        ))

    return result

@router.get("/websites/{website_id}", response_model=WebsiteWithPagesResponse)
def get_crawled_website(
    website_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user)
):
    website = session.get(Website, website_id)
    if not website or website.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Website not found")
    
    statement = select(WebPage).where(WebPage.website_id == website_id)
    pages = session.exec(statement).all()
    
    page_data = []
    for page in pages:
        page_data.append(WebPageRead(
            id=page.id,
            url=page.url,
            title=page.title,
            scraped_content=page.scraped_content,
            word_count=page.word_count,
            grammar_score=page.grammar_score,
            status_code=page.status_code,
            load_time=page.load_time,
            created_at=page.created_at
        ))
    
    return WebsiteWithPagesResponse(
        id=website.id,
        base_url=website.base_url,
        title=website.title,
        created_at=website.created_at.isoformat(),
        user_id=website.user_id,
        page_count=len(pages),
        pages=page_data
    )

@router.delete("/websites/{website_id}")
def delete_crawled_website(
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
    
    return {"message": "Crawled website and all pages deleted successfully"}