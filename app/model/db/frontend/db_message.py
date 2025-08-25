from datetime import datetime
from uuid import uuid4

from app.model.db.db_base import execute_sql_query, update_sql_query


def insert_message(conversation_id: str ):
    id = str(uuid4())[:16]
    insert_query = "INSERT INTO `message` (id, conversation_id) " \
                   "VALUES (%s, %s) "
    data = (id, conversation_id.encode())
    execute_sql_query(insert_query, data)
    return id


def update_message(uuid: str, content: str, request_timestamp: datetime, response_timestamp: datetime,
                   conversation_id: str, additional: str = None):
    duration = (response_timestamp - request_timestamp).total_seconds()
    update_query = "UPDATE `message` SET content = %s, request_timestamp = %s, response_timestamp = %s, duration = %s, additional = %s, conversation_id = %s " \
                   "WHERE id = %s"
    data = (content, request_timestamp, response_timestamp, duration, additional, conversation_id, uuid.encode())
    update_sql_query(update_query, data)
    return uuid


if __name__ == "__main__":
    # update test
    # update_message("1f356a8f-0cd0-4f", "Here's the fakeeee content of the message", datetime.now(), datetime.now())
    # insert test
    print(insert_message('44252eeb-02c8-4d'))
