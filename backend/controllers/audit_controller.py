from sqlmodel import Session, select
from models.website import Website, WebPage
from models.analysis import AnalysisSummary

class AuditController:
    @staticmethod
    def generate_audit_report(website_id: int, session: Session) -> AnalysisSummary:
        website = session.get(Website, website_id)
        if not website:
            return None
        
        statement = select(WebPage).where(WebPage.website_id == website_id)
        pages = session.exec(statement).all()
        
        total_pages = len(pages)
        
        grammar_scores = [page.grammar_score for page in pages if page.grammar_score is not None]
        average_grammar_score = round(sum(grammar_scores) / len(grammar_scores), 2) if grammar_scores else None
        
        seo_score = calculate_seo_score(pages)
        accessibility_score = calculate_accessibility_score(pages)
        
        overall_health_score = None
        if average_grammar_score and seo_score and accessibility_score:
            overall_health_score = round(
                (average_grammar_score * 0.4) +  
                (seo_score * 0.3) +                
                (accessibility_score * 0.3),       
                2
            )
        elif average_grammar_score:
            overall_health_score = round(average_grammar_score * 0.8, 2)
        
        return AnalysisSummary(
            website_id=website_id,
            total_pages=total_pages,
            broken_links_count=0,  
            image_issues_count=0, 
            average_grammar_score=average_grammar_score,
            overall_health_score=overall_health_score,
            seo_score=seo_score,
            accessibility_score=accessibility_score
        )

def calculate_seo_score(pages: list) -> float:
    """
    Calculate SEO score based on multiple dynamic factors:
    - Word count (0-30 points)
    - Grammar quality (0-40 points)
    - Content structure (0-15 points)
    - Technical factors (0-15 points)
    """
    if not pages:
        return 0.0
    
    scores = []
    for page in pages:
        score = 0  
        
        word_count = page.word_count or 0
        if word_count > 1500:
            score += 30
        elif word_count > 1000:
            score += 25
        elif word_count > 700:
            score += 20
        elif word_count > 500:
            score += 18
        elif word_count > 300:
            score += 15
        elif word_count > 150:
            score += 10
        elif word_count > 50:
            score += 5
        else:
            score += 2  
        
        if page.grammar_score:
            score += (page.grammar_score / 100) * 40
        
        content = page.scraped_content or ""
        content_lower = content.lower()
        
        if '<h1' in content_lower:
            score += 5
        
        if '<h2' in content_lower or '<h3' in content_lower:
            score += 5
        
        if 'meta' in content_lower or '<title' in content_lower:
            score += 5
        
        if page.status_code == 200:
            score += 10
        elif page.status_code and page.status_code < 400:
            score += 7
        elif page.status_code and page.status_code >= 400:
            score += 0  
        
        if page.load_time:
            if page.load_time < 1.0:  
                score += 5
            elif page.load_time < 2.0:  
                score += 3
            elif page.load_time < 3.0:  
                score += 1
        
        scores.append(max(0, min(100, score)))
    
    return round(sum(scores) / len(scores), 2)

def calculate_accessibility_score(pages: list) -> float:
    """
    Calculate accessibility score based on:
    - Semantic HTML (0-25 points)
    - Alt text for images (0-20 points)
    - ARIA attributes (0-20 points)
    - Content quality (0-15 points)
    - Grammar quality bonus (0-20 points)
    """
    if not pages:
        return 0.0
    
    scores = []
    
    for page in pages:
        score = 0  
        
        content = page.scraped_content or ""
        content_lower = content.lower()
        
        semantic_tags = ['<h1', '<h2', '<h3', '<header', '<nav', '<main', '<footer', '<article', '<section', '<aside']
        found_tags = sum(1 for tag in semantic_tags if tag in content_lower)
        
        if found_tags >= 7:
            score += 25
        elif found_tags >= 5:
            score += 20
        elif found_tags >= 3:
            score += 15
        elif found_tags >= 1:
            score += 10
        else:
            score += 2  
        
        alt_count = content_lower.count('alt=') + content_lower.count('alt =')
        img_count = content_lower.count('<img')
        
        if img_count > 0:
            alt_ratio = min(alt_count / img_count, 1.0)
            score += alt_ratio * 20
        elif alt_count > 0:
            score += 10
        
        aria_attrs = ['aria-label', 'aria-labelledby', 'aria-describedby', 'aria-hidden', 'role=']
        found_aria = sum(1 for attr in aria_attrs if attr in content_lower)
        
        if found_aria >= 4:
            score += 20
        elif found_aria >= 3:
            score += 15
        elif found_aria >= 2:
            score += 10
        elif found_aria >= 1:
            score += 5
        
        word_count = page.word_count or 0
        if word_count > 1000:
            score += 15
        elif word_count > 700:
            score += 12
        elif word_count > 500:
            score += 10
        elif word_count > 300:
            score += 8
        elif word_count > 200:
            score += 5
        elif word_count > 100:
            score += 3
        elif word_count > 50:
            score += 1
        else:
            score += 0
        
        if page.grammar_score:
            if page.grammar_score >= 90:
                score += 20
            elif page.grammar_score >= 80:
                score += 17
            elif page.grammar_score >= 70:
                score += 14
            elif page.grammar_score >= 60:
                score += 10
            elif page.grammar_score >= 50:
                score += 7
            else:
                score += 5
        
        scores.append(max(0, min(100, score)))
    
    return round(sum(scores) / len(scores), 2)