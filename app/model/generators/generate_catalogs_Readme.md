# Generate Catalogs API

This API generates catalogs (catalog_chat and catalog_system) based on search results from a database and a vector search. The input data must meet certain expectations for the API to work correctly.

## Input Data Expectations

The input data should be in the following format:

- query: A string representing the user query. It should not be empty.
- history: A list of dictionaries containing conversation history. Each dictionary should contain keys "role" and "content".
- index_name: A string representing the name of the index to be used for vector search. It should not be empty.
- account: A string representing the account name for the database. It should not be empty.
- project_type: A string representing the project type. It should not be empty.
- table_name: A string representing the table name for the database. It should not be empty.
- search_model: A string representing the search model to be used. It should not be empty.
- search_primer: A string representing the search primer. It should not be empty.
- response_model: A string representing the response model to be used. It should not be empty.
- response_primer: A string representing the response primer. It should not be empty.

## Output Data

The output data will be in the following format:

- search_terms: A list of search terms generated from the input query.
- vector_results: A list of search results from the vector search.
- db_results: A dictionary of search results from the database search.
- catalog_system: A formatted string representing the system catalog.
- catalog_chat: A formatted string representing the chat catalog.

## Example

### Input

{
  "query": "What are the differences between Python and Java?",
  "history": [],
  "index_name": "my_index",
  "account": "my_account",
  "project_type": "my_project_type",
  "table_name": "my_table_name",
  "search_model": "my_search_model",
  "search_primer": "my_search_primer",
  "response_model": "my_response_model",
  "response_primer": "my_response_primer"
}

### Output

{
  "search_terms": ["Python vs Java", "differences between Python and Java"],
  "vector_results": [...],
  "db_results": {...},
  "catalog_system": "
