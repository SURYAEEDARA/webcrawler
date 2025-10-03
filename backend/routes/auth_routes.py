from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session
from config.database import get_session
from models.user import UserCreate, UserRead, UserLogin
from controllers.user_controller import UserController
from config.dependencies import get_current_active_user

router = APIRouter(prefix="/auth", tags=["authentication"])

@router.post("/register", response_model=UserRead)
def register(user: UserCreate, session: Session = Depends(get_session)):
    """Register a new user"""
    return UserController.create_user(user, session)

@router.post("/login")
def login(login_data: UserLogin, session: Session = Depends(get_session)):
    """Login user and return JWT token"""
    return UserController.login_user(login_data, session)

@router.get("/me", response_model=UserRead)
def get_current_user(current_user: UserRead = Depends(get_current_active_user)):
    """Get current user information"""
    return current_user