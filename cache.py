#!/usr/bin/env python3
# cache.py
# ©2024, Ovais Quraishi

import logging
import json
import os
import redis

# Import required local modules
from config import get_config
import logit

# constants
get_config()

# connect to your Redis instance
r = redis.Redis(host=os.environ['redis_host'],
                port=os.environ['redis_port'],
                password=os.environ['redis_password']
               )

def ping_redis():
    """Check if Redis connection is available"""
    
    try:
        r.ping()
    except Exception as e:
        error_message = f"Redis connection failed: {e}"
        logging.error(error_message)
        logit.log_message_to_db(os.environ['SRVC_NAME'], logit.get_rollama_version()['version'], 'ERROR', error_message)
        return False
    
def add_key(setname, key):
    """Add a key to a set in redis"""

    if lookup_key(setname, key):
        info_message = f'{setname}:{key} already exists'
        logging.info(info_message)
        logit.log_message_to_db(os.environ['SRVC_NAME'], logit.get_rollama_version()['version'], 'INFO', info_message)
        return False
    else:
        r.sadd(setname, key)
        info_message = f'{setname}:{key} added'
        logging.info(info_message)
        logit.log_message_to_db(os.environ['SRVC_NAME'], logit.get_rollama_version()['version'], 'INFO', info_message)
        return True

def lookup_key(setname, key):
    """Look up if a key exists in the set"""
    try:
        result = r.sismember(setname, key)
        return result
    except redis.exceptions.DataError as e:
        logging.error(e)
        logit.log_message_to_db(os.environ['SRVC_NAME'], logit.get_rollama_version()['version'], 'ERROR', {'error':str(e)})

def get_set_contents(set_name):
    """Get contents of a redis set as a list"""

    return list(r.smembers(set_name))