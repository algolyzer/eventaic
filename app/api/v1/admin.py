from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime, timedelta
from app.core.database import get_db
from app.core.dependencies import get_super_admin
from app.models.user import User
from app.models.enums import AdStatus
from app.services.admin_service import AdminService
from app.schemas.response import (
    AdminDashboardResponse,
    CompanyListResponse,
    AdminStatisticsResponse,
    CompanyDetailResponse
)
from uuid import UUID

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
    """List all users across platform"""

    admin_service = AdminService(db)

    users = admin_service.get_all_users(
        page=page,
        per_page=per_page,
        search=search
    )

    return users
