import re
from typing import Optional
from datetime import datetime


def validate_email(email: str) -> bool:
    """Validate email format"""
    pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    return bool(re.match(pattern, email))


def validate_phone(phone: str) -> bool:
    """Validate phone number format"""
    # Remove common separators
    cleaned = re.sub(r"[\s\-\(\)]+", "", phone)
    # Check if it contains only digits and optional + at start
    pattern = r"^\+?\d{7,15}$"
    return bool(re.match(pattern, cleaned))


def validate_password_strength(password: str) -> tuple[bool, str]:
    """Validate password strength and return result with message"""

    if len(password) < 8:
        return False, "Password must be at least 8 characters long"

    if not re.search(r"[A-Z]", password):
        return False, "Password must contain at least one uppercase letter"

    if not re.search(r"[a-z]", password):
        return False, "Password must contain at least one lowercase letter"

    if not re.search(r"\d", password):
        return False, "Password must contain at least one digit"

    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        return False, "Password must contain at least one special character"

    return True, "Password is strong"


def validate_username(username: str) -> bool:
    """Validate username format"""
    # Username should be 3-50 characters, alphanumeric with underscores and hyphens
    pattern = r"^[a-zA-Z0-9_-]{3,50}$"
    return bool(re.match(pattern, username))


def validate_url(url: str) -> bool:
    """Validate URL format"""
    pattern = r"^https?:\/\/(www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b([-a-zA-Z0-9()@:%_\+.~#?&\/\/=]*)$"
    return bool(re.match(pattern, url))


def validate_company_name(name: str) -> bool:
    """Validate company name"""
    # Allow letters, numbers, spaces, and common business characters
    if not name or len(name) < 2 or len(name) > 255:
        return False

    # Check for valid characters
    pattern = r"^[a-zA-Z0-9\s\-\.\,\&\'\(\)]+$"
    return bool(re.match(pattern, name))


def validate_event_name(name: str) -> bool:
    """Validate event name"""
    if not name or len(name) < 2 or len(name) > 255:
        return False

    # Allow letters, numbers, spaces, and common punctuation
    pattern = r"^[a-zA-Z0-9\s\-\.\,\!\?\'\"\(\)]+$"
    return bool(re.match(pattern, name))


def validate_image_format(filename: str) -> bool:
    """Validate image file format"""
    allowed_extensions = ["jpg", "jpeg", "png", "webp", "gif"]
    extension = filename.split(".")[-1].lower() if "." in filename else ""
    return extension in allowed_extensions


def validate_date_range(start_date: datetime, end_date: datetime) -> bool:
    """Validate date range"""
    return start_date <= end_date


def validate_hex_color(color: str) -> bool:
    """Validate hex color code"""
    pattern = r"^#(?:[0-9a-fA-F]{3}){1,2}$"
    return bool(re.match(pattern, color))


def sanitize_input(text: str) -> str:
    """Sanitize user input to prevent XSS"""
    # Remove or escape potentially dangerous characters
    dangerous_chars = ["<", ">", '"', "'", "&", "/", "\\"]
    sanitized = text

    for char in dangerous_chars:
        sanitized = sanitized.replace(char, "")

    return sanitized.strip()


def validate_ad_budget(budget: float) -> bool:
    """Validate ad budget amount"""
    return 0 < budget <= 1000000  # Max 1 million


def validate_platform(platform: str) -> bool:
    """Validate advertising platform"""
    valid_platforms = [
        "google_ads",
        "meta_ads",
        "linkedin",
        "twitter",
        "instagram",
        "tiktok",
    ]
    return platform.lower() in valid_platforms
