# shared/database/__init__.py
# ©2024, Ovais Quraishi
"""Shared database utilities for ROLLAMA-GPT

This module provides a centralized database layer that eliminates
duplication between the backend and frontend database modules.
"""

from .connection import (
    DatabaseConnection,
    get_connection,
    psql_connection,
)
from .queries import (
    execute_query,
    get_select_query_results,
    get_select_query_result_dicts,
    insert_data_into_table,
    get_new_data_ids,
    db_get_authors,
    db_get_post_ids,
    db_get_comment_ids,
)

__all__ = [
    # Connection management
    'DatabaseConnection',
    'get_connection',
    'psql_connection',
    # Query execution
    'execute_query',
    'get_select_query_results',
    'get_select_query_result_dicts',
    'insert_data_into_table',
    'get_new_data_ids',
    # Repository functions
    'db_get_authors',
    'db_get_post_ids',
    'db_get_comment_ids',
]