from sqlmodel import Session, select
from fastapi import HTTPException, status
from models.user import User, UserCreate, UserLogin
from config.auth_config import verify_password, get_password_hash, create_access_token
from datetime import timedelta

class AuthController:
    @staticmethod
    def create_user(user: UserCreate, session: Session) -> User:
        statement = select(User).where(
            (User.email == user.email) | (User.username == user.username)
        )
        existing_user = session.exec(statement).first()
        
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email or username already registered"
            )
        
        hashed_password = get_password_hash(user.password)
        db_user = User(
            email=user.email,
            username=user.username,
            hashed_password=hashed_password
        )
        
        session.add(db_user)
        session.commit()
        session.refresh(db_user)
        return db_user

    @staticmethod
    def login_user(login_data: UserLogin, session: Session):
        statement = select(User).where(User.email == login_data.email)
        user = session.exec(statement).first()
        
        if not user or not verify_password(login_data.password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        access_token = create_access_token(data={"sub": user.email})
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": {
                "id": user.id,
                "username": user.username,
                "email": user.email
            }
        }