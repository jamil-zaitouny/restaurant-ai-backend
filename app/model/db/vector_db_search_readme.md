Sure, here's the same text with Markdown formatting that you can easily paste into an MD file:

# Vector Database Search

This script performs a vector database search using Pinecone and OpenAI's text embeddings.

## Inputs
- `pinecone_api_key`: A string representing the API key for the Pinecone service.
- `environment`: A string representing the environment in which Pinecone is running (e.g., "us-east-1-aws").
- `search_terms`: A list containing one string representing the search term for which to perform the vector database search.
- `index_name`: A string representing the name of the Pinecone index to use for the search.

## Outputs
- `search_results`: A list of tuples, where each tuple contains a search term and its corresponding search results. The search results are represented as a list of dictionaries, where each dictionary represents a single matching item.

Each dictionary in the list of search results has the following structure:

```
{
    'id': item['id'],
    'score': item['score'],
    'metadata': item['metadata'],
    'filter': applicable_condition
}
```

- `id`: A string representing the unique identifier of the matching item.
- `score`: A float representing the similarity score between the search term and the matching item.
- `metadata`: A dictionary containing metadata information about the matching item.
- `filter`: A dictionary representing the conditions used to filter the search results.

## How to Use
1. Import the required function from `vector_db_search.py`:
   ```python
   from vector_db_search import main
   ```
2. Call the `main` function with the following arguments:
   ```python
   pinecone_api_key = "your_pinecone_api_key"
   environment = "your_environment"
   search_term = "your_search_term"
   index_name = "your_index_name"

   search_results = main(pinecone_api_key, environment, [search_term], index_name)
   ```
3. The `search_results` variable now contains the processed and grouped search results.

## Search Results Structure
The search results are organized in the following structure:
- A list named `search_results` contains tuples, where each tuple has two elements:
  - The search term (a string)
  - A list of the search results for that term, where each result is represented as a dictionary with the following keys:
    - `id`: The identifier of the search result
    - `score`: The similarity score of the search result
    - `metadata`: A dictionary containing the metadata of the search result, which includes:
      - `Embedding Type`: The type of embedding (e.g., 'Title')
      - `page_type`: The type of page (e.g., 'Product')
    - `filter`: The filter conditions applied to the search result

For further processing, the exact structure of the search results can be extracted as follows:
```python
[ 
  (search_term_1, [
    {
      'id': id_1,
      'score': score_1,
      'metadata': {
        'Embedding Type': embedding_type_1,
        'page_type': page_type_1
      },
      'filter': filter_conditions_1
    },
    ...
  ]),
  (search_term_2, [
    {
      'id': id_2,
      'score': score_2,
      'metadata': {
        'Embedding Type': embedding_type_2,
        'page_type': page_type_2
      },
      'filter': filter_conditions_2
    },
    ...
  ]),
  ...
]
```

Keep in mind that the variable names may not match the rest of the codebase, so make sure