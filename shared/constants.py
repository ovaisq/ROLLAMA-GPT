# shared/constants.py
# ©2024, Ovais Quraishi
"""Application-wide constants for ROLLAMA-GPT

This module centralizes all hardcoded values to make them configurable
and easier to maintain.
"""

from typing import Tuple

# Processing
NUM_ELEMENTS_CHUNK: int = 25
"""Number of elements to process in a single chunk."""

# Language filtering
ALLOWED_LANGUAGES: Tuple[str, ...] = ('en',)
"""Languages allowed for LLM analysis. Other languages are skipped."""

# Redis caching
CACHE_EXPIRE_SECONDS: int = 2592000
"""Default cache expiration time in seconds (30 days)."""

# Rate limiting
SLEEP_RANGE: Tuple[int, int] = (60, 65)
"""Range for random sleep between API calls to avoid rate limiting."""

API_RATE_LIMIT_THRESHOLD: int = 1000
"""Maximum number of API calls before forced sleep."""

# Content filtering
FILTERED_CONTENT_VALUES: Tuple[str, ...] = ('', '[removed]', '[deleted]')
"""Content values that should be filtered out from analysis."""

# Analysis schema
ANALYSIS_SCHEMA_VERSION: str = '4'
"""Current version of the analysis document schema."""

# HTTP status codes
HTTP_OK = 200
HTTP_UNAUTHORIZED = 401
HTTP_BAD_REQUEST = 400
HTTP_INTERNAL_ERROR = 500