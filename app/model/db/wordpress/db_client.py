from typing import Tuple
from app.model.db.db_base import execute_sql_query_and_get_id, fetch_sql_query


def insert_client_instance(client_id: int, instance_id: int, role: str, access_privilege: str) -> Tuple[int, bool]:
    insert_query = """
    INSERT INTO `client_instance` 
    (
        client_id, 
        instance_id, 
        role, 
        access_privilege
    ) 
    VALUES 
    (
        %s, %s, %s, %s
    ) 
    """

    data = (
        client_id,
        instance_id,
        role,
        access_privilege
    )

    result = execute_sql_query_and_get_id(insert_query, data)

    if result is None:
        print("Database does not support returning the ID of the inserted row.")
        return None, False
    else:
        print(f"The new record has been inserted with the ID {result}.")
        return result, True


# app\model\db\wordpress\db_client.py
def get_all_instances_for_client(client_id: int):
    query = """
    SELECT 
      client_instance.instance_id, 
      instance.type AS instance_type, 
      instance.status AS instance_status,  # New field for the instance status
      location_tool.name AS location_name, 
      instance_tool.id AS instance_tool_id,
      tool.id AS tool_id,  
      tool.type AS tool_type,  
      instance_tool.status,
      instance_tool.status_details
    FROM 
      client_instance
    JOIN 
      instance ON client_instance.instance_id = instance.id
    JOIN 
      location_tool ON client_instance.instance_id = location_tool.instance_id
    JOIN
      instance_tool ON instance_tool.instance_id = instance.id
    JOIN
      tool ON instance_tool.tool_id = tool.id  
    WHERE 
      client_instance.client_id = %s
    """

    result = fetch_sql_query(query, (client_id,))
    if result is None:
        return []
    else:
        return result  # app\model\db\wordpress\db_client.py


def get_all_instance_tools_for_client(client_id: int):
    query = """
    SELECT 
      client_instance.instance_id, 
      instance.type AS instance_type, 
      instance.status AS instance_status,  # New field for the instance status
      location_tool.name AS location_name, 
      instance_tool.id AS instance_tool_id,
      tool.id AS tool_id,  
      tool.type AS tool_type,  
      instance_tool.status,
      instance_tool.status_details
    FROM 
      client_instance
    JOIN 
      instance ON client_instance.instance_id = instance.id
    JOIN 
      location_tool ON client_instance.instance_id = location_tool.instance_id
    JOIN
      instance_tool ON instance_tool.instance_id = instance.id
    JOIN
      tool ON instance_tool.tool_id = tool.id  
    WHERE 
      client_instance.client_id = %s
    """

    result = fetch_sql_query(query, (client_id,))
    if result is None:
        return []
    else:
        return result


def get_all_instance_for_client(client_id: int):
    query = """
    SELECT 
      instance_id 
    FROM 
      client_instance
    WHERE 
      client_instance.client_id = %s
    """

    result = fetch_sql_query(query, (client_id,))
    if result is None:
        return []
    else:
        return [item[0] for item in result]


def main():
    # Test insert_client_instance function
    client_id = 1  # replace with actual client_id
    instance_id = 1  # replace with actual instance_id
    role = "test_role"  # replace with actual role
    access_privilege = "test_privilege"  # replace with actual access_privilege
    insert_result, insert_success = insert_client_instance(client_id, instance_id, role, access_privilege)
    if insert_success:
        print(f"The record was successfully inserted with ID {insert_result}")
    else:
        print("An error occurred while inserting the record.")

    # Test get_all_instances_for_client function
    client_id = 1  # replace with actual client_id
    instances = get_all_instance_tools_for_client(client_id)
    if instances:
        print("Retrieved the following instances for the client:")
        for instance in instances:
            print(instance)
    else:
        print("No instances found for the client.")


if __name__ == "__main__":
    print(get_all_instance_for_client(4))
