import sys
sys.path.insert(0, 'C:\\Own Your AI GIT\\SiteAI-Backend')
from collections import defaultdict
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import RegexpTokenizer
from app.model.db.db_base import load_database, fetch_sql_query

stopwords_set = set(stopwords.words('english'))
tokenizer = RegexpTokenizer(r'\w+')

 
def preprocess_text(text):
    if text is None:
        return ""
    text = text.lower()
    tokens = tokenizer.tokenize(text)
    tokens = [token for token in tokens if token not in stopwords_set]
    return set(tokens)


def jaccard_similarity(set1, set2):
    intersection = set1.intersection(set2)
    union = set1.union(set2)
    return len(intersection) / len(union) if union else 0


def similarity_search(main_str_set, match_str_set):
    return jaccard_similarity(main_str_set, match_str_set)


def search_db(search_terms, index_tool_id):
    db_results = []
    search_conditions = [
        ("title", 5.0),
        ("content", 0.3),
        ("summary", 0.8),
    ]

    query_template = """
    SELECT site_vectors.id, site_vectors.content, site_index.url, site_vectors.vector_type as vector_type
    FROM site_vectors
    JOIN site_index ON site_vectors.site_index_id = site_index.id
    WHERE site_vectors.vector_type = '{vector_type}' AND site_index.index_tool_id = {index_tool_id}
    ;
    """

    for term in search_terms:
        if not term:
            continue

        preprocessed_term = preprocess_text(term)

        term_results_count = 0
        for vector_type, weight in search_conditions:
            query = query_template.format(vector_type=vector_type, index_tool_id=index_tool_id)
            term_results = fetch_sql_query(query)

            for row in term_results:
                matches = similarity_search(preprocessed_term, preprocess_text(row[1].decode('utf-8')))
                if matches > 0:
                    db_results.append((row, term, matches * weight))  
                    term_results_count += 1
        print(f"Results found for '{term}': {term_results_count}")

    db_results.sort(key=lambda x: x[2], reverse=True)  
    return db_results


def search_database(search_terms, index_tool_id):
    connection = load_database()
    if connection is None:
        print("Failed to load database.")
        return None

    cursor = connection.cursor()
    db_results = search_db(search_terms, index_tool_id)
    processed_db_results = process_db_results(db_results)
    grouped_results = group_results_by_term(processed_db_results, search_terms)

    cursor.close()
    connection.close()

    return grouped_results


def process_db_results(db_results):
    processed_results = []
    rank = 1
    previous_similarity = db_results[0][2] if db_results else 0  
    for ((vector_id, content, url, vector_type), search_term, similarity) in db_results:
        if similarity != previous_similarity:
            rank += 1
            previous_similarity = similarity
        processed_results.append(
            {
                'Search Term': search_term,
                'Vector ID': vector_id,
                'URL': url,
                'Vector Type': vector_type,
                'Rank': rank,
            }
        )
    return processed_results


def group_results_by_term(processed_results, search_terms):
    grouped_results = defaultdict(list)

    for result in processed_results:
        term = result['Search Term']
        grouped_results[term].append(result)

    for term in search_terms:
        grouped_results[term].sort(key=lambda x: x['Rank'])
        grouped_results[term] = grouped_results[term][:3]

    return grouped_results


if __name__ == "__main__":
    search_terms = ['Canada', 'Cactus', 'Restaurant']
    index_tool_id = 1  # Assuming a site index id for example
    print(search_database(search_terms, index_tool_id))
