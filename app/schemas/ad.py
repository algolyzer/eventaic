from pydantic import BaseModel, Field, field_validator, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID
from app.models.enums import AdStatus, AdType, Platform


class AdGenerationRequest(BaseModel):
    """Request model for ad generation"""

    event_name: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Name of the event triggering the ad",
    )
    product_name: Optional[str] = Field(
        None, max_length=255, description="Specific product name"
    )
    product_categories: List[str] = Field(
        ..., min_items=1, max_items=10, description="Product categories (1-10 items)"
    )
    location: Optional[str] = Field(None, max_length=255, description="Target location")
    company_name: Optional[str] = Field(
        None, max_length=255, description="Company name override"
    )

    @field_validator("product_categories")
    @classmethod
    def validate_categories(cls, v: List[str]) -> List[str]:
        """Validate and deduplicate product categories"""
        if len(v) > 10:
            raise ValueError("Maximum 10 product categories allowed")
        return list(dict.fromkeys(v))  # Remove duplicates while preserving order


class AdRegenerationRequest(BaseModel):
    """Request model for ad regeneration"""

    ad_id: UUID = Field(..., description="ID of the ad to regenerate")
    regenerate_image: bool = Field(
        default=False,
        description="If True, only regenerate image; if False, regenerate entire ad",
    )
    additional_instructions: Optional[str] = Field(
        None, max_length=1000, description="Additional instructions for regeneration"
    )


class AdEvaluationRequest(BaseModel):
    """Request model for ad evaluation"""

    ad_id: UUID = Field(..., description="ID of the ad to evaluate")


class AdContent(BaseModel):
    """Ad content structure"""

    headline: str = Field(..., description="Ad headline")
    description: str = Field(..., description="Ad description")
    slogan: str = Field(..., description="Ad slogan")
    cta_text: str = Field(..., description="Call-to-action text")
    keywords: List[str] = Field(default_factory=list, description="SEO keywords")
    hashtags: List[str] = Field(
        default_factory=list, description="Social media hashtags"
    )
    image_prompt: str = Field(
        default="", description="Prompt used for image generation"
    )
    image_base64: Optional[str] = Field(None, description="Base64 encoded image data")
    image_url: Optional[str] = Field(None, description="URL to hosted image")


class PlatformRecommendation(BaseModel):
    """Platform recommendation details"""

    platform: Platform = Field(..., description="Platform name")
    priority: int = Field(..., ge=1, le=5, description="Priority ranking (1=highest)")
    recommended_budget_percentage: float = Field(
        ..., ge=0, le=100, description="Recommended budget allocation"
    )
    best_posting_times: List[str] = Field(
        default_factory=list, description="Optimal posting times"
    )
    estimated_reach: Optional[int] = Field(None, description="Estimated audience reach")
    estimated_ctr: Optional[float] = Field(
        None, description="Estimated click-through rate"
    )
    notes: Optional[str] = Field(None, description="Additional platform notes")


class AdResponse(BaseModel):
    """Response model for ad data"""

    model_config = ConfigDict(from_attributes=True)

    # Basic info
    id: UUID
    event_name: str
    product_name: Optional[str] = None
    product_categories: List[str]
    location: Optional[str] = None

    # Company info
    company_id: UUID
    company_name: str

    # Ad content
    content: AdContent

    # Platform recommendations
    platforms: List[Platform] | List[str]  # Support both enum and string
    platform_details: Dict[str, Any]

    # Status
    status: AdStatus
    ad_type: AdType

    # Evaluation
    evaluation_score: Optional[float] = None
    evaluation_details: Optional[Dict[str, Any]] = None

    # Regeneration tracking
    regeneration_count: int = 0
    parent_ad_id: Optional[UUID] = None

    # Timestamps
    created_at: datetime
    updated_at: datetime
    evaluated_at: Optional[datetime] = None


class AdListResponse(BaseModel):
    """Response model for list of ads"""

    total: int = Field(..., description="Total number of ads")
    page: int = Field(..., ge=1, description="Current page number")
    per_page: int = Field(..., ge=1, le=100, description="Items per page")
    ads: List[AdResponse] = Field(default_factory=list, description="List of ads")


class EvaluationScore(BaseModel):
    """Individual evaluation score"""

    score: float = Field(..., ge=0, le=10, description="Score value (0-10)")
    feedback: Optional[str] = Field(
        None, description="Specific feedback for this metric"
    )


class EvaluationResponse(BaseModel):
    """Response model for ad evaluation"""

    model_config = ConfigDict(from_attributes=True)

    ad_id: UUID

    # Individual scores
    relevance_score: float = Field(..., ge=0, le=10)
    clarity_score: float = Field(..., ge=0, le=10)
    persuasiveness_score: float = Field(..., ge=0, le=10)
    brand_safety_score: float = Field(..., ge=0, le=10)
    overall_score: float = Field(..., ge=0, le=10)

    # Detailed feedback
    feedback: str
    recommendations: List[str] = Field(default_factory=list)

    # Metadata
    evaluated_at: datetime


class ImageGenerationRequest(BaseModel):
    """Request model for image generation/regeneration"""

    ad_id: UUID = Field(..., description="ID of the ad")
    force_regenerate: bool = Field(
        default=False, description="Force regeneration even if image exists"
    )


class ImageGenerationResponse(BaseModel):
    """Response model for image generation"""

    ad_id: UUID
    image_url: str = Field(..., description="Public URL to access the image")
    image_prompt: str = Field(..., description="Prompt used for generation")
    generated_at: datetime
