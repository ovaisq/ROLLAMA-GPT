# shared/__init__.py
# ©2024, Ovais Quraishi
"""Shared utilities and common code for ROLLAMA-GPT"""

from .config import get_config, CaseSensitiveConfigParser
from .constants import (
    NUM_ELEMENTS_CHUNK,
    ALLOWED_LANGUAGES,
    CACHE_EXPIRE_SECONDS,
    SLEEP_RANGE,
    API_RATE_LIMIT_THRESHOLD,
)
from .exceptions import (
    RollamaError,
    DatabaseError,
    RedditAPIError,
    LLMError,
    CacheError,
    ValidationError,
    ConfigurationError,
)

# Analysis module has additional dependencies (langdetect)
# Import it lazily to avoid import errors when dependencies aren't installed
def __getattr__(name):
    """Lazy import for analysis module."""
    if name in ('ContentType', 'AnalysisResult', 'ContentAnalyzer',
                'PostAnalyzer', 'CommentAnalyzer', 'analyze_post', 'analyze_comment'):
        from . import analysis
        return getattr(analysis, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

__all__ = [
    # Config
    'get_config',
    'CaseSensitiveConfigParser',
    # Constants
    'NUM_ELEMENTS_CHUNK',
    'ALLOWED_LANGUAGES',
    'CACHE_EXPIRE_SECONDS',
    'SLEEP_RANGE',
    'API_RATE_LIMIT_THRESHOLD',
    # Exceptions
    'RollamaError',
    'DatabaseError',
    'RedditAPIError',
    'LLMError',
    'CacheError',
    'ValidationError',
    'ConfigurationError',
    # Analysis (lazy loaded)
    'ContentType',
    'AnalysisResult',
    'ContentAnalyzer',
    'PostAnalyzer',
    'CommentAnalyzer',
    'analyze_post',
    'analyze_comment',
]