import openai
from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
import pinecone
import re
import concurrent.futures

from app.utilities.openai_helper import get_pinecone_api_key, get_pinecone_environment

app = FastAPI()
TEMPLATES = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")
openai.api_key = "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"

embed_model = "text-embedding-ada-002"
index_name = 'kms-tools-index'

pinecone.init(
    api_key=get_pinecone_api_key(),
    environment=get_pinecone_environment()
)

# Get the embedding dimensions
embedding_res = openai.Embedding.create(
    input=["example"],
    engine=embed_model
)
embedding_dimensions = len(embedding_res['data'][0]['embedding'])

if index_name not in pinecone.list_indexes():
    pinecone.create_index(
        index_name,
        dimension=embedding_dimensions,
        metric='dotproduct'
    )

index = index_name

@app.get("/")
async def index(req:Request):
    return TEMPLATES.TemplateResponse(
        "index.html",
        {"request": req, "recipes": ["RECIPES"]},
    )

async def process_search_term(search_term):
    # Create an embedding for the search term
    res = openai.Embedding.create(
        input=[search_term],
        engine=embed_model
    )

    # Retrieve the embedding
    xq = res['data'][0]['embedding']

    # Get relevant contexts (including the questions)
    res = index.query(xq, top_k=2, include_metadata=True)

    # Get the list of retrieved text
    contexts = [f"{item['metadata']['text']} {item['metadata']['url']}" for item in res['matches']]

    # Create the augmented query
    augmented_query = "\n\n---\n\n".join(contexts) + "\n\n-----\n\n" + search_term

    return augmented_query

async def get_search_terms(query):
    primer = f"""As an AI language model, create five distinct and coherent search queries related to customer inquiries for product-focused searches on the KMS Tools website. The queries should concentrate on researching products to deliver a thorough and captivating response to similar customer questions. Make sure the search queries prioritize product searches over article searches, and refrain from suggesting searches that are unlikely to produce results on the tools website. Present each search query using the following format: [SEARCH 1: 'Website Search Term']. Only provide the search queries without any additional information.

Example customer query:
I am planning to construct a deck, what should I begin with?
Example Response:
[SEARCH 1: 'Deck Building Tool Kit']
[SEARCH 2: 'Miter Saw']
[SEARCH 3: 'Cordless Drill']
[SEARCH 4: 'Deck Screws']
[SEARCH 5: 'Deck Hardware and Fasteners']"""

    res = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": primer},
            {"role": "user", "content": query}
        ]
    )

    response_content = res['choices'][0]['message']['content']
    search_terms = re.findall(r"\[SEARCH \d+: '(.*?)'\]", response_content)
    return search_terms
"""
    Step 0: Get Query []
    Step 1: Uses LLM to generate 5 search terms in a specific format
    Step 2: Get embeddings for each search terms 

"""
async def search(query, search_terms):
    results = {}

    with concurrent.futures.ThreadPoolExecutor() as executor:
        future_results = {executor.submit(process_search_term, search_term): search_term for search_term in search_terms}
        for future in concurrent.futures.as_completed(future_results):
            search_term = future_results[future]
            result_index = search_terms.index(search_term) + 1
            results[f"Result{result_index}"] = future.result()

    Semantic_Results = ""

    for i, search_term in enumerate(search_terms, 1):
        result_key = f"Result{i}"
        result_value = results[result_key]
        Semantic_Results += f"[Search {i}: '{search_term}', {result_key}: '{result_value}']\n"

    primer = f"""As an advanced language model, please assist customers in finding suitable products on the KMS Tools website. When responding to customer inquiries, provide detailed and accurate information about the products, emphasizing their relevance to the customer's needs. If a combination of products is necessary, explain the benefits of each and how they work together. Always include a URL to the product page for each recommendation.

When interacting with customers, treat them with respect and assume they are competent. Base your suggestions on provided information and only recommend products that genuinely meet their needs. Avoid overselling and ensure the customer understands the advantages of each product you suggest. Provide links to multiple products or ideas when appropriate, and refrain from sharing irrelevant information.

Example:

Customer: I'm looking for a good-quality drill for some home DIY projects.

Assistant: For your home DIY projects, I recommend the Milwaukee M18 1/2" Compact Brushless Drill/Driver Kit (https://www.kmstools.com/milwaukee-m18-1-2-compact-brushless-drill-driver-kit-177659). This drill is powerful, lightweight, and comes with a brushless motor for increased performance and durability. Additionally, it includes two M18 REDLITHIUM batteries and a charger, ensuring you have plenty of power for your projects.

If you need a more versatile option, consider the Bosch 12V Max Flexiclick 5-in-1 Drill/Driver System (https://www.kmstools.com/bosch-12v-max-flexiclick-5-in-1-drill-driver-system-168562). This drill offers multiple attachments, including a right-angle adapter and an offset-angle adapter, allowing you to tackle various tasks with ease.

Please let me know if you have any questions or need further assistance."""

    res = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": primer},
            {"role": "user", "content": query},
            {"role": "system", "content": Semantic_Results}
        ]
    )

    return res['choices'][0]['message']['content']

@app.post("/")
async def send_message(req: Request):
    data = await req.json()
    question = data.get("question")
    search_terms = await get_search_terms(question)
    """
        1. Chocolate
        2. Pie
        ...
    """
    chat_response = await search(question, search_terms)
    """
        prompt_before
            {query}
            {pinecone result from search term}
        promnpt_after
    """
    response = f"{question} - {chat_response}"
    return {"question": question, "response": response}