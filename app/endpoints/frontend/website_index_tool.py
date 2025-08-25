from typing import Optional

from fastapi import APIRouter
from pydantic import BaseModel


class LocationToolInput(BaseModel):
    name: str
    description: str
    address: str
    phone_number: str
    website: str
    facebook_link: str
    twitter_link: str
    instagram_link: str
    average_price_range: str
    longitude: str
    latitude: str
    status: str
    timezone: str
    agent_system_prompt_after: str
    agent_system_prompt_before: str
    order_links: str
    reservation_links: str
    client_id: int
    location_tool_id: Optional[int] = None
    instance_id: Optional[int] = None
    response_primer_before: Optional[str] = None
    response_primer_after: Optional[str] = None
    context: Optional[str] = None


router = APIRouter()


@router.post("/website_index_tool")
async def location_tool(
        location_tool_input: LocationToolInput
):
    pass
