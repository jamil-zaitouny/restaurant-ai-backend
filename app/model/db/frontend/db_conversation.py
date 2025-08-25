from uuid import uuid4

from app.model.db.db_base import execute_sql_query
import binascii

# Convert UUID to binary string
def uuid_to_bin_str(uuid_string):
    return binascii.unhexlify(uuid_string.replace('-', ''))

def insert_conversation(end_user_id: str, instance_id: int):
    id = str(uuid4())[:16]
    insert_query = "INSERT INTO `conversation` (id, end_user_id, instance_id) " \
                   "VALUES (%s, %s, %s) "
    data = (str(id), end_user_id, instance_id)
    execute_sql_query(insert_query, data)
    return str(id)