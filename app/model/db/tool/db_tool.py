from typing import Tuple

from app.model.db.db_base import fetch_sql_query, execute_sql_query, execute_sql_query_and_get_id


def get_type_from_tool_id(tool_id):
    query = "SELECT type FROM tool WHERE id = %s"
    params = (tool_id,)
    result = fetch_sql_query(query, params)

    if result:
        return result[0][0]
    else:
        print(f"No matching records found for tool_id: {tool_id}")
        return None


def get_tool_by_id(tool_id: int) -> Tuple[int, str, str, str]:
    select_query = """
    SELECT id, name, description, type
    FROM tool
    WHERE id = %s
    """

    data = (tool_id,)
    result = fetch_sql_query(select_query, data)  # Changed from execute_sql_query to fetch_sql_query

    if result:
        return result[0][0], result[0][1], result[0][2], result[0][3]
    else:
        return None, None, None, None


def insert_tool(name: str, description: str) -> Tuple[int, bool]:
    insert_query = """
    INSERT INTO `tool` 
    (
        name, 
        description
    ) 
    VALUES 
    (
        %s, %s
    ) 
    """

    data = (
        name,
        description
    )
    result = execute_sql_query_and_get_id(insert_query, data)

    if result is None:
        print("Database does not support returning the ID of the inserted row.")
        return None, False
    else:
        print(f"The new record has been inserted with the ID {result}.")
        return result, True


if __name__ == "__main__":
    tool_id = 3
    id, name, description, _ = get_tool_by_id(tool_id)

    if id is not None:
        print(f"Tool ID: {id}, Name: {name}, Description: {description}")
    else:
        print("No tool found with the given ID.")
