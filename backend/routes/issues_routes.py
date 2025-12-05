from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from config.database import get_session
from config.dependencies import get_current_active_user
from models.user import User
from models.website import Website, WebPage
from controllers.logger import AppLogger
import json

router = APIRouter(prefix="/issues", tags=["issues"])

@router.get("/website/{website_id}/broken-links")
def get_website_broken_links(
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
        
        all_broken_links = []
        for page in pages:
            if page.broken_links_data:
                try:
                    broken_links = json.loads(page.broken_links_data)
                    for link in broken_links:
                        all_broken_links.append({
                            **link,
                            'page_id': page.id,
                            'page_title': page.title
                        })
                except json.JSONDecodeError:
                    continue
        
        logger._create_log(
            level="info",
            action="broken_links_retrieved",
            message=f"Retrieved {len(all_broken_links)} broken links for website {website_id}",
            user_id=current_user.id,
            website_id=website_id
        )
        
        return {
            "website_id": website_id,
            "website_url": website.base_url,
            "total_broken_links": len(all_broken_links),
            "broken_links": all_broken_links,
            "pages_with_issues": len([p for p in pages if p.broken_links_data and json.loads(p.broken_links_data)])
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.log_error("broken_links_retrieval_error", str(e), current_user.id)
        raise HTTPException(status_code=500, detail=f"Failed to get broken links: {str(e)}")


@router.get("/website/{website_id}/large-images")
def get_website_large_images(
    website_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user)
):
    """Get all large images found across the website"""
    logger = AppLogger(session)
    
    try:
        website = session.get(Website, website_id)
        if not website or website.user_id != current_user.id:
            raise HTTPException(status_code=404, detail="Website not found")
        
        statement = select(WebPage).where(WebPage.website_id == website_id)
        pages = session.exec(statement).all()
        
        all_large_images = []
        for page in pages:
            if page.large_images_data:
                try:
                    large_images = json.loads(page.large_images_data)
                    for image in large_images:
                        all_large_images.append({
                            **image,
                            'page_id': page.id,
                            'page_title': page.title
                        })
                except json.JSONDecodeError:
                    continue
        
        all_large_images.sort(key=lambda x: x.get('size_bytes', 0), reverse=True)
        
        logger._create_log(
            level="info",
            action="large_images_retrieved",
            message=f"Retrieved {len(all_large_images)} large images for website {website_id}",
            user_id=current_user.id,
            website_id=website_id
        )
        
        return {
            "website_id": website_id,
            "website_url": website.base_url,
            "total_large_images": len(all_large_images),
            "large_images": all_large_images,
            "pages_with_issues": len([p for p in pages if p.large_images_data and json.loads(p.large_images_data)]),
            "threshold_kb": 400 
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.log_error("large_images_retrieval_error", str(e), current_user.id)
        raise HTTPException(status_code=500, detail=f"Failed to get large images: {str(e)}")


@router.get("/website/{website_id}/all-issues")
def get_website_all_issues(
    website_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user)
):
    """Get both broken links and large images for the website"""
    logger = AppLogger(session)
    
    try:
        website = session.get(Website, website_id)
        if not website or website.user_id != current_user.id:
            raise HTTPException(status_code=404, detail="Website not found")
        
        statement = select(WebPage).where(WebPage.website_id == website_id)
        pages = session.exec(statement).all()
        
        all_broken_links = []
        for page in pages:
            if page.broken_links_data:
                try:
                    broken_links = json.loads(page.broken_links_data)
                    for link in broken_links:
                        all_broken_links.append({
                            **link,
                            'page_id': page.id,
                            'page_title': page.title
                        })
                except json.JSONDecodeError:
                    continue
        
        all_large_images = []
        for page in pages:
            if page.large_images_data:
                try:
                    large_images = json.loads(page.large_images_data)
                    for image in large_images:
                        all_large_images.append({
                            **image,
                            'page_id': page.id,
                            'page_title': page.title
                        })
                except json.JSONDecodeError:
                    continue
        
        all_large_images.sort(key=lambda x: x.get('size_bytes', 0), reverse=True)
        
        logger._create_log(
            level="info",
            action="all_issues_retrieved",
            message=f"Retrieved {len(all_broken_links)} broken links and {len(all_large_images)} large images",
            user_id=current_user.id,
            website_id=website_id
        )
        
        return {
            "website_id": website_id,
            "website_url": website.base_url,
            "summary": {
                "total_broken_links": len(all_broken_links),
                "total_large_images": len(all_large_images),
                "pages_with_broken_links": len([p for p in pages if p.broken_links_data and json.loads(p.broken_links_data)]),
                "pages_with_large_images": len([p for p in pages if p.large_images_data and json.loads(p.large_images_data)])
            },
            "broken_links": all_broken_links,
            "large_images": all_large_images,
            "image_size_threshold_kb": 400
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.log_error("all_issues_retrieval_error", str(e), current_user.id)
        raise HTTPException(status_code=500, detail=f"Failed to get issues: {str(e)}")


@router.get("/page/{page_id}/issues")
def get_page_issues(
    page_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user)
):
    """Get broken links and large images for a specific page"""
    logger = AppLogger(session)
    
    try:
        page = session.get(WebPage, page_id)
        if not page:
            raise HTTPException(status_code=404, detail="Page not found")
        
        website = session.get(Website, page.website_id)
        if not website or website.user_id != current_user.id:
            raise HTTPException(status_code=404, detail="Page not found")
        
        broken_links = []
        if page.broken_links_data:
            try:
                broken_links = json.loads(page.broken_links_data)
            except json.JSONDecodeError:
                pass
    
        large_images = []
        if page.large_images_data:
            try:
                large_images = json.loads(page.large_images_data)
            except json.JSONDecodeError:
                pass
        
        logger._create_log(
            level="info",
            action="page_issues_retrieved",
            message=f"Retrieved issues for page {page_id}",
            user_id=current_user.id,
            website_id=website.id
        )
        
        return {
            "page_id": page_id,
            "page_url": page.url,
            "page_title": page.title,
            "broken_links_count": len(broken_links),
            "large_images_count": len(large_images),
            "broken_links": broken_links,
            "large_images": large_images
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.log_error("page_issues_retrieval_error", str(e), current_user.id)
        raise HTTPException(status_code=500, detail=f"Failed to get page issues: {str(e)}")