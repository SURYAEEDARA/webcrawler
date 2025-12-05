from datetime import datetime
from fastapi import APIRouter, Depends
from sqlmodel import Session, select
from config.database import get_session
from controllers.ai_controller import ai_controller
from controllers.logger import AppLogger
import requests

router = APIRouter(prefix="/health", tags=["health"])

@router.get("/ai-status")
def get_ai_status(session: Session = Depends(get_session)):
    logger = AppLogger(session)
    
    try:
        logger._create_log(
            level="info",
            action="health_check",
            message="AI service health check initiated"
        )
        
        test_result = ai_controller.analyze_grammar("Test connection")
        
        status_info = {
            "service": "huggingface_ai",
            "status": "healthy" if test_result["success"] else "unhealthy",
            "model": ai_controller.HF_MODEL,
            "responsive": test_result["success"]
        }
        
        logger._create_log(
            level="info" if status_info["status"] == "healthy" else "warning",
            action="ai_health_status",
            message=f"AI service status: {status_info['status']}",
            details=status_info
        )
        
        return status_info
        
    except Exception as e:
        error_status = {
            "service": "huggingface_ai",
            "status": "unhealthy",
            "error": str(e),
            "responsive": False
        }
        
        logger.log_error("ai_health_check_failed", str(e))
        
        return error_status

@router.get("/full")
def full_health_check(session: Session = Depends(get_session)):
    logger = AppLogger(session)
    
    try:
        logger._create_log(
            level="info",
            action="full_health_check",
            message="Full system health check initiated"
        )
        
        ai_status = get_ai_status(session)
        
        db_status = "healthy"
        try:
            from config.database import engine
            with Session(engine) as test_session:
                test_session.exec(select(1))
        except Exception as e:
            db_status = "unhealthy"
            logger.log_error("database_health_check_failed", str(e))
        
        health_status = {
            "status": "healthy" if ai_status["status"] == "healthy" and db_status == "healthy" else "degraded",
            "timestamp": datetime.now().isoformat(),
            "services": {
                "ai_service": ai_status,
                "database": {"status": db_status},
                "api": {"status": "healthy"}
            }
        }
        
        logger._create_log(
            level="info" if health_status["status"] == "healthy" else "warning",
            action="full_health_status",
            message=f"Full system status: {health_status['status']}",
            details=health_status
        )
        
        return health_status
        
    except Exception as e:
        logger.log_error("full_health_check_failed", str(e))
        
        return {
            "status": "unhealthy",
            "timestamp": datetime.now().isoformat(),
            "error": str(e),
            "services": {
                "ai_service": {"status": "unknown"},
                "database": {"status": "unknown"},
                "api": {"status": "unhealthy"}
            }
        }