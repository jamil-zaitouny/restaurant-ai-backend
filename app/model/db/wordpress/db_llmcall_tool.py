from app.model.db.db_base import fetch_sql_query, execute_sql_query_and_get_id


def get_llmcall_tool_filters_from_instance_tool_id(instance_tool_id):
    query = "SELECT id, response_primer_before, response_primer_after, context FROM llmcall_tool WHERE " \
            "instance_tool_id = %s"
    params = (instance_tool_id,)
    result = fetch_sql_query(query, params)

    if result:
        return result[0][0], result[0][1], result[0][2], result[0][3]
    else:
        print(f"No matching records found for tool_id: {instance_tool_id}")
        return None

def get_llmcall_tool_filters(llmcall_tool_id):
    query = "SELECT id, response_primer_before, response_primer_after, context FROM llmcall_tool WHERE " \
            "id = %s"
    params = (llmcall_tool_id,)
    result = fetch_sql_query(query, params)

    if result:
        return result[0][0], result[0][1], result[0][2], result[0][3]
    else:
        print(f"No matching records found for tool_id: {llmcall_tool_id}")
        return None

def insert_llm_call_tool(response_primer_before, response_primer_after, context, instance_tool_id):
    insert_query = """
    INSERT INTO `llmcall_tool` 
    (
        response_primer_before, 
        response_primer_after, 
        context, 
        instance_tool_id
    ) 
    VALUES 
    (
        %s, %s, %s, %s
    ) 
    """
    data = (
        response_primer_before,
        response_primer_after,
        context,
        instance_tool_id
    )

    return execute_sql_query_and_get_id(insert_query, data)
