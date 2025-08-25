from datetime import datetime

import tiktoken
from langchain_community.embeddings import OpenAIEmbeddings
from app.model.db.frontend.db_logging import log_token_usage, get_client_id_from_instance
from app.utilities.openai_helper import get_openai_api_key
from app.utilities.usage_billings_helper import log_gpt_usages, log_gpt_embeddings_usage

tokenizer = tiktoken.get_encoding('p50k_base')


def tiktoken_len(text):
    tokens = tokenizer.encode(
        text,
        disallowed_special=()
    )
    return len(tokens)


def get_embeddings_from_document(document, tool_type_id, tool_type_table, message_id, conversation_id, instance_id):
    start = datetime.now()
    embeddings = OpenAIEmbeddings(openai_api_key=get_openai_api_key())
    res = embeddings.embed_query(document)
    end = datetime.now()
    usage_id = log_token_usage(document, None, 0, 0, start, end, 'ada_embeddings', tool_type_id, tool_type_table, message_id, conversation_id, tokens_embeddings=tiktoken_len(document))
    log_gpt_embeddings_usage(usage_id, 1, 'ada', tiktoken_len(document), 'embeddings_search', get_client_id_from_instance(instance_id))
    print(f"The tokens for the search term {document} are {tiktoken_len(document)}")
    return res
