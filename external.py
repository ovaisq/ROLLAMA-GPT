#!/usr/bin/env python3
"""External Service connectivity function live here"""

import logging
import os
import time

import jwt
import requests

from shared.config import get_config

logger = logging.getLogger(__name__)


def cache_api(endpoint_url, payload=None):
    """Call a protected endpoint with a JSON payload."""

    caching_srvc_login_url = os.environ["caching_srvc_login_url"]
    caching_srvc_secret = os.environ["caching_srvc_secret"]
    caching_srvc_headers = {"Content-Type": "application/json"}
    caching_srvc_payload = {
        "client_id": "rollama",
        "api_key": caching_srvc_secret,
        "grant_type": "client_credentials",
    }
    curr_token = get_jwt_token(
        caching_srvc_login_url, caching_srvc_payload, caching_srvc_headers
    )

    url = f"{endpoint_url}"
    headers = {
        "Authorization": f"Bearer {curr_token}",
        "Content-Type": "application/json",
    }

    try:
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()
        response_json = response.json()
        return response_json
    except requests.exceptions.RequestException as e:
        logger.error("Error calling protected API: %s", e, exc_info=True)
        raise


def get_jwt_token(srvc_url, srvc_payload, headers):
    """Fetch JWT token using the provided authentication payload."""

    response = requests.post(srvc_url, json=srvc_payload, headers=headers)
    response.raise_for_status()
    token_data = response.json()

    return token_data["access_token"]


def check_and_refresh_token(jwt_token):
    """Check if a JWT token has expired and refresh it using get_jwt_token if necessary.

    Note: Signature verification is configurable via the JWT_VERIFY_SIGNATURE setting.
    For internal service-to-service communication, signature verification may be
    disabled for performance, but should be enabled in production for security.
    """
    config = get_config()

    try:
        # Decode the token with configurable signature verification
        decoded_token = jwt.decode(
            jwt_token,
            options={"verify_signature": config.security.jwt_verify_signature}
        )

        # Extract expiration time (exp claim)
        expiration_time = decoded_token.get("exp")

        if not expiration_time:
            raise ValueError("Expiration time ('exp') claim not found in the token.")

        # Compare the current time with the expiration time
        current_time = time.time()

        if current_time > expiration_time:
            # Token is expired; fetch a new one
            logger.info("Token has expired. Fetching a new token...")
            caching_srvc_login_url = os.environ.get("caching_srvc_login_url")
            caching_srvc_payload = {
                "client_id": "rollama",
                "api_key": os.environ.get("caching_srvc_secret"),
                "grant_type": "client_credentials",
            }
            caching_srvc_headers = {"Content-Type": "application/json"}
            return get_jwt_token(caching_srvc_login_url, caching_srvc_payload, caching_srvc_headers)

        # Token is still valid
        return jwt_token

    except jwt.InvalidTokenError as e:
        logger.error("Invalid JWT token: %s", e)
        raise ValueError("Invalid JWT token.") from e
