from app.model.db.db_base import fetch_sql_query


def get_instance_id_of_menu_tool(menu_tool_id: int):
    select_query = """
    SELECT lt.* 
    FROM menu_tool lt
    JOIN instance_tool it ON lt.tool_id = it.tool_id
    JOIN client_instance ci ON it.instance_id = ci.instance_id
    WHERE ci.client_id = %s
    """
    result = fetch_sql_query(select_query, (client_id,))
    return result
