from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class SuccessResponse(BaseModel):
    message: str
    data: Optional[Any] = None


class ErrorResponse(BaseModel):
    error: str
    detail: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class PaginatedResponse(BaseModel):
    total: int
    page: int
    per_page: int
    pages: int
    has_next: bool
    has_prev: bool
    data: List[Any]


class AdminDashboardResponse(BaseModel):
    total_companies: int
    active_companies: int
    total_users: int
    total_ads_generated: int
    ads_generated_today: int
    ads_generated_this_month: int
    total_regenerations: int
    average_evaluation_score: float
    recent_activities: List[Dict[str, Any]]
    top_companies: List[Dict[str, Any]]


class CompanyListResponse(BaseModel):
    total: int
    page: int
    per_page: int
    companies: List[Dict[str, Any]]


class CompanyDetailResponse(BaseModel):
    id: UUID
    name: str
    email: Optional[str]
    phone: Optional[str]
    website: Optional[str]
    address: Optional[str]
    city: Optional[str]
    country: Optional[str]
    industry: Optional[str]
    size: Optional[str]
    description: Optional[str]
    monthly_ad_limit: int
    ads_generated_this_month: int
    total_ads_generated: int
    is_active: bool
    is_verified: bool
    created_at: datetime
    updated_at: datetime
    users: List[Dict[str, Any]]
    recent_ads: List[Dict[str, Any]]


class AdminStatisticsResponse(BaseModel):
    period_start: datetime
    period_end: datetime
    total_ads: int
    total_regenerations: int
    total_evaluations: int
    unique_companies: int
    active_users: int
    daily_stats: List[Dict[str, Any]]
    platform_distribution: Dict[str, int]
    event_distribution: Dict[str, int]
    top_performing_ads: List[Dict[str, Any]]
    company_rankings: List[Dict[str, Any]]
