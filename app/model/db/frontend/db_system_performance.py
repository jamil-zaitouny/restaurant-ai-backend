from datetime import datetime

from app.model.db.db_base import execute_sql_query


def insert_system_performance(message_id: str, timestamp: str, response_time: int, status_code: str,
                              error_type: str,
                              error_message: str,
                              function_name: str, request_parameters: str, response_data: str, error_data: str):
    insert_query = "INSERT INTO `system_performance` (message_id, timestamp, response_time, status_code, error_type, " \
                   "error_message, " \
                   "function_name, request_parameters, response_data, error_data) VALUES (%s, %s, %s, %s, %s, %s, %s, " \
                   "%s, " \
                   "%s, %s)"
    data = (message_id, timestamp, response_time, status_code, error_type, error_message, function_name, request_parameters,
            response_data,
            error_data)
    execute_sql_query(insert_query, data)


if __name__ == "__main__":
    insert_system_performance("_44c6d007aa73218", str(datetime.now()), 200, "200", "authentication",
                              "failed to authenticate user, incorrect password",
                              "send_request", '{"client_id":"1"}', '{"data":"response"}', '{"error":"None"}')
