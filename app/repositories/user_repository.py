from typing import Optional
from uuid import UUID
from sqlalchemy.orm import Session
from app.repositories.base import BaseRepository
from app.models.user import User


class UserRepository(BaseRepository[User]):
    def __init__(self, db: Session):
        super().__init__(User, db)

    def get_by_email(self, email: str) -> Optional[User]:
        return self.db.query(User).filter(User.email == email).first()

    def get_by_username(self, username: str) -> Optional[User]:
        return self.db.query(User).filter(User.username == username).first()

    def soft_delete(self, user_id: UUID) -> bool:
        user = self.get(user_id)
        if not user:
            return False
        user.is_deleted = True
        user.is_active = False
        self.db.commit()
        return True
