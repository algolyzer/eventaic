from datetime import datetime, timedelta
import logging
from typing import Any, Dict, Optional
from uuid import UUID

from sqlalchemy import and_, func, or_
from sqlalchemy.orm import Session

from app.models.ad import Ad
from app.models.company import Company
from app.models.user import User
from app.repositories.ad_repository import AdRepository
from app.repositories.company_repository import CompanyRepository
from app.repositories.user_repository import UserRepository


logger = logging.getLogger(__name__)


class AdminService:
    def __init__(self, db: Session):
        self.db = db
        self.company_repository = CompanyRepository(db)
        self.user_repository = UserRepository(db)
        self.ad_repository = AdRepository(db)

    def get_dashboard_data(self) -> Dict[str, Any]:
        """Get admin dashboard overview data"""

        # Company stats
        total_companies = self.db.query(Company).count()
        active_companies = (
            self.db.query(Company).filter(Company.is_active.is_(True)).count()
        )

        # User stats
        total_users = self.db.query(User).filter(User.is_deleted.is_(False)).count()

        # Ad stats
        total_ads = self.db.query(Ad).count()

        # Today's stats
        today_start = datetime.utcnow().replace(hour=0, minute=0, second=0)
        ads_today = self.db.query(Ad).filter(Ad.created_at >= today_start).count()

        # This month's stats
        month_start = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0)
        ads_this_month = self.db.query(Ad).filter(Ad.created_at >= month_start).count()

        # Regeneration stats
        total_regenerations = (
            self.db.query(Ad).filter(Ad.parent_ad_id.isnot(None)).count()
        )

        # Average evaluation score
        avg_score = (
            self.db.query(func.avg(Ad.evaluation_score))
            .filter(Ad.evaluation_score.isnot(None))
            .scalar()
            or 0
        )

        # Recent activities (last 10 ads)
        recent_ads = self.db.query(Ad).order_by(Ad.created_at.desc()).limit(10).all()
        recent_activities = [
            {
                "id": str(ad.id),
                "type": "ad_created",
                "company": ad.company.name,
                "event": ad.event_name,
                "created_at": ad.created_at.isoformat(),
            }
            for ad in recent_ads
        ]

        # Top companies by ads generated
        top_companies = (
            self.db.query(Company.name, Company.id, func.count(Ad.id).label("ad_count"))
            .join(Ad)
            .group_by(Company.id, Company.name)
            .order_by(func.count(Ad.id).desc())
            .limit(5)
            .all()
        )

        top_companies_list = [
            {"id": str(company_id), "name": name, "ads_generated": ad_count}
            for name, company_id, ad_count in top_companies
        ]

        return {
            "total_companies": total_companies,
            "active_companies": active_companies,
            "total_users": total_users,
            "total_ads_generated": total_ads,
            "ads_generated_today": ads_today,
            "ads_generated_this_month": ads_this_month,
            "total_regenerations": total_regenerations,
            "average_evaluation_score": round(avg_score, 2),
            "recent_activities": recent_activities,
            "top_companies": top_companies_list,
        }

    def get_companies(
        self,
        page: int = 1,
        per_page: int = 20,
        search: Optional[str] = None,
        is_active: Optional[bool] = None,
    ) -> Dict[str, Any]:
        """Get paginated list of companies"""

        query = self.db.query(Company)

        if search:
            query = query.filter(
                or_(
                    Company.name.ilike(f"%{search}%"),
                    Company.email.ilike(f"%{search}%"),
                )
            )

        if is_active is not None:
            query = query.filter(Company.is_active == is_active)

        total = query.count()

        companies = (
            query.order_by(Company.created_at.desc())
            .offset((page - 1) * per_page)
            .limit(per_page)
            .all()
        )

        companies_list = []
        for company in companies:
            ad_count = self.db.query(Ad).filter(Ad.company_id == company.id).count()
            user_count = (
                self.db.query(User).filter(User.company_id == company.id).count()
            )

            companies_list.append(
                {
                    "id": str(company.id),
                    "name": company.name,
                    "email": company.email,
                    "is_active": company.is_active,
                    "is_verified": company.is_verified,
                    "total_ads": ad_count,
                    "total_users": user_count,
                    "ads_this_month": company.ads_generated_this_month,
                    "monthly_limit": company.monthly_ad_limit,
                    "created_at": company.created_at.isoformat(),
                }
            )

        return {
            "total": total,
            "page": page,
            "per_page": per_page,
            "companies": companies_list,
        }

    def get_company_detail(self, company_id: UUID) -> Optional[Dict[str, Any]]:
        """Get detailed company information"""

        company = self.company_repository.get(company_id)
        if not company:
            return None

        # Get users
        users = self.db.query(User).filter(User.company_id == company_id).all()
        users_list = [
            {
                "id": str(user.id),
                "email": user.email,
                "username": user.username,
                "full_name": user.full_name,
                "is_active": user.is_active,
                "created_at": user.created_at.isoformat(),
            }
            for user in users
        ]

        # Get recent ads
        recent_ads = (
            self.db.query(Ad)
            .filter(Ad.company_id == company_id)
            .order_by(Ad.created_at.desc())
            .limit(10)
            .all()
        )

        recent_ads_list = [
            {
                "id": str(ad.id),
                "event_name": ad.event_name,
                "headline": ad.headline,
                "status": ad.status.value,
                "created_at": ad.created_at.isoformat(),
            }
            for ad in recent_ads
        ]

        return {
            "id": company.id,
            "name": company.name,
            "email": company.email,
            "phone": company.phone,
            "website": company.website,
            "address": company.address,
            "city": company.city,
            "country": company.country,
            "industry": company.industry,
            "size": company.size,
            "description": company.description,
            "monthly_ad_limit": company.monthly_ad_limit,
            "ads_generated_this_month": company.ads_generated_this_month,
            "total_ads_generated": company.total_ads_generated,
            "is_active": company.is_active,
            "is_verified": company.is_verified,
            "created_at": company.created_at,
            "updated_at": company.updated_at,
            "users": users_list,
            "recent_ads": recent_ads_list,
        }

    def get_statistics(
        self,
        start_date: datetime,
        end_date: datetime,
        company_id: Optional[UUID] = None,
    ) -> Dict[str, Any]:
        """Get platform statistics for a date range"""

        # Base queries
        ad_query = self.db.query(Ad).filter(
            and_(Ad.created_at >= start_date, Ad.created_at <= end_date)
        )

        if company_id:
            ad_query = ad_query.filter(Ad.company_id == company_id)

        # Total stats
        total_ads = ad_query.count()
        total_regenerations = ad_query.filter(Ad.parent_ad_id.isnot(None)).count()
        total_evaluations = ad_query.filter(Ad.evaluation_score.isnot(None)).count()

        # Unique companies
        unique_companies = len(set([ad.company_id for ad in ad_query.all()]))

        # Active users
        active_users = len(set([ad.created_by_id for ad in ad_query.all()]))

        # Daily stats
        daily_stats = []
        current_date = start_date.date()
        while current_date <= end_date.date():
            day_start = datetime.combine(current_date, datetime.min.time())
            day_end = datetime.combine(current_date, datetime.max.time())

            day_query = ad_query.filter(
                and_(Ad.created_at >= day_start, Ad.created_at <= day_end)
            )

            daily_stats.append(
                {
                    "date": current_date.isoformat(),
                    "ads_created": day_query.count(),
                    "evaluations": day_query.filter(
                        Ad.evaluation_score.isnot(None)
                    ).count(),
                }
            )

            current_date += timedelta(days=1)

        # Platform distribution
        platform_distribution = {}
        for ad in ad_query.all():
            if ad.platforms:
                for platform in ad.platforms:
                    platform_distribution[platform] = (
                        platform_distribution.get(platform, 0) + 1
                    )

        # Event distribution (top 10)
        event_distribution = {}
        event_counts = (
            self.db.query(Ad.event_name, func.count(Ad.id).label("count"))
            .filter(and_(Ad.created_at >= start_date, Ad.created_at <= end_date))
            .group_by(Ad.event_name)
            .order_by(func.count(Ad.id).desc())
            .limit(10)
            .all()
        )

        for event, count in event_counts:
            event_distribution[event] = count

        # Top performing ads
        top_ads = (
            ad_query.filter(Ad.evaluation_score.isnot(None))
            .order_by(Ad.evaluation_score.desc())
            .limit(10)
            .all()
        )

        top_performing_ads = [
            {
                "id": str(ad.id),
                "headline": ad.headline,
                "event": ad.event_name,
                "company": ad.company.name,
                "score": ad.evaluation_score,
            }
            for ad in top_ads
        ]

        # Company rankings
        company_rankings = (
            self.db.query(
                Company.name,
                func.count(Ad.id).label("ad_count"),
                func.avg(Ad.evaluation_score).label("avg_score"),
            )
            .join(Ad)
            .filter(and_(Ad.created_at >= start_date, Ad.created_at <= end_date))
            .group_by(Company.name)
            .order_by(func.count(Ad.id).desc())
            .limit(10)
            .all()
        )

        company_rankings_list = [
            {
                "name": name,
                "ads_generated": ad_count,
                "average_score": round(avg_score, 2) if avg_score else 0,
            }
            for name, ad_count, avg_score in company_rankings
        ]

        return {
            "period_start": start_date,
            "period_end": end_date,
            "total_ads": total_ads,
            "total_regenerations": total_regenerations,
            "total_evaluations": total_evaluations,
            "unique_companies": unique_companies,
            "active_users": active_users,
            "daily_stats": daily_stats,
            "platform_distribution": platform_distribution,
            "event_distribution": event_distribution,
            "top_performing_ads": top_performing_ads,
            "company_rankings": company_rankings_list,
        }

    def update_company_status(self, company_id: UUID, is_active: bool) -> bool:
        """Update company active status"""

        company = self.company_repository.get(company_id)
        if not company:
            return False

        company.is_active = is_active
        company.updated_at = datetime.utcnow()
        self.db.commit()

        return True

    def update_company_limits(self, company_id: UUID, monthly_limit: int) -> bool:
        """Update company's monthly ad generation limit"""

        company = self.company_repository.get(company_id)
        if not company:
            return False

        company.monthly_ad_limit = monthly_limit
        company.updated_at = datetime.utcnow()
        self.db.commit()

        return True

    def get_all_users(
        self, page: int = 1, per_page: int = 20, search: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get all users with pagination"""

        query = self.db.query(User).filter(User.is_deleted.is_(False))

        if search:
            query = query.filter(
                or_(
                    User.email.ilike(f"%{search}%"),
                    User.username.ilike(f"%{search}%"),
                    User.full_name.ilike(f"%{search}%"),
                )
            )

        total = query.count()

        users = (
            query.order_by(User.created_at.desc())
            .offset((page - 1) * per_page)
            .limit(per_page)
            .all()
        )

        users_list = [
            {
                "id": str(user.id),
                "email": user.email,
                "username": user.username,
                "full_name": user.full_name,
                "role": user.role.value,
                "company": user.company.name if user.company else None,
                "is_active": user.is_active,
                "is_email_verified": user.is_email_verified,
                "created_at": user.created_at.isoformat(),
                "last_login": user.last_login.isoformat() if user.last_login else None,
            }
            for user in users
        ]

        return {"total": total, "page": page, "per_page": per_page, "users": users_list}
