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
import re

logger = logging.getLogger(__name__)


class AuthService:
    def __init__(self, db: Session):
        self.db = db
        self.user_repository = UserRepository(db)
        self.company_repository = CompanyRepository(db)
        self.security = Security()

    def _sanitize_input(self, text: str) -> str:
        """Sanitize user input to prevent XSS"""
        if not text:
            return text
        # Remove potentially dangerous characters
        dangerous_chars = ['<', '>', '"', "'", '&', '/', '\\', ';']
        sanitized = text
        for char in dangerous_chars:
            sanitized = sanitized.replace(char, '')
        return sanitized.strip()

    def _validate_email_format(self, email: str) -> bool:
        """Validate email format"""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email))

    def _validate_username_format(self, username: str) -> bool:
        """Validate username format"""
        # 3-50 chars, alphanumeric, underscore, hyphen only
        pattern = r'^[a-zA-Z0-9_-]{3,50}$'
        return bool(re.match(pattern, username))

    async def create_user(self, request: RegisterRequest) -> User:
        """Create new user with optional company - with enhanced security"""

        # Sanitize inputs
        email = self._sanitize_input(request.email.lower())
        username = self._sanitize_input(request.username)
        full_name = self._sanitize_input(request.full_name) if request.full_name else None
        company_name = self._sanitize_input(request.company_name) if request.company_name else None

        # Validate formats
        if not self._validate_email_format(email):
            raise ValueError("Invalid email format")

        if not self._validate_username_format(username):
            raise ValueError("Username must be 3-50 characters, alphanumeric with _ or - only")

        # Check if user already exists
        if self.user_repository.get_by_email(email):
            raise ValueError("Email already registered")

        if self.user_repository.get_by_username(username):
            raise ValueError("Username already taken")

        # Hash password with bcrypt (not sha256_crypt)
        hashed_password = self.security.get_password_hash(request.password)

        # Create or get company if company name provided
        company = None
        if company_name:
            company = self.company_repository.get_by_name(company_name)
            if not company:
                company = Company(
                    name=company_name,
                    email=email
                )
                self.db.add(company)
                self.db.flush()

        # Create user
        user = User(
            email=email,
            username=username,
            full_name=full_name,
            phone=self._sanitize_input(request.phone) if request.phone else None,
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

        logger.info(f"New user created: {user.id} ({user.email})")
        return user

    def authenticate_user(self, username: str, password: str) -> Optional[User]:
        """Authenticate user by username - with enhanced security"""
        # Sanitize input
        username = self._sanitize_input(username)

        # Find user by username
        user = self.user_repository.get_by_username(username)

        if not user:
            # Use constant-time comparison to prevent timing attacks
            # Hash a dummy password to make timing consistent
            self.security.get_password_hash("dummy_password_for_timing")
            return None

        # Verify password
        if not self.security.verify_password(password, user.hashed_password):
            logger.warning(f"Failed login attempt for username: {username}")
            return None

        # Check if user is active
        if not user.is_active or user.is_deleted:
            logger.warning(f"Login attempt for inactive/deleted user: {username}")
            return None

        return user

    def authenticate_user_by_email(self, email: str, password: str) -> Optional[User]:
        """Authenticate user by email - with enhanced security"""
        # Sanitize and validate input
        email = self._sanitize_input(email.lower())

        if not self._validate_email_format(email):
            return None

        # Find user by email
        user = self.user_repository.get_by_email(email)

        if not user:
            # Use constant-time comparison to prevent timing attacks
            self.security.get_password_hash("dummy_password_for_timing")
            return None

        # Verify password
        if not self.security.verify_password(password, user.hashed_password):
            logger.warning(f"Failed login attempt for email: {email}")
            return None

        # Check if user is active
        if not user.is_active or user.is_deleted:
            logger.warning(f"Login attempt for inactive/deleted user: {email}")
            return None

        return user

    def authenticate_user_flexible(self, identifier: str, password: str) -> Optional[User]:
        """
        Authenticate user by either username or email - with enhanced security
        Tries email first if @ is present, otherwise username
        """
        # Sanitize identifier
        identifier = self._sanitize_input(identifier)

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
            logger.warning("Invalid token type for refresh")
            return None

        user_id = payload.get("sub")
        if not user_id:
            return None

        try:
            user = self.user_repository.get(UUID(user_id))
            # Verify user is still active
            if user and (not user.is_active or user.is_deleted):
                return None
            return user
        except (ValueError, TypeError):
            return None

    def create_password_reset_token(self, user: User) -> str:
        """Create password reset token"""
        reset_token = self.security.generate_token()
        user.password_reset_token = self.security.hash_token(reset_token)
        user.password_reset_sent_at = datetime.utcnow()

        self.db.commit()
        logger.info(f"Password reset token created for user: {user.id}")

        return reset_token

    def reset_password(self, token: str, new_password: str) -> bool:
        """Reset user password with token"""
        hashed_token = self.security.hash_token(token)

        user = self.db.query(User).filter(
            User.password_reset_token == hashed_token
        ).first()

        if not user:
            logger.warning("Invalid password reset token used")
            return False

        # Check if token is expired (24 hours)
        if user.password_reset_sent_at:
            if datetime.utcnow() - user.password_reset_sent_at > timedelta(hours=24):
                logger.warning(f"Expired password reset token for user: {user.id}")
                return False

        # Update password
        user.hashed_password = self.security.get_password_hash(new_password)
        user.password_reset_token = None
        user.password_reset_sent_at = None

        self.db.commit()
        logger.info(f"Password reset successful for user: {user.id}")

        return True

    def verify_email(self, token: str) -> bool:
        """Verify user email with token"""
        hashed_token = self.security.hash_token(token)

        user = self.db.query(User).filter(
            User.email_verification_token == hashed_token
        ).first()

        if not user:
            logger.warning("Invalid email verification token used")
            return False

        # Check if token is expired (48 hours)
        if user.email_verification_sent_at:
            if datetime.utcnow() - user.email_verification_sent_at > timedelta(hours=48):
                logger.warning(f"Expired email verification token for user: {user.id}")
                return False

        # Verify email
        user.is_email_verified = True
        user.email_verification_token = None
        user.email_verification_sent_at = None

        self.db.commit()
        logger.info(f"Email verified for user: {user.id}")

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
        logger.info(f"User login: {user.id} ({user.email})")

    def update_password(self, user: User, new_password: str):
        """Update user password"""
        user.hashed_password = self.security.get_password_hash(new_password)
        self.db.commit()
        logger.info(f"Password updated for user: {user.id}")

    def get_user_by_email(self, email: str) -> Optional[User]:
        """Get user by email"""
        email = self._sanitize_input(email.lower())
        if not self._validate_email_format(email):
            return None
        return self.user_repository.get_by_email(email)

    def get_user_by_username(self, username: str) -> Optional[User]:
        """Get user by username"""
        username = self._sanitize_input(username)
        if not self._validate_username_format(username):
            return None
        return self.user_repository.get_by_username(username)

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify password"""
        return self.security.verify_password(plain_password, hashed_password)
