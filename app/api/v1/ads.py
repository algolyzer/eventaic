from datetime import datetime
import logging
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_active_user
from app.models.enums import AdStatus
from app.models.user import User
from app.schemas.ad import (
    AdEvaluationRequest,
    AdGenerationRequest,
    AdListResponse,
    AdRegenerationRequest,
    AdResponse,
    EvaluationResponse,
    ImageGenerationRequest,
    ImageGenerationResponse,
)
from app.services.ad_service import AdService


logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ads", tags=["Ads"])


@router.post(
    "/generate", response_model=AdResponse, status_code=status.HTTP_201_CREATED
)
async def generate_ad(
    request: AdGenerationRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    Generate new ad with content and image

    Flow:
    1. Generate ad content via Dify
    2. Extract image prompt from response
    3. Generate image via Dify using the prompt
    4. Return complete ad with image

    **Note**: This endpoint may take 10-30 seconds due to image generation.
    """

    ad_service = AdService(db)

    # Check company limits
    if not ad_service.check_generation_limit(current_user.company_id):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Monthly ad generation limit reached. Please upgrade your plan.",
        )

    try:
        # Generate ad with image
        ad = await ad_service.generate_ad(user=current_user, request=request)

        logger.info(f"Ad {ad.id} generated successfully for user {current_user.id}")
        return ad

    except Exception as e:
        logger.error(f"Ad generation failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate ad: {str(e)}",
        )


@router.post("/regenerate", response_model=AdResponse)
async def regenerate_ad(
    request: AdRegenerationRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    Regenerate existing ad

    Options:
    - Set `regenerate_image=true` to only regenerate the image
    - Set `regenerate_image=false` to regenerate entire ad content and image
    - Provide `additional_instructions` for specific regeneration guidance
    """

    ad_service = AdService(db)

    # Get and validate original ad
    original_ad = ad_service.get_ad(request.ad_id)
    if not original_ad:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Ad not found"
        )

    # Check ownership
    if original_ad.company_id != current_user.company_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to regenerate this ad",
        )

    try:
        # Regenerate
        new_ad = await ad_service.regenerate_ad(
            user=current_user,
            original_ad=original_ad,
            regenerate_image=request.regenerate_image,
            additional_instructions=request.additional_instructions,
        )

        logger.info(
            f"Ad regenerated successfully: "
            f"original={request.ad_id}, new={new_ad.id if new_ad.id != request.ad_id else 'same'}, "
            f"image_only={request.regenerate_image}"
        )
        return new_ad

    except Exception as e:
        logger.error(f"Ad regeneration failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to regenerate ad: {str(e)}",
        )


@router.post("/generate-image", response_model=ImageGenerationResponse)
async def generate_image(
    request: ImageGenerationRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    Generate or regenerate image for an existing ad

    This endpoint specifically handles image generation using the ad's image_prompt.
    Use this when you want to regenerate just the image without changing ad content.
    """

    ad_service = AdService(db)

    # Get and validate ad
    ad = ad_service.get_ad(request.ad_id)
    if not ad:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Ad not found"
        )

    # Check ownership
    if ad.company_id != current_user.company_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to modify this ad",
        )

    # Check if image exists and force_regenerate is False
    if ad.image_url and not request.force_regenerate:
        return ImageGenerationResponse(
            ad_id=ad.id,
            image_url=ad.image_url,
            image_prompt=ad.image_prompt or "",
            generated_at=ad.updated_at,
        )

    try:
        # Regenerate image only
        updated_ad = await ad_service.regenerate_ad(
            user=current_user, original_ad=ad, regenerate_image=True
        )

        return ImageGenerationResponse(
            ad_id=updated_ad.id,
            image_url=updated_ad.image_url or "",
            image_prompt=updated_ad.image_prompt or "",
            generated_at=datetime.utcnow(),
        )

    except Exception as e:
        logger.error(f"Image generation failed for ad {request.ad_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate image: {str(e)}",
        )


@router.post("/evaluate", response_model=EvaluationResponse)
async def evaluate_ad(
    request: AdEvaluationRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    Evaluate ad quality using AI

    Returns scores for:
    - Relevance (0-10)
    - Clarity (0-10)
    - Persuasiveness (0-10)
    - Brand Safety (0-10)
    - Overall Score (0-10)

    Also provides detailed feedback and recommendations.
    """

    ad_service = AdService(db)

    # Get and validate ad
    ad = ad_service.get_ad(request.ad_id)
    if not ad:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Ad not found"
        )

    # Check ownership
    if ad.company_id != current_user.company_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to evaluate this ad",
        )

    try:
        # Evaluate
        evaluation = await ad_service.evaluate_ad(ad)
        logger.info(f"Ad {ad.id} evaluated with score {evaluation.overall_score}")
        return evaluation

    except Exception as e:
        logger.error(f"Ad evaluation failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to evaluate ad: {str(e)}",
        )


@router.get("/", response_model=AdListResponse)
async def list_ads(
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(20, ge=1, le=100, description="Items per page"),
    status: Optional[AdStatus] = Query(None, description="Filter by status"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    List company ads with pagination

    Supports filtering by status and pagination.
    """

    ad_service = AdService(db)

    try:
        result = ad_service.list_company_ads(
            company_id=current_user.company_id,
            page=page,
            per_page=per_page,
            status=status,
        )

        return result

    except Exception as e:
        logger.error(f"Failed to list ads: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list ads: {str(e)}",
        )


@router.get("/{ad_id}", response_model=AdResponse)
async def get_ad(
    ad_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    Get specific ad by ID

    Returns complete ad data including:
    - Ad content (headline, description, etc.)
    - Image (base64 encoded)
    - Platform recommendations
    - Evaluation scores (if evaluated)
    """

    ad_service = AdService(db)

    # Get ad
    ad = ad_service.get_ad(ad_id)
    if not ad:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Ad not found"
        )

    # Check ownership
    if ad.company_id != current_user.company_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to view this ad",
        )

    try:
        return ad_service._format_ad_response(ad)
    except Exception as e:
        logger.error(f"Failed to format ad response: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve ad: {str(e)}",
        )


@router.delete("/{ad_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_ad(
    ad_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    Delete ad

    Permanently deletes the ad and all associated data.
    This action cannot be undone.
    """

    ad_service = AdService(db)

    # Get and validate ad
    ad = ad_service.get_ad(ad_id)
    if not ad:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Ad not found"
        )

    # Check ownership
    if ad.company_id != current_user.company_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to delete this ad",
        )

    try:
        ad_service.delete_ad(ad_id)
        logger.info(f"Ad {ad_id} deleted by user {current_user.id}")
        return None

    except Exception as e:
        logger.error(f"Failed to delete ad {ad_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete ad: {str(e)}",
        )


@router.get("/{ad_id}/history", response_model=List[AdResponse])
async def get_ad_history(
    ad_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    Get ad regeneration history

    Returns all versions of an ad (original + all regenerations).
    """

    ad_service = AdService(db)

    # Get original ad
    original_ad = ad_service.get_ad(ad_id)
    if not original_ad:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Ad not found"
        )

    # Check ownership
    if original_ad.company_id != current_user.company_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to view this ad",
        )

    try:
        # Get all related ads (parent and children)
        from app.models.ad import Ad

        # Find the root parent
        root_ad = original_ad
        while root_ad.parent_ad_id:
            root_ad = ad_service.get_ad(root_ad.parent_ad_id)
            if not root_ad:
                break

        # Get all versions
        if root_ad:
            versions = (
                db.query(Ad)
                .filter((Ad.id == root_ad.id) | (Ad.parent_ad_id == root_ad.id))
                .order_by(Ad.created_at)
                .all()
            )
        else:
            versions = [original_ad]

        return [ad_service._format_ad_response(ad) for ad in versions]

    except Exception as e:
        logger.error(f"Failed to get ad history: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve ad history: {str(e)}",
        )
