from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status, Request, UploadFile, File
from fastapi.security import HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from src.database.db import get_db
from src.database.models import User
from src.schemas import UserCreate, UserResponse, UserLogin, Token
from src.repository.users import UserRepository
from src.services.auth import AuthService, get_current_active_user
from src.services.cloudinary import CloudinaryService
from src.services.email import email_service
from src.services.rate_limiter import limiter
from src.conf.config import settings

router = APIRouter()


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("5/minute")  # 5 registrations per minute
async def register_user(request: Request, user: UserCreate, db: Session = Depends(get_db)):
    """Register a new user."""
    # Check if user already exists
    existing_user = UserRepository.get_user_by_username(db, user.username)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Username already registered"
        )
    
    existing_email = UserRepository.get_user_by_email(db, user.email)
    if existing_email:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered"
        )
    
    # Create new user
    new_user = UserRepository.create_user(db, user)
    
    # Generate verification token and send email
    verification_token = AuthService.create_email_verification_token({"sub": new_user.email})
    new_user.verification_token = verification_token
    db.commit()
    
    # Send verification email
    base_url = str(request.base_url).rstrip('/')
    try:
        await email_service.send_verification_email(
            new_user.email, 
            verification_token, 
            base_url
        )
    except Exception as e:
        # Log error but don't fail registration
        print(f"Failed to send verification email: {e}")
    
    return new_user


@router.post("/login", response_model=Token)
@limiter.limit("10/minute")  # 10 login attempts per minute
async def login_user(request: Request, user_credentials: UserLogin, db: Session = Depends(get_db)):
    """Login user and return access token."""
    user = UserRepository.authenticate_user(db, user_credentials.username, user_credentials.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
    access_token = AuthService.create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/me", response_model=UserResponse)
@limiter.limit(settings.auth_me_rate_limit)
async def read_users_me(
    request: Request, 
    current_user = Depends(get_current_active_user)
):
    """Get current user information. Rate limited to prevent abuse."""
    return current_user


@router.post("/avatar", response_model=UserResponse)
@limiter.limit("5/minute")  # 5 avatar uploads per minute
async def upload_avatar(
    request: Request,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Upload user avatar."""
    try:
        # Upload avatar to Cloudinary
        avatar_url = await CloudinaryService.upload_avatar(file, current_user.id)
        
        # Delete old avatar if exists
        if current_user.avatar_url:
            CloudinaryService.delete_avatar(current_user.avatar_url)
        
        # Update user avatar in database
        updated_user = UserRepository.update_avatar(db, current_user.id, avatar_url)
        
        if not updated_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        return updated_user
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to upload avatar"
        )


@router.delete("/avatar", response_model=UserResponse)
@limiter.limit("10/minute")
async def delete_avatar(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Delete user avatar."""
    try:
        # Delete avatar from Cloudinary
        if current_user.avatar_url:
            CloudinaryService.delete_avatar(current_user.avatar_url)
        
        # Remove avatar URL from database
        updated_user = UserRepository.update_avatar(db, current_user.id, None)
        
        if not updated_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        return updated_user
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete avatar"
        )


@router.get("/verify-email")
@limiter.limit("10/minute")  # 10 verification attempts per minute
async def verify_email(
    request: Request,
    token: str,
    db: Session = Depends(get_db)
):
    """Verify user email with token."""
    # Verify the token
    email = AuthService.verify_email_token(token)
    if not email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired verification token"
        )
    
    # Find user by email
    user = UserRepository.get_user_by_email(db, email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Check if already verified
    if user.is_verified:
        return {"message": "Email already verified"}
    
    # Verify user
    user.is_verified = True
    user.verification_token = None
    db.commit()
    
    return {"message": "Email successfully verified"}


@router.post("/resend-verification")
@limiter.limit("3/minute")  # 3 resend attempts per minute  
async def resend_verification_email(
    request: Request,
    email_request: dict,  # Will contain {"email": "user@example.com"}
    db: Session = Depends(get_db)
):
    """Resend verification email."""
    # Extract email from request
    email = email_request.get("email")
    if not email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email is required"
        )
    
    # Find user by email
    user = UserRepository.get_user_by_email(db, email)
    if not user:
        # Don't reveal if email exists
        return {"message": "If the email exists, verification email has been sent"}
    
    # Check if already verified
    if user.is_verified:
        return {"message": "Email is already verified"}
    
    # Generate new verification token
    verification_token = AuthService.create_email_verification_token({"sub": user.email})
    user.verification_token = verification_token
    db.commit()
    
    # Send verification email
    base_url = str(request.base_url).rstrip('/')
    try:
        await email_service.send_verification_email(
            user.email, 
            verification_token, 
            base_url
        )
    except Exception as e:
        print(f"Failed to send verification email: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send verification email"
        )
    
    return {"message": "If the email exists, verification email has been sent"}