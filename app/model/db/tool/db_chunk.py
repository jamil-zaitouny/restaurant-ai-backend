from app.model.db.db_base import fetch_sql_query


def get_chunks_by_menu_tool_id(menu_tool_id):
    query = "SELECT * FROM chunk WHERE menu_tool_id = %s"
    params = (menu_tool_id,)

    result = fetch_sql_query(query, params)

    return result
