from datetime import datetime, timedelta
import logging
from typing import Any, Dict, List, Optional
from uuid import UUID

from sqlalchemy import and_, func
from sqlalchemy.orm import Session, joinedload

from app.core.exceptions import CompanyLimitException, DifyAPIException
from app.models.ad import Ad, AdEvaluation
from app.models.company import Company
from app.models.enums import AdStatus, AdType
from app.models.user import User
from app.repositories.ad_repository import AdRepository
from app.schemas.ad import AdGenerationRequest, AdResponse, EvaluationResponse
from app.services.dify_service import DifyService
from app.utils.image_utils import delete_ad_images, download_image_from_url


logger = logging.getLogger(__name__)


class AdService:
    """Service for ad generation, evaluation, and management"""

    def __init__(self, db: Session):
        self.db = db
        self.ad_repository = AdRepository(db)
        self.dify_service = DifyService()

    async def generate_ad(self, user: User, request: AdGenerationRequest) -> AdResponse:
        """
        Generate new ad with content and image

        Flow:
        1. Check company limit
        2. Generate ad content via Dify
        3. Create ad record
        4. Generate image via Dify using the image_prompt
        5. Save everything
        """

        # Check company limit
        if not self.check_generation_limit(user.company_id):
            raise CompanyLimitException("Monthly ad generation limit reached")

        # Step 1: Generate ad content
        try:
            logger.info(f"Generating ad content for event: {request.event_name}")
            dify_response = await self.dify_service.generate_ad(
                event_name=request.event_name,
                product_categories=request.product_categories,
                company_name=request.company_name or user.company.name,
                location=request.location,
                product_name=request.product_name,
            )
            logger.info("Ad content generated successfully")
        except Exception as e:
            logger.error(f"Failed to generate ad content: {str(e)}")
            raise DifyAPIException(f"Unable to generate ad content: {str(e)}")

        # Step 2: Create ad record with content
        ad = Ad(
            event_name=request.event_name,
            product_name=request.product_name,
            product_categories=request.product_categories,
            location=request.location,
            headline=dify_response.get("headline"),
            description=dify_response.get("description"),
            slogan=dify_response.get("slogan"),
            cta_text=dify_response.get("cta_text"),
            keywords=dify_response.get("keywords", []),
            hashtags=dify_response.get("hashtags", []),
            image_prompt=dify_response.get("image_prompt"),
            platforms=dify_response.get("platforms", []),
            platform_details=dify_response.get("platform_details", {}),
            recommended_posting_times=dify_response.get("posting_times", []),
            budget_allocation=dify_response.get("budget_allocation", {}),
            status=AdStatus.GENERATED,
            ad_type=AdType.PRODUCT_GEN,
            company_id=user.company_id,
            created_by_id=user.id,
            dify_response=dify_response,
        )

        self.db.add(ad)
        self.db.flush()  # Get the ad ID

        # Step 3: Generate image using Dify
        if ad.image_prompt:
            try:
                logger.info(
                    f"Generating image for ad {ad.id} with prompt: {ad.image_prompt[:100]}..."
                )

                # Prepare context for better image generation
                image_context = {
                    "event_name": ad.event_name,
                    "product_categories": ad.product_categories,
                    "headline": ad.headline,
                    "description": ad.description,
                }

                # Get image URL from Dify
                image_url = await self.dify_service.generate_image(
                    image_prompt=ad.image_prompt, ad_context=image_context
                )

                if image_url:
                    logger.info(
                        f"Image URL received for ad {ad.id}: {image_url[:100]}..."
                    )

                    # Download and save the image
                    result = await download_image_from_url(
                        url=image_url,
                        ad_id=ad.id,
                        original_filename=None,  # Will auto-generate from hash
                    )

                    if result:
                        filename, public_url = result
                        ad.image_url = public_url
                        logger.info(
                            f"Image saved successfully for ad {ad.id}: {public_url}"
                        )
                    else:
                        logger.warning(f"Failed to download image for ad {ad.id}")
                else:
                    logger.warning(f"No image URL received for ad {ad.id}")

            except Exception as e:
                logger.error(f"Failed to generate image for ad {ad.id}: {str(e)}")
                # Continue without image - not critical for ad creation
        else:
            logger.warning(f"No image prompt provided for ad {ad.id}")

        # Step 4: Update company counters
        company = self.db.query(Company).filter(Company.id == user.company_id).first()
        if company:
            company.ads_generated_this_month += 1
            company.total_ads_generated += 1

        # Step 5: Commit and return
        self.db.commit()
        self.db.refresh(ad)

        logger.info(f"Ad {ad.id} created successfully with image")
        return self._format_ad_response(ad)

    async def regenerate_ad(
        self,
        user: User,
        original_ad: Ad,
        regenerate_image: bool = False,
        additional_instructions: Optional[str] = None,
    ) -> AdResponse:
        """
        Regenerate ad content or just the image

        Args:
            user: Current user
            original_ad: Original ad to regenerate from
            regenerate_image: If True, only regenerate image; if False, regenerate entire ad
            additional_instructions: Optional instructions for regeneration
        """

        if regenerate_image:
            # Only regenerate the image
            logger.info(f"🖼️ Regenerating image only for ad {original_ad.id}")

            if not original_ad.image_prompt:
                logger.error(f"❌ No image prompt available for ad {original_ad.id}")
                raise ValueError("No image prompt available for regeneration")

            try:
                image_context = {
                    "event_name": original_ad.event_name,
                    "product_categories": original_ad.product_categories,
                    "headline": original_ad.headline,
                    "description": original_ad.description,
                }

                logger.info(f"📝 Image prompt: {original_ad.image_prompt[:100]}...")
                logger.info(f"🎯 Context: {image_context}")

                # Get new image URL from Dify
                logger.info("🚀 Calling Dify image generation...")
                image_url = await self.dify_service.generate_image(
                    image_prompt=original_ad.image_prompt, ad_context=image_context
                )

                if not image_url:
                    logger.error("❌ Dify returned no image URL")
                    raise ValueError(
                        "Failed to generate image: No URL returned from Dify"
                    )

                logger.info(f"✅ Image URL received: {image_url[:100]}...")

                # Download and save the new image
                logger.info("⬇️ Downloading image from URL...")
                result = await download_image_from_url(
                    url=image_url, ad_id=original_ad.id, original_filename=None
                )

                if not result:
                    logger.error("❌ Failed to download image from URL")
                    raise ValueError("Failed to download image from generated URL")

                filename, public_url = result
                logger.info("💾 Image saved successfully!")
                logger.info(f"   Filename: {filename}")
                logger.info(f"   Public URL: {public_url}")

                # Update ad with new image
                original_ad.image_url = public_url
                original_ad.regeneration_count += 1
                original_ad.updated_at = datetime.utcnow()

                self.db.commit()
                self.db.refresh(original_ad)

                logger.info(
                    f"✅ Image regenerated successfully for ad {original_ad.id}"
                )

            except Exception as e:
                logger.error(f"💥 Failed to regenerate image: {str(e)}")
                logger.exception("Full traceback:")
                self.db.rollback()
                raise DifyAPIException(f"Unable to regenerate image: {str(e)}")

            return self._format_ad_response(original_ad)

        # Regenerate entire ad
        logger.info(f"🔄 Regenerating entire ad based on {original_ad.id}")

        ad_data = {
            "event_name": original_ad.event_name,
            "company_name": user.company.name,
            "product_categories": original_ad.product_categories,
            "headline": original_ad.headline,
            "description": original_ad.description,
            "slogan": original_ad.slogan,
        }

        try:
            dify_response = await self.dify_service.regenerate_ad(
                ad_data=ad_data,
                regenerate_image=False,
                additional_instructions=additional_instructions,
            )
            logger.info("✅ Ad content regenerated successfully")
        except Exception as e:
            logger.error(f"💥 Failed to regenerate ad content: {str(e)}")
            raise DifyAPIException(f"Unable to regenerate ad: {str(e)}")

        # Create new ad version
        ad = Ad(
            event_name=original_ad.event_name,
            product_name=original_ad.product_name,
            product_categories=original_ad.product_categories,
            location=original_ad.location,
            headline=dify_response.get("headline"),
            description=dify_response.get("description"),
            slogan=dify_response.get("slogan"),
            cta_text=dify_response.get("cta_text"),
            keywords=dify_response.get("keywords", []),
            hashtags=dify_response.get("hashtags", []),
            image_prompt=dify_response.get("image_prompt"),
            platforms=dify_response.get("platforms", []),
            platform_details=dify_response.get("platform_details", {}),
            recommended_posting_times=dify_response.get("posting_times", []),
            budget_allocation=dify_response.get("budget_allocation", {}),
            status=AdStatus.REGENERATED,
            ad_type=AdType.REGEN,
            parent_ad_id=original_ad.id,
            regeneration_count=original_ad.regeneration_count + 1,
            company_id=user.company_id,
            created_by_id=user.id,
            dify_response=dify_response,
        )

        self.db.add(ad)
        self.db.flush()

        # Generate new image
        if ad.image_prompt:
            try:
                logger.info(f"🖼️ Generating image for regenerated ad {ad.id}")

                image_context = {
                    "event_name": ad.event_name,
                    "product_categories": ad.product_categories,
                    "headline": ad.headline,
                    "description": ad.description,
                }

                image_url = await self.dify_service.generate_image(
                    image_prompt=ad.image_prompt, ad_context=image_context
                )

                if image_url:
                    result = await download_image_from_url(
                        url=image_url, ad_id=ad.id, original_filename=None
                    )

                    if result:
                        filename, public_url = result
                        ad.image_url = public_url
                        logger.info(f"✅ Image generated for regenerated ad {ad.id}")

            except Exception as e:
                logger.error(f"⚠️ Failed to generate image for regenerated ad: {str(e)}")
                # Continue without image - not critical

        self.db.commit()
        self.db.refresh(ad)

        logger.info(f"✅ Regenerated ad {ad.id} created successfully")
        return self._format_ad_response(ad)

    async def evaluate_ad(self, ad: Ad) -> EvaluationResponse:
        """Evaluate ad quality using Dify"""

        logger.info(f"Evaluating ad {ad.id}")

        ad_data = {
            "id": str(ad.id),
            "event_name": ad.event_name,
            "company_name": ad.company.name,
            "product_categories": ad.product_categories,
            "headline": ad.headline,
            "description": ad.description,
            "slogan": ad.slogan,
            "cta_text": ad.cta_text,
            "keywords": ad.keywords,
            "hashtags": ad.hashtags,
        }

        try:
            evaluation_result = await self.dify_service.evaluate_ad(ad_data)
            logger.info(f"Ad {ad.id} evaluated successfully")
        except Exception as e:
            logger.error(f"Failed to evaluate ad {ad.id}: {str(e)}")
            raise DifyAPIException(f"Unable to evaluate ad: {str(e)}")

        # Create evaluation record
        evaluation = AdEvaluation(
            ad_id=ad.id,
            relevance_score=evaluation_result.get("relevance_score", 0),
            clarity_score=evaluation_result.get("clarity_score", 0),
            persuasiveness_score=evaluation_result.get("persuasiveness_score", 0),
            brand_safety_score=evaluation_result.get("brand_safety_score", 0),
            overall_score=evaluation_result.get("overall_score", 0),
            feedback=evaluation_result.get("feedback", ""),
            recommendations=evaluation_result.get("recommendations", []),
            evaluator_model="dify",
            evaluation_prompt=str(ad_data),
        )

        self.db.add(evaluation)

        # Update ad with evaluation results
        ad.evaluation_score = evaluation.overall_score
        ad.evaluation_details = evaluation_result
        ad.evaluated_at = datetime.utcnow()
        ad.status = AdStatus.EVALUATED

        self.db.commit()
        self.db.refresh(evaluation)

        logger.info(
            f"Evaluation saved for ad {ad.id} with score {evaluation.overall_score}"
        )

        return EvaluationResponse(
            ad_id=ad.id,
            relevance_score=evaluation.relevance_score,
            clarity_score=evaluation.clarity_score,
            persuasiveness_score=evaluation.persuasiveness_score,
            brand_safety_score=evaluation.brand_safety_score,
            overall_score=evaluation.overall_score,
            feedback=evaluation.feedback,
            recommendations=evaluation.recommendations,
            evaluated_at=evaluation.created_at,
        )

    def get_ad(self, ad_id: UUID) -> Optional[Ad]:
        """Get ad by ID with company relationship loaded"""
        return (
            self.db.query(Ad)
            .options(joinedload(Ad.company))
            .filter(Ad.id == ad_id)
            .first()
        )

    def list_company_ads(
        self,
        company_id: UUID,
        page: int = 1,
        per_page: int = 20,
        status: Optional[AdStatus] = None,
    ) -> Dict[str, Any]:
        """List company ads with pagination"""

        query = (
            self.db.query(Ad)
            .options(joinedload(Ad.company))
            .filter(Ad.company_id == company_id)
        )

        if status:
            query = query.filter(Ad.status == status)

        total = query.count()
        ads = (
            query.order_by(Ad.created_at.desc())
            .offset((page - 1) * per_page)
            .limit(per_page)
            .all()
        )

        return {
            "total": total,
            "page": page,
            "per_page": per_page,
            "ads": [self._format_ad_response(ad) for ad in ads],
        }

    def check_generation_limit(self, company_id: UUID) -> bool:
        """Check if company can generate more ads"""
        company = self.db.query(Company).filter(Company.id == company_id).first()
        if not company:
            return False
        return company.ads_generated_this_month < company.monthly_ad_limit

    def get_company_ad_count(self, company_id: UUID) -> int:
        """Get total ad count for company"""
        return self.db.query(Ad).filter(Ad.company_id == company_id).count()

    def get_company_monthly_count(self, company_id: UUID) -> int:
        """Get monthly ad count for company"""
        start_of_month = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0)
        return (
            self.db.query(Ad)
            .filter(and_(Ad.company_id == company_id, Ad.created_at >= start_of_month))
            .count()
        )

    def get_recent_ads(self, company_id: UUID, limit: int = 5) -> List[Dict[str, Any]]:
        """Get recent ads for company"""
        ads = (
            self.db.query(Ad)
            .filter(Ad.company_id == company_id)
            .order_by(Ad.created_at.desc())
            .limit(limit)
            .all()
        )

        return [
            {
                "id": str(ad.id),
                "event_name": ad.event_name,
                "headline": ad.headline,
                "status": ad.status.value,
                "created_at": ad.created_at.isoformat(),
            }
            for ad in ads
        ]

    def get_average_evaluation_score(self, company_id: UUID) -> Optional[float]:
        """Get average evaluation score for company ads"""
        result = (
            self.db.query(func.avg(Ad.evaluation_score))
            .filter(and_(Ad.company_id == company_id, Ad.evaluation_score.isnot(None)))
            .scalar()
        )

        return round(result, 2) if result else None

    def get_company_usage(
        self, company_id: UUID, start_date: datetime, end_date: datetime
    ) -> Dict[str, Any]:
        """Get detailed company usage statistics"""

        total_generated = (
            self.db.query(Ad)
            .filter(
                and_(
                    Ad.company_id == company_id,
                    Ad.created_at >= start_date,
                    Ad.created_at <= end_date,
                    Ad.ad_type == AdType.PRODUCT_GEN,
                )
            )
            .count()
        )

        total_regenerated = (
            self.db.query(Ad)
            .filter(
                and_(
                    Ad.company_id == company_id,
                    Ad.created_at >= start_date,
                    Ad.created_at <= end_date,
                    Ad.ad_type == AdType.REGEN,
                )
            )
            .count()
        )

        total_evaluated = (
            self.db.query(Ad)
            .filter(
                and_(
                    Ad.company_id == company_id,
                    Ad.evaluated_at >= start_date,
                    Ad.evaluated_at <= end_date,
                )
            )
            .count()
        )

        # Daily breakdown
        daily_breakdown = []
        current_date = start_date.date()
        while current_date <= end_date.date():
            day_start = datetime.combine(current_date, datetime.min.time())
            day_end = datetime.combine(current_date, datetime.max.time())

            day_count = (
                self.db.query(Ad)
                .filter(
                    and_(
                        Ad.company_id == company_id,
                        Ad.created_at >= day_start,
                        Ad.created_at <= day_end,
                    )
                )
                .count()
            )

            daily_breakdown.append(
                {"date": current_date.isoformat(), "count": day_count}
            )

            current_date += timedelta(days=1)

        # Platform distribution
        platform_distribution = {}
        ads = (
            self.db.query(Ad)
            .filter(
                and_(
                    Ad.company_id == company_id,
                    Ad.created_at >= start_date,
                    Ad.created_at <= end_date,
                )
            )
            .all()
        )

        for ad in ads:
            if ad.platforms:
                for platform in ad.platforms:
                    platform_distribution[platform] = (
                        platform_distribution.get(platform, 0) + 1
                    )

        return {
            "total_generated": total_generated,
            "total_regenerated": total_regenerated,
            "total_evaluated": total_evaluated,
            "daily_breakdown": daily_breakdown,
            "platform_distribution": platform_distribution,
        }

    def get_company_ad_statistics(self, company_id: UUID) -> Dict[str, Any]:
        """Get comprehensive ad statistics for company"""

        total = self.db.query(Ad).filter(Ad.company_id == company_id).count()

        # By status
        by_status = {}
        for status in AdStatus:
            count = (
                self.db.query(Ad)
                .filter(and_(Ad.company_id == company_id, Ad.status == status))
                .count()
            )
            by_status[status.value] = count

        # By event
        by_event = (
            self.db.query(Ad.event_name, func.count(Ad.id).label("count"))
            .filter(Ad.company_id == company_id)
            .group_by(Ad.event_name)
            .order_by(func.count(Ad.id).desc())
            .limit(10)
            .all()
        )

        by_event_dict = {event: count for event, count in by_event}

        # Regeneration stats
        total_regenerations = (
            self.db.query(Ad)
            .filter(and_(Ad.company_id == company_id, Ad.ad_type == AdType.REGEN))
            .count()
        )

        avg_regenerations = (
            self.db.query(func.avg(Ad.regeneration_count))
            .filter(Ad.company_id == company_id)
            .scalar()
            or 0
        )

        # Evaluation stats
        total_evaluated = (
            self.db.query(Ad)
            .filter(and_(Ad.company_id == company_id, Ad.evaluation_score.isnot(None)))
            .count()
        )

        avg_score = self.get_average_evaluation_score(company_id)

        # Score distribution
        score_distribution = {"0-2": 0, "2-4": 0, "4-6": 0, "6-8": 0, "8-10": 0}

        evaluated_ads = (
            self.db.query(Ad)
            .filter(and_(Ad.company_id == company_id, Ad.evaluation_score.isnot(None)))
            .all()
        )

        for ad in evaluated_ads:
            score = ad.evaluation_score
            if score <= 2:
                score_distribution["0-2"] += 1
            elif score <= 4:
                score_distribution["2-4"] += 1
            elif score <= 6:
                score_distribution["4-6"] += 1
            elif score <= 8:
                score_distribution["6-8"] += 1
            else:
                score_distribution["8-10"] += 1

        return {
            "total": total,
            "by_status": by_status,
            "by_event": by_event_dict,
            "total_regenerations": total_regenerations,
            "avg_regenerations": round(avg_regenerations, 2),
            "total_evaluated": total_evaluated,
            "avg_score": avg_score,
            "score_distribution": score_distribution,
        }

    def delete_ad(self, ad_id: UUID) -> None:
        """Delete ad and associated images"""
        ad = self.get_ad(ad_id)
        if ad:
            # Delete the ad from database
            self.db.delete(ad)
            self.db.commit()
            logger.info(f"Ad {ad_id} deleted from database")

            # Delete associated images asynchronously
            import asyncio

            try:
                asyncio.create_task(delete_ad_images(ad_id))
            except RuntimeError:
                # If no event loop, run synchronously
                asyncio.run(delete_ad_images(ad_id))

            logger.info(f"Ad {ad_id} and images deleted successfully")

    def _format_ad_response(self, ad: Ad) -> AdResponse:
        """Format ad for response with proper field mapping"""

        # Ensure company is loaded
        if not ad.company:
            company = self.db.query(Company).filter(Company.id == ad.company_id).first()
            company_name = company.name if company else "Unknown Company"
        else:
            company_name = ad.company.name

        return AdResponse(
            id=ad.id,
            event_name=ad.event_name,
            product_name=ad.product_name,
            product_categories=ad.product_categories or [],
            location=ad.location,
            company_id=ad.company_id,
            company_name=company_name,
            content={
                "headline": ad.headline or "",
                "description": ad.description or "",
                "slogan": ad.slogan or "",
                "cta_text": ad.cta_text or "",
                "keywords": ad.keywords or [],
                "hashtags": ad.hashtags or [],
                "image_prompt": ad.image_prompt or "",
                "image_base64": None,  # No longer using base64
                "image_url": ad.image_url,  # Use the public URL instead
            },
            platforms=ad.platforms or [],
            platform_details=ad.platform_details or {},
            status=ad.status,
            ad_type=ad.ad_type,
            evaluation_score=ad.evaluation_score,
            evaluation_details=ad.evaluation_details,
            regeneration_count=ad.regeneration_count or 0,
            parent_ad_id=ad.parent_ad_id,
            created_at=ad.created_at,
            updated_at=ad.updated_at,
            evaluated_at=ad.evaluated_at,
        )
