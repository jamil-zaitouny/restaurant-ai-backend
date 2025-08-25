from app.model.db.db_base import execute_sql_query, fetch_sql_query, load_database
from app.model.db.wordpress.db_tool import insert_tool
from typing import Tuple, Optional
from app.model.db.db_base import execute_sql_query, execute_sql_query_and_get_id

from typing import Tuple, Optional
from app.model.db.db_base import execute_sql_query, execute_sql_query_and_get_id, fetch_sql_query


def insert_or_update_location_tool(
        name: str,
        description: str,
        address: str,
        phone_number: str,
        website: str,
        facebook_link: str,
        twitter_link: str,
        instagram_link: str,
        average_price_range: str,
        longitude: str,
        latitude: str,
        status: str,
        timezone: str,
        order_links: str,
        reservation_links: str,
        instance_tool_id: int,
        instance_id: int,
        location_tool_id: Optional[int] = None,
        provided_instance_id: Optional[int] = None
) -> Tuple[int, bool]:
    if location_tool_id or provided_instance_id:
        # Update existing location_tool record
        update_query = """
        UPDATE `location_tool`
        SET
            name=%s,
            description=%s,
            address=%s,
            phone_number=%s,
            website=%s,
            facebook_link=%s,
            twitter_link=%s,
            instagram_link=%s,
            average_price_range=%s,
            longitude=%s,
            latitude=%s,
            status=%s,
            timezone=%s,
            order_links=%s,
            reservation_links=%s
        WHERE
            id=%s OR instance_id=%s
        """

        data = (
            name,
            description,
            address,
            phone_number,
            website,
            facebook_link,
            twitter_link,
            instagram_link,
            average_price_range,
            longitude,
            latitude,
            status,
            timezone,
            order_links,
            reservation_links,
            location_tool_id,
            provided_instance_id
        )
        execute_sql_query(update_query, data)
        return location_tool_id or provided_instance_id, True
    else:
        # Insert new location_tool record
        insert_query = """
        INSERT INTO `location_tool`
        (
            name,
            description,
            address,
            phone_number,
            website,
            facebook_link,
            twitter_link,
            instagram_link,
            average_price_range,
            longitude,
            latitude,
            status,
            timezone,
            order_links,
            reservation_links,
            instance_tool_id,
            instance_id
        )
        VALUES
        (
            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
        )
        """

        data = (
            name,
            description,
            address,
            phone_number,
            website,
            facebook_link,
            twitter_link,
            instagram_link,
            average_price_range,
            longitude,
            latitude,
            status,
            timezone,
            order_links,
            reservation_links,
            instance_tool_id,
            instance_id
        )
        result = execute_sql_query_and_get_id(insert_query, data)

        if result is None:
            print("Database does not support returning the ID of the inserted row.")
            return None, False
        else:
            print(f"The new record has been inserted with the ID {result}.")
            return result, True


def get_instance_id_from_location_tool(location_tool_id):
    connection = load_database()
    cursor = connection.cursor()

    tool_id_query = f"SELECT tool_id FROM location_tool WHERE id = {location_tool_id};"
    cursor.execute(tool_id_query)
    tool_id_result = cursor.fetchall()
    print(f"tool_id_result: {tool_id_result}")  # New print statement

    if tool_id_result:  # New condition check
        tool_id = tool_id_result[0][0]  # Assuming the query will return a list of tuples
    else:
        print("tool_id_result was empty.")  # New print statement
        return None  # Or raise an exception, etc.

    instance_id_query = f"SELECT instance_id FROM instance_tool WHERE tool_id = {tool_id};"
    cursor.execute(instance_id_query)
    instance_id_result = cursor.fetchall()
    print(f"instance_id_result: {instance_id_result}")  # New print statement

    if instance_id_result:  # New condition check
        instance_id = instance_id_result[0][0]  # Assuming the query will return a list of tuples
    else:
        print("instance_id_result was empty.")  # New print statement
        return None  # Or raise an exception, etc.

    return instance_id


def update_instance_associated_with_location_tool(location_tool_id, agent_prompt_before, agent_prompt_after, status):
    # Load database connection
    conn = load_database()

    if conn is not None:
        cursor = conn.cursor()

        # Get the tool_id associated with the location_tool_id from the location_tool table
        query_tool_id = "SELECT tool_id FROM location_tool WHERE id = %s"
        cursor.execute(query_tool_id, (location_tool_id,))
        tool_id = cursor.fetchone()[0]

        # Get the instance_id associated with the tool_id from the instance_tool table
        query_instance_id = "SELECT instance_id FROM instance_tool WHERE tool_id = %s"
        cursor.execute(query_instance_id, (tool_id,))
        instance_id = cursor.fetchone()[0]

        # Update agent_primer_before and agent_primer_after in the instance table
        update_instance_query = """
        UPDATE instance
        SET agent_primer_before = %s, agent_primer_after = %s, last_edited = NOW()
        WHERE id = %s
        """
        cursor.execute(update_instance_query, (agent_prompt_before, agent_prompt_after, instance_id))

        # Update status in the instance_tool table
        update_instance_tool_query = """
        UPDATE instance_tool
        SET status = %s
        WHERE instance_id = %s AND tool_id = %s
        """
        cursor.execute(update_instance_tool_query, (status, instance_id, tool_id))

        # commit the transaction
        conn.commit()

        # close the cursor and connection
        cursor.close()
        conn.close()


def update_location_tool(location_tool_id, tools_status, agent_system_prompt_after, agent_system_prompt_before):
    update_instance_associated_with_location_tool(location_tool_id, agent_system_prompt_before,
                                                  agent_system_prompt_after, tools_status)


def get_all_location_tools_for_client(client_id: int):
    select_query = """
     SELECT lt.* 
     FROM location_tool lt
     JOIN instance_tool it ON lt.instance_tool_id = it.id
     JOIN client_instance ci ON it.instance_id = ci.instance_id
     WHERE ci.client_id = %s    
     """
    result = fetch_sql_query(select_query, (client_id,))
    return result


if __name__ == "__main__":
    # Sample data for a new location tool
    name = "Sample Restaurant"
    description = "A sample restaurant description"
    address = "123 Sample Street"
    phone_number = "555-1234"
    website = "https://www.sample-restaurant.com"
    facebook_link = "https://www.facebook.com/sample-restaurant"
    twitter_link = "https://www.twitter.com/sample-restaurant"
    instagram_link = "https://www.instagram.com/sample-restaurant"
    average_price_range = "10-20"
    longitude = "12.345678"
    latitude = "98.765432"
    status = "active"
    timezone = "UTC"
    agent_system_prompt_after = "Thank you for using our service."
    agent_system_prompt_before = "Welcome to our service."
    order_links = "https://www.sample-restaurant.com/order"
    reservation_links = "https://www.sample-restaurant.com/reservation"
    tool_id = 1  # Assuming the tool ID is 1
    instance_id = 1  # Assuming the instance ID is 1

    # Insert a new location tool
    location_tool_id, success = insert_or_update_location_tool(
        name, description, address, phone_number, website, facebook_link,
        twitter_link, instagram_link, average_price_range, longitude, latitude,
        status, timezone, agent_system_prompt_after, agent_system_prompt_before,
        order_links, reservation_links, tool_id, instance_id
    )

    if success:
        print(f"New location tool inserted with ID: {location_tool_id}")
    else:
        print("Failed to insert new location tool")

    # Update an existing location tool
    location_tool_id_to_update = 1  # Assuming the location tool ID to update is 1
    updated_name = "Updated Sample Restaurant"

    updated_location_tool_id, success = insert_or_update_location_tool(
        updated_name, description, address, phone_number, website, facebook_link,
        twitter_link, instagram_link, average_price_range, longitude, latitude,
        status, timezone, agent_system_prompt_after, agent_system_prompt_before,
        order_links, reservation_links, tool_id, instance_id,
        location_tool_id=location_tool_id_to_update
    )

    if success:
        print(f"Location tool with ID {location_tool_id_to_update} updated")
    else:
        print("Failed to update location tool")
