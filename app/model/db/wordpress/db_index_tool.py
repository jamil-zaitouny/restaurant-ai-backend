from app.model.db.db_base import load_database


def  insert_index_tool(
    response_primer_before: str,
    response_primer_after: str,
    filter_primer_before: str,
    filter_primer_after: str,
    site_index_name: str,
    instance_tool_id: int,
    summary_primer_before: str,
    summary_primer_after: str,
):
    # load the database
    db = load_database()
    cursor = db.cursor()

    # SQL insert statement
    insert_query = '''INSERT INTO index_tool
                    (response_primer_before, 
                    response_primer_after, 
                    filter_primer_before, 
                    filter_primer_after, 
                    site_index_name,
                    instance_tool_id,
                    summary_primer_before,
                    summary_primer_after)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s);'''  # include it in the VALUES list

    # execute the SQL insert statement
    cursor.execute(insert_query, (response_primer_before,
                                  response_primer_after,
                                  filter_primer_before,
                                  filter_primer_after,
                                  site_index_name,
                                  instance_tool_id,
                                  summary_primer_before,
                                  summary_primer_after))  # add the new parameter here

    # get the last inserted id
    index_tool_id = cursor.lastrowid

    # commit the transaction
    db.commit()

    return index_tool_id
