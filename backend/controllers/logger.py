from sqlmodel import Session, select
from datetime import datetime
from typing import Dict, Any, List
from models.analysis import AuditLog

class AppLogger:
    def __init__(self, session: Session):
        self.session = session

    def log_analysis_start(self, url: str, user_id: int, website_id: int = None):
        return self._create_log(
            level="info",
            action="analysis_started",
            message=f"Analysis started for URL: {url}",
            user_id=user_id,
            url=url,
            website_id=website_id
        )

    def log_crawl_progress(self, url: str, pages_crawled: int, total_pages: int, user_id: int, website_id: int = None):
        return self._create_log(
            level="info",
            action="crawl_progress",
            message=f"Crawl progress: {pages_crawled}/{total_pages} pages crawled",
            user_id=user_id,
            url=url,
            website_id=website_id,
            details={"pages_crawled": pages_crawled, "total_pages": total_pages}
        )

    def log_analysis_complete(self, url: str, user_id: int, results: Dict[str, Any], website_id: int = None):
        return self._create_log(
            level="info",
            action="analysis_complete",
            message=f"Analysis complete for {url}",
            user_id=user_id,
            url=url,
            website_id=website_id,
            details=results
        )

    def log_ai_analysis(self, analysis_type: str, user_id: int, score: int = None, website_id: int = None):
        message = f"AI analysis completed: {analysis_type}"
        if score is not None:
            message += f" - Score: {score}"
            
        return self._create_log(
            level="info",
            action="ai_analysis_complete",
            message=message,
            user_id=user_id,
            website_id=website_id,
            details={"analysis_type": analysis_type, "score": score}
        )

    def log_error(self, error_type: str, error_message: str, user_id: int = None, url: str = None):
        return self._create_log(
            level="error",
            action=error_type,
            message=f"Error: {error_message}",
            user_id=user_id,
            url=url,
            details={"error_type": error_type, "error_message": error_message}
        )

    def log_link_check(self, url: str, user_id: int, broken_count: int, total_links: int):
        return self._create_log(
            level="info",
            action="link_check_complete",
            message=f"Link check completed for {url}: {broken_count}/{total_links} broken",
            user_id=user_id,
            url=url,
            details={"broken_count": broken_count, "total_links": total_links}
        )

    def log_image_analysis(self, url: str, user_id: int, problematic_count: int, total_images: int):
        return self._create_log(
            level="info",
            action="image_analysis_complete",
            message=f"Image analysis completed for {url}: {problematic_count}/{total_images} problematic",
            user_id=user_id,
            url=url,
            details={"problematic_count": problematic_count, "total_images": total_images}
        )

    def _create_log(self, level: str, action: str, message: str, user_id: int = None,
                   url: str = None, details: Dict = None, website_id: int = None):
        log_entry = AuditLog(
            level=level,
            user_id=user_id,
            action=action,
            message=message,
            url=url,
            details=str(details) if details else None,
            website_id=website_id
        )

        self.session.add(log_entry)
        self.session.commit()
        return log_entry

    def get_user_logs(self, user_id: int, limit: int = 100) -> List[AuditLog]:
        statement = select(AuditLog).where(
            AuditLog.user_id == user_id
        ).order_by(AuditLog.timestamp.desc()).limit(limit)

        return self.session.exec(statement).all()