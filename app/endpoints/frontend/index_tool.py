from fastapi import FastAPI, APIRouter
from pydantic import BaseModel

from app.indexer.crawler import crawler
from app.model.db.tool.db_instance_tool import insert_or_update_instance_tool
from app.model.db.wordpress.db_index_tool import insert_index_tool

router = APIRouter()

class IndexToolCreateRequest(BaseModel):
    start_url: str
    follow_index: bool
    follow_subdomains: bool
    follow_links_not_in_sitemap: bool
    follow_links_not_in_robot: bool
    max_depth: int
    max_pages_to_crawl: int
    instance_id: int
    category: str
    agent_name: str
    agent_description: str
    llm_model: str
    response_primer_before: str
    response_primer_after: str
    filter_primer_before: str
    filter_primer_after: str
    summary_primer_after: str
    summary_primer_before: str
    site_index_name: str


@router.post("/index_tool")
def create_index_tool(request: IndexToolCreateRequest):
    # Extract the variables from the request
    start_url = request.start_url
    follow_index = request.follow_index
    follow_subdomains = request.follow_subdomains
    follow_links_not_in_sitemap = request.follow_links_not_in_sitemap
    follow_links_not_in_robot = request.follow_links_not_in_robot
    max_depth = request.max_depth
    max_pages_to_crawl = request.max_pages_to_crawl

    tool_id = 3

    instance_tool_id, _ = insert_or_update_instance_tool(
        request.instance_id,
        tool_id,
        request.agent_name,
        request.agent_description,
        True,
        "Initial state of instance tool is on",
        request.llm_model
    )

    index_tool_id = insert_index_tool(
        request.response_primer_before,
        request.response_primer_after,
        request.filter_primer_before,
        request.filter_primer_after,
        request.site_index_name,
        instance_tool_id,
        request.summary_primer_before,
        request.summary_primer_after
    )
    category = request.category

    # Call your crawler function here with the extracted variables
    crawler(start_url,
            follow_index,
            follow_subdomains,
            follow_links_not_in_sitemap,
            follow_links_not_in_robot,
            max_depth,
            max_pages_to_crawl,
            request.llm_model,
            index_tool_id,
            category,
            request.instance_id)

    return {"message": "Index tool created successfully"}
