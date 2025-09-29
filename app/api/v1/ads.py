from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID
from app.core.database import get_db
from app.core.dependencies import get_current_active_user
from app.models.user import User
from app.models.enums import AdStatus
from app.schemas.ad import *
from app.services.ad_service import AdService
from app.services.dify_service import DifyService

router = APIRouter(prefix="/ads", tags=["Ads"])


@router.post("/generate", response_model=AdResponse)
async def generate_ad(
        request: AdGenerationRequest,
        current_user: User = Depends(get_current_active_user),
        db: Session = Depends(get_db)
):
    """Generate new ad"""

    ad_service = AdService(db)

    # Check company limits
    if not ad_service.check_generation_limit(current_user.company_id):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Monthly ad generation limit reached"
        )

    # Generate ad
    ad = await ad_service.generate_ad(
        user=current_user,
        request=request
    )

    return ad


@router.post("/regenerate", response_model=AdResponse)
async def regenerate_ad(
        request: AdRegenerationRequest,
        current_user: User = Depends(get_current_active_user),
        db: Session = Depends(get_db)
):
    """Regenerate existing ad"""

    ad_service = AdService(db)

    # Check ownership
    original_ad = ad_service.get_ad(request.ad_id)
    if not original_ad:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ad not found"
        )

    if original_ad.company_id != current_user.company_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to regenerate this ad"
        )

    # Regenerate
    new_ad = await ad_service.regenerate_ad(
        user=current_user,
        original_ad=original_ad,
        regenerate_image=request.regenerate_image,
        additional_instructions=request.additional_instructions
    )

    return new_ad


@router.post("/evaluate", response_model=EvaluationResponse)
async def evaluate_ad(
        request: AdEvaluationRequest,
        current_user: User = Depends(get_current_active_user),
        db: Session = Depends(get_db)
):
    """Evaluate ad quality"""

    ad_service = AdService(db)

    # Check ownership
    ad = ad_service.get_ad(request.ad_id)
    if not ad:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ad not found"
        )

    if ad.company_id != current_user.company_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to evaluate this ad"
        )

    # Evaluate
    evaluation = await ad_service.evaluate_ad(ad)

    return evaluation


@router.get("/", response_model=AdListResponse)
async def list_ads(
        page: int = Query(1, ge=1),
        per_page: int = Query(20, ge=1, le=100),
        status: Optional[AdStatus] = None,
        current_user: User = Depends(get_current_active_user),
        db: Session = Depends(get_db)
):
    """List company ads"""

    ad_service = AdService(db)

    result = ad_service.list_company_ads(
        company_id=current_user.company_id,
        page=page,
        per_page=per_page,
        status=status
    )

    return result


@router.get("/{ad_id}", response_model=AdResponse)
async def get_ad(
        ad_id: UUID,
        current_user: User = Depends(get_current_active_user),
        db: Session = Depends(get_db)
):
    """Get specific ad"""

    ad_service = AdService(db)

    ad = ad_service.get_ad(ad_id)
    if not ad:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ad not found"
        )

    # Check ownership
    if ad.company_id != current_user.company_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to view this ad"
        )

    return ad


@router.delete("/{ad_id}")
async def delete_ad(
        ad_id: UUID,
        current_user: User = Depends(get_current_active_user),
        db: Session = Depends(get_db)
):
    """Delete ad"""

    ad_service = AdService(db)

    ad = ad_service.get_ad(ad_id)
    if not ad:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ad not found"
        )

    # Check ownership
    if ad.company_id != current_user.company_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to delete this ad"
        )

    ad_service.delete_ad(ad_id)

    return {"message": "Ad deleted successfully"}
