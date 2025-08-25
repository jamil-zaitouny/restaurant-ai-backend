from typing import Tuple
from app.model.db.db_base import execute_sql_query, execute_sql_query_and_get_id


def insert_tool(name: str, description: str) -> Tuple[int, bool]:
    insert_query = """
    INSERT INTO `tool` 
    (
        name, 
        description,
        type
    ) 
    VALUES 
    (
        %s, %s, %s
    ) 
    """

    data = (
        name,
        description,
        "default_type"  # Set the default value for the 'type' field here
    )
    result = execute_sql_query_and_get_id(insert_query, data)

    if result is None:
        print("Database does not support returning the ID of the inserted row.")
        return None, False
    else:
        print(f"The new record has been inserted with the ID {result}.")
        return result, True


if __name__ == "__main__":
    name = "name"
    description = "description"
    id, success = insert_tool(name, description)

    if not success:
        print("You will have to manually retrieve the ID.")
