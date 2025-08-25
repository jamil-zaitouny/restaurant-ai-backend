import openai
import re
from collections.abc import MutableSequence as List
from collections.abc import MutableMapping as Dict
from langchain_community.chat_models import ChatOpenAI

#from langchain.chat_models import ChatOpenAI
from langchain.schema import SystemMessage, HumanMessage

from app.model.callbacks.token_logging_callback import TokenLoggingCallback
from app.utilities.openai_helper import get_history_from_roles, get_openai_api_key


def get_search_terms(query: str, model_type: str, filter_before, filter_after, history: List[Dict[str, str]],
                     message_id: str, conversation_id: str, tool_type_id, tool_type_table, instance_id) -> \
        List[str]:
    openai.api_key = get_openai_api_key()

    history = get_history_from_roles(history)

    messages = [SystemMessage(content=filter_before)] + history + [
        HumanMessage(content=query),
        SystemMessage(content=filter_after)
    ]

    llm = ChatOpenAI(model_name=model_type, openai_api_key=get_openai_api_key(),
                     callbacks=[TokenLoggingCallback("1", "search term", model_type, message_id, conversation_id, tool_type_id, tool_type_table, 'usage', instance_id)])
    response_content = llm.generate(messages=[messages])

    search_terms = extract_search_terms(response_content.generations[0][0].text)
    search_terms.append(query)

    return search_terms


def extract_search_terms(response_content: str) -> List[str]:
    return re.findall(r"\[SEARCH \d+: '(.*?)'\]", response_content)


def truncate_history(history: List[Dict[str, str]]) -> List[Dict[str, str]]:
    history_str = " ".join([msg["content"] for msg in history])
    if len(history_str) > 1500:
        truncated_history_str = history_str[-1500:]
        return [{"role": msg["role"], "content": msg["content"]} for msg in history if
                msg["content"] in truncated_history_str]
    else:
        return history


if __name__ == "__main__":
    query = "I am considering between a reciprican and band saw for my birdhouse project, which one should I get?"
    history = []
    search_model = "gpt-3.5-turbo"
    search_primer = f"""You will be given customer message and if any, history, from it you will generate 5 non-repetitive searche terms offering a range of directly and indirectly related options, including add-ons, follow these steps: 
    1. Understand the customer's primary need: Identify the main product or service the customer is looking for based on their query. This will be the focus of your first search.
    2. Explore related categories: Think of relevant categories that may contain products that complement or enhance the primary product. These can be accessories, attachments, or similar products in the same category with different features or prices.
    3. Consider the customer's intended use: Reflect on the customer's specific needs or requirements, which may help you find more tailored options. For example, if they mention a preference for cordless tools, focus one search on cordless options.
    4. Identify alternative solutions: If applicable, think of different approaches to achieve the same goal. For instance, if the customer is searching for a power tool to perform a specific task, you could also search for a multi-tool that includes that function.
    5. Search for products likely to be on our website, we are KMS Tools - a Canadian retailer of power, automotive, woodworking, welding, metalworking tools with construction equipment and car parts.
    6. Use best search practices to maximize results, always reduce the search queary to its base word form.
    Conduct searches to deliver a thorough response to customer message. Make sure the search queries prioritize product searches over article searches. Searches should be writen with the understand of how to get range of results from database.  refrain from running searches that are unlikely to produce results on our website. Present each search query using the following format: [SEARCH 1: 'Website Search Term']. Only provide the search queries (keywords) without any additional information.
    
    
    Example customer query:
    Example:
    Customer Query: I need a good-quality jigsaw for cutting intricate shapes in wood.

    Search Queries:
    [SEARCH 1: 'Jigsaws']
    [SEARCH 2: 'Jigsaw Kit']
    [SEARCH 3: 'Jigsaw Blades']
    [SEARCH 4: 'Scroll Saw']
    [SEARCH 5: 'Saw Guide']

    This approach provides a variety of options, including add-ons, while keeping the language concise."""

    api_key = get_openai_api_key()

    search_terms = get_search_terms(api_key, query, history, search_model, search_primer)
    print(search_terms)
