from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session
from config.database import get_session
from config.dependencies import get_current_active_user
from models.user import User
from controllers.logger import AppLogger

router = APIRouter(prefix="/logs", tags=["logs"])

@router.get("/my-logs")
def get_my_logs(
    limit: int = 100,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user)
):
    logger = AppLogger(session)
    logs = logger.get_user_logs(current_user.id, limit)
    return {
        "success": True,
        "logs": logs,
        "total": len(logs)
    }