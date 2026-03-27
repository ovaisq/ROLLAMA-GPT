# shared/database/queries.py
# ©2024, Ovais Quraishi
"""Database query utilities for ROLLAMA-GPT

This module provides safe, parameterized query execution functions
that eliminate SQL injection vulnerabilities.
"""

import json
import logging
import os
from typing import Any, Dict, List, Optional, Tuple, Union

import psycopg2
from psycopg2 import sql

import cache
from shared.config import get_config
from shared.constants import FILTERED_CONTENT_VALUES
from shared.database.connection import get_connection, psql_connection
from shared.exceptions import DatabaseError
from utils import subtract_lists


def _log_to_db(service_name: str, version: str, severity: str, message: str) -> None:
    """Log a message to the database (lazy import to avoid circular dependency)."""
    try:
        import logit
        logit.log_message_to_db(service_name, version, severity, message)
    except Exception:
        pass  # Don't fail if logging to DB fails


def _get_version() -> str:
    """Get the current version (lazy import to avoid circular dependency)."""
    try:
        import logit
        return logit.get_rollama_version().get('version', 'unknown')
    except Exception:
        return 'unknown'


def execute_query(sql_query: str, params: Optional[Tuple] = None) -> List[Tuple]:
    """Execute a SQL query and return all results.

    Args:
        sql_query: SQL query string.
        params: Optional query parameters for parameterized queries.

    Returns:
        List of result tuples.

    Raises:
        DatabaseError: If query execution fails.
    """
    with get_connection() as (conn, cur):
        try:
            cur.execute(sql_query, params)
            result = cur.fetchall()
            conn.commit()
            return result
        except psycopg2.Error as e:
            error_message = f'Query execution error: {e}'
            logging.error(error_message)
            _log_to_db(
                os.environ.get('SRVC_NAME', 'rollama'),
                _get_version(),
                'ERROR',
                error_message
            )
            raise DatabaseError(error_message, {'query': sql_query, 'original_error': str(e)}) from e


def get_select_query_results(sql_query: Union[str, sql.Composable], params: Optional[Tuple] = None) -> List[Tuple]:
    """Execute a SELECT query and return all rows.

    This function supports both string queries and psycopg2.sql.Composable
    queries for safe dynamic SQL construction.

    Args:
        sql_query: SQL query (string or Composable).
        params: Optional query parameters.

    Returns:
        List of result tuples.

    Raises:
        DatabaseError: If query execution fails.
    """
    conn, cur = psql_connection()
    try:
        cur.execute(sql_query, params)

        # Check if it's a SELECT query
        if isinstance(sql_query, str) and sql_query.upper().strip().startswith('SELECT'):
            result = cur.fetchall()
            return result
        elif isinstance(sql_query, sql.Composable):
            # For Composable queries, assume SELECT
            result = cur.fetchall()
            return result
        else:
            # For UPDATE, DELETE, INSERT
            conn.commit()
            return []
    except psycopg2.Error as e:
        error_message = f'{e}'
        logging.error(error_message)
        _log_to_db(
            os.environ.get('SRVC_NAME', 'rollama'),
            _get_version(),
            'ERROR',
            error_message
        )
        raise DatabaseError(error_message, {'query': str(sql_query), 'original_error': str(e)}) from e
    finally:
        # Properly handle connection cleanup
        if cur is not None:
            try:
                cur.close()
            except psycopg2.Error as e:
                logging.warning("Error closing cursor: %s", e)
        if conn is not None:
            try:
                conn.close()
            except psycopg2.Error as e:
                logging.warning("Error closing connection: %s", e)


def get_select_query_result_dicts(
    sql_query: Union[str, sql.Composable],
    params: Optional[Tuple] = None
) -> List[Dict[str, Any]]:
    """Execute a query and return all rows as list of dictionaries.

    Args:
        sql_query: SQL query (string or Composable).
        params: Optional query parameters.

    Returns:
        List of dictionaries with column names as keys.

    Raises:
        DatabaseError: If query execution fails.
    """
    conn, cur = psql_connection()
    try:
        cur.execute(sql_query, params)
        columns = [desc[0] for desc in cur.description]
        result = [dict(zip(columns, row)) for row in cur.fetchall()]
        return result
    except psycopg2.Error as e:
        error_message = f'{e}'
        logging.error(error_message)
        _log_to_db(
            os.environ.get('SRVC_NAME', 'rollama'),
            _get_version(),
            'ERROR',
            error_message
        )
        raise DatabaseError(error_message, {'query': str(sql_query), 'original_error': str(e)}) from e
    finally:
        if conn is not None:
            try:
                conn.close()
            except psycopg2.Error as e:
                logging.warning("Error closing connection: %s", e)


def insert_data_into_table(table_name: str, data: Dict[str, Any]) -> bool:
    """Insert data into a table with safe parameterization.

    This function uses psycopg2.sql for safe identifier quoting to prevent
    SQL injection vulnerabilities.

    Args:
        table_name: Name of the target table.
        data: Dictionary of column names and values to insert.

    Returns:
        True if insertion was successful.

    Raises:
        DatabaseError: If insertion fails.
    """
    conn, cur = psql_connection()
    try:
        placeholders = ', '.join(['%s'] * len(data))
        columns = sql.SQL(', ').join(map(sql.Identifier, data.keys()))
        table = sql.Identifier(table_name)
        query = sql.SQL(
            "INSERT INTO {} ({}) VALUES ({}) ON CONFLICT DO NOTHING;"
        ).format(table, columns, sql.SQL(placeholders))

        cur.execute(query, list(data.values()))
        conn.commit()

        info_message = f'Inserted into {table_name}'
        logging.info(info_message)

        # Log to database (but not for log tables to avoid recursion)
        if table_name not in ['rollamalogs', 'servicelogs']:
            _log_to_db(
                os.environ.get('SRVC_NAME', 'rollama'),
                _get_version(),
                'INFO',
                info_message
            )

        return True
    except psycopg2.Error as e:
        logging.error("%s", e)
        raise DatabaseError(f'Insert failed: {e}', {'table': table_name, 'original_error': str(e)}) from e
    finally:
        if conn is not None:
            try:
                conn.close()
            except psycopg2.Error as e:
                logging.warning("Error closing connection: %s", e)


def get_new_data_ids(table_name: str, unique_column: str, reddit_data: List[Any]) -> List[str]:
    """Get object ids for new messages on Reddit.

    Queries the database for existing IDs, compares with Reddit API results,
    and returns only the new IDs.

    Args:
        table_name: Name of the database table.
        unique_column: Name of the unique ID column.
        reddit_data: List of Reddit objects with 'id' attribute.

    Returns:
        List of new IDs that don't exist in the database.

    Note:
        This function uses psycopg2.sql for safe identifier quoting to prevent
        SQL injection vulnerabilities.
    """
    # Use safe SQL construction with sql.Identifier
    query = sql.SQL("SELECT {} FROM {} GROUP BY {};").format(
        sql.Identifier(unique_column),
        sql.Identifier(table_name),
        sql.Identifier(unique_column)
    )

    data_ids_db = []
    data_ids_reddit = []

    try:
        result = get_select_query_results(query)
        for row in result:
            data_ids_db.append(row[0])
    except psycopg2.Error as e:
        logging.warning("Error fetching existing IDs: %s", e)
        # Continue with empty list if query fails

    for item in reddit_data:
        data_ids_reddit.append(item.id)

    new_list = set(data_ids_reddit) - set(data_ids_db)
    return list(new_list)


def db_get_authors() -> List[str]:
    """Get list of authors from database table.

    Returns:
        List of author names.
    """
    author_list = []
    query = "SELECT author_name FROM authors GROUP BY author_name;"

    try:
        authors = get_select_query_results(query)
        for row in authors:
            author_list.append(row[0])
    except psycopg2.Error as e:
        logging.warning("Error fetching authors: %s", e)

    return author_list


def db_get_post_ids() -> Optional[List[str]]:
    """Get list of post IDs that haven't been analyzed yet.

    Filters out:
    - Posts with empty, removed, or deleted bodies
    - Posts that have already been analyzed

    Returns:
        List of post IDs to analyze, or None if none found.
    """
    post_id_list = []

    sql_query = """
                SELECT post_id
                FROM posts
                WHERE post_body NOT IN ('', '[removed]', '[deleted]')
                AND NOT EXISTS (
                    SELECT 1
                    FROM analysis_documents
                    WHERE analysis_document ->> 'post_id' = posts.post_id
                        AND analysis_document ->> 'post_id' IS NOT NULL
                )
                AND NOT EXISTS (
                    SELECT 1
                    FROM analysis_documents
                    WHERE analysis_document ->> 'reference_id' = posts.post_id
                        AND analysis_document ->> 'reference_id' IS NOT NULL
                );
                """

    try:
        post_ids = get_select_query_results(sql_query)
    except psycopg2.Error as e:
        logging.warning("Error fetching post IDs: %s", e)
        return None

    if not post_ids:
        warn_message = 'db_get_post_ids(): no post_ids found in DB'
        logging.warning(warn_message)
        _log_to_db(
            os.environ.get('SRVC_NAME', 'rollama'),
            _get_version(),
            'WARN',
            warn_message
        )
        return None

    for a_post_id in post_ids:
        post_id_list.append(a_post_id[0])

    # Filter out already cached IDs
    try:
        cached_list = cache.get_set_contents('post_id')
        post_id_list = subtract_lists(post_id_list, cached_list)
    except Exception as e:
        logging.warning("Error checking cache for post IDs: %s", e)

    return post_id_list


def db_get_comment_ids() -> Optional[List[str]]:
    """Get list of comment IDs that haven't been analyzed yet.

    Filters out:
    - Comments with empty, removed, or deleted bodies
    - Comments that have already been analyzed

    Returns:
        List of comment IDs to analyze, or None if none found.
    """
    comment_id_list = []

    sql_query = """
                SELECT comment_id
                FROM comments
                WHERE md5(comment_body) NOT IN (md5(''), md5('[removed]'), md5('[deleted]'))
                AND NOT EXISTS (
                    SELECT 1
                    FROM analysis_documents
                    WHERE (analysis_document ->> 'comment_id' = comments.comment_id
                            OR analysis_document ->> 'reference_id' = comments.comment_id)
                        AND (analysis_document ->> 'comment_id' IS NOT NULL
                            OR analysis_document ->> 'reference_id' IS NOT NULL)
                );
                """

    try:
        comment_ids = get_select_query_results(sql_query)
    except psycopg2.Error as e:
        logging.warning("Error fetching comment IDs: %s", e)
        return None

    if not comment_ids:
        warn_message = 'db_get_comment_ids(): no comment_ids found in DB'
        logging.warning(warn_message)
        _log_to_db(
            os.environ.get('SRVC_NAME', 'rollama'),
            _get_version(),
            'WARN',
            warn_message
        )
        return None

    for a_comment_id in comment_ids:
        comment_id_list.append(a_comment_id[0])

    # Filter out already cached IDs
    try:
        cached_list = cache.get_set_contents('comment_id')
        comment_id_list = subtract_lists(comment_id_list, cached_list)
    except Exception as e:
        logging.warning("Error checking cache for comment IDs: %s", e)

    return comment_id_list