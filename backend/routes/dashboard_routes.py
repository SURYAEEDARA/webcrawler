from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session
from config.database import get_session
from config.dependencies import get_current_active_user
from models.user import User
from controllers.dashboard import DashboardController
from controllers.logger import AppLogger

router = APIRouter(prefix="/dashboard", tags=["dashboard"])

@router.get("/")
def get_dashboard(
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user)
):
    logger = AppLogger(session)
    
    try:
        logger._create_log(
            level="info",
            action="dashboard_viewed",
            message=f"User {current_user.username} accessed dashboard",
            user_id=current_user.id
        )
        
        dashboard_data = DashboardController.get_user_dashboard(current_user.id, session)
        
        return {
            "success": True,
            "data": dashboard_data,
            "user": {
                "id": current_user.id,
                "username": current_user.username,
                "email": current_user.email
            }
        }
        
    except Exception as e:
        logger.log_error("dashboard_error", str(e), current_user.id)
        raise HTTPException(status_code=500, detail=f"Failed to load dashboard: {str(e)}")


@router.get("/website/{website_id}")
def get_website_dashboard(
    website_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user)
):
    logger = AppLogger(session)
    
    try:
        website_data = DashboardController.get_website_summary(website_id, current_user.id, session)
        
        if not website_data:
            raise HTTPException(status_code=404, detail="Website not found or access denied")
        
        logger._create_log(
            level="info",
            action="website_dashboard_viewed",
            message=f"User viewed website dashboard for ID {website_id}",
            user_id=current_user.id,
            website_id=website_id
        )
        
        return {
            "success": True,
            "data": website_data
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.log_error("website_dashboard_error", str(e), current_user.id)
        raise HTTPException(status_code=500, detail=f"Failed to load website dashboard: {str(e)}")


@router.get("/stats")
def get_quick_stats(
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user)
):
    try:
        dashboard_data = DashboardController.get_user_dashboard(current_user.id, session)
        
        return {
            "success": True,
            "stats": {
                "total_websites": dashboard_data["overview"]["total_websites"],
                "analyzed_pages": dashboard_data["overview"]["analyzed_pages"],
                "average_score": dashboard_data["overview"]["average_score"],
                "pending_analysis": dashboard_data["overview"]["pending_analysis"]
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load stats: {str(e)}")