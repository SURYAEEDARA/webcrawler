from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from config.database import get_session
from config.dependencies import get_current_active_user
from models.user import User
from models.website import WebPage, Website
from models.analysis import BulkAnalysisRequest, LinkCheckRequest, ImageCheckRequest
from controllers.ai_controller import ai_controller
from controllers.link_checker import LinkChecker
from controllers.image_analyzer import ImageAnalyzer
from controllers.audit_controller import AuditController
from controllers.logger import AppLogger
import asyncio
import re

router = APIRouter(prefix="/analysis", tags=["analysis"])

@router.post("/bulk/analyze-pages")
async def bulk_analyze_pages(
    request: BulkAnalysisRequest,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user)
):
    logger = AppLogger(session)
    
    try:
        logger.log_analysis_start(f"Bulk Analysis ({len(request.page_ids)} pages)", current_user.id)
        
        page_ids = request.page_ids
        if not page_ids:
            raise HTTPException(status_code=400, detail="No page IDs provided")
        
        results = []
        analyzed_count = 0
        
        for page_id in page_ids:
            try:
                page = session.get(WebPage, page_id)
                if not page:
                    results.append({
                        "page_id": page_id,
                        "success": False,
                        "error": "Page not found"
                    })
                    continue
                
                if not page.scraped_content:
                    results.append({
                        "page_id": page_id,
                        "success": False,
                        "error": "No content to analyze"
                    })
                    continue
                
                analysis_result = ai_controller.analyze_grammar(page.scraped_content)
                grammar_score = extract_grammar_score(analysis_result["analysis"])
                
                if grammar_score is not None:
                    page.grammar_score = grammar_score
                    page.analysis_result = analysis_result["analysis"][:5000]
                    session.add(page)
                    analyzed_count += 1
                
                results.append({
                    "page_id": page_id,
                    "url": page.url,
                    "success": grammar_score is not None,
                    "grammar_score": grammar_score,
                    "word_count": page.word_count,
                    "error": None if grammar_score is not None else "Score extraction failed"
                })
                
                await asyncio.sleep(1)
                
            except Exception as e:
                results.append({
                    "page_id": page_id,
                    "success": False,
                    "error": str(e)
                })
        
        session.commit()
        
        logger.log_analysis_complete("Bulk Analysis", current_user.id, {
            "total_requested": len(page_ids),
            "successfully_analyzed": analyzed_count,
            "failed_analysis": len(page_ids) - analyzed_count
        })
        
        return {
            "total_requested": len(page_ids),
            "successfully_analyzed": analyzed_count,
            "failed_analysis": len(page_ids) - analyzed_count,
            "results": results
        }
        
    except Exception as e:
        logger.log_error("bulk_analysis_error", str(e), current_user.id)
        raise HTTPException(status_code=500, detail=f"Bulk analysis failed: {str(e)}")

@router.post("/check-links")
def check_links(
    request: LinkCheckRequest,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user)
):
    logger = AppLogger(session)
    
    try:
        logger.log_analysis_start(f"Link Check for {request.url}", current_user.id)
        
        if not request.links:
            raise HTTPException(status_code=400, detail="No links provided")
        
        result = LinkChecker.check_multiple_links(request.links, request.url)
        
        logger.log_link_check(
            request.url, current_user.id,
            result["broken_count"],
            result["total_links"]
        )
        
        return {
            "url": request.url,
            "results": result
        }
        
    except Exception as e:
        logger.log_error("link_check_error", str(e), current_user.id, request.url)
        raise HTTPException(status_code=500, detail=f"Link check failed: {str(e)}")

@router.post("/check-images")
def check_images(
    request: ImageCheckRequest,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user)
):
    logger = AppLogger(session)
    
    try:
        logger.log_analysis_start(f"Image Check for {request.url}", current_user.id)
        
        if not request.image_urls:
            raise HTTPException(status_code=400, detail="No image URLs provided")
        
        result = ImageAnalyzer.analyze_multiple_images(request.image_urls, request.url)
        
        logger.log_image_analysis(
            request.url, current_user.id,
            result["problematic_count"],
            result["total_images"]
        )
        
        return {
            "url": request.url,
            "results": result
        }
        
    except Exception as e:
        logger.log_error("image_analysis_error", str(e), current_user.id, request.url)
        raise HTTPException(status_code=500, detail=f"Image analysis failed: {str(e)}")

@router.get("/audit/{website_id}")
def get_audit_report(
    website_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user)
):
    logger = AppLogger(session)
    
    try:
        website = session.get(Website, website_id)
        if not website or website.user_id != current_user.id:
            raise HTTPException(status_code=404, detail="Website not found")
        
        report = AuditController.generate_audit_report(website_id, session)
        if not report:
            raise HTTPException(status_code=404, detail="Website not found or no data")
        
        logger._create_log(
            level="info",
            action="audit_report_generated",
            message=f"Audit report generated for website {website_id}",
            user_id=current_user.id,
            website_id=website_id
        )
        
        return report
        
    except HTTPException:
        raise
    except Exception as e:
        logger.log_error("audit_report_error", str(e), current_user.id)
        raise HTTPException(status_code=500, detail=f"Failed to generate audit report: {str(e)}")

@router.post("/audit/{website_id}/regenerate")
def regenerate_audit_report(
    website_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user)
):
    """
    Force regeneration of audit report with fresh calculations.
    Useful when page analyses have been updated.
    """
    logger = AppLogger(session)
    
    try:
        website = session.get(Website, website_id)
        if not website or website.user_id != current_user.id:
            raise HTTPException(status_code=404, detail="Website not found or access denied")
        
        report = AuditController.generate_audit_report(website_id, session)
        if not report:
            raise HTTPException(status_code=404, detail="Failed to generate audit report")
        
        logger._create_log(
            level="info",
            action="audit_regenerated",
            message=f"Audit report regenerated for website {website_id}",
            user_id=current_user.id,
            website_id=website_id,
            details={
                "overall_score": report.overall_health_score,
                "seo_score": report.seo_score,
                "accessibility_score": report.accessibility_score,
                "grammar_score": report.average_grammar_score
            }
        )
        
        return report
        
    except HTTPException:
        raise
    except Exception as e:
        logger.log_error("audit_regeneration_error", str(e), current_user.id, website_id=website_id)
        raise HTTPException(status_code=500, detail=f"Failed to regenerate audit: {str(e)}")

def extract_grammar_score(analysis_text: str) -> int:
    patterns = [
        r'SCORE:\s*(\d{1,3})',
        r'Score:\s*(\d{1,3})', 
        r'(\d{1,3})\s*\/\s*100'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, analysis_text, re.IGNORECASE)
        if match:
            score = int(match.group(1))
            if 0 <= score <= 100:
                return score
    return None