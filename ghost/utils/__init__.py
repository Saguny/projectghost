"""Utility functions and helpers.

This module provides common utilities used throughout the system:
- Logging configuration
- Retry decorators
- Input validation
- Data sanitization

Usage:
    from ghost.utils import (
        setup_logging,
        async_retry,
        validate_discord_token,
        sanitize_message
    )
    
    # Setup logging
    setup_logging(debug_mode=True, log_level="DEBUG")
    
    # Use retry decorator
    @async_retry(max_attempts=3, delay_seconds=1.0)
    async def unreliable_operation():
        ...
"""

from ghost.utils.logging_config import setup_logging
from ghost.utils.retry import async_retry
from ghost.utils.validation import (
    ValidationError,
    validate_discord_token,
    validate_discord_id,
    validate_url,
    validate_temperature,
    validate_pad_value,
    sanitize_message,
)

__all__ = [
    # Logging
    "setup_logging",
    
    # Retry
    "async_retry",
    
    # Validation
    "ValidationError",
    "validate_discord_token",
    "validate_discord_id",
    "validate_url",
    "validate_temperature",
    "validate_pad_value",
    "sanitize_message",
]


def configure_production_logging(log_file: str = "data/logs/ghost.log"):
    """Configure production-grade logging with rotation.
    
    Args:
        log_file: Path to log file
    """
    setup_logging(debug_mode=False, log_level="INFO")


def configure_debug_logging():
    """Configure verbose debug logging."""
    setup_logging(debug_mode=True, log_level="DEBUG")