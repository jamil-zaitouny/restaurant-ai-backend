import sys

sys.path.insert(0, 'C:\\Own Your AI GIT\\SiteAI-Backend')
import json
import re
from collections import defaultdict
from urllib.parse import urlparse, urlunparse
from app.utilities.openai_helper import get_openai_api_key, get_pinecone_api_key, get_pinecone_environment, \
    get_pinecone_index_name
from app.model.db.indexing.db_search import search_database
from app.model.db.indexing.vector_db_search import vector_db_search
from app.model.db.db_base import load_database, fetch_sql_query, fetch_sql_query_and_key
from sqlalchemy import text


"""
    1. LLM call to Search terms -> we'll end up with
    2. Pass the search to both vector_db/db
    3. merge results
"""

def normalize_bytes(value):
    """Decodes bytes to strings if necessary."""
    if isinstance(value, bytes):
        try:
            return value.decode()
        except UnicodeDecodeError:
            print("Error: Could not decode bytes to string.")
            return None
    else:
        return value


def normalize_url(url):
    if url is None:
        return None

    try:
        if isinstance(url, bytes):  # Check if the url is bytes
            url = url.decode()  # Decode to string if it's bytes

        parsed = urlparse(url)
        scheme = parsed.scheme.lower().replace("https", "http")
        netloc = parsed.netloc.lower().lstrip("www.")
        path = re.sub(r"/$", "", parsed.path)
        path = re.sub(r"\.html$", "", path)
        return urlunparse((scheme, netloc, path, parsed.params, "", ""))
    except Exception as e:
        raise ValueError(f"Failed to normalize URL '{url}': {str(e)}")


def truncate_text(text, max_tokens):
    if text is None:
        return None
    tokens = text.split()
    truncated_tokens = tokens[:max_tokens]
    return ' '.join(truncated_tokens)


def normalize_results(results, is_db_results=False):
    normalized_results = {}

    for search_term, search_results in results.items():
        print(f"Processing search term: {search_term}")
        normalized_search_results = []
        for result in search_results:
            result = {k: normalize_bytes(v) for k, v in result.items()}  # Normalize bytes to strings
            url = result.get('url') or result.get('URL')
            vector_type = result.get('vector_type') or result.get('Vector Type')
            rank = result.get('Rank')
            vector_id = result.get('Vector ID')

            normalized_result = {
                'search_term': search_term,
                'url': normalize_url(url),
                'vector_type': vector_type,
                'vector_id': vector_id,
                'rank': rank,
            }
            normalized_search_results.append(normalized_result)

        normalized_results[search_term] = normalized_search_results

    print("Normalized Results:")
    print(normalized_results)
    return normalized_results


def merge_results(db_results, vector_results):
    merged_results = defaultdict(list)

    for search_term, results in db_results.items():
        merged_results[search_term].extend(results)

    for search_term, results in vector_results.items():
        merged_results[search_term].extend(results)

    for search_term, results in merged_results.items():
        results.sort(key=lambda x: x['rank'])

    return merged_results


def generate_catalogs(merged_result, max_results_per_term=3, max_total_results=8):
    engine = load_database()  # Assuming this function returns a SQLAlchemy Engine instance

    catalogs = defaultdict(list)
    total_results_count = 0

    for search_term in merged_result:
        if total_results_count >= max_total_results:
            break

        # Use SQLAlchemy's text function for parameterized query
        query = """
            SELECT 
                site_vectors.id AS vector_id,
                site_index.pagetitle AS title,
                site_index.url,
                site_index.image_url AS img_url,
                site_index.summary,
                site_vectors.vector_type,
                site_index.llmid AS llm_id,
                site_index.id AS site_index_id,
                site_index.content
            FROM 
                site_vectors
            INNER JOIN 
                site_index ON site_vectors.site_index_id = site_index.id
            WHERE 
                site_vectors.id LIKE %s
            ORDER BY 
                site_vectors.id
            LIMIT 
                %s;
        """

        # Provide parameters as tuple
        params = (merged_result[search_term][0]['vector_id'], max_results_per_term)

        # Pass both query and params to the fetch_sql_query function
        results = [fetch_sql_query(query, (merged_result[search_term][i]['vector_id'], max_results_per_term)) for i in
                   range(len(merged_result[search_term]))]

        for result in results:
            if not result: continue

            result = [normalize_bytes(value) for value in result[0]]
            if total_results_count >= max_total_results:
                break
            """
            SELECT 
                site_vectors.id AS vector_id,
                site_index.pagetitle AS title,
                site_index.url,
                site_index.image_url AS img_url,
                site_index.summary,
                site_vectors.vector_type,
                site_index.llmid AS llm_id,
                site_index.id AS site_index_id,
                site_index.content
            """
            catalog = {
                'search_term': search_term,
                'title': result[1],
                'url': result[2],
                'img_url': result[3],
                'summary': truncate_text(result[4], 50),
                'vector_type': result[5],
                'llm_id': result[6],
                'site_index_id': result[7],
                'content': truncate_text(result[8], 30),
            }
            catalogs[search_term].append(catalog)
            total_results_count += 1

    print("Generated Catalogs:")
    print(json.dumps(catalogs, indent=2))
    #TODO  ARE WE DOING 2 SEPERATE CATALOGS, AND IF SO, I THINK LLM IS SEEING THE THINGS IT SHOULDNT I>E IMG URL etc.,

    return catalogs


def get_index_system_from_ids(catalog):
    # define keys to keep
    keys_to_keep = ['llm_id', 'title', 'summary', 'url', 'img_url']

    return filter_catalog(catalog, keys_to_keep)


def get_index_chat_from_system_ids(catalog):
    # define keys to keep
    keys_to_keep = ['llm_id', 'title', 'summary', 'content']

    filtered_catalog = filter_catalog(catalog, keys_to_keep)
    filtered_catalog[keys_to_keep[1]] = f"[#{filtered_catalog[keys_to_keep[0]]}] {filtered_catalog[keys_to_keep[1]]} [/#{filtered_catalog[keys_to_keep[0]]}]"

    return f"""
        {filtered_catalog[keys_to_keep[1]]}
        snippet:
            {filtered_catalog[keys_to_keep[3]]}
        result summary:
            {filtered_catalog[keys_to_keep[2]]}
    """



def filter_catalog(catalog, keys_to_keep):
    # use dictionary comprehension to create a new dictionary that only includes the keys to keep
    filtered_catalog = {key: value for key, value in catalog.items() if key in keys_to_keep}

    return filtered_catalog


if __name__ == '__main__':
    pass
    # pinecone_api_key = get_pinecone_api_key()
    # environment = get_pinecone_environment()
    # index_name = get_pinecone_index_name()
    # search_terms = ['AI tools', 'generative text', 'sales ai agent', 'restauran ai solution']
    # index_tool_id = 1  # Assuming a site index id for example
    #
    # db_results = search_database(search_terms, index_tool_id)
    # vector_results = vector_db_search(pinecone_api_key, get_openai_api_key(), environment, search_terms, index_name,
    #                                   index_tool_id)
    #
    # normalized_db_results = normalize_results(db_results, is_db_results=True)
    # normalized_vector_results = normalize_results(vector_results)
    #
    # merged_results = merge_results(normalized_db_results, normalized_vector_results)
    #
    # catalogs = generate_catalogs(merged_results, max_results_per_term=2, max_total_results=8)
    # [print(get_index_chat_from_system_ids(catalog)) for catalog_list in catalogs.values() for catalog in catalog_list]
    # [print(get_index_system_from_ids(catalog)) for catalog_list in catalogs.values() for catalog in catalog_list]
    # You can now use the `catalogs` variable for further processing or output.
# TODO add async.
# TODO play with the mixing logic.
