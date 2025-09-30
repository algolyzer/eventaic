from datetime import datetime
import uuid

from sqlalchemy import Boolean, Column, DateTime, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import Base


class Company(Base):
    __tablename__ = "companies"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False, index=True)
    email = Column(String(255))
    phone = Column(String(20))
    website = Column(String(255))
    address = Column(Text)
    city = Column(String(100))
    country = Column(String(100))

    # Company details
    industry = Column(String(100))
    size = Column(String(50))  # e.g., "1-10", "11-50", "51-200", etc.
    description = Column(Text)

    # Subscription/limits
    monthly_ad_limit = Column(Integer, default=100)
    ads_generated_this_month = Column(Integer, default=0)
    total_ads_generated = Column(Integer, default=0)

    # Status
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    users = relationship("User", back_populates="company")
    ads = relationship("Ad", back_populates="company", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Company {self.name}>"
