import sys
import os
from typing import Tuple, Optional

# Navigate two levels up to get to the project root
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../'))
# Add the project root to sys.path
sys.path.insert(0, project_root)

# Now Python knows where to look for the 'app' module
from app.model.db.db_base import execute_sql_query, execute_sql_query_and_get_id, fetch_sql_query


# The rest of your code...

def insert_or_update_instance_tool(instance_id: int, tool_id: int, agent_prompt_title: str,
                                   agent_prompt_description: str,
                                   status: bool, status_details: str, llm_model: str,
                                   return_direct: Optional[bool] = True,
                                   instance_tool_id: Optional[int] = None) -> Tuple[int, bool]:
    if instance_tool_id is None:  # Insert new instance_tool
        insert_query = """
        INSERT INTO `instance_tool` 
        (
            instance_id, 
            tool_id, 
            agent_prompt_title,
            agent_prompt_description, 
            status, 
            status_details,
            llm_model,
            return_direct
        ) 
        VALUES 
        (
            %s, %s, %s, %s, %s, %s, %s, %s
        ) 
        """

        data = (
            instance_id,
            tool_id,
            agent_prompt_title,
            agent_prompt_description,
            status,
            status_details,
            llm_model,
            return_direct
        )

        result = execute_sql_query_and_get_id(insert_query, data)

        if result is None:
            print("Database does not support returning the ID of the inserted row.")
            return None, False
        else:
            print(f"The new record has been inserted with the ID {result}.")
            return result, True
    else:  # Update an existing instance_tool
        update_query = """
        UPDATE `instance_tool`
        SET 
            tool_id = %s, 
            agent_prompt_title = %s,
            agent_prompt_description = %s, 
            status = %s, 
            status_details = %s
        WHERE 
            id = %s
        """

        data = (
            tool_id,
            agent_prompt_title,
            agent_prompt_description,
            status,
            status_details,
            instance_tool_id
        )

        result = execute_sql_query(update_query, data)

        if result is None:
            print("Failed to update the instance tool.")
            return None, False
        else:
            print(f"The record with the ID {instance_tool_id} has been updated.")
            return instance_tool_id, True


def get_instance_tools(instance_id):
    query = "SELECT tool_id, agent_prompt_description, agent_prompt_title, return_direct, status, llm_model, id FROM " \
            "instance_tool WHERE instance_id = %s "
    params = (instance_id,)

    result = fetch_sql_query(query, params)

    return result


if __name__ == "__main__":
    print(get_instance_tools(10))

'''
There are some anticipated inputs and outputs for the provided functions for your documentation:

insert_or_update_instance_tool:

Inputs:

instance_id: An integer representing the ID of the instance (e.g., 1)
tool_id: An integer representing the ID of the tool (e.g., 2)
agent_prompt_title: A string representing the title of the agent prompt (e.g., "Start Prompt")
agent_prompt_description: A string representing the description of the agent prompt (e.g., "This is a start prompt")
status: A boolean representing the status (e.g., True)
status_details: A string representing the status details (e.g., "Status OK")
instance_tool_id: An integer representing the ID of the instance tool (optional, e.g., 3)
Outputs:

Returns a tuple containing the ID of the newly inserted or updated record and a boolean indicating success or failure.
get_instance_tools:

Inputs:

instance_id: An integer representing the ID of the instance (e.g., 1)
Outputs:

Returns the result of the SQL query, which could be a list of tuples containing the details of all tools associated with the instance.
Note: The actual output for these functions can vary based on the SQL query results. The specific structure of the output will depend on your database schema and the data contained within it.

These functions also print status messages about the operations, but these are not returned by the functions





'''
