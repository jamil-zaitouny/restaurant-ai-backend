import sys

sys.path.insert(0, 'C:\\Own Your AI GIT\\SiteAI-Backend')
import openai
import pinecone
import time
import traceback
from concurrent.futures import ThreadPoolExecutor, as_completed
import tiktoken
from collections import defaultdict
from langchain_community.callbacks import get_openai_callback
from langchain_community.embeddings import OpenAIEmbeddings

from app.utilities.openai_helper import get_openai_api_key, get_pinecone_api_key, get_pinecone_environment, \
    get_pinecone_index_name
from app.utilities.embeddings_helpers import get_embeddings_from_document
from app.model.db.db_base import load_database

embed_model = "text-embedding-ada-002"
tokenizer = tiktoken.get_encoding('p50k_base')


def initialize_pinecone(pinecone_api_key, environment, index_name):
    pinecone.init(
        pinecone_api_key,
        environment=environment
    )

    if index_name not in pinecone.list_indexes():
        pinecone.create_index(
            index_name,
            dimension=1536,
            metric='dotproduct'
        )
    index = pinecone.Index(index_name)
    return index


def process_search_term(search_term, index, embed_model, cache, index_tool_id, message_id, conversation_id,
                        instance_id):
    tries = 7
    delay = 0.1
    backoff = 0.1
    max_delay = 2

    for attempt in range(tries):
        try:
            if search_term not in cache:
                res = get_embeddings_from_document(search_term, index_tool_id, 'index_tool', message_id,
                                                   conversation_id, instance_id)
                cache[search_term] = res

            else:
                res = cache[search_term]

            xq = res

            conditions = {
                'index_tool_id': {'$eq': index_tool_id},
            }

            query = {
                "query": xq,
                "filter": conditions,
                "top_k": 5
            }

            response = index.query(
                vector=query["query"],
                filter=query["filter"],
                top_k=query["top_k"],
                include_metadata=True
            )

            cleaned_results = []
            rank = 1
            previous_score = None
            for match in response['matches']:
                if match['score'] != previous_score:
                    rank += 1
                    previous_score = match['score']
                cleaned_results.append({
                    'Search Term': search_term,
                    'Vector ID': match['id'],
                    'URL': match['metadata'].get('url'),
                    'Image URL': match['metadata'].get('image_url'),
                    'Vector Type': match['metadata'].get('vector_type'),
                    'Content': match['metadata'].get('content'),
                    'Rank': rank,
                })

            return cleaned_results
        except:
            traceback.print_exc()
            time.sleep(delay)
            delay = min(delay * (1 + backoff), max_delay)
    return []


def vector_db_search(pinecone_api_key, openai_api_key, environment, search_terms, index_name, index_tool_id, message_id,
                     conversation_id, instance_id):
    index = initialize_pinecone(pinecone_api_key, environment, index_name)
    cache = {}

    search_results = defaultdict(list)
    with ThreadPoolExecutor() as executor:
        futures = {
            executor.submit(process_search_term, search_term, index, embed_model, cache, index_tool_id, message_id,
                            conversation_id, instance_id): search_term for
            search_term in search_terms}
        for future in as_completed(futures):
            search_term = futures[future]
            try:
                results = future.result()
                search_results[search_term].extend(results)
            except Exception as e:
                print(f"Error for search_term '{search_term}': {e}")

    for term in search_terms:
        search_results[term].sort(key=lambda x: x['Rank'])
        search_results[term] = search_results[term][:3]

    print(f"Search results: {dict(search_results)}".encode('utf-8'))
    return search_results


if __name__ == "__main__":
    pinecone_api_key = get_pinecone_api_key()
    environment = get_pinecone_environment()
    index_name = get_pinecone_index_name()
    search_terms = [
        "Korean BBQ Pork Lettuce Wraps",
    ]

    search_results = main(pinecone_api_key, get_openai_api_key(), environment, search_terms, index_name, 1)
