from pydantic import BaseModel, Field, field_validator, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID
from app.models.enums import AdStatus, AdType, Platform


class AdGenerationRequest(BaseModel):
    event_name: str = Field(..., min_length=1, max_length=255)
    product_name: Optional[str] = Field(None, max_length=255)
    product_categories: List[str] = Field(..., min_items=1, max_items=10)
    location: Optional[str] = Field(None, max_length=255)
    company_name: Optional[str] = Field(None, max_length=255)

    @field_validator('product_categories')
    @classmethod
    def validate_categories(cls, v: List[str]) -> List[str]:
        if len(v) > 10:
            raise ValueError("Maximum 10 product categories allowed")
        return list(dict.fromkeys(v))  # dedupe and preserve order


class AdRegenerationRequest(BaseModel):
    ad_id: UUID
    regenerate_image: bool = False
    additional_instructions: Optional[str] = Field(None, max_length=1000)


class AdEvaluationRequest(BaseModel):
    ad_id: UUID


class AdContent(BaseModel):
    headline: str
    description: str
    slogan: str
    cta_text: str
    keywords: List[str]
    hashtags: List[str]
    image_prompt: str
    image_base64: Optional[str] = None
    image_url: Optional[str] = None


class PlatformRecommendation(BaseModel):
    platform: Platform
    priority: int = Field(..., ge=1, le=5)
    recommended_budget_percentage: float
    best_posting_times: List[str]
    estimated_reach: Optional[int] = None
    estimated_ctr: Optional[float] = None
    notes: Optional[str] = None


class AdResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    event_name: str
    product_name: Optional[str]
    product_categories: List[str]
    location: Optional[str]
    company_id: UUID
    company_name: str

    content: AdContent
    platforms: List[Platform] | List[str]  # tolerate str list from DB
    platform_details: Dict[str, Any]

    status: AdStatus
    ad_type: AdType

    evaluation_score: Optional[float]
    evaluation_details: Optional[Dict[str, Any]]

    regeneration_count: int
    parent_ad_id: Optional[UUID]

    created_at: datetime
    updated_at: datetime
    evaluated_at: Optional[datetime]


class AdListResponse(BaseModel):
    total: int
    page: int
    per_page: int
    ads: List[AdResponse]


class EvaluationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    ad_id: UUID
    relevance_score: float
    clarity_score: float
    persuasiveness_score: float
    brand_safety_score: float
    overall_score: float
    feedback: str
    recommendations: List[str]
    evaluated_at: datetime
