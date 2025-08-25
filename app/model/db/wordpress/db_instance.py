import sys

sys.path.insert(0, 'C:\\Own Your AI GIT\\SiteAI-Backend')
from typing import Tuple, Optional
from app.model.db.db_base import execute_sql_query, execute_sql_query_and_get_id, fetch_sql_query
from datetime import datetime


def insert_or_update_instance(type: str, status: str, description: str, tool_id: int,
                              agent_primer_before: str, agent_primer_after: str, llm_model: str,
                              menu_tool_id: Optional[int] = None,
                              location_tool_id: Optional[int] = None,
                              index_tool_id: Optional[int] = None,
                              instance_id: Optional[int] = None) -> Tuple[int, bool]:
    if instance_id is None:  # Insert a new instance
        query = """
        INSERT INTO `instance` 
        (
            type, 
            registration_date, 
            last_edited, 
            status, 
            description,
            agent_primer_before,
            agent_primer_after,
            llm_model
        ) 
        VALUES 
        (
            %s, %s, %s, %s, %s, %s, %s, %s
        ) 
        """

        data = (
            type,
            datetime.now(),
            datetime.now(),
            status,
            description,
            agent_primer_before,
            agent_primer_after,
            llm_model
        )

        result = execute_sql_query_and_get_id(query, data)

        if result is None:
            print("Database does not support returning the ID of the inserted row.")
            return None, False
        else:
            print(f"The new record has been inserted with the ID {result}.")
            # TODO is the bottom needed? FFS

            # link instance to menu tool
            if menu_tool_id is not None:
                link_instance_to_tool(result, 'filter_and_respond', menu_tool_id, tool_id)

            # link instance to location tool
            if location_tool_id is not None:
                link_instance_to_tool(result, 'single_call', location_tool_id, tool_id)

            # link instance to location tool
            if index_tool_id is not None:
                link_instance_to_tool(result, 'website_search', location_tool_id, tool_id)

            return result, True

    else:  # Update an existing instance
        query = """
        UPDATE `instance` 
        SET 
            type = %s, 
            last_edited = %s, 
            status = %s, 
            description = %s
        WHERE
            id = %s
        """

        data = (
            type,
            datetime.now(),
            status,
            description,
            instance_id
        )

        result = execute_sql_query(query, data)

        if result is None:
            print("Failed to update the instance.")
            return None, False
        else:
            print(f"The record with the ID {instance_id} has been updated.")

            # Update the tool connection
            # For simplicity, we're assuming that an instance can only be linked to one menu tool or location tool
            if menu_tool_id is not None:
                update_instance_tool_link(instance_id, 'menu_tool', menu_tool_id)

            if location_tool_id is not None:
                update_instance_tool_link(instance_id, 'location_tool', location_tool_id)

            return instance_id, True


""""
    instance
"""


def link_instance_to_tool(instance_id: int, tool_type: str, tool_type_id: int, tool_id: int):
    # Verify if tool_type exists in the tool table
    verify_query = f"""
    SELECT id 
    FROM tool
    WHERE id = %s and type = %s
    """
    result = fetch_sql_query(verify_query, (tool_id, tool_type,))
    if not result:
        print(f"Tool with type {tool_type} not found in tool table with id {tool_type_id}")
        return

    link_query = """
    INSERT INTO `instance_tool` 
    (
        instance_id, 
        tool_id
    ) 
    VALUES 
    (
        %s, 
        %s
    )
    """
    data = (instance_id, tool_type_id)
    execute_sql_query(link_query, data)


def update_instance_tool_link(instance_id: int, tool_type: str, tool_id: int):
    # Verify if tool_type exists in the tool table
    verify_query = """
    SELECT id 
    FROM tool
    WHERE type = %s AND id = %s
    """
    result = fetch_sql_query(verify_query, (tool_type, tool_id))
    if not result:
        print(f"Tool with type {tool_type} not found in tool table with id {tool_id}")
        return

    update_query = """
    UPDATE `instance_tool`
    SET tool_id = %s
    WHERE instance_id = %s
    """
    data = (tool_id, instance_id)
    execute_sql_query(update_query, data)

def get_instance_id(instance_id: int):
    select_query = """
    SELECT status
    FROM instance
    WHERE id = %s
    """
    result = fetch_sql_query(select_query, (instance_id,))[0][0]
    return result


if __name__ == "__main__":
    type = "filter_and_respond"
    status = "status"
    description = "description"
    tool_id = 1
    type_tool_id = 18

    id, success = insert_or_update_instance(type, status, description, tool_id, menu_tool_id=type_tool_id)

    if not success:
        print("You will have to manually retrieve the ID.")
