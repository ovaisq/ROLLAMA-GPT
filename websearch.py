#!/usr/bin/env python3
# ©2024, Ovais Quraishi
"""duckduckgo websearch functions for LLM function calling
"""

import json
import logging
from datetime import datetime
from duckduckgo_search import DDGS

from database import insert_data_into_table

def store_websearch_results(source, post_id, lookup_text, list_of_dicts):
    """Takes a source name, a prefix for the post ID, a lookup text, and a list of dictionaries.
		For each dictionary in the list, it creates a new dictionary with 'source', 'post_id',
		'lookup_text', and 'web_search_result' keys. The 'post_id'
		is supplied when called. Each new dictionary is then inserted into a PostgreSQL table.
    """

    for index, item in enumerate(list_of_dicts, start=1):  # Using start=1 to make post_id more human-readable
        # Convert the dictionary to a JSON string and then parse it back into a new dictionary
        web_search_result = json.loads(json.dumps(item))

        data = {
            'source': source,
            'post_id': post_id,
            'lookup_text': lookup_text,
            'websearch_result': json.dumps(web_search_result)
        }
        
        # Insert the data into the PostgreSQL table
        insert_data_into_table('websearch_results_ts', data)