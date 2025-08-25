from app.model.db.db_base import update_sql_query, fetch_sql_query, fetch_sql_query_and_key
from app.model.db.wordpress.db_client import get_all_instance_tools_for_client, get_all_instance_for_client


def get_credit_transaction_sum(client_id, credit_type_id):
    query = """
    SELECT SUM(amount)
    FROM credit_transaction
    WHERE client_id = %s
    AND amount > 0
    AND credit_expiration_date >= CURDATE()
    AND credit_type_id = %s
    """
    result = fetch_sql_query(query, (client_id, credit_type_id))
    return 0 if result[0][0] is None else result[0][0]


def turn_off_chatbot(instance_id):
    query = """
    UPDATE instance
    SET status = '2'
    WHERE id = %s
    """
    affected_rows = update_sql_query(query, (instance_id,))
    return affected_rows


def get_sorted_credit_transactions(client_id, credit_type_id):
    query = """
    SELECT *
    FROM credit_transaction
    WHERE client_id = %s
    AND amount > 0
    AND credit_type_id = %s
    AND credit_expiration_date >= CURDATE()
    ORDER BY credit_expiration_date ASC
    """
    result = fetch_sql_query_and_key(query, (client_id, credit_type_id))
    return [{"id": key, **value} for key, value in result.items()]


def subtract_usage_billing_from_credit(client_id, credit_type_id, usage_billing_id):
    # Default values for amount and credit transaction ID
    default_amount = 0  # Adjust as necessary
    default_credit_transaction_id = None  # Adjust as necessary or provide a default ID if applicable

    credit_transactions = get_sorted_credit_transactions(client_id, credit_type_id)
    if not credit_transactions:
        # No credit transactions found; return default values
        return default_amount, default_credit_transaction_id

    query = """
    SELECT amount
    FROM usage_billing
    WHERE id = %s
    """
    usage_billing_sum = fetch_sql_query(query, (usage_billing_id,))

    if not usage_billing_sum or not usage_billing_sum[0]:
        # No usage billing sum found; return default values
        return default_amount, default_credit_transaction_id

    # Calculate the new amount and return it along with the credit transaction ID
    new_amount = credit_transactions[0]['amount'] - usage_billing_sum[0][0]
    return new_amount, credit_transactions[0]['id']



def update_usage_billing(credit_transaction_id, usage_billing_id):
    query = """
    UPDATE usage_billing
    SET credit_transaction_id = %s
    WHERE id = %s
    """
    affected_rows = update_sql_query(query, (credit_transaction_id, usage_billing_id))
    return affected_rows


def update_credit_transaction_amount(credit_transaction_id, new_amount):
    query = """
    UPDATE credit_transaction
    SET amount = %s
    WHERE id = %s
    """
    affected_rows = update_sql_query(query, (new_amount, credit_transaction_id))
    return affected_rows


if __name__ == '__main__':
    update_usage_billing(2, 1)
