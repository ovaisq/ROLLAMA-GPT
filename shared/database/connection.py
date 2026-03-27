# shared/database/connection.py
# ©2024, Ovais Quraishi
"""Database connection management for ROLLAMA-GPT

This module provides connection pooling and context management for
PostgreSQL database connections.
"""

import logging
import os
from contextlib import contextmanager
from typing import Optional, Tuple

import psycopg2
from psycopg2 import sql
from psycopg2.extras import RealDictCursor

from shared.config import get_config
from shared.exceptions import DatabaseError


class DatabaseConnection:
    """Context manager for database connections.

    Provides automatic connection cleanup and error handling.

    Usage:
        with DatabaseConnection() as (conn, cur):
            cur.execute("SELECT * FROM posts")
            results = cur.fetchall()
    """

    def __init__(self, cursor_factory=None, autocommit: bool = False):
        """Initialize database connection context manager.

        Args:
            cursor_factory: Optional cursor factory (e.g., RealDictCursor).
            autocommit: If True, automatically commit on success.
        """
        self.cursor_factory = cursor_factory
        self.autocommit = autocommit
        self.conn = None
        self.cur = None

    def __enter__(self) -> Tuple['psycopg2.connection', 'psycopg2.cursor']:
        """Establish connection and return cursor."""
        config = get_config()

        db_config = {
            'host': config.database.host or os.environ.get('host', ''),
            'database': config.database.database or os.environ.get('database', ''),
            'user': config.database.user or os.environ.get('user', ''),
            'password': config.database.password or os.environ.get('password', ''),
            'port': config.database.port or int(os.environ.get('port', 5432))
        }

        try:
            self.conn = psycopg2.connect(**db_config)
            self.cur = self.conn.cursor(cursor_factory=self.cursor_factory)
            return self.conn, self.cur
        except psycopg2.Error as e:
            error_message = f'Error connecting to PostgreSQL: {e}'
            logging.error(error_message)
            # Lazy import to avoid circular dependency
            try:
                import logit
                logit.log_message_to_db(
                    os.environ.get('SRVC_NAME', 'rollama'),
                    logit.get_rollama_version().get('version', 'unknown'),
                    'ERROR',
                    error_message
                )
            except Exception:
                pass  # Don't fail if logging to DB fails
            raise DatabaseError(error_message, {'original_error': str(e)}) from e

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Clean up connection resources."""
        if self.cur is not None:
            try:
                self.cur.close()
            except psycopg2.Error as e:
                logging.warning("Error closing cursor: %s", e)

        if self.conn is not None:
            try:
                if exc_type is None and self.autocommit:
                    self.conn.commit()
                elif exc_type is None:
                    pass  # Caller is responsible for commit
                else:
                    self.conn.rollback()
            except psycopg2.Error as e:
                logging.warning("Error during connection cleanup: %s", e)
            finally:
                try:
                    self.conn.close()
                except psycopg2.Error as e:
                    logging.warning("Error closing connection: %s", e)

        return False  # Don't suppress exceptions


@contextmanager
def get_connection(cursor_factory=None, autocommit: bool = False):
    """Context manager for database connections.

    This is the preferred way to get a database connection.

    Args:
        cursor_factory: Optional cursor factory (e.g., RealDictCursor).
        autocommit: If True, automatically commit on success.

    Yields:
        Tuple of (connection, cursor).

    Example:
        with get_connection() as (conn, cur):
            cur.execute("SELECT * FROM posts")
            results = cur.fetchall()
    """
    db_conn = DatabaseConnection(cursor_factory=cursor_factory, autocommit=autocommit)
    yield db_conn.__enter__()
    db_conn.__exit__(None, None, None)


def psql_connection(cursor_factory=None) -> Tuple['psycopg2.connection', 'psycopg2.cursor']:
    """Connect to PostgreSQL server.

    This function is provided for backward compatibility with existing code.
    New code should use get_connection() context manager instead.

    Args:
        cursor_factory: Optional cursor factory (e.g., RealDictCursor).

    Returns:
        Tuple of (connection, cursor).

    Note:
        Caller is responsible for closing the connection.
    """
    config = get_config()

    db_config = {
        'host': config.database.host or os.environ.get('host', ''),
        'database': config.database.database or os.environ.get('database', ''),
        'user': config.database.user or os.environ.get('user', ''),
        'password': config.database.password or os.environ.get('password', ''),
        'port': config.database.port or int(os.environ.get('port', 5432))
    }

    try:
        psql_conn = psycopg2.connect(**db_config)
        psql_cur = psql_conn.cursor(cursor_factory=cursor_factory)
        return psql_conn, psql_cur
    except psycopg2.Error as e:
        error_message = f'Error connecting to PostgreSQL: {e}'
        logging.error(error_message)
        # Lazy import to avoid circular dependency
        try:
            import logit
            logit.log_message_to_db(
                os.environ.get('SRVC_NAME', 'rollama'),
                logit.get_rollama_version().get('version', 'unknown'),
                'ERROR',
                error_message
            )
        except Exception:
            pass
        raise DatabaseError(error_message, {'original_error': str(e)}) from e