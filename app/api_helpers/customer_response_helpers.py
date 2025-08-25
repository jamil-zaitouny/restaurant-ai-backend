from asyncio import FIRST_COMPLETED
from concurrent.futures import ThreadPoolExecutor, wait
import time  # For sleep
from datetime import datetime  # For timestamps
import json
import queue
import os
import threading
import traceback
from typing import Dict
from typing import List
import logging
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate
from langchain.agents import Tool
# from langchain.chat_models import ChatOpenAI
from langchain_community.chat_models import ChatOpenAI
from langchain.prompts import ChatPromptTemplate, SystemMessagePromptTemplate
from langchain.schema import HumanMessage, SystemMessage
from tenacity import stop_after_attempt, wait_fixed, retry
from langchain_groq import ChatGroq
from queue import Queue, Empty  # Make sure to import Queue
from concurrent.futures import ThreadPoolExecutor, as_completed

from app.model.callbacks.streaming_response_callback import StreamingResponseCallback
from app.model.callbacks.token_logging_callback import TokenLoggingCallback
from app.model.db.db_base import fetch_sql_query, fetch_sql_query_and_key
from app.model.db.indexing.db_search import search_database
from app.model.db.indexing.vector_db_search import vector_db_search
from app.model.db.tool.db_chunk import get_chunks_by_menu_tool_id
from app.model.db.tool.db_instance import get_instance_primers
from app.model.db.tool.db_instance_tool import get_instance_tools
from app.model.db.tool.db_menu_tool import get_menu_tool_filters_from_instance_tool_id, get_menu_tool_primers, \
    get_index_tool_filters, get_index_tool_filters_from_instance_tool_id
from app.model.db.tool.db_tool import get_type_from_tool_id
from app.model.db.wordpress.db_llmcall_tool import get_llmcall_tool_filters, \
    get_llmcall_tool_filters_from_instance_tool_id
from app.model.generators import search_terms_generator
from app.model.generators.generate_catalogs import generate_catalogs, merge_results, normalize_results, \
    get_index_chat_from_system_ids, get_index_system_from_ids
from app.utilities.agent_utilities import get_agent_executor
from app.utilities.openai_helper import get_openai_api_key, get_history_from_roles, get_pinecone_api_key, \
    get_pinecone_environment, get_pinecone_index_name
from app.utilities.time_utilities import get_current_time_in_tz


#  TODO in filter&response in llm_call,
#  between customer query and prompt after there's kwargs being passed
#  which should be removed

# todo work on chunk size and increase history length, current limit factor is chunk size
def truncate_history(history, max_history_length=10000):
    truncated_history = []
    history_length = 0
    for message in reversed(history):
        message_length = len(message["content"])
        if history_length + message_length <= max_history_length:
            truncated_history.insert(0, message)
            history_length += message_length
        else:
            break

    return truncated_history

def generate_search_terms_with_retries(
        query: str,
        history: List[Dict[str, str]],
        model_type: str,
        filter_before: str,
        filter_after: str,
        message_id: str,
        conversation_id: str,
        tool_type_id: str,
        tool_type_table: str,
        instance_id,
        max_retries: int = 3
):
    retries = 0
    search_terms = None
    while retries < max_retries:
        search_terms = search_terms_generator.get_search_terms(
            query, model_type, filter_before, filter_after, history, message_id, conversation_id, tool_type_id, tool_type_table, instance_id
        )

        # Check if search_terms has more than 1 term
        if len(search_terms) > 1:
            return search_terms

        retries += 1

    return search_terms

def merge_llm_calls(query, model_name, menu_tool_id, filter_before, filter_after, history, message_id, conversation_id, instance_id):
    #    nest_asyncio.apply()

    system_message_prompt = SystemMessagePromptTemplate(
        prompt=PromptTemplate(
            template="""
                {filter_before}
                ---
                SELECT ONLY FROM THIS MENU:
                ---
                {menu} 
                ---
                Conversation History:
                {history}   
                Customer Query: {query}
                ---
                {filter_after}
                """,
            input_variables=["query", "menu", "filter_before", "filter_after", "history"],
        )
    )
    chat_prompt_template = ChatPromptTemplate.from_messages([system_message_prompt])
    # TODO clean up credit transactions to use variable
    chat = ChatOpenAI(temperature=0.0, model_name=model_name, max_retries=3, max_tokens=25, #request_timeout=5,
                      callbacks=[TokenLoggingCallback(1, 'merge_llm_calls', model_name, message_id, conversation_id, menu_tool_id, 'menu_tool', 'usage', instance_id)])
    chain = LLMChain(llm=chat, prompt=chat_prompt_template, verbose=False)
    grouped_chunks = get_chunks_by_menu_tool_id(menu_tool_id)
    return run_chats_with_retry(chain, query, grouped_chunks, filter_before, filter_after, history)


# TODO check kwargs from chain
@retry(stop=stop_after_attempt(5), wait=wait_fixed(10))
def run_chat(chain, query, menu, results, filter_before, filter_after, history):
    result = chain.run({
        'query': query,
        'menu': menu,
        'filter_before': str(filter_before),
        'filter_after': str(filter_after),
        'history': str(history)
    })
    results.append(result)


def run_chats_with_retry(chain, query, grouped_chunks, filter_before, filter_after, history):
    results = []

    threads = [
        threading.Thread(target=run_chat, args=(chain, query, chunk, results, filter_before, filter_after, history)) for
        chunk in grouped_chunks]

    # Start all threads
    for thread in threads:
        thread.start()

    # Wait for all threads to complete
    for thread in threads:
        thread.join()

    # Return the results
    return results


def get_items_from_menu_tool_id(menu_tool_id):
    # SQL query to fetch data from category_items table
    query = """SELECT llm_id, category, sub_category, image_url, url, location, contact_info, delivery_area, 
    delivery_time, name, description, price, upgrades, tags, serving_size, calories, total_fat, saturated_fat, 
    trans_fat, cholesterol, sodium, carbohydrate, dietary_fiber, sugars, protein FROM category_items WHERE 
    menu_tool_id = %s """

    # Fetch data from database
    data = fetch_sql_query(query, (menu_tool_id,))

    # Transform raw data into list of dictionaries
    result = []
    for row in data:
        result.append({
            'llmid': row[0],
            'category': row[1],
            'sub_category': row[2],
            'image_url': row[3],
            'url': row[4],
            'location': row[5],
            'contact_info': row[6],
            'delivery_area': row[7],
            'delivery_time': row[8],
            'name': row[9],
            'description': row[10],
            'price': row[11],
            'upgrades': row[12],
            'tags': row[13],
            'serving_size': row[14],
            'calories': row[15],
            'total_fat': row[16],
            'saturated_fat': row[17],
            'trans_fat': row[18],
            'cholesterol': row[19],
            'sodium': row[20],
            'carbohydrate': row[21],
            'dietary_fiber': row[22],
            'sugars': row[23],
            'protein': row[24],
        })

    return result


def get_categories_from_menu_tool_id_as_dict(menu_tool_id):
    # SQL query to fetch data from category_items table
    query = """SELECT llm_id FROM category_items WHERE 
    menu_tool_id = %s """

    # Fetch data from database
    data = fetch_sql_query(query, (menu_tool_id,))

    # Transform raw data into list of dictionaries
    result = {}
    for row in data:
        result[row[0]] += {
            'llmid': row[0],
        }
    return result


# TODO remove default value for menu_tool_id
def match_unique_ids(output, menu_tool_id, max_results=5):
    menu_chat = []
    found_ids = []
    missing_ids = []
    # If you move data outside the function, and you pass it in, you can make that part generic as well
    data = get_items_from_menu_tool_id(menu_tool_id)
    # Transform output into a list of lists
    output = [group.split() for group in output]
    """
        If there are no results make sure you return appropriate text
    """
    # Continue until we have enough results, or all IDs are used
    while len(menu_chat) < max_results and any(output):
        # Loop through each group
        for group in output:
            # If the group is not empty
            if group:
                # Get the first ID in the group
                id = group.pop(0)
                # Search for the ID in data
                found = False
                for item in data:
                    if str(id) == str(item['llmid']):
                        menu_chat.append(item)
                        found_ids.append(id)
                        found = True
                        break
                if not found:
                    missing_ids.append(id)
                # Stop if we have enough results
                if len(menu_chat) == max_results:
                    break

    # Print IDs not found in data
    if missing_ids:
        print('IDs not found in data:', ', '.join(missing_ids))

    return found_ids


def get_menu_system_from_ids(found_ids, menu_tool_id):
    query = """SELECT llm_id, name, description, url, image_url FROM category_items 
               WHERE llm_id = %s AND menu_tool_id = %s """

    # Fetch data from database
    result_dict = {}
    for catalog_item_id in found_ids:
        data = fetch_sql_query(query, [catalog_item_id, menu_tool_id])
        if data:
            # Assumption: Each data entry is a list of tuples
            for result in data:
                # Restructure the tuple into a dictionary
                result_dict[result[0]] = {
                    'name': result[1],
                    'description': result[2],
                    'url': result[3],
                    'image_url': result[4],
                }

    return result_dict



# TODO Boris mess around here
menu_headers = """llm_id, category, sub_category, location, contact_info, delivery_area, 
delivery_time, name, description, price, upgrades, tags, serving_size, calories, total_fat, saturated_fat, 
trans_fat, cholesterol, sodium, carbohydrate, dietary_fiber, sugars, protein"""


def get_menu_chat(found_ids, menu_tool_id):
    query = f"""SELECT {menu_headers} FROM category_items WHERE 
    llm_id = %s and menu_tool_id = %s"""

    # Fetch data from database
    data = [fetch_sql_query(query, [catalog_item_id, menu_tool_id]) for catalog_item_id in found_ids]

    # Modify the 8th item in each tuple
    for i in range(len(data)):
        # Extract the first (and only) tuple in each inner list
        old_tuple = data[i][0]
        old_item = old_tuple[7]
        new_item = f"[#{old_tuple[0]}] {old_item} [/#{old_tuple[0]}]"
        new_tuple = old_tuple[:7] + (new_item,) + old_tuple[8:]
        # Replace the inner list with the new tuple
        data[i] = [new_tuple]

    return data


def build_menu_response(menu_chat, query, model_name, history, primer_items, instance_id, message_id, conversation_id, menu_tool_id):
    current_time_primer = SystemMessage(content=f"It is: {get_current_time_in_tz(instance_id)}")
    primer_before = SystemMessage(content=primer_items[0])
    menu = None
    if menu_chat:
        menu = SystemMessage(content=f"""      
                        Autogenerated menu
                        Menu Headers: {menu_headers}
                        
                        Menu Values: {menu_chat}
                        
                        conversation:
         """)
    else:
        # TODO write behavior when the menu is empty
        menu = SystemMessage(content=f"""      
            We Werent Able To Find Any Items In The Menu That Matched Your Customer Request.
            This is probably because we do not have matches to the customers request but could be due to techincal issues.
            If you suspect the lack of results correct, please informt the customer that there are no matches. If you feel 
            our automated system is wrong, please apologize and tell the cusotomer that you were not able to find any matches,
            but they should double check with our in person team members as our state of the art technology still gets its wires crossed
            once in a while.
         """)

    primer_after = SystemMessage(content=primer_items[1])

    token_queue = queue.Queue()  # Use a queue to store the tokens.

    callback = StreamingResponseCallback(token_queue, 1, model_name, message_id, conversation_id, menu_tool_id, 'menu_tool', 'response', instance_id)

    chat = ChatOpenAI(model_name=model_name,
                      openai_api_key=get_openai_api_key(),
                      #request_timeout=6,
                      temperature=0.0,
                      max_retries=5,
                      streaming=True,
                      max_tokens=350,
                      callbacks=[callback])

    messages = [
        [current_time_primer, primer_before, menu] +
        get_history_from_roles(history) + [
            HumanMessage(content=query),
            primer_after
        ]
    ]

    # Send the formatted messages to the chat model
    def generate_messages():
        chat.generate(messages)

    """
        1. Callback llm_start is called
        2. Catalog system is saved to db
        3. an endpoint retreives it from the db
    
    """
    # Start a new thread that runs the llm.generate(messages) function.
    generate_thread = threading.Thread(target=generate_messages)
    generate_thread.start()

    try:
        # Retrieve the tokens from the queue and add them to the generated_tokens list.
        while generate_thread.is_alive() or not token_queue.empty():
            token = token_queue.get()
            if token == "end_message_id:back_end":
                break
            yield token

    except Exception as exception:
        traceback.print_exc()

        print(exception)
    finally:
        # Once all tokens have been retrieved or if an exception occurs, stop the print thread.
        generate_thread.join()  # Wait for the print thread to finish before exiting the function.


def build_index_response(index_chat, query, model_name, history, primer_items, instance_id, message_id, conversation_id, tool_type_id):
    current_time_primer = SystemMessage(content=f"It is: {get_current_time_in_tz(instance_id)}")
    primer_before = SystemMessage(content=primer_items[0])

    index_message = SystemMessage(content=f"""      
                    Autogenerated menu
                    Search Results: {index_chat}
                    conversation:
""")
    primer_after = SystemMessage(content=primer_items[1])

    token_queue = queue.Queue()  # Use a queue to store the tokens.

    callback = StreamingResponseCallback(token_queue, 1, model_name, message_id, conversation_id, tool_type_id, 'index_tool', 'response', instance_id)

    chat = ChatOpenAI(model_name=model_name,
                      openai_api_key=get_openai_api_key(),
                      #request_timeout=6,
                      temperature=0.0,
                      max_retries=5,
                      streaming=True,
                      max_tokens=350,
                      callbacks=[callback])

    messages = [
        [current_time_primer, primer_before, index_message] +
        get_history_from_roles(history) + [
            HumanMessage(content=query),
            primer_after
        ]
    ]

    # Send the formatted messages to the chat model
    def generate_messages():
        chat.generate(messages)

    """
        1. Callback llm_start is called
        2. Catalog system is saved to db
        3. an endpoint retreives it from the db
    
    """
    # Start a new thread that runs the llm.generate(messages) function.
    generate_thread = threading.Thread(target=generate_messages)
    generate_thread.start()

    try:
        # Retrieve the tokens from the queue and add them to the generated_tokens list.
        while generate_thread.is_alive() or not token_queue.empty():
            token = token_queue.get()
            if token == "end_message_id:back_end":
                break
            yield token

    except Exception as exception:
        traceback.print_exc()
        print(exception)
    finally:
        # Once all tokens have been retrieved or if an exception occurs, stop the print thread.
        generate_thread.join()  # Wait for the print thread to finish before exiting the function.


#
def resolve_menu_items(query, model_type, instance_tool_id, type, history, message_id, conversation_id, instance_id):
    menu_tool_id, filter_before, filter_after = get_menu_tool_filters_from_instance_tool_id(instance_tool_id)
    result = merge_llm_calls(query, model_type, menu_tool_id, filter_before, filter_after, history, message_id,
                             conversation_id, instance_id)
    ids = match_unique_ids(result, menu_tool_id)
    return type, ids, menu_tool_id, model_type


# def resolve_menu_items(query, model_type, instance_tool_id, type, history):
#     return "How you doin?"

def get_simple_response(query, model_type, instance_tool_id, type, history, message_id, conversation_id, instance_id):
    llmcall_tool_id, filter_before, filter_after, context = get_llmcall_tool_filters_from_instance_tool_id(
        instance_tool_id)
    return type, llmcall_tool_id, model_type, context


def get_index_tool_response(query, model_type, instance_tool_id, type, history, message_id, conversation_id, instance_id):
    index_tool_id, filter_before, filter_after = get_index_tool_filters_from_instance_tool_id(instance_tool_id)
    search_terms = generate_search_terms_with_retries(query, history, model_type, filter_before,
                                                                 filter_after, message_id, conversation_id,
                                                                 index_tool_id, "index_tool", instance_id)
    pinecone_api_key = get_pinecone_api_key()
    environment = get_pinecone_environment()
    index_name = get_pinecone_index_name()
    db_results = search_database(search_terms, index_tool_id)
    vector_results = vector_db_search(pinecone_api_key, get_openai_api_key(), environment, search_terms, index_name,
                                      index_tool_id, message_id, conversation_id, instance_id)

    normalized_db_results = normalize_results(db_results, is_db_results=True)
    normalized_vector_results = normalize_results(vector_results)

    merged_results = merge_results(normalized_db_results, normalized_vector_results)

    catalogs = generate_catalogs(merged_results, max_results_per_term=3, max_total_results=15)
    index_chat = [get_index_chat_from_system_ids(catalog) for catalog_list in catalogs.values() for catalog in
                  catalog_list]
    index_system = [get_index_system_from_ids(catalog) for catalog_list in catalogs.values() for catalog in
                    catalog_list]

    return type, index_tool_id, model_type, index_chat, index_system


# def get_search_terms(query, model_type, fitler_primer_before, filter_primer_after):
#     callback = TokenLoggingCallback(1, "search terms")
#
#     chat = ChatOpenAI(model_name=model_type,
#                       openai_api_key=get_openai_api_key(),
#                       streaming=True,
#                       callbacks=[callback])
#
#     primer_before = SystemMessage(content=filter_primer_before)
#     primer_before = SystemMessage(content=filter_primer_after)
#     template = f"""
#         {fitler_primer_before}
#         {query}
#         {filter_primer_after}
#     """
#     return chat.generate(template)

def build_single_response(context, query, model_name, history, primer_items, instance_id, message_id, conversation_id, tool_type_id):
    current_time_primer = SystemMessage(content=f"It is: {get_current_time_in_tz(instance_id)}")
    primer_before = SystemMessage(content=primer_items[1])

    # Check if primer_items[3] is of type bytes and decode if necessary
    primer_item_3 = primer_items[3].decode('utf-8') if isinstance(primer_items[3], bytes) else primer_items[3]
    context = SystemMessage(content="Most Current Information Available: " + primer_item_3)
    primer_after = SystemMessage(content=primer_items[2])

    token_queue = queue.Queue()  # Use a queue to store the tokens.

    callback = StreamingResponseCallback(token_queue, 1, model_name, message_id, conversation_id, tool_type_id, 'llmcall_tool', 'response', instance_id)

    chat = ChatOpenAI(model_name=model_name,
                      openai_api_key=get_openai_api_key(),
                      #request_timeout=6,
                      temperature=0.0,
                      max_retries=5,
                      streaming=True,
                      max_tokens=350,
                      callbacks=[callback])

    messages = [
        [current_time_primer, primer_before] +
        get_history_from_roles(history) + [
            context,
            HumanMessage(content=query),
            primer_after
        ]
    ]

    # Send the formatted messages to the chat model
    def generate_messages():
        chat.generate(messages)

    # Start a new thread that runs the chat.generate(messages) function.
    generate_thread = threading.Thread(target=generate_messages)
    generate_thread.start()

    try:
        # Retrieve the tokens from the queue.
        while generate_thread.is_alive() or not token_queue.empty():
            token = token_queue.get()
            if token == "end_message_id:back_end":
                break
            yield token
    except Exception as exception:
        traceback.print_exc()
        print(exception)
    finally:
        # Ensure the thread is joined back to avoid any loose ends.
        generate_thread.join()



# AGENT SECTION


def stream_response(instance_id, query, history, credit_transaction_id, message_id, conversation_id, provider="openai"):
    """Stream response with improved error handling and debug logging"""
    try:
        print("\n=== STREAM RESPONSE START ===")
        print(f"Environment check:")
        print(f"HTTP_PROXY: {os.environ.get('HTTP_PROXY')}")
        print(f"HTTPS_PROXY: {os.environ.get('HTTPS_PROXY')}")
        print(f"NO_PROXY: {os.environ.get('NO_PROXY')}")
        print(f"OPENAI_API_KEY set: {'OPENAI_API_KEY' in os.environ}")
        
        print(f"\nInput parameters:")
        print(f"- instance_id: {instance_id}")
        print(f"- query: {query}")
        print(f"- credit_transaction_id: {credit_transaction_id}")
        print(f"- message_id: {message_id}")
        print(f"- conversation_id: {conversation_id}")
        print(f"- provider: {provider}")

        if not query or not instance_id:
            raise ValueError(f"Missing required parameters: query={bool(query)}, instance_id={bool(instance_id)}")

        history = truncate_history(history)
        print(f"\nTruncated history length: {len(history)}")
        print(f"History content: {json.dumps(history, indent=2)}")

        # Get primers and model
        try:
            agent_primer_before, agent_primer_after, llm_model = get_instance_primers(instance_id)
            print(f"\nRetrieved primers and model:")
            print(f"- Model: {llm_model}")
            print(f"- Primer before length: {len(agent_primer_before.content)}")
            print(f"- Primer after length: {len(agent_primer_after.content)}")
            print(f"- Primer before content: {agent_primer_before.content[:100]}...")
            print(f"- Primer after content: {agent_primer_after.content[:100]}...")
        except Exception as e:
            print(f"Error getting primers: {str(e)}")
            traceback.print_exc()
            raise Exception(f"Failed to get primers: {str(e)}")

        # Get instance tools
        try:
            instances = get_instance_tools(instance_id)
            print(f"\nRetrieved {len(instances)} instance tools")
            for inst in instances:
                print(f"- Tool ID: {inst[0]}")
                print(f"  Name: {inst[2]}")
                print(f"  Model: {inst[5]}")
                print(f"  Instance Tool ID: {inst[6]}")
        except Exception as e:
            print(f"Error getting instance tools: {str(e)}")
            traceback.print_exc()
            raise Exception(f"Failed to get instance tools: {str(e)}")

        def create_llm(model_type=None):
            print(f"\nCreating LLM:")
            print(f"- Requested model: {model_type or llm_model}")
            
            try:
                api_key = get_openai_api_key()
                if not api_key:
                    raise ValueError("OpenAI API key not found")

                # Create ChatOpenAI instance with direct parameters rather than unpacking
                return ChatOpenAI(
                    model_name=model_type or llm_model,
                    temperature=0.0,
                    openai_api_key=api_key,
                    max_tokens=350,
                    streaming=True,
                    request_timeout=60,
                    max_retries=5,
                    callbacks=[TokenLoggingCallback(
                        credit_transaction_id, 
                        "agent_call",
                        model_type or llm_model,
                        message_id,
                        conversation_id,
                        instance_id,
                        "agent",
                        'usage',
                        instance_id
                    )]
                )
                
            except Exception as e:
                print(f"Error creating LLM instance:")
                print(f"- Error type: {type(e)}")
                print(f"- Error message: {str(e)}")
                print(f"- Full traceback:")
                traceback.print_exc()
                raise



        functions = {
            "filter_and_respond": resolve_menu_items,
            "single_call": get_simple_response,
            "end_call": get_simple_response,
            "website_search": get_index_tool_response,
        }

        print("\nCreating tools...")
        tools = []
        for instance in instances:
            if instance[4] == '1':  # Only active tools
                try:
                    tool_type = get_type_from_tool_id(instance[0])
                    print(f"\nProcessing tool:")
                    print(f"- Name: {instance[2]}")
                    print(f"- Type: {tool_type}")
                    print(f"- Tool ID: {instance[0]}")
                    print(f"- LLM Model: {instance[5]}")
                    print(f"- Instance Tool ID: {instance[6]}")
                    
                    tool = Tool.from_function(
                        func=lambda bot_query, tool_id=instance[0], llm_model=instance[5], instance_tool_id=instance[6]: 
                            functions[get_type_from_tool_id(tool_id)](
                                query, 
                                llm_model, 
                                instance_tool_id,
                                get_type_from_tool_id(tool_id),
                                history,
                                message_id,
                                conversation_id,
                                instance_id
                            ),
                        name=instance[2],
                        description=instance[1],
                        return_direct=instance[3],
                        verbose=True,
                    )
                    tools.append(tool)
                    print(f"Tool created successfully")
                except Exception as e:
                    print(f"Error creating tool {instance[2]}:")
                    print(f"- Error type: {type(e)}")
                    print(f"- Error message: {str(e)}")
                    traceback.print_exc()
                    # Continue with other tools rather than failing completely
                    continue

        if not tools:
            raise Exception("No valid tools were created")

        print(f"\nCreated {len(tools)} tools successfully")

        def attempt_query(attempt):
            print(f"\nAttempt {attempt} to execute query")
            try:
                llm = create_llm()
                print("LLM created successfully")
                
                agent = get_agent_executor(
                    tools,
                    instance_id,
                    llm,
                    history,
                    agent_primer_before.content,
                    agent_primer_after.content
                )
                print("Agent executor created successfully")
                
                print("Executing query...")
                result = agent({'input': query, 'history': history})
                print(f"Query executed successfully")
                print(f"Result type: {type(result)}")
                print(f"Result structure: {json.dumps(result, default=str)[:200]}...")
                
                return result['output']
            except Exception as e:
                print(f"Error in attempt {attempt}:")
                print(f"- Error type: {type(e)}")
                print(f"- Error message: {str(e)}")
                print("- Full traceback:")
                traceback.print_exc()
                raise

        max_attempts = 3
        last_error = None

        for attempt in range(1, max_attempts + 1):
            try:
                print(f"\nStarting attempt {attempt} of {max_attempts}")
                result = attempt_query(attempt)
                print(f"Attempt {attempt} successful")
                return result
            except Exception as e:
                last_error = e
                print(f"Attempt {attempt} failed:")
                print(f"- Error type: {type(e)}")
                print(f"- Error message: {str(e)}")
                if attempt == max_attempts:
                    print("All attempts exhausted")
                    raise Exception(
                        f"All {max_attempts} attempts failed. Last error: {str(last_error)}. "
                        f"Error type: {type(last_error)}"
                    )

    except Exception as e:
        print(f"\n!!! FATAL ERROR in stream_response:")
        print(f"- Error type: {type(e)}")
        print(f"- Error message: {str(e)}")
        print("- Full traceback:")
        traceback.print_exc()
        raise


def generate_tool_response(query: str,
                           history: List[Dict[str, str]],
                           context: str,
                           type: str,
                           model_name: str,
                           tool_type_id: str,
                           instance_id: int,
                           message_id: str,
                           conversation_id: str):
    history = truncate_history(history)
    functions = {
        "filter_and_respond": build_menu_response,
        "single_call": build_single_response,
        "end_call": build_single_response,
        "website_search": build_index_response,
    }

    primer_getter = {
        "filter_and_respond": get_menu_tool_primers,
        "single_call": get_llmcall_tool_filters,
        "end_call": get_llmcall_tool_filters,
        "website_search": get_index_tool_filters,
    }
# print what its about to return
    logging.debug("Generating tool response with parameters: query: %s, history: %s, context: %s, type: %s, model_name: %s, tool_type_id: %s, instance_id: %s, message_id: %s, conversation_id: %s", query, history, context, type, model_name, tool_type_id, instance_id, message_id, conversation_id)
    return functions[type](context, query, model_name, history, primer_getter[type](tool_type_id), instance_id,
                           message_id, conversation_id, tool_type_id)


if __name__ == "__main__":
    query = "How Cheers!"
    history = []
    openai_api_key = get_openai_api_key()
    catalog_chat = """[|# 1 |]\nDeWalt 20V MAX Cordless 30 Paper Collated Framing Nailer\nNone\n[|/ # 1 |"""
    print("Generic menu", stream_response(63, query, [], 1))
