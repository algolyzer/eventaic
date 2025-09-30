from datetime import datetime
import uuid

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import ARRAY, UUID
from sqlalchemy.orm import relationship

from app.core.database import Base
from app.models.enums import AdStatus, AdType, Platform


class Ad(Base):
    __tablename__ = "ads"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Ad basic info
    event_name = Column(String(255), nullable=False)
    product_name = Column(String(255))
    product_categories = Column(ARRAY(String), nullable=False)
    location = Column(String(255))

    # Generated content
    headline = Column(String(500))
    description = Column(Text)
    slogan = Column(String(500))
    cta_text = Column(String(100))
    keywords = Column(ARRAY(String))
    hashtags = Column(ARRAY(String))

    # Image
    image_prompt = Column(Text)
    image_base64 = Column(Text)
    image_url = Column(String(500))

    # Platform recommendations
    platforms = Column(ARRAY(String))
    platform_details = Column(JSON)
    recommended_posting_times = Column(ARRAY(String))
    budget_allocation = Column(JSON)

    # Evaluation metrics
    evaluation_score = Column(Float)
    evaluation_details = Column(JSON)
    evaluated_at = Column(DateTime)

    # Status and type
    status = Column(Enum(AdStatus), default=AdStatus.DRAFT, nullable=False)
    ad_type = Column(Enum(AdType), nullable=False)

    # Regeneration tracking
    parent_ad_id = Column(UUID(as_uuid=True), ForeignKey("ads.id"))
    regeneration_count = Column(Integer, default=0)

    # Relationships
    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False)
    company = relationship("Company", back_populates="ads")

    created_by_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    created_by_user = relationship("User", back_populates="ads")

    # Self-referential relationship for regenerations
    parent_ad = relationship("Ad", remote_side=[id], backref="regenerations")

    # FIXED: Cascade delete evaluations when ad is deleted
    evaluations = relationship(
        "AdEvaluation", back_populates="ad", cascade="all, delete-orphan"
    )

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Dify response storage
    dify_response = Column(JSON)

    def __repr__(self):
        return f"<Ad {self.id} - {self.event_name}>"


class AdEvaluation(Base):
    __tablename__ = "ad_evaluations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    ad_id = Column(
        UUID(as_uuid=True), ForeignKey("ads.id", ondelete="CASCADE"), nullable=False
    )

    # Evaluation scores
    relevance_score = Column(Float)
    clarity_score = Column(Float)
    persuasiveness_score = Column(Float)
    brand_safety_score = Column(Float)
    overall_score = Column(Float)

    # Detailed feedback
    feedback = Column(Text)
    recommendations = Column(ARRAY(String))

    # Metadata
    evaluator_model = Column(String(50))
    evaluation_prompt = Column(Text)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships - FIXED: back_populates instead of backref
    ad = relationship("Ad", back_populates="evaluations")
