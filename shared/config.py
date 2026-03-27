# shared/config.py
# ©2024, Ovais Quraishi
"""Unified configuration module for ROLLAMA-GPT

This module provides a centralized configuration system that eliminates
the duplication of CaseSensitiveConfigParser across multiple files.
"""

import configparser
import logging
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional


class CaseSensitiveConfigParser(configparser.RawConfigParser):
    """ConfigParser that preserves case sensitivity of option names.

    This is required because Reddit API and other services use case-sensitive
    parameter names that must be preserved.
    """

    def optionxform(self, optionstr: str) -> str:
        """Override to preserve case of option names."""
        return optionstr


# Default config file name
CONFIG_FILE = 'setup.config'

# Global config instance (lazy loaded)
_config: Optional['Config'] = None


@dataclass
class DatabaseConfig:
    """Database connection configuration."""
    host: str
    port: int = 5432
    database: str = ''
    user: str = ''
    password: str = ''


@dataclass
class CacheConfig:
    """Redis cache configuration."""
    redis_host: str = 'localhost'
    redis_port: int = 6379
    redis_password: str = ''
    expire_seconds: int = 2592000  # 30 days


@dataclass
class ApplicationConfig:
    """Application-level configuration."""
    num_elements_chunk: int = 25
    allowed_languages: List[str] = field(default_factory=lambda: ['en'])
    sleep_min: int = 60
    sleep_max: int = 65
    api_rate_limit: int = 1000


@dataclass
class SecurityConfig:
    """Security-related configuration."""
    ssl_verify: bool = True
    jwt_verify_signature: bool = True
    django_allowed_hosts: List[str] = field(default_factory=lambda: ['localhost', '127.0.0.1'])


@dataclass
class Config:
    """Main configuration container."""
    database: DatabaseConfig = None
    cache: CacheConfig = None
    application: ApplicationConfig = None
    security: SecurityConfig = None
    raw_config: Dict[str, str] = field(default_factory=dict)

    def __post_init__(self):
        if self.database is None:
            self.database = DatabaseConfig(host='')
        if self.cache is None:
            self.cache = CacheConfig()
        if self.application is None:
            self.application = ApplicationConfig()
        if self.security is None:
            self.security = SecurityConfig()


def read_config(file_path: str = CONFIG_FILE) -> Dict[str, str]:
    """Read configuration file and return as dictionary.

    Args:
        file_path: Path to the configuration file.

    Returns:
        Dictionary containing all configuration values.
    """
    config_dict = {}

    resolved_path = Path(file_path).resolve()

    if resolved_path.exists():
        config_obj = CaseSensitiveConfigParser()
        config_obj.read(file_path)

        for section_name, options in config_obj.items():
            for option_name, option_value in options.items():
                config_dict[option_name] = option_value
    else:
        logging.warning(
            '%s file not found. Assuming ENV VARS are set up using some other method',
            CONFIG_FILE
        )

    return config_dict


def _load_config_from_env() -> Config:
    """Load configuration from environment variables."""
    config = Config()

    # Database config
    config.database = DatabaseConfig(
        host=os.environ.get('host', ''),
        port=int(os.environ.get('port', 5432)),
        database=os.environ.get('database', ''),
        user=os.environ.get('user', ''),
        password=os.environ.get('password', '')
    )

    # Cache config
    config.cache = CacheConfig(
        redis_host=os.environ.get('redis_host', 'localhost'),
        redis_port=int(os.environ.get('redis_port', 6379)),
        redis_password=os.environ.get('redis_password', ''),
        expire_seconds=int(os.environ.get('CACHE_EXPIRE_SECONDS', 2592000))
    )

    # Application config
    allowed_langs = os.environ.get('ALLOWED_LANGUAGES', 'en')
    config.application = ApplicationConfig(
        num_elements_chunk=int(os.environ.get('NUM_ELEMENTS_CHUNK', 25)),
        allowed_languages=allowed_langs.split(',') if allowed_langs else ['en'],
        sleep_min=int(os.environ.get('SLEEP_MIN_SECONDS', 60)),
        sleep_max=int(os.environ.get('SLEEP_MAX_SECONDS', 65)),
        api_rate_limit=int(os.environ.get('API_RATE_LIMIT_THRESHOLD', 1000))
    )

    # Security config
    allowed_hosts = os.environ.get('DJANGO_ALLOWED_HOSTS', 'localhost,127.0.0.1')
    config.security = SecurityConfig(
        ssl_verify=os.environ.get('SSL_VERIFY', 'true').lower() == 'true',
        jwt_verify_signature=os.environ.get('JWT_VERIFY_SIGNATURE', 'true').lower() == 'true',
        django_allowed_hosts=allowed_hosts.split(',') if allowed_hosts else ['localhost']
    )

    return config


def get_config() -> Config:
    """Get the global configuration instance.

    This function loads configuration from the config file (if exists) and
    sets environment variables for backward compatibility with existing code.

    Returns:
        Config object containing all configuration values.
    """
    global _config

    if _config is None:
        # First, read from config file and set env vars (backward compatibility)
        config_dict = read_config(CONFIG_FILE)

        for key, value in config_dict.items():
            if key not in os.environ:
                os.environ[key] = value

        # Then load from env (which now includes file values)
        _config = _load_config_from_env()
        _config.raw_config = config_dict

    return _config


def set_env_from_config() -> None:
    """Set environment variables from config file.

    This is provided for backward compatibility with existing code that
    expects environment variables to be set at module import time.
    """
    config_dict = read_config(CONFIG_FILE)

    for key, value in config_dict.items():
        os.environ[key] = value


def get_flask_config() -> Dict[str, str]:
    """Get Flask-specific configuration from environment variables."""
    return {
        'JWT_SECRET_KEY': os.environ.get('JWT_SECRET_KEY', ''),
        'SECRET_KEY': os.environ.get('APP_SECRET_KEY', ''),
        'PERMANENT_SESSION_LIFETIME': 172800  # 2 days
    }