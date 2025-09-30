from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_company_user
from app.models.user import User
from app.schemas.company import (
    CompanyDashboardResponse,
    CompanyProfileResponse,
    CompanyProfileUpdate,
    CompanyUsageResponse,
)
from app.services.ad_service import AdService


router = APIRouter(prefix="/company", tags=["Company"])


@router.get("/dashboard", response_model=CompanyDashboardResponse)
async def get_company_dashboard(
    current_user: User = Depends(get_company_user), db: Session = Depends(get_db)
):
    """Get company dashboard data"""

    ad_service = AdService(db)

    # Get company stats
    total_ads = ad_service.get_company_ad_count(current_user.company_id)
    ads_this_month = ad_service.get_company_monthly_count(current_user.company_id)

    # Get recent ads
    recent_ads = ad_service.get_recent_ads(current_user.company_id, limit=5)

    # Get evaluation stats
    avg_score = ad_service.get_average_evaluation_score(current_user.company_id)

    return CompanyDashboardResponse(
        company_id=current_user.company_id,
        company_name=current_user.company.name,
        total_ads_generated=total_ads,
        ads_generated_this_month=ads_this_month,
        monthly_limit=current_user.company.monthly_ad_limit,
        average_evaluation_score=avg_score,
        recent_ads=recent_ads,
    )


@router.get("/usage", response_model=CompanyUsageResponse)
async def get_company_usage(
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    current_user: User = Depends(get_company_user),
    db: Session = Depends(get_db),
):
    """Get company usage statistics"""

    ad_service = AdService(db)

    # Default to current month if no dates provided
    if not end_date:
        end_date = datetime.utcnow()
    if not start_date:
        start_date = datetime(end_date.year, end_date.month, 1)

    usage_data = ad_service.get_company_usage(
        company_id=current_user.company_id, start_date=start_date, end_date=end_date
    )

    return CompanyUsageResponse(
        company_id=current_user.company_id,
        period_start=start_date,
        period_end=end_date,
        total_generated=usage_data["total_generated"],
        total_regenerated=usage_data["total_regenerated"],
        total_evaluated=usage_data["total_evaluated"],
        daily_breakdown=usage_data["daily_breakdown"],
        platform_distribution=usage_data["platform_distribution"],
        remaining_monthly_limit=current_user.company.monthly_ad_limit
        - current_user.company.ads_generated_this_month,
    )


@router.get("/profile", response_model=CompanyProfileResponse)
async def get_company_profile(
    current_user: User = Depends(get_company_user), db: Session = Depends(get_db)
):
    """Get company profile"""

    company = current_user.company

    return CompanyProfileResponse(
        id=company.id,
        name=company.name,
        email=company.email,
        phone=company.phone,
        website=company.website,
        address=company.address,
        city=company.city,
        country=company.country,
        industry=company.industry,
        size=company.size,
        description=company.description,
        is_verified=company.is_verified,
        created_at=company.created_at,
    )


@router.put("/profile", response_model=CompanyProfileResponse)
async def update_company_profile(
    update_data: CompanyProfileUpdate,
    current_user: User = Depends(get_company_user),
    db: Session = Depends(get_db),
):
    """Update company profile"""

    company = current_user.company

    # Update fields if provided
    update_dict = update_data.dict(exclude_unset=True)
    for field, value in update_dict.items():
        setattr(company, field, value)

    company.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(company)

    # ✅ Return explicit mapping (works with Pydantic v2)
    return CompanyProfileResponse(
        id=company.id,
        name=company.name,
        email=company.email,
        phone=company.phone,
        website=company.website,
        address=company.address,
        city=company.city,
        country=company.country,
        industry=company.industry,
        size=company.size,
        description=company.description,
        is_verified=company.is_verified,
        created_at=company.created_at,
    )


@router.get("/ads/statistics")
async def get_ad_statistics(
    current_user: User = Depends(get_company_user), db: Session = Depends(get_db)
):
    """Get detailed ad statistics for the company"""

    ad_service = AdService(db)

    stats = ad_service.get_company_ad_statistics(current_user.company_id)

    return {
        "total_ads": stats["total"],
        "by_status": stats["by_status"],
        "by_event": stats["by_event"],
        "regeneration_stats": {
            "total_regenerations": stats["total_regenerations"],
            "average_regenerations_per_ad": stats["avg_regenerations"],
        },
        "evaluation_stats": {
            "total_evaluated": stats["total_evaluated"],
            "average_score": stats["avg_score"],
            "score_distribution": stats["score_distribution"],
        },
    }
