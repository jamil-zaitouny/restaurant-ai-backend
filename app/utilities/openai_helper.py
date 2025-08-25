import os

from langchain.schema import SystemMessage, HumanMessage, AIMessage


def get_openai_api_key():
    api_key = os.environ.get('OPENAI_API_KEY')
    if not api_key:
        raise ValueError("OPENAI_API_KEY environment variable is not set")
    return api_key


def get_pinecone_api_key():
    return os.environ.get('PINECONE_API_KEY')


def get_pinecone_environment():
    return os.environ.get('PINECONE_ENVIRONMENT')
def get_pinecone_index_name():
    return os.environ.get('PINECONE_INDEX_NAME')


def convert_to_langchain_message(message):
    if message['role'] == "system":
        return SystemMessage(content=message["content"])
    if message['role'] == "assistant":
        return AIMessage(content=message["content"])
    if message['role'] == "user":
        return HumanMessage(content=message["content"])

def validate_environment():
    required_vars = [
        'OPENAI_API_KEY',
        'PINECONE_API_KEY',
        'PINECONE_ENVIRONMENT',
        'PINECONE_INDEX_NAME'
    ]
    
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        raise EnvironmentError(f"Missing required environment variables: {', '.join(missing_vars)}")


def get_history_from_roles(history):
    langchain_history = []
    for message in history:
        langchain_history.append(convert_to_langchain_message(message))
    return langchain_history
