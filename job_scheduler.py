#!/usr/bin/env python3
"""Schedule API polling from Reddit

    LICENSE: The 3-Clause BSD License - license.txt

    ©2024, Ovais Quraishi
"""

import json
import logging
import os
import time

import daemon
import requests
import schedule

from config import get_config
from shared.config import Config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Get configuration
get_config()


# Constants
LOGIN_HEADERS = {
    'Content-Type': 'application/json'
}


def get_auth_token():
    """Get authentication token from the API."""

    end_point = 'login'
    url = os.environ['ENDPOINT_URL'] + end_point
    svc_shared_secret = os.environ['SRVC_SHARED_SECRET']
    auth_data = {
        'api_key': svc_shared_secret
    }

    # Get SSL verification setting from config
    config = get_config()
    if isinstance(config, Config):
        verify_ssl = config.security.ssl_verify
    else:
        verify_ssl = os.environ.get('SSL_VERIFY', 'true').lower() == 'true'

    response = requests.post(
        url,
        headers=LOGIN_HEADERS,
        json=auth_data,  # Use json parameter instead of data=json.dumps()
        verify=verify_ssl
    )
    response.raise_for_status()
    response_json = response.json()
    return response_json.get('access_token')


def do_get(end_point):
    """Make a GET request to the API endpoint."""

    url = os.environ['ENDPOINT_URL'] + end_point
    auth_token = get_auth_token()
    headers = {
        'Authorization': f'Bearer {auth_token}'
    }

    # Get SSL verification setting from config
    config = get_config()
    if isinstance(config, Config):
        verify_ssl = config.security.ssl_verify
    else:
        verify_ssl = os.environ.get('SSL_VERIFY', 'true').lower() == 'true'

    response = requests.get(url, headers=headers, verify=verify_ssl)
    response.raise_for_status()
    return response.json()


# Tasks setup
def get_authors_comments():
    """Get all comments of all authors listed in the author table."""
    logger.info("Get all comments of all authors listed in the author table")
    do_get('get_authors_comments')


def join_new_subs():
    """Join new subreddits listed in the subscription table."""
    logger.info("Join new subreddits listed in the subscription table")


def get_sub_posts():
    """Get all submissions from a subreddit."""
    logger.info("Get all submissions from a subreddit")


# Task scheduling
# After every 5 to 10mins in between run get_sub_posts()
schedule.every(5).to(10).minutes.do(get_sub_posts)

# Every monday join_new_subs() is called
schedule.every().monday.do(join_new_subs)

# Every tuesday at 18:00 get_authors_comments() is called
schedule.every().tuesday.at("18:00").do(get_authors_comments)


def main():
    """Main loop for the scheduler daemon."""
    # Loop so that the scheduling task keeps on running
    while True:
        # Checks whether a scheduled task is pending to run or not
        schedule.run_pending()
        time.sleep(2)


if __name__ == '__main__':
    with daemon.DaemonContext():
        main()
