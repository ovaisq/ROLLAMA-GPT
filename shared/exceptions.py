# shared/exceptions.py
# ©2024, Ovais Quraishi
"""Custom exception hierarchy for ROLLAMA-GPT

This module provides a structured exception hierarchy for consistent
error handling across the application.
"""

from typing import Any, Dict, Optional


class RollamaError(Exception):
    """Base exception for all ROLLAMA-GPT errors.

    All custom exceptions should inherit from this class to enable
    consistent error handling and logging.

    Attributes:
        message: Human-readable error message.
        details: Additional context about the error.
    """

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        self.message = message
        self.details = details or {}
        super().__init__(self.message)

    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary for JSON serialization."""
        return {
            'error': self.message,
            'details': self.details
        }


class DatabaseError(RollamaError):
    """Exception raised for database-related errors.

    Raised when:
    - Connection to database fails
    - Query execution fails
    - Data integrity constraints are violated
    """
    pass


class RedditAPIError(RollamaError):
    """Exception raised for Reddit API-related errors.

    Raised when:
    - Reddit API rate limit is exceeded
    - Reddit API returns an error response
    - Requested content is not found or forbidden
    """
    pass


class LLMError(RollamaError):
    """Exception raised for LLM/Ollama-related errors.

    Raised when:
    - Connection to Ollama server fails
    - Model loading fails
    - Inference produces an error
    """
    pass


class CacheError(RollamaError):
    """Exception raised for Redis cache-related errors.

    Raised when:
    - Connection to Redis fails
    - Cache read/write operations fail
    """
    pass


class ValidationError(RollamaError):
    """Exception raised for input validation errors.

    Raised when:
    - Required parameters are missing
    - Parameter values are invalid
    - Data format is incorrect
    """
    pass


class ConfigurationError(RollamaError):
    """Exception raised for configuration-related errors.

    Raised when:
    - Required configuration is missing
    - Configuration values are invalid
    - Configuration file cannot be read
    """
    pass


class AuthenticationError(RollamaError):
    """Exception raised for authentication-related errors.

    Raised when:
    - Invalid credentials provided
    - JWT token is expired or invalid
    - API key is invalid
    """
    pass