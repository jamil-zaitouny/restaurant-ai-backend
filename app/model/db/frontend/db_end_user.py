from datetime import datetime

from app.model.db.db_base import execute_sql_query


def insert_end_user(end_user_id: str, ip_address: str):
    insert_query = "INSERT INTO `end_user` (id, end_user_ip, create_time) VALUES (%s, %s, %s) "
    data = (end_user_id, ip_address, str(datetime.now()))
    execute_sql_query(insert_query, data)


if __name__ == "__main__":
    insert_end_user("1", "8.8.8.8")
