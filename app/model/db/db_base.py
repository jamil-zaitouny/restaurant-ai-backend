import os
import mysql.connector
from mysql.connector import Error
from dotenv import load_dotenv


def load_database():
    try:
        load_dotenv()

        connection = mysql.connector.connect(
            host=os.getenv('DB_HOST'),
            user=os.getenv('DB_USER'),
            password=os.getenv('DB_PASSWORD'),
            database=os.getenv('DB_DATABASE'),
            port=os.getenv('DB_PORT')
        )
        if connection.is_connected():
            return connection
    except Error as e:
        print("Error while connecting to MySQL", e)

    return None


def execute_sql_query(query, data):
    connection = load_database()
    cursor = connection.cursor()

    cursor.execute(query, data)
    connection.commit()

    last_inserted_id = cursor.lastrowid

    cursor.close()
    connection.close()

    return last_inserted_id


def fetch_sql_query(query, params=None):
    connection = load_database()
    if connection is None:
        print("Failed to connect to database.")
        return None

    cursor = connection.cursor()

    cursor.execute(query, params)
    result = cursor.fetchall()

    cursor.close()
    connection.close()

    return result


def fetch_sql_query_and_key(query, params=None):
    connection = load_database()
    if connection is None:
        print("Failed to connect to database.")
        return None

    cursor = connection.cursor()

    cursor.execute(query, params)
    result = cursor.fetchall()

    # Fetch field names
    field_names = [desc[0] for desc in cursor.description]

    # Transform the result to a dictionary where each value is a dictionary itself
    dict_result = {row[0]: {field_name: value for field_name, value in zip(field_names[1:], row[1:])} for row in result}

    cursor.close()
    connection.close()

    return dict_result


def execute_sql_query_and_get_id(query, data):
    connection = load_database()
    cursor = connection.cursor()

    cursor.execute(query, data)
    connection.commit()

    lastrowid = cursor.lastrowid

    cursor.close()
    connection.close()

    return lastrowid

def update_sql_query(query, data):
    connection = load_database()
    cursor = connection.cursor()

    cursor.execute(query, data)
    connection.commit()

    affected_rows = cursor.rowcount

    cursor.close()
    connection.close()

    return affected_rows
