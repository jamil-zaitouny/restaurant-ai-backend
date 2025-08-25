from datetime import datetime

import pytz

from app.model.db.db_base import fetch_sql_query


def get_current_time_in_tz(instance_id):
    tz = pytz.timezone(get_timezone_from_instance_id(instance_id))
    dt = datetime.now(tz)

    # Get the adjusted day of the week, date, and time
    day_of_week = dt.strftime('%A')  # e.g., Monday
    date = dt.strftime('%Y-%m-%d')  # e.g., 2023-06-24
    time = dt.strftime('%H:%M:%S')  # e.g., 13:55:26

    return f"{day_of_week}, {date}, {time}"


def get_timezone_from_instance_id(instance_id: int):
    select_query = """
     SELECT lt.timezone 
     FROM location_tool lt
     WHERE lt.instance_id = %s    
     """
    result = fetch_sql_query(select_query, (instance_id,))
    return result[0][0]
