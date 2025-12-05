from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session
from config.database import get_session
from models.user import UserCreate, UserRead, UserLogin
from controllers.auth_controller import AuthController
from controllers.logger import AppLogger
from config.dependencies import get_current_active_user

router = APIRouter(prefix="/auth", tags=["authentication"])

@router.post("/register", response_model=UserRead)
def register(user: UserCreate, session: Session = Depends(get_session)):
    logger = AppLogger(session)
    
    try:
        result = AuthController.create_user(user, session)
        
        logger._create_log(
            level="info",
            action="user_registered",
            message=f"New user registered: {user.email}",
            user_id=result.id
        )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.log_error("user_registration_error", str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration failed due to server error"
        )

@router.post("/login")
def login(login_data: UserLogin, session: Session = Depends(get_session)):
    logger = AppLogger(session)
    
    try:
        result = AuthController.login_user(login_data, session)
        
        logger._create_log(
            level="info",
            action="user_logged_in",
            message=f"User logged in: {login_data.email}",
            user_id=result["user"]["id"]
        )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.log_error("user_login_error", str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Login failed due to server error"
        )

@router.get("/me", response_model=UserRead)
def get_current_user(current_user: UserRead = Depends(get_current_active_user)):
    return current_user