"""Input validation utilities."""

import re
from typing import Any, Optional


class ValidationError(Exception):
    """Validation error."""
    pass


def validate_discord_token(token: str) -> bool:
    """Validate Discord bot token format."""
    if not token or len(token) < 50:
        return False
    
    # Discord tokens have specific format
    pattern = r'^[A-Za-z0-9\-_\.]{50,}$'
    return bool(re.match(pattern, token))


def validate_discord_id(user_id: str) -> bool:
    """Validate Discord user/channel ID."""
    if not user_id:
        return False
    
    # Discord IDs are numeric strings
    return user_id.isdigit() and len(user_id) >= 17


def validate_url(url: str) -> bool:
    """Validate URL format."""
    if not url:
        return False
    
    pattern = r'^https?://[^\s<>"{}|\\^`\[\]]+$'
    return bool(re.match(pattern, url))


def validate_temperature(temp: float) -> bool:
    """Validate LLM temperature parameter."""
    return 0.0 <= temp <= 2.0


def validate_pad_value(value: float) -> bool:
    """Validate PAD model value."""
    return -1.0 <= value <= 1.0


def sanitize_message(content: str, max_length: int = 2000) -> str:
    """Sanitize and truncate message content."""
    # Remove control characters except newlines and tabs
    sanitized = re.sub(r'[\x00-\x08\x0b-\x0c\x0e-\x1f\x7f-\x9f]', '', content)
    
    # Truncate if needed
    if len(sanitized) > max_length:
        sanitized = sanitized[:max_length-3] + "..."
    
    return sanitized.strip()