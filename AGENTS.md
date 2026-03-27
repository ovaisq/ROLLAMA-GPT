# AGENTS.md

Guidelines for AI agents working on the ROLLAMA-GPT codebase.

## Project Overview

ROLLAMA-GPT is a Reddit data scraper and LLM analyzer using Flask (backend API) and Django (frontend dashboard). It collects Reddit posts/comments, analyzes them with Ollama LLMs, and stores results in PostgreSQL.

## Build/Run Commands

### Setup
```bash
pip3 install -r requirements.txt
# Also install frontend requirements:
pip3 install -r frontend/analysis_frontend/requirements.txt
```

### Testing
```bash
# Run all tests
python -m unittest testit

# Run single test class
python -m unittest testit.TestFlaskApp

# Run single test method
python -m unittest testit.TestFlaskApp.perform_login
```

### Running Services
```bash
# Development (Flask backend)
gunicorn --certfile=cert.pem --keyfile=key.pem --bind 0.0.0.0:5001 rollama:app --timeout 2592000 --workers 2 --log-level info

# Django frontend
cd frontend/analysis_frontend && python manage.py runserver
```

### Build/Deploy
```bash
# Build deployment package
./build.sh

# Build Docker image
./build_docker.py

# Docker run
docker run -d -p 5001:5001 rollama:<version>
```

## Code Style Guidelines

### General
- Python 3.9+ compatible
- Line length: 100 characters maximum
- Indentation: 4 spaces (no tabs)
- UTF-8 encoding

### File Headers
All Python files must include copyright header:
```python
#!/usr/bin/env python3
# ©2024, Ovais Quraishi
"""Brief module description."""
```

### Imports
1. Standard library imports first
2. Third-party imports second
3. Local application imports last
4. Group imports with blank line between groups
5. Alphabetize within groups

Example:
```python
import asyncio
import json
import os

from flask import Flask
from flask_jwt_extended import JWTManager

from cache import add_key
from config import get_config
```

### Naming Conventions
- `snake_case` for functions, variables, methods
- `PascalCase` for class names
- `SCREAMING_SNAKE_CASE` for constants
- `_prefix` for private/internal functions
- Descriptive names (avoid single letters except loop indices)

### Type Hints
Use type hints for function signatures (new code):
```python
def process_data(data: Dict[str, Any]) -> Optional[str]:
    """Process data and return result."""
    pass
```

### Docstrings
- Use triple double-quotes
- First line: brief description
- Add Args/Returns for complex functions
- Keep docstrings under 100 chars per line

### Error Handling
- Use custom exceptions from `shared/exceptions.py`
- Always catch specific exceptions, never bare `except:`
- Log errors using the `logit` module
- Return meaningful error messages to API consumers

### Database
- Use parameterized queries (never string interpolation)
- Import from `shared.database.queries` for SQL
- Use `database.py` functions for common operations
- Handle connection errors gracefully

### Configuration
- Never hardcode secrets or credentials
- Use `get_config()` from `shared.config`
- Environment variables set from `setup.config` file
- Add new config to `shared/config.py` dataclasses

### Comments
- Explain "why", not "what" (code should be self-explanatory)
- Use `#` for inline comments
- Keep comments current with code changes
- Remove commented-out code before committing

### Constants
Define in `shared/constants.py`:
```python
from typing import Final
NUM_ELEMENTS_CHUNK: Final[int] = 25
```

## Testing Guidelines

- Tests in `testit.py` using unittest framework
- Mock external dependencies (Reddit API, Ollama)
- Test both success and error cases
- Use `setUp()` and `tearDown()` for test fixtures
- Test files must handle missing `setup.config` gracefully

## Security

- Never commit secrets, keys, or credentials
- JWT tokens for API authentication
- Encrypt sensitive data using `encryption.py`
- Validate all user inputs
- SQL injection prevention (use parameterized queries)

## Architecture

- `rollama.py` - Main Flask application (API endpoints)
- `shared/` - Shared modules (database, config, exceptions, constants)
- `frontend/analysis_frontend/` - Django web dashboard
- Database operations in `database.py` and `shared/database/`
- Reddit API wrapper in `reddit_api.py`
- LLM utilities in `gptutils.py`
- Caching via `cache.py` (Redis)
