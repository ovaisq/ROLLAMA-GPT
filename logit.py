# logit.py
# ©2024, Ovais Quraishi

import datetime
import os
import json
import logging
import re
import socket
from pathlib import Path


def _get_insert_function():
    """Lazy import to avoid circular dependency."""
    from shared.database.queries import insert_data_into_table
    return insert_data_into_table


def log_message_to_db(program_name, program_version, severity, log_message):
    """Log a message to the database.

        Args:
            host_name (str): The name of the host where the program is running.
            program_name (str): The name of the program that generated the log.
            severity (str): The severity level of the log.
            log_message (str): The actual content of the log.

        Returns:
            None

        Notes:
            This function assumes that 'rollamalogs' table exists in the database with required columns.
    """
    
    ts_now = datetime.datetime.now(tz=datetime.timezone.utc).isoformat(timespec='seconds', sep=' ')
    
    
    # Define a dictionary with placeholder values
    log_data = {
                'timestamp': ts_now,
                'host': socket.gethostname(),
                'program_name': program_name,
                'program_version' : program_version,
                'severity': severity,
                'message': log_message
               }

    # payload for database
    data = {
            'timestamp' : ts_now,
            'log_json' : json.dumps(log_data)
           }
    
    # insert data into table
    insert_fn = _get_insert_function()
    insert_fn('rollamalogs', data)

def get_rollama_version():
    """Reads the first line from /usr/local/rollama/ver.txt,
        checks if it matches semver (0.1.2) format and returns it.

        Returns:
            str: The version string if valid, otherwise False.
    """

    ver_file_path = '/usr/local/rollama/ver.txt'
    ver_file_path = 'ver.txt'

    try:
        with open(str(Path(ver_file_path).resolve()), 'r') as f:
            first_line = f.readline().strip()
    except FileNotFoundError:
        log_message = f"File {ver_file_path} not found."
        logging.error(log_message)
        return False

    semver_pattern = r'^\d+\.\d+\.\d+$'

    if re.match(semver_pattern, first_line):
        return {"version":first_line}
    else:
        log_message = "Invalid version format. Expected semver (0.1.2)."
        logging.error(log_message)
        return False
