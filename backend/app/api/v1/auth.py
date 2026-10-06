from datetime import timedelta
from typing import Any
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.core.config import settings
from app.core.security import create_access_token, get_password_hash, verify_password
from app.models.user import User, UserRole
from app.schemas.auth import LoginRequest, RegisterRequest, Token
from app.schemas.user import UserResponse

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=Token, status_code=status.HTTP_201_CREATED)
def register(
    req: RegisterRequest,
    db: Session = Depends(get_db)
) -> Any:
    """Register a new student or teacher account."""
    existing_user = db.query(User).filter(User.email == req.email.lower()).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A user with this email address already exists"
        )
    
    # Enforce STUDENT role strictly on public registration to prevent privilege escalation
    user = User(
        email=req.email.lower(),
        hashed_password=get_password_hash(req.password),
        full_name=req.full_name,
        role=UserRole.STUDENT,
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    access_token = create_access_token(
        subject=user.id,
        role=user.role.value,
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )

    return Token(
        access_token=access_token,
        token_type="bearer",
        user=UserResponse.model_validate(user)
    )


@router.post("/login", response_model=Token)
def login(
    req: LoginRequest,
    db: Session = Depends(get_db)
) -> Any:
    """Log in with email and password to receive a JWT access token."""
    user = db.query(User).filter(User.email == req.email.lower()).first()
    if not user or not verify_password(req.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This account has been deactivated"
        )

    access_token = create_access_token(
        subject=user.id,
        role=user.role.value,
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )

    return Token(
        access_token=access_token,
        token_type="bearer",
        user=UserResponse.model_validate(user)
    )


@router.post("/login/oauth", response_model=Token, include_in_schema=False)
def login_oauth_form(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
) -> Any:
    """Swagger UI OAuth2 password compatibility endpoint."""
    user = db.query(User).filter(User.email == form_data.username.lower()).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token(
        subject=user.id,
        role=user.role.value,
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    return Token(
        access_token=access_token,
        token_type="bearer",
        user=UserResponse.model_validate(user)
    )


@router.get("/me", response_model=UserResponse)
def get_current_user_profile(
    current_user: User = Depends(get_current_user)
) -> Any:
    """Get profile information for the authenticated user."""
    return UserResponse.model_validate(current_user)


@router.post("/logout")
def logout(current_user: User = Depends(get_current_user)) -> Any:
    """Acknowledge logout (JWT tokens are stateless and cleared client-side)."""
    return {"message": "Successfully logged out"}
