# File: db_helpers.py
# ...
# Other database helper methods
import json

from app.model.db.db_base import execute_sql_query_and_get_id


def insert_into_index_tool(instance_tool_id, response_primer_before, response_primer_after, filter_primer_before,
                           filter_primer_after, site_index_name):
    query = "INSERT INTO index_tool (instance_tool_id, response_primer_before, response_primer_after, filter_primer_before, filter_primer_after, site_index_name) VALUES (%s, %s, %s, %s, %s, %s)"
    data = (instance_tool_id, response_primer_before, response_primer_after, filter_primer_before, filter_primer_after,
            site_index_name)
    return execute_sql_query_and_get_id(query, data)


def insert_into_site_index(index_tool_id, llmid, url, status_code, crawltime, updatetime, page_type, category,
                           image_url, description, wordcount, pagetitle, content, summary, structured_data):
    query = "INSERT INTO site_index (index_tool_id, llmid, url, status_code, crawltime, updatetime, page_type, category, image_url, description, wordcount, pagetitle, content, summary, structured_data) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
    data = (index_tool_id, llmid, url, status_code, crawltime, updatetime, page_type, category, image_url, description,
            wordcount, pagetitle, content, summary, json.dumps(structured_data))
    return execute_sql_query_and_get_id(query, data)
# ...
# Other database helper methods
