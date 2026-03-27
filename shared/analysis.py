#!/usr/bin/env python3
# shared/analysis.py
# ©2024, Ovais Quraishi
"""Unified content analysis module for ROLLAMA-GPT

This module consolidates the analyze_post() and analyze_comment() functions
which were previously ~70% duplicated code in rollama.py.
"""

import asyncio
import hashlib
import json
import logging
import os
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional

import langdetect
from langdetect import detect

from cache import add_key
from database import get_select_query_results, get_select_query_result_dicts, insert_data_into_table
from gptutils import prompt_chat
from logit import log_message_to_db, get_rollama_version
from shared.config import get_config
from shared.constants import ALLOWED_LANGUAGES, ANALYSIS_SCHEMA_VERSION
from utils import calculate_prompt_completion_time, store_model_perf_info


logger = logging.getLogger(__name__)


class ContentType(Enum):
    """Type of content being analyzed."""
    POST = "post"
    COMMENT = "comment"


@dataclass
class AnalysisResult:
    """Result of a content analysis operation."""
    success: bool
    content_id: str
    content_type: ContentType
    error_message: Optional[str] = None
    analysis_document: Optional[Dict[str, Any]] = None


class ContentAnalyzer(ABC):
    """Base class for content analysis.

    This abstract base class provides a template method pattern for
    analyzing different types of content (posts, comments).
    """

    def __init__(self, content_type: ContentType):
        """Initialize the analyzer.

        Args:
            content_type: The type of content this analyzer handles.
        """
        self.content_type = content_type
        config = get_config()
        self.llms = os.environ.get('LLMS', '').split(',')

    def analyze(self, content_id: str) -> AnalysisResult:
        """Analyze a piece of content.

        This is the main entry point for analysis. It follows these steps:
        1. Fetch content from database
        2. Check if already analyzed (cache check)
        3. Validate language
        4. Run LLM analysis
        5. Store results

        Args:
            content_id: The unique identifier of the content to analyze.

        Returns:
            AnalysisResult containing the outcome of the analysis.
        """
        # Log start
        info_message = f'Analyzing {self.content_type.value} ID {content_id}'
        logger.info(info_message)
        log_message_to_db(
            os.environ.get('SRVC_NAME', 'rollama'),
            get_rollama_version().get('version', 'unknown'),
            'INFO',
            info_message
        )

        # Fetch content
        content = self._fetch_content(content_id)
        if not content:
            warn_message = f'{self.content_type.value.capitalize()} ID {content_id} contains no body'
            logger.warning(warn_message)
            log_message_to_db(
                os.environ.get('SRVC_NAME', 'rollama'),
                get_rollama_version().get('version', 'unknown'),
                'WARNING',
                warn_message
            )
            return AnalysisResult(
                success=False,
                content_id=content_id,
                content_type=self.content_type,
                error_message='Content not found or empty'
            )

        # Check cache
        cache_key = f'{self.content_type.value}_id_{content_id}'
        if not add_key(cache_key):
            return AnalysisResult(
                success=False,
                content_id=content_id,
                content_type=self.content_type,
                error_message='Already analyzed'
            )

        # Validate language
        text = self._get_text(content)
        if not self._validate_language(text, content_id):
            return AnalysisResult(
                success=False,
                content_id=content_id,
                content_type=self.content_type,
                error_message='Language not allowed'
            )

        # Run LLM analysis
        prompt = self._get_prompt() + text

        for llm in self.llms:
            try:
                start_time = time.time()
                analyzed_obj, _ = asyncio.run(prompt_chat(llm, prompt, False))
                end_time = time.time()
                prompt_completion_time = calculate_prompt_completion_time(start_time, end_time)

                # Build analysis document
                analysis_document = {
                    'schema_version': ANALYSIS_SCHEMA_VERSION,
                    'source': 'reddit',
                    'category': self.content_type.value,
                    'reference_id': content_id,
                    'llm': llm,
                    'analysis': analyzed_obj['analysis']
                }

                analysis_data = {
                    'timestamp': analyzed_obj['timestamp'],
                    'shasum_512': analyzed_obj['shasum_512'],
                    'analysis_document': json.dumps(analysis_document),
                    'ollama_ver': analyzed_obj['ollama_ver']
                }

                insert_data_into_table('analysis_documents', analysis_data)
                store_model_perf_info(llm, analyzed_obj, prompt_completion_time)

            except Exception as e:
                logger.error("Error analyzing %s %s with %s: %s",
                           self.content_type.value, content_id, llm, e)
                continue

        return AnalysisResult(
            success=True,
            content_id=content_id,
            content_type=self.content_type,
            analysis_document=analysis_document
        )

    def _validate_language(self, text: str, content_id: str) -> bool:
        """Validate that the content is in an allowed language.

        Args:
            text: The text to validate.
            content_id: The content ID for logging purposes.

        Returns:
            True if the language is allowed, False otherwise.
        """
        try:
            language = detect(text)
            if language not in ALLOWED_LANGUAGES:
                cache_key = f'{self.content_type.value}_id_{content_id}'
                add_key(cache_key)
                info_message = f'Skipping {content_id} - language detected {language}'
                logger.info(info_message)
                log_message_to_db(
                    os.environ.get('SRVC_NAME', 'rollama'),
                    get_rollama_version().get('version', 'unknown'),
                    'INFO',
                    info_message
                )
                return False
        except langdetect.lang_detect_exception.LangDetectException as e:
            cache_key = f'{self.content_type.value}_id_{content_id}'
            add_key(cache_key)
            info_message = f'Skipping {content_id} - language detected UNKNOWN {e}'
            logger.info(info_message)
            log_message_to_db(
                os.environ.get('SRVC_NAME', 'rollama'),
                get_rollama_version().get('version', 'unknown'),
                'INFO',
                info_message
            )
            return False

        return True

    @abstractmethod
    def _fetch_content(self, content_id: str) -> Optional[Dict[str, Any]]:
        """Fetch content from the database.

        Args:
            content_id: The unique identifier of the content.

        Returns:
            Dictionary containing content data, or None if not found.
        """
        pass

    @abstractmethod
    def _get_text(self, content: Dict[str, Any]) -> str:
        """Extract the text to analyze from content.

        Args:
            content: Dictionary containing content data.

        Returns:
            The text to analyze.
        """
        pass

    @abstractmethod
    def _get_prompt(self) -> str:
        """Get the prompt prefix for LLM analysis.

        Returns:
            The prompt prefix string.
        """
        pass


class PostAnalyzer(ContentAnalyzer):
    """Analyzer for Reddit posts."""

    def __init__(self):
        super().__init__(ContentType.POST)

    def _fetch_content(self, post_id: str) -> Optional[Dict[str, Any]]:
        """Fetch a post from the database."""
        sql_query = """SELECT
                            post_title, post_body, post_id, post_upvote_count
                        FROM
                            posts
                        WHERE
                            post_id=%s
                        AND
                            post_body
                        NOT IN ('', '[removed]', '[deleted]');
                    """
        post_data_list = get_select_query_result_dicts(sql_query, (post_id,))

        if len(post_data_list) == 1:
            return post_data_list[0]
        return None

    def _get_text(self, content: Dict[str, Any]) -> str:
        """Get post title + body for analysis."""
        return content['post_title'] + content['post_body']

    def _get_prompt(self) -> str:
        """Get the prompt for post analysis."""
        return 'respond to this post title and post body: '


class CommentAnalyzer(ContentAnalyzer):
    """Analyzer for Reddit comments."""

    def __init__(self):
        super().__init__(ContentType.COMMENT)

    def _fetch_content(self, comment_id: str) -> Optional[Dict[str, Any]]:
        """Fetch a comment from the database."""
        sql_query = """SELECT
                            comment_id, comment_body
                        FROM
                            comments
                        WHERE
                            comment_id=%s
                        AND
                            comment_body
                        NOT IN ('', '[removed]', '[deleted]');
                    """
        comment_data = get_select_query_results(sql_query, (comment_id,))

        if comment_data:
            return {
                'comment_id': comment_data[0][0],
                'comment_body': comment_data[0][1]
            }
        return None

    def _get_text(self, content: Dict[str, Any]) -> str:
        """Get comment body for analysis."""
        return content['comment_body']

    def _get_prompt(self) -> str:
        """Get the prompt for comment analysis."""
        return 'respond to this comment: '


# Convenience functions for backward compatibility
def analyze_post(post_id: str) -> bool:
    """Analyze a post.

    This function is provided for backward compatibility.

    Args:
        post_id: The ID of the post to analyze.

    Returns:
        True if analysis succeeded, False otherwise.
    """
    analyzer = PostAnalyzer()
    result = analyzer.analyze(post_id)
    return result.success


def analyze_comment(comment_id: str) -> bool:
    """Analyze a comment.

    This function is provided for backward compatibility.

    Args:
        comment_id: The ID of the comment to analyze.

    Returns:
        True if analysis succeeded, False otherwise.
    """
    analyzer = CommentAnalyzer()
    result = analyzer.analyze(comment_id)
    return result.success
