# app\endpoints\frontend\client_instance.py
from typing import List, Optional

from fastapi import APIRouter
from typing import List
from pydantic import BaseModel
from fastapi import Path

from app.model.db.wordpress.db_client import get_all_instance_tools_for_client


class ToolOutput(BaseModel):
    instance_tool_id: int
    tool_id: int
    tool_name: str
    type: str  # Added the type attribute
    status: bool
    status_details: str


class ClientInstanceOutput(BaseModel):
    instance_id: int
    instance_type: str
    location_name: str
    status: str  # New field for the instance status
    tools: List[ToolOutput]


router = APIRouter()

@router.get("/client_instance/{client_id}", response_model=List[ClientInstanceOutput])
async def get_all_client_instances(client_id: int = Path(..., description="The ID of the client")):
    client_instances = get_all_instance_tools_for_client(client_id)

    # Group by instance
    grouped_instances = {}
    for row in client_instances:
        if row[0] not in grouped_instances:
            grouped_instances[row[0]] = {
                "instance_id": row[0],
                "instance_type": row[1],
                "status": row[2],  # New field for the instance status
                "location_name": row[3],  # Updated index
                "tools": []
            }
        grouped_instances[row[0]]["tools"].append(ToolOutput(
            instance_tool_id=row[4],  # Updated index
            tool_id=row[5],  # Updated index
            tool_name=row[3],  # Updated index
            type=row[6],  # Updated index
            status=row[7],  # Updated index
            status_details=row[8]  # Updated index
        ))

    return list(grouped_instances.values())
