# config.py
# ©2024, Ovais Quraishi
"""Load setup.config content

This module is a backward-compatible wrapper around the shared config module.
New code should import from shared.config directly.
"""

# Re-export for backward compatibility
from shared.config import (
    get_config,
    read_config,
    CaseSensitiveConfigParser,
    CONFIG_FILE,
)

__all__ = ['get_config', 'read_config', 'CaseSensitiveConfigParser', 'CONFIG_FILE']
