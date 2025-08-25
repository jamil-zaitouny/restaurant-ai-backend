from app.model.db.db_base import execute_sql_query, fetch_sql_query

def insert_category_item(menu_tool_id: int, row: dict):
    insert_query = f"""
    INSERT INTO `category_items`
    (
        menu_tool_id,
        llm_id,
        category,
        sub_category,
        image_url,
        url,
        location,
        contact_info,
        delivery_area,
        delivery_time,
        description,
        name,
        price,
        upgrades,
        tags,
        serving_size,
        calories,
        total_fat,
        saturated_fat,
        trans_fat,
        cholesterol,
        sodium,
        carbohydrate,
        dietary_fiber,
        sugars,
        protein
    )
    VALUES
    (
        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
    )
    """
    data = (
        menu_tool_id,
        row.get('llm_id', '').replace('\n', ''),
        row.get('category', '').replace('\n', ''),
        row.get('sub_category', '').replace('\n', ''),
        row.get('image_url', '').replace('\n', ''),
        row.get('url', '').replace('\n', ''),
        '',  # Default value for location
        '',  # Default value for contact_info
        '',  # Default value for delivery_area
        '',  # Default value for delivery_time
        row.get('description', '').replace('\n', ''),
        row.get('name', '').replace('\n', ''),
        row.get('price', '').replace('\n', ''),
        row.get('upgrades', '').replace('\n', ''),
        row.get('tags', '').replace('\n', ''),
        row.get('serving_size', '').replace('\n', ''),
        row.get('calories', '').replace('\n', ''),
        row.get('total_fat', '').replace('\n', ''),
        row.get('saturated_fat', '').replace('\n', ''),
        row.get('trans_fat', '').replace('\n', ''),
        row.get('cholesterol', '').replace('\n', ''),
        row.get('sodium', '').replace('\n', ''),
        row.get('carbohydrate', '').replace('\n', ''),
        row.get('dietary_fiber', '').replace('\n', ''),
        row.get('sugars', '').replace('\n', ''),
        row.get('protein', '').replace('\n', '')
    )

    print(f"Inserting the following data: {data}")

    last_inserted_id = execute_sql_query(insert_query, data)

    # return the last inserted id
    return last_inserted_id




def get_all_menu_tools_for_tool(instance_id: int):
    select_query = """
    SELECT mt.response_primer_before, mt.response_primer_after, 
           mt.filter_primer_before, mt.filter_primer_after, mt.category_name, t.name, t.description
    FROM menu_tool mt
    JOIN tool t on mt.tool_id = t.id
    JOIN instance_tool it ON mt.tool_id = it.tool_id
    JOIN client_instance ci ON it.instance_id = ci.instance_id
    WHERE ci.instance_id = %s
    """

    result = fetch_sql_query(select_query, (instance_id,))
    return result


def insert_chunk_item(
        menu_tool_id: int,
        chunk: str
):
    insert_query = f"""
    INSERT INTO `chunk`
    (
        menu_tool_id,
        chunk_data
    )
    VALUES
    (
        %s, %s
    )
    """
    data = (
        menu_tool_id,
        chunk
    )
    execute_sql_query(insert_query, data)
