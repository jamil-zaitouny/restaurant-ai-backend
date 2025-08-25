# Search Terms Generator

This Python script generates search terms based on the provided query, history, search model, and search primer.

## Input variables

- `api_key` (str): Your OpenAI API key
- `query` (str): The user's query
- `history` (List[Dict[str, str]]): A list of dictionaries containing message history. Each dictionary has two keys: "role" (either "system" or "user") and "content" (the message text).
- `search_model` (str): The identifier of the search model to be used
- `search_primer` (str): The search primer text

## Output variable

- `search_terms` (List[str]): A list of search terms extracted from the OpenAI API response

## How to call

Call the `get_search_terms` function with the required input variables:

```python
search_terms = get_search_terms(api_key, query, history, search_model, search_primer)
