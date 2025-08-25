import datetime

from app.model.db.db_base import execute_sql_query, fetch_sql_query


def log_token_usage(content_sent, content_received, tokens_prompt, tokens_completion, requested_time, completed_time,
                    call_type, tool_type_id, tool_type_table, message_id, conversation_id, tokens_embeddings=None,
                    status="Completed"):
    # Define the usage data
    duration = (requested_time - completed_time).seconds

    requested_time = requested_time.strftime("%Y-%m-%d %H:%M:%S")
    completed_time = completed_time.strftime("%Y-%m-%d %H:%M:%S")
    # Execute the SQL INSERT statement
    insert_query = "INSERT INTO `usage` (type, completed_time, requested_time, " \
                   "content_sent, content_received, tokens_completion, tokens_prompt, " \
                   "tokens_embeddings, duration, " \
                   "`status`, message_id, conversation_id, tool_type_id, tool_type_table) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
    data = (call_type, completed_time, requested_time, content_sent,
            content_received, tokens_completion, tokens_prompt, tokens_embeddings, duration, status, message_id,
            conversation_id, tool_type_id, tool_type_table)
    return execute_sql_query(insert_query, data)


def log_usage_billing(usage_id, credit_transaction_id, amount, credit_type_id, client_id):
    insert_query = "INSERT INTO `usage_billing` (credit_type_id, usage_id, credit_transaction_id, amount, client_id)" \
                   "VALUES (%s, %s, %s, %s, %s)"
    data = (credit_type_id, usage_id, credit_transaction_id, amount, client_id)

    return execute_sql_query(insert_query, data)


def create_credit_id(client_id, amount=None, woocommerce_order_id=None, credit_expiration_date=None,
                     credit_type_id=None):
    insert_query = "INSERT INTO `credit_transaction` (id, client_id, credit_type_id, amount, woocommerce_order_id, " \
                   "credit_expiration_date" \
                   ") VALUES (%s, %s, %s, %s, %s, %s) "
    data = (None, client_id, credit_type_id, amount, woocommerce_order_id, credit_expiration_date)
    execute_sql_query(insert_query, data)


def get_client_id_from_instance(instance_id: int):
    query = """
        SELECT client_id FROM client_instance WHERE instance_id = %s
    """
    return fetch_sql_query(query, (instance_id,))[0][0]


if __name__ == "__main__":
    print(get_client_id_from_instance(1))
