Here's a README.md file for the project:

markdown
Copy code
# AI-Powered Search Engine

This project is an AI-powered search engine that uses OpenAI's GPT model to generate search terms and Pinecone to retrieve vector results from a given index. It also performs a database search to find relevant results based on the generated search terms and their synonyms.

## Dependencies

- FastAPI
- uvicorn
- Pydantic
- OpenAI
- Pinecone
- NLTK

## Installation

1. Install required packages:

pip install fastapi uvicorn pydantic openai pinecone-client nltk

scss
Copy code

2. Download the NLTK `wordnet` corpus (if not already downloaded):

```python
import nltk
nltk.download('wordnet')
Usage
Run the FastAPI server:
css
Copy code
uvicorn main:app --host 127.0.0.1 --port 8214
Make a POST request to the /generate_search_terms/ endpoint with the required query input parameters.
Project Structure
main.py: The main FastAPI application file that handles the API endpoint and coordinates the search


generation and retrieval of results from Pinecone and the database.

search_terms_generator.py: A module that uses OpenAI's GPT model to generate search terms based on the input query and history.

vector_db_search.py: A module that interacts with Pinecone to initialize an index, fetch vector search results, and deinitialize the index.

db_search.py: A module that performs a database search to find relevant results based on the generated search terms and their synonyms.

Results Format
The results returned by the /generate_search_terms/ endpoint will be in the following format:

{
  "search_terms": [array of generated search terms],
  "vector_results": [
    {
      "id": string,
      "vector_score": float,
      "metadata": {
        "title": string,
        "url": string,
        "img_url": string,
        "summary": string,
        "page_type": string
      }
    },
    ...
  ],
  "db_results": {
    "search_term": [
      {
        "Search Term": string,
        "Applicable Condition": {
          "page_type": { "$eq": string },
          "Embedding Type": { "$eq": string }
        },
        "Title": string,
        "URL": string,
        "Image URL": string,
        "Summary": string,
        "Page Type": string,
        "Embedding Type": string,
        "Similarity": float
      },
      ...
    ],
    ...
  }
}




search_terms: An array containing the generated search terms.
vector_results: An array of objects containing the Pinecone vector search results, with each object having an id, vector_score, and a metadata object containing title, url, img_url, summary, and page_type.
db_results: An object with keys corresponding to the search terms and values being arrays containing the most relevant database search results for each search term. Each result object contains the Search Term, Applicable Condition, Title, URL, Image URL, Summary, Page Type, Embedding Type, and a Similarity score.
Contributing
Feel free to submit issues, feature requests, and pull requests to improve the project.