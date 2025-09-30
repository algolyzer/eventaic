from pydantic import BaseModel, EmailStr, Field, field_validator, ConfigDict
from typing import Optional, List
from datetime import datetime
from uuid import UUID
from app.models.enums import UserRole


class UserBase(BaseModel):
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=50)
    full_name: Optional[str] = Field(None, max_length=255)
    phone: Optional[str] = Field(None, max_length=20)


class UserCreate(UserBase):
    password: str = Field(..., min_length=8)
    company_id: Optional[UUID] = None
    company_name: Optional[str] = None
    role: UserRole = UserRole.COMPANY


class UserProfileUpdate(BaseModel):
    email: Optional[EmailStr] = None
    username: Optional[str] = Field(None, min_length=3, max_length=50)
    full_name: Optional[str] = Field(None, max_length=255)
    phone: Optional[str] = Field(None, max_length=20)

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v: Optional[str]) -> Optional[str]:
        if v and not v.replace("+", "").replace("-", "").replace(" ", "").isdigit():
            raise ValueError("Invalid phone number format")
        return v


class UserProfileResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    email: str
    username: str
    full_name: Optional[str]
    phone: Optional[str]
    role: UserRole
    is_email_verified: bool
    company_id: Optional[UUID]
    company_name: Optional[str]
    created_at: datetime
    last_login: Optional[datetime]


class UserListResponse(BaseModel):
    total: int
    page: int
    per_page: int
    users: List[UserProfileResponse]


class UserActivityResponse(BaseModel):
    user_id: UUID
    total_ads_created: int
    last_ad_created: Optional[datetime]
    total_evaluations: int
    account_created: datetime
    last_login: Optional[datetime]
