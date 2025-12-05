from sqlmodel import Session, select, func
from models.website import Website, WebPage
from models.analysis import AuditLog
from models.user import User
from datetime import datetime, timedelta
from typing import Dict, List, Any

class DashboardController:
    @staticmethod
    def get_user_dashboard(user_id: int, session: Session) -> Dict[str, Any]:
                
        single_websites_stmt = select(Website).where(Website.user_id == user_id)
        single_websites = session.exec(single_websites_stmt).all()
        
        crawled_websites_stmt = select(Website).where(
            Website.user_id == user_id
        )
        all_websites = session.exec(crawled_websites_stmt).all()
        
        website_ids = [w.id for w in all_websites]
        pages_stmt = select(WebPage).where(WebPage.website_id.in_(website_ids)) if website_ids else select(WebPage).where(False)
        all_pages = session.exec(pages_stmt).all() if website_ids else []
        
        total_websites = len(all_websites)
        total_pages = len(all_pages)
        
        analyzed_pages = [p for p in all_pages if p.grammar_score is not None]
        total_analyzed = len(analyzed_pages)
        
        average_score = None
        if analyzed_pages:
            scores = [p.grammar_score for p in analyzed_pages]
            average_score = round(sum(scores) / len(scores), 2)
        
        score_distribution = {
            "excellent": len([p for p in analyzed_pages if p.grammar_score >= 80]),
            "good": len([p for p in analyzed_pages if 60 <= p.grammar_score < 80]),
            "needs_improvement": len([p for p in analyzed_pages if p.grammar_score < 60])
        }
        
        seven_days_ago = datetime.utcnow() - timedelta(days=7)
        recent_logs_stmt = select(AuditLog).where(
            AuditLog.user_id == user_id,
            AuditLog.timestamp >= seven_days_ago
        ).order_by(AuditLog.timestamp.desc()).limit(10)
        recent_activity = session.exec(recent_logs_stmt).all()
        
        websites_summary = []
        for website in all_websites:
            pages_stmt = select(WebPage).where(WebPage.website_id == website.id)
            website_pages = session.exec(pages_stmt).all()
            
            analyzed_count = len([p for p in website_pages if p.grammar_score is not None])
            avg_score = None
            if analyzed_count > 0:
                scores = [p.grammar_score for p in website_pages if p.grammar_score is not None]
                avg_score = round(sum(scores) / len(scores), 2)
            
            websites_summary.append({
                "id": website.id,
                "base_url": website.base_url,
                "title": website.title,
                "created_at": website.created_at.isoformat(),
                "total_pages": len(website_pages),
                "analyzed_pages": analyzed_count,
                "average_score": avg_score,
                "status": "analyzed" if analyzed_count == len(website_pages) and len(website_pages) > 0 else "partial" if analyzed_count > 0 else "pending"
            })
        
        pending_pages = [p for p in all_pages if p.grammar_score is None]
        
        top_pages = sorted(
            [p for p in analyzed_pages],
            key=lambda x: x.grammar_score,
            reverse=True
        )[:5]
        
        low_scoring_pages = sorted(
            [p for p in analyzed_pages if p.grammar_score < 60],
            key=lambda x: x.grammar_score
        )[:5]
        
        return {
            "overview": {
                "total_websites": total_websites,
                "total_pages": total_pages,
                "analyzed_pages": total_analyzed,
                "pending_analysis": len(pending_pages),
                "average_score": average_score,
                "score_distribution": score_distribution
            },
            "websites": websites_summary,
            "recent_activity": [
                {
                    "id": log.id,
                    "action": log.action,
                    "message": log.message,
                    "timestamp": log.timestamp.isoformat(),
                    "level": log.level
                }
                for log in recent_activity
            ],
            "top_performing_pages": [
                {
                    "id": page.id,
                    "url": page.url,
                    "title": page.title,
                    "score": page.grammar_score,
                    "website_id": page.website_id
                }
                for page in top_pages
            ],
            "pages_needing_improvement": [
                {
                    "id": page.id,
                    "url": page.url,
                    "title": page.title,
                    "score": page.grammar_score,
                    "website_id": page.website_id
                }
                for page in low_scoring_pages
            ],
            "quick_stats": {
                "analyses_this_week": len([log for log in recent_activity if "analysis" in log.action.lower()]),
                "crawls_this_week": len([log for log in recent_activity if "crawl" in log.action.lower()]),
                "last_activity": recent_activity[0].timestamp.isoformat() if recent_activity else None
            }
        }
    
    @staticmethod
    def get_website_summary(website_id: int, user_id: int, session: Session) -> Dict[str, Any]:
        website = session.get(Website, website_id)
        
        if not website or website.user_id != user_id:
            return None
        
        pages_stmt = select(WebPage).where(WebPage.website_id == website_id)
        pages = session.exec(pages_stmt).all()
        
        analyzed_pages = [p for p in pages if p.grammar_score is not None]
        
        return {
            "website": {
                "id": website.id,
                "base_url": website.base_url,
                "title": website.title,
                "created_at": website.created_at.isoformat()
            },
            "statistics": {
                "total_pages": len(pages),
                "analyzed_pages": len(analyzed_pages),
                "average_score": round(sum(p.grammar_score for p in analyzed_pages) / len(analyzed_pages), 2) if analyzed_pages else None,
                "total_words": sum(p.word_count or 0 for p in pages)
            },
            "pages": [
                {
                    "id": page.id,
                    "url": page.url,
                    "title": page.title,
                    "word_count": page.word_count,
                    "grammar_score": page.grammar_score,
                    "status_code": page.status_code,
                    "load_time": page.load_time,
                    "has_analysis": page.grammar_score is not None
                }
                for page in pages
            ]
        }