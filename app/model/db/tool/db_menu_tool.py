from app.model.db.db_base import fetch_sql_query


def get_menu_tool_primers(menu_tool_id):
    query = f"SELECT response_primer_before, response_primer_after FROM menu_tool WHERE id = %s"
    params = (menu_tool_id,)
    result = fetch_sql_query(query, params)

    if result:
        return result[0][0], result[0][1]
    else:
        print(f"No matching records found for tool_id: {menu_tool_id}")
        return None


def get_menu_tool_filters_from_instance_tool_id(instance_tool_id):
    query = "SELECT id, filter_primer_before, filter_primer_after FROM menu_tool WHERE instance_tool_id = %s"
    params = (instance_tool_id,)
    result = fetch_sql_query(query, params)

    if result:
        return result[0][0], result[0][1], result[0][2]
    else:
        print(f"No matching records found for tool_id: {instance_tool_id}")
        return None




def get_index_tool_filters_from_instance_tool_id(instance_tool_id):
    query = "SELECT id, filter_primer_before, filter_primer_after FROM index_tool WHERE " \
            "instance_tool_id = %s"
    params = (instance_tool_id,)
    result = fetch_sql_query(query, params)

    if result:
        return result[0][0], result[0][1], result[0][2]
    else:
        print(f"No matching records found for tool_id: {instance_tool_id}")
        return None

def get_index_tool_filters(index_tool_id):
    query = "SELECT response_primer_before, response_primer_after FROM index_tool WHERE " \
            "id = %s"
    params = (index_tool_id,)
    result = fetch_sql_query(query, params)

    if result:
        return result[0][0], result[0][1]
    else:
        print(f"No matching records found for tool_id: {index_tool_id}")
        return None


if __name__ == '__main__':
    print(get_menu_tool_filters_from_instance_tool_id(20))
