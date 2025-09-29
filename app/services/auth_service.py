from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import Optional
from uuid import UUID
from app.models.user import User
from app.models.company import Company
from app.models.enums import UserRole
from app.schemas.auth import RegisterRequest, TokenResponse
from app.core.security import Security
from app.core.config import settings
from app.repositories.user_repository import UserRepository
from app.repositories.company_repository import CompanyRepository
import logging

logger = logging.getLogger(__name__)


class AuthService:
    def __init__(self, db: Session):
        self.db = db
        self.user_repository = UserRepository(db)
        self.company_repository = CompanyRepository(db)
        self.security = Security()

    async def create_user(self, request: RegisterRequest) -> User:
        """Create new user with optional company"""

        # Hash password
        hashed_password = self.security.get_password_hash(request.password)

        # Create or get company if company name provided
        company = None
        if request.company_name:
            company = self.company_repository.get_by_name(request.company_name)
            if not company:
                company = Company(
                    name=request.company_name,
                    email=request.email
                )
                self.db.add(company)
                self.db.flush()

        # Create user
        user = User(
            email=request.email,
            username=request.username,
            full_name=request.full_name,
            phone=request.phone,
            hashed_password=hashed_password,
            role=UserRole.COMPANY if company else UserRole.SUPER_ADMIN,
            company_id=company.id if company else None,
            is_email_verified=not settings.EMAIL_VERIFICATION_REQUIRED
        )

        # Generate email verification token if required
        if settings.EMAIL_VERIFICATION_REQUIRED:
            verification_token = self.security.generate_token()
            user.email_verification_token = self.security.hash_token(verification_token)
            user.email_verification_sent_at = datetime.utcnow()

        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)

        return user

    def authenticate_user(self, username: str, password: str) -> Optional[User]:
        """Authenticate user by username"""

        # Find user by username
        user = self.user_repository.get_by_username(username)

        if not user:
            return None

        # Verify password
        if not self.security.verify_password(password, user.hashed_password):
            return None

        # Check if user is active
        if not user.is_active or user.is_deleted:
            return None

        return user

    def authenticate_user_by_email(self, email: str, password: str) -> Optional[User]:
        """Authenticate user by email"""

        # Find user by email
        user = self.user_repository.get_by_email(email)

        if not user:
            return None

        # Verify password
        if not self.security.verify_password(password, user.hashed_password):
            return None

        # Check if user is active
        if not user.is_active or user.is_deleted:
            return None

        return user

    def authenticate_user_flexible(self, identifier: str, password: str) -> Optional[User]:
        """
        Authenticate user by either username or email
        Tries email first if @ is present, otherwise username
        """

        # Determine if identifier looks like an email
        if '@' in identifier:
            # Try email first, then username as fallback
            user = self.authenticate_user_by_email(identifier, password)
            if not user:
                user = self.authenticate_user(identifier, password)
        else:
            # Try username first, then email as fallback
            user = self.authenticate_user(identifier, password)
            if not user:
                user = self.authenticate_user_by_email(identifier, password)

        return user

    def create_tokens(self, user: User) -> TokenResponse:
        """Create access and refresh tokens"""

        access_token = self.security.create_access_token(subject=str(user.id))
        refresh_token = self.security.create_refresh_token(subject=str(user.id))

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
        )

    def validate_refresh_token(self, refresh_token: str) -> Optional[User]:
        """Validate refresh token and return user"""

        payload = self.security.decode_token(refresh_token)
        if not payload:
            return None

        if payload.get("type") != "refresh":
            return None

        user_id = payload.get("sub")
        if not user_id:
            return None

        return self.user_repository.get(UUID(user_id))

    def create_password_reset_token(self, user: User) -> str:
        """Create password reset token"""

        reset_token = self.security.generate_token()
        user.password_reset_token = self.security.hash_token(reset_token)
        user.password_reset_sent_at = datetime.utcnow()

        self.db.commit()

        return reset_token

    def reset_password(self, token: str, new_password: str) -> bool:
        """Reset user password with token"""

        hashed_token = self.security.hash_token(token)

        user = self.db.query(User).filter(
            User.password_reset_token == hashed_token
        ).first()

        if not user:
            return False

        # Check if token is expired (24 hours)
        if user.password_reset_sent_at:
            if datetime.utcnow() - user.password_reset_sent_at > timedelta(hours=24):
                return False

        # Update password
        user.hashed_password = self.security.get_password_hash(new_password)
        user.password_reset_token = None
        user.password_reset_sent_at = None

        self.db.commit()

        return True

    def verify_email(self, token: str) -> bool:
        """Verify user email with token"""

        hashed_token = self.security.hash_token(token)

        user = self.db.query(User).filter(
            User.email_verification_token == hashed_token
        ).first()

        if not user:
            return False

        # Check if token is expired (48 hours)
        if user.email_verification_sent_at:
            if datetime.utcnow() - user.email_verification_sent_at > timedelta(hours=48):
                return False

        # Verify email
        user.is_email_verified = True
        user.email_verification_token = None
        user.email_verification_sent_at = None

        self.db.commit()

        return True

    def create_verification_link(self, user: User) -> str:
        """Create email verification link"""

        token = self.security.generate_token()
        user.email_verification_token = self.security.hash_token(token)
        user.email_verification_sent_at = datetime.utcnow()

        self.db.commit()

        return f"{settings.EMAIL_VERIFY_URL}?token={token}"

    def update_last_login(self, user: User):
        """Update user's last login timestamp"""

        user.last_login = datetime.utcnow()
        self.db.commit()

    def update_password(self, user: User, new_password: str):
        """Update user password"""

        user.hashed_password = self.security.get_password_hash(new_password)
        self.db.commit()

    def get_user_by_email(self, email: str) -> Optional[User]:
        """Get user by email"""
        return self.user_repository.get_by_email(email)

    def get_user_by_username(self, username: str) -> Optional[User]:
        """Get user by username"""
        return self.user_repository.get_by_username(username)

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify password"""
        return self.security.verify_password(plain_password, hashed_password)
