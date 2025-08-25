import sys
from datetime import datetime
from app.model.callbacks.token_logging_callback import TokenLoggingCallback
from app.model.db.frontend.db_logging import log_token_usage
from app.utilities.usage_billings_helper import log_gpt_embeddings_usage

sys.path.insert(0, 'C:\\Own Your AI GIT\\SiteAI-Backend')
import threading
import time
import gzip
import io
import traceback
from queue import Queue, Empty
from threading import Lock
from concurrent.futures import ThreadPoolExecutor, TimeoutError
from urllib.parse import urljoin, parse_qs, urlencode, urlparse, urlunparse
from urllib.robotparser import RobotFileParser
from bs4 import BeautifulSoup
#from langchain.chat_models import ChatOpenAI
from langchain_community.chat_models import ChatOpenAI

from tldextract import extract
import requests
from requests.adapters import HTTPAdapter
from urllib3.util import Retry
import xml.etree.ElementTree as ET
import openai
import tiktoken
from pinecone import Pinecone, ServerlessSpec
from time import sleep
from app.model.db.db_base import execute_sql_query
from app.model.db.db_base import load_database
from langchain.text_splitter import RecursiveCharacterTextSplitter
from concurrent.futures import as_completed
from app.utilities.openai_helper import get_openai_api_key, convert_to_langchain_message, get_pinecone_api_key, \
    get_pinecone_environment, get_pinecone_index_name
from dotenv import load_dotenv
import os

load_dotenv()  # load variables from .env

embed_model = "text-embedding-ada-002"
index_tool_id = 1

def get_pinecone_api_key():
    return os.environ.get('PINECONE_API_KEY')

def get_pinecone_environment():
    return os.environ.get('PINECONE_ENVIRONMENT')

pc = Pinecone(
    api_key=get_pinecone_api_key()
)

tokenizer = tiktoken.get_encoding('p50k_base')

# Create the length function
def tiktoken_len(text):
    tokens = tokenizer.encode(
        text,
        disallowed_special=()
    )
    return len(tokens)

text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=200,  # TODO put in db or front end with default values
    chunk_overlap=10,  # TODO put in db or front end with default values
    length_function=tiktoken_len,
    separators=["\n\n", "\n", " ", ""]
)

# Helper functions in full form

def is_valid_url(url):
    """Check if the given URL is valid."""
    parsed = urlparse(url)
    return bool(parsed.netloc) and bool(parsed.scheme)

def get_domain(url):
    """Extract the domain from the given URL."""
    tsd, td, tsu = extract(url)
    return td + '.' + tsu

def is_same_domain(url1, url2):
    """Check if two URLs belong to the same domain."""
    return get_domain(url1) == get_domain(url2)

def is_subdomain(url1, url2):
    """Check if two URLs are subdomains of each other."""
    subdomain1 = extract(url1).subdomain
    subdomain2 = extract(url2).subdomain
    return subdomain1 != subdomain2

def create_session():
    """Create a session with retries and a custom User-Agent."""
    session = requests.Session()
    retry = Retry(total=3, backoff_factor=0.1, status_forcelist=[500, 502, 503, 504])
    adapter = HTTPAdapter(max_retries=retry)
    session.mount('http://', adapter)
    session.mount('https://', adapter)
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/93.0.4577.63 Safari/537.36'
    })
    return session

def get_robots_txt_url(url):
    """Get the robots.txt URL for the given URL."""
    parsed = urlparse(url)
    return f"{parsed.scheme}://{parsed.netloc}/robots.txt"

def filter_url_parameters(url, exclude_params=None):
    """Filter out unwanted URL parameters."""
    if exclude_params is None:
        exclude_params = {'utm_source', 'utm_medium', 'utm_campaign', 'utm_term', 'utm_content', 'sessionid'}

    parsed = urlparse(url)
    query_params = parse_qs(parsed.query)

    filtered_query_params = {k: v for k, v in query_params.items() if k not in exclude_params}
    filtered_query = urlencode(filtered_query_params, doseq=True)

    filtered_url = urlunparse((parsed.scheme, parsed.netloc, parsed.path, parsed.params, filtered_query,
                               ''))  # Set fragment to an empty string
    return filtered_url

def extract_main_content(soup):
    """Extract the main content from the BeautifulSoup object."""
    for tag in soup(['script', 'style', 'header', 'footer', 'nav', 'aside']):
        tag.decompose()

    main_content = soup.find_all(['article', 'main', 'section', 'div'], recursive=True)

    if main_content:
        main_content = max(main_content, key=lambda x: len(x.text))
        return main_content.get_text(strip=True)
    else:
        return soup.get_text(strip=True)

def process_content(site_index_id, content, vector_type, tool_index_id, url, image_url, instance_id):
    texts = text_splitter.split_text(content)
    threads = []

    for i, text in enumerate(texts):
        thread = threading.Thread(target=save_chunk_to_db,
                                  args=(site_index_id, text, vector_type, tool_index_id, url, image_url, instance_id))
        thread.start()
        threads.append(thread)

    # Wait for all threads to finish
    for thread in threads:
        thread.join()

def save_chunk_to_db(site_index_id, content, vector_type, index_tool_id, url, image_url, instance_id):
    query = "INSERT INTO site_vectors (site_index_id, content, vector_type) VALUES (%s, %s, %s)"
    data = (site_index_id, content, vector_type)
    site_vector_id = execute_sql_query(query, data)

    # Upsert to Pinecone
    pinecone_namespace = get_pinecone_index_name()
    index = pc.Index(index_name=pinecone_namespace)

    # Create embeddings
    try:
        start = datetime.now()
        res = openai.Embedding.create(input=[content], engine=embed_model)
        end = datetime.now()
        usage_id = log_token_usage(content, None, 0, 0, start, end, 'ada_embeddings', index_tool_id, 'index_tool',
                                   None, None, tokens_embeddings=tiktoken_len(content))
        log_gpt_embeddings_usage(usage_id, 1, 'ada', tiktoken_len(content), 'embeddings_search', instance_id)
    except:
        done = False
        while not done:
            sleep(5)
            try:
                res = openai.Embedding.create(input=[content], engine=embed_model)
                done = True
            except:
                pass

    embeds = [record['embedding'] for record in res['data']]

    metadata = {
        "vector_type": vector_type,
        "index_tool_id": index_tool_id,
        "site_index_id": site_index_id,
        "content": content,
        "url": url,
        "image_url": image_url
    }

    to_upsert = [(str(site_vector_id), embeds[0], metadata,)]
    index.upsert(vectors=to_upsert)

def execute_sql_query(query, data):
    connection = load_database()
    cursor = connection.cursor()

    cursor.execute(query, data)
    connection.commit()

    last_inserted_id = cursor.lastrowid

    cursor.close()
    connection.close()

    return last_inserted_id

def fetch_sql_query(query, params=None):
    connection = load_database()
    if connection is None:
        print("Failed to connect to database.")
        return None

    cursor = connection.cursor()

    if params:
        cursor.execute(query, params)
    else:
        cursor.execute(query)

    result = cursor.fetchall()
    field_names = [i[0] for i in cursor.description]
    cursor.close()
    connection.close()

    return [dict(zip(field_names, row)) for row in result]

def get_primers(index_tool_id):
    query = "SELECT summary_primer_before, summary_primer_after FROM index_tool WHERE id = %s"
    params = (index_tool_id,)
    result = fetch_sql_query(query, params)
    if result:
        return result[0]['summary_primer_before'], result[0]['summary_primer_after']
    else:
        return None, None

"""
    1. Create site_index
    2. get site_index_id
    3. Use that site_index_id after processing to run process_site_index_records
"""
import re
from urllib.parse import urlparse, urlunparse
import json

class URLNormalizationError(Exception):
    pass

def process_site_index_records(site_index_id, tool_index_id, instance_id):
    query = "SELECT id, content, summary, pagetitle, image_url, url FROM site_index WHERE id = %s"

    records = fetch_sql_query(query, (site_index_id,))
    for record in records:
        process_content(site_index_id, record['content'].decode('utf-8'), 'content', tool_index_id,
                        record['url'].decode('utf-8'), record['image_url'].decode('utf-8'), instance_id)
        process_content(site_index_id, record['summary'].decode('utf-8'), 'summary', tool_index_id,
                        record['url'].decode('utf-8'), record['image_url'].decode('utf-8'), instance_id)
        process_content(site_index_id, record['pagetitle'].decode('utf-8'), 'title', tool_index_id,
                        record['url'].decode('utf-8'), record['image_url'].decode('utf-8'), instance_id)

def get_summary(index_tool_id, truncate_content, model_type, instance_id):
    filter_primer_before, filter_primer_after = get_primers(index_tool_id)
    llm = ChatOpenAI(max_retries=3, max_tokens=150, request_timeout=10, openai_api_key=get_openai_api_key(), callbacks=[TokenLoggingCallback(1,
                                                                                                                                             'get_summary',
                                                                                                                                             model_type,
                                                                                                                                             None,
                                                                                                                                             None,
                                                                                                                                             index_tool_id,
                                                                                                                                             'index_tool',
                                                                                                                                             'summary',
                                                                                                                                             instance_id)])
    messages = [
        {"role": "system", "content": filter_primer_before},
        {"role": "user", "content": truncate_content},
        {"role": "system", "content": filter_primer_after},
    ]

    messages = [convert_to_langchain_message(message) for message in messages]
    return llm.generate([messages]).generations[0][0].text

def extract_page_info(soup):
    """Extract page information from the BeautifulSoup object."""
    title_tag = soup.find("title")
    page_title = title_tag.text if title_tag else ""

    main_image = extract_main_image(soup)

    structured_data = extract_structured_data(soup)

    page_type = "Unknown"
    for data in structured_data:
        if "@type" in data:
            page_type = data["@type"]
            break

    description = extract_description(soup)

    return page_type, page_title, main_image, structured_data, description

def extract_description(soup):
    """Extract the description from the BeautifulSoup object."""
    meta_description = soup.find("meta", attrs={"name": "description"})
    if meta_description and meta_description.get("content"):
        return meta_description["content"]
    else:
        main_content = extract_main_content(soup)
        sentences = main_content.split(".")
        return ". ".join(sentences[:2]) + "."

def extract_main_image(soup):
    """Extract the main image from the BeautifulSoup object."""
    og_image = soup.find("meta", property="og:image")
    if og_image and og_image.get("content"):
        return og_image["content"]
    else:
        main_tag = soup.find("main")
        if main_tag:
            img_tag = main_tag.find("img")
            if img_tag and img_tag.get("src"):
                return img_tag["src"]
    return ""

def extract_structured_data(soup):
    """Extract structured data from the BeautifulSoup object."""
    structured_data = []

    # Extract JSON-LD scripts
    for script in soup.find_all("script", type="application/ld+json"):
        try:
            data = json.loads(script.string)
            structured_data.append(data)
        except json.JSONDecodeError:
            pass

    # Add logic to extract Microdata and RDFa if needed

    return structured_data

def truncate_content(content, max_words=1000):
    """Truncate the content to a specified number of words."""
    words = content.split()
    truncated_words = words[:max_words]
    return " ".join(truncated_words)

def sitemap_parser(url, session):
    """Parse the sitemap and return a list of URLs."""
    urls_to_return = []
    try:
        status_code = session.get(url, timeout=10, allow_redirects=True)
        content_type = status_code.headers.get('Content-Type', '')

        if 'xml' in content_type:
            root = ET.fromstring(status_code.content)
        elif 'gzip' in content_type:
            with gzip.open(io.BytesIO(status_code.content), 'rb') as f:
                root = ET.parse(f).getroot()
        else:
            return []

        for sitemap in root:
            for loc in sitemap:
                if loc.tag.endswith("loc"):
                    if 'sitemap' in loc.text:
                        urls_to_return.extend(sitemap_parser(loc.text, session))
                    else:
                        urls_to_return.append(loc.text)
    except Exception as e:
        print(f"Error parsing sitemap: {url}, {str(e)}")
        traceback.print_exc()  # print the traceback
    return urls_to_return


def should_skip_url(url):
    """Check if the URL should be skipped based on predefined patterns."""
    patterns_to_skip = [
        r"/(feed|trackback|comment|attachment)/",
        r"\?(p|share|replytocom|print|add-to-cart|lang|cal|event|filter)=",
        r"#(comment|respond|reviews|tab|add-your-review|product-tab)",
        r"/(wp-json|oembed|wp-admin|wp-login|wp-content|wp-includes|xmlrpc)/",
        r"/(cgi-bin|wp-trackback)/",
        r"/(category|tag|author|search)/",
        r"/(cart|checkout|my-account|wishlist|shop|terms|privacy|cookie)/",
        r"/(login|register|logout|password-reset|account|profile)/",
        r"/(ajax|json|js|css|img|fonts|media)/",
        r"/(assets|static|uploads|cache|tmp|plugins|themes)/",
        r"/(calendar|events|schedule|bookings)/",
        r"/(sitemap|robots)/",
        r"/(page|index|default|home)\d*",
        r"\.(jpg|jpeg|png|gif|bmp|tiff|webp|ico|svg|pdf|doc|docx|xls|xlsx|ppt|pptx|txt|csv|zip|rar|tar|gz|bz2|7z|mp3|mp4|wav|ogg|webm|flv|swf|avi|mov|wmv|mkv|iso|dmg|exe)$",
    ]

    for pattern in patterns_to_skip:
        if re.search(pattern, url, re.IGNORECASE):
            return True

    return False

def crawler(start_url, follow_index, follow_subdomains, follow_links_not_in_sitemap, follow_links_not_in_robot,
            max_depth, max_pages_to_crawl, model_type, index_tool_id=1, category="cactus_club", instance_id = None):
    """Main crawler function."""

    visited_urls = set()
    queued_urls = set()
    visited_urls_lock = Lock()
    queued_urls_lock = Lock()
    num_crawled_lock = Lock()
    to_visit = Queue()
    to_visit.put((start_url, 0))  # Also store depth with each URL
    domain = get_domain(start_url)
    num_crawled = 0

    session = create_session()

    # Start with sitemap
    sitemap_url = f"{urlparse(start_url)._replace(path='/sitemap.xml').geturl()}"
    for url in sitemap_parser(sitemap_url, session):
        to_visit.put((url, 0))

    robot_parser = RobotFileParser()
    robot_parser.set_url(get_robots_txt_url(start_url))
    robot_parser.read()

    def worker(url, depth):
        nonlocal num_crawled
        with visited_urls_lock:
            if url in visited_urls or (max_pages_to_crawl is not None and num_crawled >= max_pages_to_crawl):
                return

        try:
            if not follow_links_not_in_robot and not robot_parser.can_fetch("*", url):
                return

            status_code = session.get(url, timeout=10, allow_redirects=True)
            print(f"Crawling: {url}")
            crawl_time = int(time.time())

            soup = BeautifulSoup(status_code.content, "html.parser")

            main_content = extract_main_content(soup)

            page_type, page_title, main_image, structured_data, description = extract_page_info(soup)

            word_count = len(main_content.split())
            summary = get_summary(index_tool_id, truncate_content(main_content), model_type, instance_id)

            with num_crawled_lock:
                num_crawled += 1
                llmid = f"A{num_crawled:03}"

            insert_site_index_query = "INSERT INTO site_index (index_tool_id, llmid, url, status_code, crawltime, updatetime, page_type, category, image_url, description, wordcount, pagetitle, content, summary, structured_data) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
            insert_site_index_data = (
                index_tool_id, llmid, url, status_code.status_code, crawl_time, None, page_type, category,
                main_image, description, word_count, page_title, main_content, summary, json.dumps(structured_data))
            site_index_id = execute_sql_query(insert_site_index_query, insert_site_index_data)
            process_site_index_records(site_index_id, index_tool_id, instance_id)

            if status_code.status_code != 200:
                return

            if max_depth is None or depth < max_depth:
                for link in soup.find_all(['a', 'link']):
                    href = link.get('href') or link.get('data-href')
                    if not href or "#" in href:
                        continue

                    href = urljoin(url, href)
                    href = filter_url_parameters(href)

                    if not is_valid_url(href):
                        continue

                    if not follow_links_not_in_sitemap and "sitemap" in href.lower():
                        continue

                    if not is_same_domain(href, domain):
                        continue

                    if not follow_subdomains and is_subdomain(href, domain):
                        continue

                    if not should_skip_url(href):
                        with queued_urls_lock:
                            if href not in queued_urls:
                                queued_urls.add(href)
                                to_visit.put((href, depth + 1))

            with visited_urls_lock:
                visited_urls.add(url)

        except Exception as e:
            traceback.print_exc()  # print the traceback
            print(f"Error: {e}")

        finally:
            time.sleep(0.5)

    num_threads = 30
    executor = ThreadPoolExecutor(max_workers=num_threads)

    while not to_visit.empty():
        futures = []
        while not to_visit.empty():
            try:
                url, depth = to_visit.get(timeout=10)
                future = executor.submit(worker, url, depth)
                futures.append(future)
            except Empty:
                break

        for future in as_completed(futures):
            try:
                future.result(timeout=30)
            except TimeoutError:
                print(f"Timeout : Skipping {url}")

    executor.shutdown(wait=True)


if __name__ == '__main__':
    # Inputs
    start_url = "https://cactusclubcafe.com"
    follow_index = True
    follow_subdomains = True
    follow_links_not_in_sitemap = True
    follow_links_not_in_robot = True
    max_depth = None  # Set max_depth as required, None for unlimited
    max_pages_to_crawl = 5000  # Set max_pages_to_crawl as required, None for unlimited

    crawler(start_url, follow_index, follow_subdomains, follow_links_not_in_sitemap, follow_links_not_in_robot, max_depth,
            max_pages_to_crawl, index_tool_id)
