# app/utilities/usage_billings_helper.py

import logging
from app.model.db.frontend.db_billing import get_credit_transaction_sum, turn_off_chatbot, \
    subtract_usage_billing_from_credit, update_credit_transaction_amount, update_usage_billing
from app.model.db.frontend.db_logging import log_usage_billing
from app.model.db.tool.db_credit_type import get_credit_type_by_search
from app.model.db.wordpress.db_client import get_all_instance_for_client

logger = logging.getLogger(__name__)

def log_inbound_message(usage_id, credit_transaction_id, client_id):
    try:
        criteria = {
            "name": 'inbound_message',
        }
        credit_type = get_credit_type_by_search(criteria)
        if not credit_type:
            logger.error("No credit type found for inbound message")
            return
            
        credit_type_id = credit_type[0][0]
        log_usage_billing(usage_id, credit_transaction_id, 1, credit_type_id, client_id)
        logger.debug(f"Logged inbound message: usage_id={usage_id}, credit_type_id={credit_type_id}")
    except Exception as e:
        logger.error(f"Error logging inbound message: {str(e)}")
        raise

def log_outbound_message(usage_id, credit_transaction_id, model_type, client_id):
    try:
        criteria = {
            "name": 'outbound_message',
            "model_type": model_type,
        }
        credit_type = get_credit_type_by_search(criteria)
        if not credit_type:
            logger.error(f"No credit type found for outbound message with model {model_type}")
            return
            
        credit_type_id = credit_type[0][0]
        usage_billing_id = log_usage_billing(usage_id, credit_transaction_id, 1, credit_type_id, client_id)
        bill_user(client_id, usage_billing_id, credit_type_id)
        logger.debug(f"Logged outbound message: usage_id={usage_id}, credit_type_id={credit_type_id}")
    except Exception as e:
        logger.error(f"Error logging outbound message: {str(e)}")
        raise

def log_gpt_usages(usage_id, credit_transaction_id, model_type, token_completion, token_prompt, name, client_id):
    try:
        base_criteria = {
            "name": name,
            "model_type": model_type,
        }
        
        # Get completion credit type
        completion_criteria = {**base_criteria, "usage_type": 'completion'}
        completion_type = get_credit_type_by_search(completion_criteria)
        if completion_type:
            completion_credit_type_id = completion_type[0][0]
            log_usage_billing(usage_id, credit_transaction_id, token_completion, completion_credit_type_id, client_id)
            
        # Get prompt credit type
        prompt_criteria = {**base_criteria, "usage_type": 'prompt'}
        prompt_type = get_credit_type_by_search(prompt_criteria)
        if prompt_type:
            prompt_credit_type_id = prompt_type[0][0]
            log_usage_billing(usage_id, credit_transaction_id, token_prompt, prompt_credit_type_id, client_id)
            
        logger.debug(f"Logged GPT usage: usage_id={usage_id}, model_type={model_type}")
    except Exception as e:
        logger.error(f"Error logging GPT usage: {str(e)}")
        raise

def log_gpt_embeddings_usage(usage_id, credit_transaction_id, model_type, tokens_embeddings, name, client_id):
    try:
        criteria = {
            "name": name,
            "model_type": model_type,
            "usage_type": 'embedding',
        }
        credit_type = get_credit_type_by_search(criteria)
        if not credit_type:
            logger.error(f"No credit type found for embeddings with model {model_type}")
            return
            
        credit_type_id = credit_type[0][0]
        log_usage_billing(usage_id, credit_transaction_id, tokens_embeddings, credit_type_id, client_id)
        logger.debug(f"Logged embeddings usage: usage_id={usage_id}, credit_type_id={credit_type_id}")
    except Exception as e:
        logger.error(f"Error logging embeddings usage: {str(e)}")
        raise

def bill_user(client_id, usage_billing_id, credit_type_id):
    try:
        credit_transaction_sum = get_credit_transaction_sum(client_id, credit_type_id)

        if credit_transaction_sum <= 0:
            instances = get_all_instance_for_client(client_id)
            for instance_id in instances:
                turn_off_chatbot(instance_id)
                logger.warning(f"Turned off chatbot for instance {instance_id} due to insufficient credits")

        new_amount, credit_transaction_id = subtract_usage_billing_from_credit(
            client_id, credit_type_id, usage_billing_id)
        update_credit_transaction_amount(credit_transaction_id, new_amount)
        update_usage_billing(credit_transaction_id, usage_billing_id)
        logger.debug(f"Billed user: client_id={client_id}, new_amount={new_amount}")
    except Exception as e:
        logger.error(f"Error billing user: {str(e)}")
        raise