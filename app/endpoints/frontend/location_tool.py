from typing import List, Optional

from fastapi import APIRouter
from fastapi.responses import Response

from pydantic import BaseModel
from fastapi import Path

from app.model.db.tool.db_tool import get_tool_by_id
from app.model.db.wordpress.db_client import insert_client_instance
from app.model.db.wordpress.db_instance import insert_or_update_instance
from app.model.db.tool.db_instance_tool import insert_or_update_instance_tool
from app.model.db.tool.db_location_tool import insert_or_update_location_tool, get_all_location_tools_for_client, \
    update_location_tool
from app.model.db.wordpress.db_llmcall_tool import insert_llm_call_tool


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
    llm_model: str
    client_id: int
    agent_prompt_description: Optional[str]
    agent_prompt_title: Optional[str]
    location_tool_id: Optional[int] = None
    instance_id: Optional[int] = None
    response_primer_before: Optional[str] = None
    response_primer_after: Optional[str] = None
    context: Optional[str] = None


class LocationToolOutput(BaseModel):
    id: int
    tool_id: Optional[int]
    name: Optional[str]
    description: Optional[str]
    address: Optional[str]
    phone_number: Optional[str]
    website: Optional[str]
    facebook_link: Optional[str]
    twitter_link: Optional[str]
    instagram_link: Optional[str]
    average_price_range: Optional[str]
    status: Optional[str]
    timezone: Optional[str]
    longitude: Optional[str]
    latitude: Optional[str]
    agent_system_prompt_after: Optional[str]
    agent_system_prompt_before: Optional[str]
    order_links: Optional[str]
    reservation_links: Optional[str]


class LocationToolUpdate(BaseModel):
    tools_status: Optional[str]
    agent_system_prompt_after: Optional[str]
    agent_system_prompt_before: Optional[str]


router = APIRouter()


# TODO double check to see if we even need the get/patch endpoints
@router.get("/location_tool/{client_id}", response_model=List[LocationToolOutput])
async def get_all_location_tools_endpoint(client_id: int = Path(..., description="The ID of the client of the tool")):
    location_tools = get_all_location_tools_for_client(client_id)

    # Convert tuples to LocationToolOutput objects
    location_tools = [
        LocationToolOutput(
            id=row[0],
            tool_id=row[1],
            name=row[2],
            description=row[3],
            address=row[4],
            phone_number=row[5],
            website=row[6],
            facebook_link=row[7],
            twitter_link=row[8],
            instagram_link=row[9],
            average_price_range=row[10],
            longitude=row[11],
            latitude=row[12],
            status=row[13],
            timezone=row[14],
            agent_system_prompt_after=row[15],
            agent_system_prompt_before=row[16],
            order_links=row[17],
            reservation_links=row[18],
        )
        for row in location_tools
    ]

    return location_tools


@router.patch("/location_tool/{location_tool}", response_model=LocationToolUpdate)
async def location_tool_update(location_tool: int = Path(..., description="The ID of the location tool"),
                               update: LocationToolUpdate = None):
    try:
        update_location_tool(location_tool, update.tools_status, update.agent_system_prompt_after,
                             update.agent_system_prompt_before)

        return Response(status_code=200)
    except Exception as exception:
        return Response(status_code=500, content=str(exception))


@router.post("/location_tool")
async def location_tool(
        location_tool_input: LocationToolInput
):
    tool_id, _, _, _ = get_tool_by_id(1)
    instance_id, _ = insert_or_update_instance(
        "restaurant location",
        "initiated",
        location_tool_input.description,
        tool_id,
        location_tool_input.agent_system_prompt_before,
        location_tool_input.agent_system_prompt_after,
        location_tool_input.llm_model,
    )

    instance_tool_id, _ = insert_or_update_instance_tool(
        instance_id,
        tool_id,
        location_tool_input.agent_prompt_title,
        location_tool_input.agent_prompt_description,
        True,
        "Initial state of instance tool is on",
        location_tool_input.llm_model
    )

    insert_or_update_location_tool(
        location_tool_input.name,
        location_tool_input.description,
        location_tool_input.address,
        location_tool_input.phone_number,
        location_tool_input.website,
        location_tool_input.facebook_link,
        location_tool_input.twitter_link,
        location_tool_input.instagram_link,
        location_tool_input.average_price_range,
        location_tool_input.longitude,
        location_tool_input.latitude,
        location_tool_input.status,
        location_tool_input.timezone,
        location_tool_input.order_links,
        location_tool_input.reservation_links,
        tool_id,
        instance_id  # pass instance_id here
    )

    insert_client_instance(
        location_tool_input.client_id,
        instance_id,
        "default_role",
        "default_access_privilege"
    )

    insert_llm_call_tool(location_tool_input.response_primer_before,
                         location_tool_input.response_primer_after,
                         location_tool_input.context,
                         instance_tool_id)

    return Response(status_code=200)
