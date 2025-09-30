from sqlalchemy import Column, String, Boolean, DateTime, Enum, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.core.database import Base
from app.models.enums import UserRole
from datetime import datetime
import uuid


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, index=True, nullable=False)
    username = Column(String(100), unique=True, index=True, nullable=False)
    full_name = Column(String(255))
    phone = Column(String(20))
    hashed_password = Column(Text, nullable=False)
    role = Column(Enum(UserRole), default=UserRole.COMPANY, nullable=False)

    # Email verification
    is_email_verified = Column(Boolean, default=False)
    email_verification_token = Column(Text)
    email_verification_sent_at = Column(DateTime)

    # Password reset
    password_reset_token = Column(Text)
    password_reset_sent_at = Column(DateTime)

    # Account status
    is_active = Column(Boolean, default=True)
    is_deleted = Column(Boolean, default=False)

    # Company relationship
    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id"))
    company = relationship("Company", back_populates="users")

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login = Column(DateTime)

    # Relationships
    ads = relationship(
        "Ad", back_populates="created_by_user", cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<User {self.email}>"
