# database.py
# ©2024, Ovais Quraishi
"""DB Utils for Django frontend

This module provides database utilities for the Django frontend.
Shared functions are imported from the shared.database module.
"""

import ast
import logging
import markdown
import os

from psycopg2 import sql
from psycopg2.extras import RealDictCursor

from . import config

# Import shared database functions
from shared.database import (
    psql_connection,
    get_select_query_results,
    get_select_query_result_dicts,
    db_get_authors,
    db_get_post_ids,
    db_get_comment_ids,
)

config.get_config()


def insert_data_into_table(table_name, data):
    """Insert data into table with safe parameterization.

    Uses psycopg2.sql for safe identifier quoting to prevent SQL injection.
    """
    conn, cur = psql_connection()

    try:
        # Use psycopg2.sql for safe SQL construction
        placeholders = sql.SQL(', ').join([sql.Literal(value) for value in data.values()])
        columns = sql.SQL(', ').join(map(sql.Identifier, data.keys()))
        table = sql.Identifier(table_name)

        query = sql.SQL("INSERT INTO {} ({}) VALUES ({}) ON CONFLICT DO NOTHING;").format(
            table, columns, placeholders
        )

        cur.execute(query)
        conn.commit()
    except Exception as e:
        logging.error("Error inserting data: %s", e)
        conn.rollback()
        raise
    finally:
        if conn:
            conn.close()


def get_new_data_ids(table_name, unique_column, reddit_data):
    """Get object ids for new messages on reddit.

    Uses psycopg2.sql for safe identifier quoting to prevent SQL injection.
    """
    # Use safe SQL construction with sql.Identifier
    query = sql.SQL("SELECT {} FROM {} GROUP BY {};").format(
        sql.Identifier(unique_column),
        sql.Identifier(table_name),
        sql.Identifier(unique_column)
    )

    data_ids_db = []
    data_ids_reddit = []

    result = get_select_query_results(query)
    for row in result:
        data_ids_db.append(row[0])

    for item in reddit_data:
        data_ids_reddit.append(item.id)

    new_list = set(data_ids_reddit) - set(data_ids_db)
    return list(new_list)


def deb_get_post_analysis_comments():
    """Retrieve a random post body and any or all GPT responses related to the post,
        for a specific post_id. Returns a dictionary. Text is
        rendered to html for the convenience of UI rendering.
    """

    sql_query = """
                WITH random_post AS (
                    SELECT ad.analysis_document->>'reference_id' as pid
                    FROM analysis_documents ad
                    WHERE ad.analysis_document->>'category' = 'post'
                    AND ad.analysis_document->>'llm' = 'phi4'
                    ORDER BY random() LIMIT 1
                ), post_comments AS (
                    SELECT
                        c.post_id,
                        array_agg(c.comment_body) AS comment_bodies
                    FROM
                        public.comments c
                    WHERE
                        c.post_id IN (SELECT pid FROM random_post)
                    GROUP BY
                        c.post_id
                )
                SELECT
                    p.subreddit,
                    MAX(p.post_title || '  -  ' || p.post_body) AS post,
                    array_to_string(array_agg(ad.analysis_document), ', ') as analysis_docs,
                    pc.comment_bodies
                FROM
                    public.posts p
                JOIN
                    public.analysis_documents ad ON p.post_id = (ad.analysis_document->>'reference_id')::varchar
                LEFT JOIN
                    post_comments pc ON p.post_id = pc.post_id
                WHERE
                    p.post_id IN (SELECT pid FROM random_post)
                    AND p.post_body NOT LIKE '[ Removed by Reddit ]%'
                    AND pc.comment_bodies NOTNULL
                GROUP BY
                    p.subreddit, pc.comment_bodies;
                """

    conn, cur = psql_connection(cursorfactory=RealDictCursor)

    try:
        cur.execute(sql_query)
        result = cur.fetchone()

        if result:
            # Convert markdown to HTML for UI rendering
            post_html = markdown.markdown(result['post'])
            # Convert analysis docs to list of dictionaries with analysis converted to HTML
            analysis_docs = [dict({**row, 'analysis': markdown.markdown(row['analysis'])}) for row in ast.literal_eval(result['analysis_docs'])]
            new_list = [markdown.markdown(text) for text in result['comment_bodies']]
            return {
                'subreddit': result['subreddit'],
                'post': post_html,
                'analysis_docs': analysis_docs,
                'comment_bodies': new_list  # Including comment bodies in the result
            }
        else:
            return False
    finally:
        if conn:
            conn.close()
