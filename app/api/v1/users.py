from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.dependencies import get_current_active_user
from app.models.user import User
from app.schemas.user import (
    UserProfileResponse,
    UserProfileUpdate,
    UserListResponse
)
from app.services.user_service import UserService

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("/profile", response_model=UserProfileResponse)
async def get_profile(
        current_user: User = Depends(get_current_active_user)
):
    """Get current user profile"""

    return UserProfileResponse(
        id=current_user.id,
        email=current_user.email,
        username=current_user.username,
        full_name=current_user.full_name,
        phone=current_user.phone,
        role=current_user.role,
        is_email_verified=current_user.is_email_verified,
        company_id=current_user.company_id,
        company_name=current_user.company.name if current_user.company else None,
        created_at=current_user.created_at,
        last_login=current_user.last_login
    )


@router.put("/profile", response_model=UserProfileResponse)
async def update_profile(
        update_data: UserProfileUpdate,
        current_user: User = Depends(get_current_active_user),
        db: Session = Depends(get_db)
):
    """Update user profile"""

    user_service = UserService(db)

    # Check if email is being changed
    if update_data.email and update_data.email != current_user.email:
        if user_service.get_by_email(update_data.email):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already in use"
            )

    # Check if username is being changed
    if update_data.username and update_data.username != current_user.username:
        if user_service.get_by_username(update_data.username):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already taken"
            )

    # Update user
    updated_user = user_service.update_user(current_user.id, update_data)

    # ✅ Return explicit mapping (avoids from_orm + missing company_name)
    return UserProfileResponse(
        id=updated_user.id,
        email=updated_user.email,
        username=updated_user.username,
        full_name=updated_user.full_name,
        phone=updated_user.phone,
        role=updated_user.role,
        is_email_verified=updated_user.is_email_verified,
        company_id=updated_user.company_id,
        company_name=updated_user.company.name if updated_user.company else None,
        created_at=updated_user.created_at,
        last_login=updated_user.last_login
    )


@router.delete("/profile")
async def delete_account(
        current_user: User = Depends(get_current_active_user),
        db: Session = Depends(get_db)
):
    """Soft delete user account"""

    user_service = UserService(db)

    # Soft delete the user
    user_service.soft_delete_user(current_user.id)

    return {"message": "Account successfully deleted"}


@router.get("/activity")
async def get_user_activity(
        current_user: User = Depends(get_current_active_user),
        db: Session = Depends(get_db)
):
    """Get user activity log"""

    user_service = UserService(db)

    activity = user_service.get_user_activity(current_user.id)

    return {
        "user_id": current_user.id,
        "total_ads_created": activity['total_ads'],
        "last_ad_created": activity['last_ad_date'],
        "total_evaluations": activity['total_evaluations'],
        "account_created": current_user.created_at,
        "last_login": current_user.last_login
    }
