from typing import List

from app.model.db.db_base import execute_sql_query, fetch_sql_query, load_database, execute_sql_query_and_get_id

def insert_menu_tool(
    tool_id: int, 
    response_primer_before: str, 
    response_primer_after: str, 
    filter_primer_before: str, 
    filter_primer_after: str, 
    category_name: str, 
    instance_tool_id: int  # new parameter here
):
    # load the database
    db = load_database()
    cursor = db.cursor()

    # SQL insert statement
    insert_query = '''INSERT INTO menu_tool
                    (response_primer_before, 
                    response_primer_after, 
                    filter_primer_before, 
                    filter_primer_after, 
                    category_name,
                    instance_tool_id)  # make sure your database schema supports this field
                    VALUES (%s, %s, %s, %s, %s, %s);'''  # include it in the VALUES list

    # execute the SQL insert statement
    cursor.execute(insert_query, (response_primer_before, 
                                  response_primer_after, 
                                  filter_primer_before, 
                                  filter_primer_after, 
                                  category_name,
                                  instance_tool_id))  # add the new parameter here

    # get the last inserted id
    menu_tool_id = cursor.lastrowid

    # commit the transaction
    db.commit()

    return menu_tool_id


if __name__ == "__main__":
    # Test parameters for insert_menu_tool
    tool_id = 1
    response_primer_before = "Test Before"
    response_primer_after = "Test After"
    filter_primer_before = "Test Filter Before"
    filter_primer_after = "Test Filter After"
    category_name = "Test Category"
    instance_tool_id = 100

    # Call function
    menu_tool_id = insert_menu_tool(
        tool_id,
        response_primer_before,
        response_primer_after,
        filter_primer_before,
        filter_primer_after,
        category_name,
        instance_tool_id
    )

    print(f"New menu tool has been inserted with the ID: {menu_tool_id}")
