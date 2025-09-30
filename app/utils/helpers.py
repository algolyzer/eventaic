from datetime import datetime, timedelta
from functools import wraps
import hashlib
import logging
import random
import string
import sys
import time
from typing import Any, Dict, List, Optional


def setup_logging(level: str = "INFO") -> None:
    """Setup application logging"""

    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler(
                f'logs/eventaic_{datetime.now().strftime("%Y%m%d")}.log'
            ),
        ],
    )


def generate_random_string(length: int = 32) -> str:
    """Generate random alphanumeric string"""
    return "".join(random.choices(string.ascii_letters + string.digits, k=length))


def hash_string(text: str) -> str:
    """Generate SHA256 hash of string"""
    return hashlib.sha256(text.encode()).hexdigest()


def format_datetime(dt: datetime, format_str: str = "%Y-%m-%d %H:%M:%S") -> str:
    """Format datetime to string"""
    return dt.strftime(format_str) if dt else ""


def parse_datetime(
    date_str: str, format_str: str = "%Y-%m-%d %H:%M:%S"
) -> Optional[datetime]:
    """Parse string to datetime"""
    try:
        return datetime.strptime(date_str, format_str)
    except (ValueError, TypeError):
        return None


def calculate_percentage(part: int, whole: int) -> float:
    """Calculate percentage safely"""
    if whole == 0:
        return 0.0
    return round((part / whole) * 100, 2)


def truncate_string(text: str, max_length: int, suffix: str = "...") -> str:
    """Truncate string to maximum length"""
    if len(text) <= max_length:
        return text
    return text[: max_length - len(suffix)] + suffix


def sanitize_filename(filename: str) -> str:
    """Sanitize filename for safe storage"""
    invalid_chars = '<>:"/\\|?*'
    for char in invalid_chars:
        filename = filename.replace(char, "_")
    return filename


def get_file_extension(filename: str) -> str:
    """Get file extension from filename"""
    parts = filename.split(".")
    return parts[-1].lower() if len(parts) > 1 else ""


def timing_decorator(func):
    """Decorator to measure function execution time"""

    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        execution_time = end_time - start_time
        logging.debug(f"{func.__name__} took {execution_time:.2f} seconds")
        return result

    return wrapper


def retry_on_exception(max_retries: int = 3, delay: float = 1.0):
    """Decorator to retry function on exception"""

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            retries = 0
            while retries < max_retries:
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    retries += 1
                    if retries == max_retries:
                        raise e
                    time.sleep(delay * retries)
                    logging.warning(
                        f"Retry {retries}/{max_retries} for {func.__name__}"
                    )
            return None

        return wrapper

    return decorator


def paginate_results(total: int, page: int, per_page: int) -> Dict[str, Any]:
    """Calculate pagination metadata"""
    total_pages = (total + per_page - 1) // per_page

    return {
        "total": total,
        "page": page,
        "per_page": per_page,
        "pages": total_pages,
        "has_next": page < total_pages,
        "has_prev": page > 1,
    }


def format_file_size(size_bytes: int) -> str:
    """Format file size in human readable format"""
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if size_bytes < 1024.0:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.2f} PB"


def get_date_range(period: str) -> tuple[datetime, datetime]:
    """Get date range based on period string"""
    now = datetime.utcnow()

    if period == "today":
        start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        end = now
    elif period == "yesterday":
        yesterday = now - timedelta(days=1)
        start = yesterday.replace(hour=0, minute=0, second=0, microsecond=0)
        end = yesterday.replace(hour=23, minute=59, second=59, microsecond=999999)
    elif period == "this_week":
        start = now - timedelta(days=now.weekday())
        start = start.replace(hour=0, minute=0, second=0, microsecond=0)
        end = now
    elif period == "this_month":
        start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        end = now
    elif period == "last_month":
        first_day_this_month = now.replace(day=1)
        last_day_last_month = first_day_this_month - timedelta(days=1)
        start = last_day_last_month.replace(
            day=1, hour=0, minute=0, second=0, microsecond=0
        )
        end = last_day_last_month.replace(
            hour=23, minute=59, second=59, microsecond=999999
        )
    else:
        # Default to last 30 days
        start = now - timedelta(days=30)
        end = now

    return start, end


def mask_sensitive_data(data: str, visible_chars: int = 4) -> str:
    """Mask sensitive data showing only few characters"""
    if len(data) <= visible_chars * 2:
        return "*" * len(data)

    return (
        data[:visible_chars]
        + "*" * (len(data) - visible_chars * 2)
        + data[-visible_chars:]
    )


def is_valid_uuid(uuid_string: str) -> bool:
    """Check if string is valid UUID"""
    try:
        from uuid import UUID

        UUID(uuid_string)
        return True
    except (ValueError, AttributeError):
        return False
