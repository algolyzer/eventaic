from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class CompanyBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    email: Optional[str] = Field(None, max_length=255)
    phone: Optional[str] = Field(None, max_length=20)
    website: Optional[str] = Field(None, max_length=255)
    address: Optional[str] = None
    city: Optional[str] = Field(None, max_length=100)
    country: Optional[str] = Field(None, max_length=100)
    industry: Optional[str] = Field(None, max_length=100)
    size: Optional[str] = Field(None, max_length=50)
    description: Optional[str] = None


class CompanyCreate(CompanyBase):
    pass


class CompanyProfileUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    email: Optional[str] = Field(None, max_length=255)
    phone: Optional[str] = Field(None, max_length=20)
    website: Optional[str] = Field(None, max_length=255)
    address: Optional[str] = None
    city: Optional[str] = Field(None, max_length=100)
    country: Optional[str] = Field(None, max_length=100)
    industry: Optional[str] = Field(None, max_length=100)
    size: Optional[str] = Field(None, max_length=50)
    description: Optional[str] = None


class CompanyProfileResponse(CompanyBase):
    # ✅ Pydantic v2 replacement for orm_mode
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    is_verified: bool
    created_at: datetime


class CompanyDashboardResponse(BaseModel):
    company_id: UUID
    company_name: str
    total_ads_generated: int
    ads_generated_this_month: int
    monthly_limit: int
    average_evaluation_score: Optional[float]
    recent_ads: List[Dict[str, Any]]


class CompanyUsageResponse(BaseModel):
    company_id: UUID
    period_start: datetime
    period_end: datetime
    total_generated: int
    total_regenerated: int
    total_evaluated: int
    daily_breakdown: List[Dict[str, Any]]
    platform_distribution: Dict[str, int]
    remaining_monthly_limit: int


class CompanyStatistics(BaseModel):
    company_id: UUID
    company_name: str
    total_ads: int
    ads_this_month: int
    total_regenerations: int
    average_evaluation_score: Optional[float]
    is_active: bool
