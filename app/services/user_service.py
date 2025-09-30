from sqlalchemy.orm import Session
from typing import Optional, Dict, Any
from datetime import datetime
from uuid import UUID
from app.models.user import User
from app.models.ad import Ad
from app.schemas.user import UserProfileUpdate
from app.repositories.user_repository import UserRepository
import logging

logger = logging.getLogger(__name__)


class UserService:
    def __init__(self, db: Session):
        self.db = db
        self.user_repository = UserRepository(db)

    def get_by_email(self, email: str) -> Optional[User]:
        """Get user by email"""
        return self.user_repository.get_by_email(email)

    def get_by_username(self, username: str) -> Optional[User]:
        """Get user by username"""
        return self.user_repository.get_by_username(username)

    def update_user(self, user_id: UUID, update_data: UserProfileUpdate) -> User:
        """Update user profile"""

        user = self.user_repository.get(user_id)
        if not user:
            raise ValueError("User not found")

        # Update fields if provided
        update_dict = update_data.dict(exclude_unset=True)
        for field, value in update_dict.items():
            if value is not None:
                setattr(user, field, value)

        user.updated_at = datetime.utcnow()

        self.db.commit()
        self.db.refresh(user)

        return user

    def soft_delete_user(self, user_id: UUID) -> bool:
        """Soft delete user account"""

        user = self.user_repository.get(user_id)
        if not user:
            return False

        user.is_deleted = True
        user.is_active = False
        user.updated_at = datetime.utcnow()

        self.db.commit()

        return True

    def get_user_activity(self, user_id: UUID) -> Dict[str, Any]:
        """Get user activity statistics"""

        # Get total ads created by user
        total_ads = self.db.query(Ad).filter(Ad.created_by_id == user_id).count()

        # Get last ad creation date
        last_ad = (
            self.db.query(Ad)
            .filter(Ad.created_by_id == user_id)
            .order_by(Ad.created_at.desc())
            .first()
        )

        last_ad_date = last_ad.created_at if last_ad else None

        # Get total evaluations
        total_evaluations = (
            self.db.query(Ad)
            .filter(Ad.created_by_id == user_id, Ad.evaluation_score.isnot(None))
            .count()
        )

        return {
            "total_ads": total_ads,
            "last_ad_date": last_ad_date,
            "total_evaluations": total_evaluations,
        }
