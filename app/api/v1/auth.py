import logging

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.core.dependencies import get_current_active_user, get_current_user
from app.models.user import User
from app.schemas.auth import (
    ChangePasswordRequest,
    EmailVerificationRequest,
    LoginRequest,
    PasswordResetConfirm,
    PasswordResetRequest,
    RefreshTokenRequest,
    RegisterRequest,
    TokenResponse,
)
from app.services.auth_service import AuthService
from app.services.email_service import EmailService


logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=TokenResponse)
async def register(
    request: RegisterRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """Register new user"""

    auth_service = AuthService(db)
    email_service = EmailService()

    try:
        # Check if user exists (auth_service will also check, but we check here for clearer errors)
        if auth_service.get_user_by_email(request.email):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered",
            )

        if auth_service.get_user_by_username(request.username):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Username already taken"
            )

        # Create user
        user = await auth_service.create_user(request)

        # Send verification email if enabled
        if settings.EMAIL_VERIFICATION_REQUIRED:
            verification_link = auth_service.create_verification_link(user)
            background_tasks.add_task(
                email_service.send_verification_email,
                user.email,
                user.username,
                verification_link,
            )

        # Generate tokens
        tokens = auth_service.create_tokens(user)

        # Return response with user data
        return {
            "access_token": tokens.access_token,
            "refresh_token": tokens.refresh_token,
            "token_type": tokens.token_type,
            "expires_in": tokens.expires_in,
            "user": {
                "id": str(user.id),
                "email": user.email,
                "username": user.username,
                "full_name": user.full_name,
                "name": user.full_name or user.username,
                "role": user.role.value if hasattr(user.role, "value") else user.role,
                "company_id": str(user.company_id) if user.company_id else None,
                "company_name": user.company.name if user.company else None,
            },
        }
    except ValueError as e:
        # Handle validation errors from auth service
        logger.warning(f"Registration validation error: {str(e)}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        # Handle unexpected errors
        logger.error(f"Registration failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Registration failed: {str(e)}",
        )


@router.post("/login")
async def login(request: LoginRequest, db: Session = Depends(get_db)):
    """Login user with username OR email"""

    auth_service = AuthService(db)
    login_identifier = request.username

    # Try to authenticate
    if "@" in login_identifier:
        user = auth_service.authenticate_user_by_email(
            login_identifier, request.password
        )
        if not user:
            user = auth_service.authenticate_user(login_identifier, request.password)
    else:
        user = auth_service.authenticate_user(login_identifier, request.password)
        if not user:
            user = auth_service.authenticate_user_by_email(
                login_identifier, request.password
            )

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username/email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Check email verification
    if settings.EMAIL_VERIFICATION_REQUIRED and not user.is_email_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Email not verified. Please verify your email first.",
        )

    # Update last login
    auth_service.update_last_login(user)

    # Generate tokens
    tokens = auth_service.create_tokens(user)

    # THIS IS THE FIX - Return proper response with user object
    return {
        "access_token": tokens.access_token,
        "refresh_token": tokens.refresh_token,
        "token_type": "bearer",
        "expires_in": 1800,
        "user": {
            "id": str(user.id),
            "email": user.email,
            "username": user.username,
            "full_name": user.full_name,
            "name": user.full_name or user.username,
            "role": user.role.value if hasattr(user.role, "value") else user.role,
            "company_id": str(user.company_id) if user.company_id else None,
            "company_name": user.company.name if user.company else None,
        },
    }


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(request: RefreshTokenRequest, db: Session = Depends(get_db)):
    """Refresh access token"""

    auth_service = AuthService(db)

    # Validate refresh token
    user = auth_service.validate_refresh_token(request.refresh_token)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token"
        )

    # Generate new tokens
    tokens = auth_service.create_tokens(user)

    # Return response with user data
    return {
        "access_token": tokens.access_token,
        "refresh_token": tokens.refresh_token,
        "token_type": tokens.token_type,
        "expires_in": tokens.expires_in,
        "user": {
            "id": str(user.id),
            "email": user.email,
            "username": user.username,
            "full_name": user.full_name,
            "name": user.full_name or user.username,
            "role": user.role.value if hasattr(user.role, "value") else user.role,
            "company_id": str(user.company_id) if user.company_id else None,
            "company_name": user.company.name if user.company else None,
        },
    }


@router.post("/logout")
async def logout(current_user: User = Depends(get_current_user)):
    """Logout user (client should discard tokens)"""

    # In a more complex implementation, you might want to:
    # - Blacklist the token
    # - Clear server-side sessions
    # - Log the logout event

    return {"message": "Successfully logged out"}


@router.post("/password-reset/request")
async def request_password_reset(
    request: PasswordResetRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """Request password reset"""

    auth_service = AuthService(db)
    email_service = EmailService()

    user = auth_service.get_user_by_email(request.email)
    if user:
        # Generate reset token
        reset_token = auth_service.create_password_reset_token(user)
        reset_link = f"{settings.PASSWORD_RESET_URL}?token={reset_token}"

        # Send email
        background_tasks.add_task(
            email_service.send_password_reset_email,
            user.email,
            user.username,
            reset_link,
        )

    # Always return success to prevent email enumeration
    return {"message": "If the email exists, a password reset link has been sent"}


@router.post("/password-reset/confirm")
async def confirm_password_reset(
    request: PasswordResetConfirm, db: Session = Depends(get_db)
):
    """Confirm password reset with token"""

    auth_service = AuthService(db)

    # Reset password
    success = auth_service.reset_password(request.token, request.new_password)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token",
        )

    return {"message": "Password successfully reset"}


@router.post("/verify-email")
async def verify_email(
    request: EmailVerificationRequest, db: Session = Depends(get_db)
):
    """Verify email with token"""

    auth_service = AuthService(db)

    success = auth_service.verify_email(request.token)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired verification token",
        )

    return {"message": "Email successfully verified"}


@router.post("/resend-verification")
async def resend_verification(
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Resend verification email"""

    if current_user.is_email_verified:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Email already verified"
        )

    auth_service = AuthService(db)
    email_service = EmailService()

    # Generate new verification token
    verification_link = auth_service.create_verification_link(current_user)

    # Send email
    background_tasks.add_task(
        email_service.send_verification_email,
        current_user.email,
        current_user.username,
        verification_link,
    )

    return {"message": "Verification email sent"}


@router.post("/change-password")
async def change_password(
    request: ChangePasswordRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Change user password"""

    auth_service = AuthService(db)

    # Verify current password
    if not auth_service.verify_password(
        request.current_password, current_user.hashed_password
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect",
        )

    # Update password
    auth_service.update_password(current_user, request.new_password)

    return {"message": "Password successfully changed"}


@router.get("/me")
async def get_current_user_info(current_user: User = Depends(get_current_active_user)):
    """Get current user information"""

    return {
        "id": str(current_user.id),
        "email": current_user.email,
        "username": current_user.username,
        "full_name": current_user.full_name,
        "name": current_user.full_name or current_user.username,
        "phone": current_user.phone,
        "role": (
            current_user.role.value
            if hasattr(current_user.role, "value")
            else current_user.role
        ),
        "is_email_verified": current_user.is_email_verified,
        "company_id": str(current_user.company_id) if current_user.company_id else None,
        "company_name": current_user.company.name if current_user.company else None,
        "created_at": (
            current_user.created_at.isoformat() if current_user.created_at else None
        ),
        "last_login": (
            current_user.last_login.isoformat() if current_user.last_login else None
        ),
    }
