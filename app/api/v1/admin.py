from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime, timedelta
from app.core.database import get_db
from app.core.dependencies import get_super_admin
from app.models.user import User
from app.models.user import User as UserModel
from app.models.company import Company
from app.models.ad import Ad
from app.repositories.user_repository import UserRepository
from app.services.admin_service import AdminService
from app.schemas.response import (
    AdminDashboardResponse,
    CompanyListResponse,
    AdminStatisticsResponse,
    CompanyDetailResponse
)

from app.schemas.user import UserCreate
from app.services.auth_service import AuthService
from app.core.security import Security

from uuid import UUID
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/admin", tags=["Admin"])


@router.get("/dashboard", response_model=AdminDashboardResponse)
async def get_admin_dashboard(
        current_user: User = Depends(get_super_admin),
        db: Session = Depends(get_db)
):
    """Get admin dashboard overview"""

    admin_service = AdminService(db)

    dashboard_data = admin_service.get_dashboard_data()

    return dashboard_data


@router.get("/companies", response_model=CompanyListResponse)
async def list_companies(
        page: int = Query(1, ge=1),
        per_page: int = Query(20, ge=1, le=100),
        search: Optional[str] = None,
        is_active: Optional[bool] = None,
        current_user: User = Depends(get_super_admin),
        db: Session = Depends(get_db)
):
    """List all companies with pagination"""

    admin_service = AdminService(db)

    companies = admin_service.get_companies(
        page=page,
        per_page=per_page,
        search=search,
        is_active=is_active
    )

    return companies


@router.get("/companies/{company_id}", response_model=CompanyDetailResponse)
async def get_company_detail(
        company_id: UUID,
        current_user: User = Depends(get_super_admin),
        db: Session = Depends(get_db)
):
    """Get detailed information about a specific company"""

    admin_service = AdminService(db)

    company = admin_service.get_company_detail(company_id)

    if not company:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Company not found"
        )

    return company


@router.get("/statistics", response_model=AdminStatisticsResponse)
async def get_statistics(
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        company_id: Optional[UUID] = None,
        current_user: User = Depends(get_super_admin),
        db: Session = Depends(get_db)
):
    """Get platform statistics"""

    admin_service = AdminService(db)

    # Default to last 30 days if no dates provided
    if not end_date:
        end_date = datetime.utcnow()
    if not start_date:
        start_date = end_date - timedelta(days=30)

    stats = admin_service.get_statistics(
        start_date=start_date,
        end_date=end_date,
        company_id=company_id
    )

    return stats


@router.post("/companies/{company_id}/activate")
async def activate_company(
        company_id: UUID,
        current_user: User = Depends(get_super_admin),
        db: Session = Depends(get_db)
):
    """Activate a company"""

    admin_service = AdminService(db)

    success = admin_service.update_company_status(company_id, is_active=True)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Company not found"
        )

    return {"message": "Company activated successfully"}


@router.post("/companies/{company_id}/deactivate")
async def deactivate_company(
        company_id: UUID,
        current_user: User = Depends(get_super_admin),
        db: Session = Depends(get_db)
):
    """Deactivate a company"""

    admin_service = AdminService(db)

    success = admin_service.update_company_status(company_id, is_active=False)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Company not found"
        )

    return {"message": "Company deactivated successfully"}


@router.put("/companies/{company_id}/limits")
async def update_company_limits(
        company_id: UUID,
        monthly_limit: int = Query(..., ge=0, le=10000),
        current_user: User = Depends(get_super_admin),
        db: Session = Depends(get_db)
):
    """Update company's monthly ad generation limit"""

    admin_service = AdminService(db)

    success = admin_service.update_company_limits(company_id, monthly_limit)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Company not found"
        )

    return {"message": f"Monthly limit updated to {monthly_limit}"}


@router.get("/users")
async def list_all_users(
        page: int = Query(1, ge=1),
        per_page: int = Query(20, ge=1, le=100),
        search: Optional[str] = None,
        current_user: User = Depends(get_super_admin),
        db: Session = Depends(get_db)
):
    """List all users with pagination (admin only)"""

    admin_service = AdminService(db)

    users = admin_service.get_all_users(
        page=page,
        per_page=per_page,
        search=search
    )

    return users


@router.post("/users")
async def create_user_by_admin(
        user_data: UserCreate,
        current_user: User = Depends(get_super_admin),
        db: Session = Depends(get_db)
):
    """Create a new user (admin only)"""

    try:
        auth_service = AuthService(db)
        security = Security()

        # Validate and sanitize inputs
        email = user_data.email.strip().lower()
        username = user_data.username.strip()
        full_name = user_data.full_name.strip() if user_data.full_name else None
        company_name = user_data.company_name.strip() if user_data.company_name else None

        # Check if user already exists
        if auth_service.get_user_by_email(email):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )

        if auth_service.get_user_by_username(username):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already taken"
            )

        # Validate password strength
        if len(user_data.password) < 8:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Password must be at least 8 characters long"
            )

        # Create or get company if company_name provided and not empty
        company = None
        if company_name:
            from app.repositories.company_repository import CompanyRepository
            company_repo = CompanyRepository(db)
            company = company_repo.get_by_name(company_name)
            if not company:
                # Create new company
                company = Company(
                    name=company_name,
                    email=email
                )
                db.add(company)
                db.flush()
                logger.info(f"New company created by admin: {company.name}")

        # Hash password
        hashed_password = security.get_password_hash(user_data.password)

        # Create user with specified role
        user = UserModel(
            email=email,
            username=username,
            full_name=full_name,
            phone=user_data.phone.strip() if user_data.phone else None,
            hashed_password=hashed_password,
            role=user_data.role,
            company_id=company.id if company else None,
            is_email_verified=True,  # Admin-created users are auto-verified
            is_active=True
        )

        db.add(user)
        db.commit()
        db.refresh(user)

        logger.info(f"User {user.id} ({user.email}) created by admin {current_user.id}")

        return {
            "message": "User created successfully",
            "user": {
                "id": str(user.id),
                "email": user.email,
                "username": user.username,
                "full_name": user.full_name,
                "role": user.role.value,
                "company_id": str(user.company_id) if user.company_id else None,
                "company_name": company.name if company else None
            }
        }

    except HTTPException:
        # Re-raise HTTP exceptions
        db.rollback()
        raise
    except Exception as e:
        # Rollback and log any other errors
        db.rollback()
        logger.error(f"Admin user creation failed: {str(e)}")
        logger.exception("Full traceback:")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create user: {str(e)}"
        )


@router.post("/users/{user_id}/deactivate")
async def deactivate_user(
        user_id: UUID,
        current_user: User = Depends(get_super_admin),
        db: Session = Depends(get_db)
):
    """Deactivate a user"""

    user_repository = UserRepository(db)
    user = user_repository.get(user_id)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    if user.id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You cannot deactivate your own account"
        )

    user.is_active = False
    db.commit()

    logger.info(f"User {user_id} deactivated by admin {current_user.id}")

    return {"message": "User deactivated successfully"}


@router.post("/users/{user_id}/activate")
async def activate_user(
        user_id: UUID,
        current_user: User = Depends(get_super_admin),
        db: Session = Depends(get_db)
):
    """Activate a user"""

    user_repository = UserRepository(db)
    user = user_repository.get(user_id)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    user.is_active = True
    user.is_deleted = False  # Also un-delete if deleted
    db.commit()

    logger.info(f"User {user_id} activated by admin {current_user.id}")

    return {"message": "User activated successfully"}


@router.delete("/users/{user_id}")
async def delete_user(
        user_id: UUID,
        permanent: bool = Query(False, description="Permanently delete user"),
        current_user: User = Depends(get_super_admin),
        db: Session = Depends(get_db)
):
    """Delete a user (soft delete by default, permanent if specified)"""

    user_repository = UserRepository(db)
    user = user_repository.get(user_id)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # Prevent deleting yourself
    if user.id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You cannot delete your own account"
        )

    if permanent:
        # Permanent delete - remove from database
        db.delete(user)
        db.commit()
        logger.warning(f"User {user_id} permanently deleted by admin {current_user.id}")
        return {"message": "User permanently deleted"}
    else:
        # Soft delete - mark as deleted
        success = user_repository.soft_delete(user_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete user"
            )
        logger.info(f"User {user_id} soft deleted by admin {current_user.id}")
        return {"message": "User deleted successfully"}


@router.get("/users/{user_id}")
async def get_user_detail(
        user_id: UUID,
        current_user: User = Depends(get_super_admin),
        db: Session = Depends(get_db)
):
    """Get detailed user information"""

    user_repository = UserRepository(db)
    user = user_repository.get(user_id)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # Count user's ads
    ad_count = db.query(Ad).filter(Ad.created_by_id == user_id).count()

    return {
        "id": str(user.id),
        "email": user.email,
        "username": user.username,
        "full_name": user.full_name,
        "phone": user.phone,
        "role": user.role.value,
        "is_active": user.is_active,
        "is_deleted": user.is_deleted,
        "is_email_verified": user.is_email_verified,
        "company_id": str(user.company_id) if user.company_id else None,
        "company_name": user.company.name if user.company else None,
        "total_ads_created": ad_count,
        "created_at": user.created_at.isoformat(),
        "last_login": user.last_login.isoformat() if user.last_login else None
    }
