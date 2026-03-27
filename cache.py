#!/usr/bin/env python3
# cache.py
# ©2024, Ovais Quraishi

"""Cache client"""

import os
import logging
import redis

# Import required local modules
import logit
from config import get_config
import external
from shared.constants import CACHE_EXPIRE_SECONDS

get_config()


def redis_client() -> redis.StrictRedis:
    """Configure and return a Redis client instance."""

    host = os.environ["redis_host"]
    port = os.environ["redis_port"]
    password = os.environ["redis_password"]

    return redis.StrictRedis(host=host, port=port, password=password)


def add_key(key):
    """Add a key to a set in redis"""

    caching_srvc_crud_url = os.environ["caching_srvc_crud_url"]

    if lookup_key(key):
        info_message = f"{key} already exists"
        logging.info(info_message)
        logit.log_message_to_db(
            os.environ["SRVC_NAME"],
            logit.get_rollama_version()["version"],
            "INFO",
            info_message,
        )
        return False
    else:
        data_payload = {
            "command": "WRITE",
            "key": key,
            "value": "",
            "expire": CACHE_EXPIRE_SECONDS,
        }
        json_resp = external.cache_api(caching_srvc_crud_url, payload=data_payload)
        if json_resp["status"] == "SUCCESS":
            info_message = f"{key} added"
            logging.info(info_message)
            logit.log_message_to_db(
                os.environ["SRVC_NAME"],
                logit.get_rollama_version()["version"],
                "INFO",
                info_message,
            )
            return True
    return False


def lookup_key(key):
    """Look up if a key exists"""

    caching_srvc_crud_url = os.environ["caching_srvc_crud_url"]

    data_payload = {"command": "READ", "key": key}
    json_resp = external.cache_api(caching_srvc_crud_url, payload=data_payload)
    if json_resp["status"] == "SUCCESS":
        return True
    return False


def check_and_increment(key):
    """Checks an integer value of a specified Redis key. If the value is less than or equal to 1000,
        increment it by one and return True. If the resulting value is greater than 1000, then
        return False.

        return: True if the incremented value is <= 1000, otherwise False.
    """

    try:
        # Use a Lua script for atomic operation
        lua_script = """
        local current_value = tonumber(redis.call('GET', KEYS[1]))

        if current_value == nil then
            current_value = 0 -- Default to 0 if the key doesn't exist or is not an integer
        end

        if current_value == 10 then
            redis.call('SET', KEYS[1], 0)
            current_value = 0
            return false
        end

        if current_value <= 10 then
            redis.call('INCRBY', KEYS[1], 1)
            return (current_value + 1) <= 10
        else
            return false
        end
        """

        # Run the Lua script with the specified key
        result = redis_client().eval(lua_script, 1, key)
        return bool(result)

    except Exception as e:
        logging.error("An error occurred in check_and_increment: %s", e, exc_info=True)
        return False


def get_set_contents(set_name):
    """Get contents of a redis keys as a list"""

    # now use keys instead of sets
    byte_list = list(redis_client().scan_iter(set_name + "*"))
    string_list = [y.decode("utf-8") for y in byte_list]  # bytes to string

    # update list with just the ids
    for index, value in enumerate(string_list):
        if set_name in value:
            string_list[index] = value.replace(set_name + "_", "")
    return string_list
