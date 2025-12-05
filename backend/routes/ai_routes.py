from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from config.database import get_session
from config.dependencies import get_current_active_user
from models.user import User
from models.website import Website, WebPage
from controllers.ai_controller import ai_controller
from controllers.logger import AppLogger
import re
import asyncio

router = APIRouter(prefix="/ai", tags=["ai-analysis"])

@router.post("/analyze/page/{page_id}")
def analyze_page(
    page_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user)
):
    logger = AppLogger(session)
    
    try:
        logger.log_analysis_start(f"AI Page Analysis {page_id}", current_user.id, website_id=None)
        
        page = session.get(WebPage, page_id)
        if not page:
            raise HTTPException(status_code=404, detail="Page not found")
        
        if not page.scraped_content:
            raise HTTPException(status_code=400, detail="No content to analyze")
        
        analysis_result = ai_controller.analyze_grammar(page.scraped_content)
        grammar_score = extract_grammar_score(analysis_result["analysis"])
        
        page.grammar_score = grammar_score
        page.analysis_result = analysis_result["analysis"][:5000]
        page.improvement_suggestions = extract_suggestions(analysis_result["analysis"])
        
        session.add(page)
        session.commit()
        session.refresh(page)
        
        logger.log_ai_analysis(f"Page {page_id}", current_user.id, grammar_score, website_id=page.website_id)
        
        return {
            "page_id": page_id,
            "grammar_score": grammar_score,
            "analysis_preview": analysis_result["analysis"][:500] + "..." if len(analysis_result["analysis"]) > 500 else analysis_result["analysis"],
            "success": True
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.log_error("ai_page_analysis_error", str(e), current_user.id)
        raise HTTPException(status_code=500, detail=f"Page analysis failed: {str(e)}")

@router.post("/analyze/text")
def analyze_text(
    request: dict,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user)
):
    logger = AppLogger(session)
    
    try:
        text = request.get("text", "")
        if not text:
            raise HTTPException(status_code=400, detail="Text is required")
        
        logger.log_analysis_start("AI Text Analysis", current_user.id)
        
        analysis_result = ai_controller.analyze_grammar(text)
        grammar_score = extract_grammar_score(analysis_result["analysis"])
        
        logger.log_ai_analysis("Text Analysis", current_user.id, grammar_score)
        
        return {
            "text_preview": text[:200] + "..." if len(text) > 200 else text,
            "grammar_score": grammar_score,
            "analysis": analysis_result["analysis"],
            "success": True
        }
        
    except Exception as e:
        logger.log_error("ai_text_analysis_error", str(e), current_user.id)
        raise HTTPException(status_code=500, detail=f"Text analysis failed: {str(e)}")

@router.post("/analyze/raw")
def analyze_raw_text(
    request: dict,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user)
):
    logger = AppLogger(session)
    
    try:
        text = request.get("text", "")
        if not text:
            raise HTTPException(status_code=400, detail="Text is required")
        
        logger.log_analysis_start("AI Raw Analysis", current_user.id)
        
        analysis_result = ai_controller.analyze_grammar(text)
        
        return {
            "raw_analysis": analysis_result["analysis"],
            "content_preview": text[:200] + "..." if len(text) > 200 else text
        }
        
    except Exception as e:
        logger.log_error("ai_raw_analysis_error", str(e), current_user.id)
        raise HTTPException(status_code=500, detail=f"Raw analysis failed: {str(e)}")

@router.get("/analysis/full/{page_id}")
def get_full_analysis(
    page_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user)
):
    logger = AppLogger(session)
    
    try:
        page = session.get(WebPage, page_id)
        if not page:
            raise HTTPException(status_code=404, detail="Page not found")
        
        logger._create_log(
            level="info",
            action="full_analysis_retrieved",
            message=f"User retrieved full analysis for page {page_id}",
            user_id=current_user.id,
            website_id=page.website_id
        )
        
        return {
            "page_id": page_id,
            "url": page.url,
            "grammar_score": page.grammar_score,
            "full_analysis": page.analysis_result,
            "suggestions": page.improvement_suggestions,
            "analyzed_at": page.created_at
        }
        
    except Exception as e:
        logger.log_error("full_analysis_retrieval_error", str(e), current_user.id)
        raise HTTPException(status_code=500, detail=f"Failed to get full analysis: {str(e)}")

@router.get("/debug/content/{page_id}")
def debug_page_content(
    page_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user)
):
    logger = AppLogger(session)
    
    try:
        page = session.get(WebPage, page_id)
        if not page:
            raise HTTPException(status_code=404, detail="Page not found")
        
        logger._create_log(
            level="info",
            action="content_debug",
            message=f"User debugged content for page {page_id}",
            user_id=current_user.id,
            website_id=page.website_id
        )
        
        return {
            "page_id": page_id,
            "url": page.url,
            "title": page.title,
            "content_length": len(page.scraped_content or ""),
            "content_preview": (page.scraped_content or "")[:500] + "..." if len(page.scraped_content or "") > 500 else page.scraped_content
        }
        
    except Exception as e:
        logger.log_error("content_debug_error", str(e), current_user.id)
        raise HTTPException(status_code=500, detail=f"Debug failed: {str(e)}")

@router.post("/analyze/seo")
def analyze_seo(
    request: dict,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user)
):
    logger = AppLogger(session)
    
    try:
        text = request.get("text", "")
        if not text:
            raise HTTPException(status_code=400, detail="Text is required")
        
        logger.log_analysis_start("SEO Analysis", current_user.id)
        
        analysis_result = ai_controller.analyze_seo(text)
        
        logger._create_log(
            level="info",
            action="seo_analysis_complete",
            message=f"SEO analysis completed for text preview",
            user_id=current_user.id
        )
        
        return {
            "text_preview": text[:200] + "..." if len(text) > 200 else text,
            "analysis": analysis_result["analysis"],
            "success": True
        }
        
    except Exception as e:
        logger.log_error("seo_analysis_error", str(e), current_user.id)
        raise HTTPException(status_code=500, detail=f"SEO analysis failed: {str(e)}")

@router.post("/analyze/accessibility")
def analyze_accessibility(
    request: dict,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user)
):
    logger = AppLogger(session)
    
    try:
        text = request.get("text", "")
        if not text:
            raise HTTPException(status_code=400, detail="Text is required")
        
        logger.log_analysis_start("Accessibility Analysis", current_user.id)
        
        analysis_result = ai_controller.analyze_accessibility(text)
        
        logger._create_log(
            level="info",
            action="accessibility_analysis_complete",
            message=f"Accessibility analysis completed for text preview",
            user_id=current_user.id
        )
        
        return {
            "text_preview": text[:200] + "..." if len(text) > 200 else text,
            "analysis": analysis_result["analysis"],
            "success": True
        }
        
    except Exception as e:
        logger.log_error("accessibility_analysis_error", str(e), current_user.id)
        raise HTTPException(status_code=500, detail=f"Accessibility analysis failed: {str(e)}")

def extract_grammar_score(analysis_text: str) -> int:
    patterns = [
        r'SCORE:\s*(\d{1,3})',
        r'Score:\s*(\d{1,3})', 
        r'(\d{1,3})\s*\/\s*100',
        r'score[^\d]*(\d{1,3})'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, analysis_text, re.IGNORECASE)
        if match:
            score = int(match.group(1))
            if 0 <= score <= 100:
                return score
    
    raise HTTPException(
        status_code=500,
        detail="Failed to extract grammar score from AI analysis. Please try again."
    )

def extract_suggestions(analysis_text: str) -> str:
    suggestions_match = re.search(
        r'SUGGESTIONS:(.*?)(?=\Z|^[A-Z\s&]+:)', 
        analysis_text, 
        re.IGNORECASE | re.DOTALL | re.MULTILINE
    )
    
    if suggestions_match:
        suggestions_text = suggestions_match.group(1).strip()
        suggestion_items = re.findall(
            r'^\d+\.\s*(.+?)(?=^\d+\.|$)', 
            suggestions_text, 
            re.MULTILINE | re.DOTALL
        )
        
        if suggestion_items:
            cleaned = []
            for i, item in enumerate(suggestion_items[:10], 1):
                clean_item = ' '.join(item.strip().split())
                if len(clean_item) > 300:
                    clean_item = clean_item[:297] + "..."
                cleaned.append(f"{i}. {clean_item}")
            
            return "\n".join(cleaned)
    
    return "No specific suggestions extracted"

@router.post("/analyze/website/{website_id}")
async def analyze_website(
    website_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user)
):
    logger = AppLogger(session)
    
    try:
        logger.log_analysis_start(f"Website Analysis {website_id}", current_user.id, website_id)
        
        website = session.get(Website, website_id)
        if not website or website.user_id != current_user.id:
            raise HTTPException(status_code=404, detail="Website not found")
        
        statement = select(WebPage).where(WebPage.website_id == website_id)
        pages = session.exec(statement).all()
        
        if not pages:
            raise HTTPException(status_code=400, detail="No pages found for this website")
        
        results = []
        analyzed_count = 0
        
        for page in pages:
            try:
                if not page.scraped_content:
                    results.append({
                        "page_id": page.id,
                        "url": page.url,
                        "success": False,
                        "error": "No content to analyze"
                    })
                    continue
                
                analysis_result = ai_controller.analyze_grammar(page.scraped_content)
                grammar_score = extract_grammar_score(analysis_result["analysis"])
                
                if grammar_score is not None:
                    page.grammar_score = grammar_score
                    page.analysis_result = analysis_result["analysis"][:5000]
                    page.improvement_suggestions = extract_suggestions(analysis_result["analysis"])
                    session.add(page)
                    analyzed_count += 1
                
                results.append({
                    "page_id": page.id,
                    "url": page.url,
                    "success": grammar_score is not None,
                    "grammar_score": grammar_score,
                    "word_count": page.word_count,
                    "error": None if grammar_score is not None else "Score extraction failed"
                })
                
                await asyncio.sleep(1)
                
            except Exception as e:
                results.append({
                    "page_id": page.id,
                    "success": False,
                    "error": str(e)
                })
        
        session.commit()
        
        logger.log_analysis_complete(f"Website Analysis {website_id}", current_user.id, {
            "total_pages": len(pages),
            "successfully_analyzed": analyzed_count,
            "failed_analysis": len(pages) - analyzed_count
        }, website_id=website_id)
        
        return {
            "website_id": website_id,
            "total_pages": len(pages),
            "successfully_analyzed": analyzed_count,
            "failed_analysis": len(pages) - analyzed_count,
            "results": results
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.log_error("website_analysis_error", str(e), current_user.id, website_id=website_id)
        raise HTTPException(status_code=500, detail=f"Website analysis failed: {str(e)}")
    
@router.post("/analyze/url")
def analyze_url_direct(
    request: dict,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user)
):
    logger = AppLogger(session)
    
    try:
        url = request.get("url", "")
        if not url:
            raise HTTPException(status_code=400, detail="URL is required")
        
        logger.log_analysis_start(f"Direct URL Analysis: {url}", current_user.id)
        
        from controllers.scraper_controller import ScraperController
        website = ScraperController.scrape_website(url, session, current_user)
        
        statement = select(WebPage).where(WebPage.website_id == website.id)
        page = session.exec(statement).first()
        
        if not page:
            raise HTTPException(status_code=404, detail="Page not found after scraping")
        
        analysis_result = ai_controller.analyze_grammar(page.scraped_content)
        grammar_score = extract_grammar_score(analysis_result["analysis"])
        
        page.grammar_score = grammar_score
        page.analysis_result = analysis_result["analysis"][:5000]
        page.improvement_suggestions = extract_suggestions(analysis_result["analysis"])
        
        session.add(page)
        session.commit()
        session.refresh(page)
        
        return {
            "website_id": website.id,
            "page_id": page.id,
            "url": url,
            "grammar_score": grammar_score,
            "analysis_preview": analysis_result["analysis"][:500] + "..." if len(analysis_result["analysis"]) > 500 else analysis_result["analysis"],
            "success": True
        }
        
    except Exception as e:
        logger.log_error("direct_url_analysis_error", str(e), current_user.id)
        raise HTTPException(status_code=500, detail=f"Direct URL analysis failed: {str(e)}")