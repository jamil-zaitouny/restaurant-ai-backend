from fastapi import APIRouter, Path, HTTPException
from pydantic import BaseModel
import logging

from app.model.db.tool.db_instance_tool import insert_or_update_instance_tool
from app.model.db.wordpress.db_instance import get_instance_id

router = APIRouter()
logger = logging.getLogger(__name__)


class InstanceIdOutput(BaseModel):
    id: int
    success: bool


@router.get("/instance/menu_tool/{menu_tool_id}", response_model=InstanceIdOutput)
async def get_instance_with_menu_tool(
        menu_tool_id: int = Path(..., description="The ID of the menu tool instance")):
    try:
        type = "type"  # Replace with the actual type
        status = "status"  # Replace with the actual status
        description = "description"  # Replace with the actual description
        tool_id = 1  # Replace with the actual tool_id

        instance_id, success = insert_or_update_instance_tool(type, status, description, tool_id, menu_tool_id=menu_tool_id)
        return InstanceIdOutput(id=instance_id, success=success)
    except Exception as exception:
        logger.error(f"An error occurred: {str(exception)}")
        raise HTTPException(status_code=500, detail="An error occurred while processing your request.")


@router.get("/instance/location_tool/{location_tool_id}", response_model=InstanceIdOutput)
async def get_instance_with_location_tool(
        location_tool_id: int = Path(..., description="The ID of the location tool instance")):
    try:
        type = "type"  # Replace with the actual type
        status = "status"  # Replace with the actual status
        description = "description"  # Replace with the actual description
        tool_id = 1  # Replace with the actual tool_id

        instance_id, success = insert_or_update_instance_tool(type, status, description, tool_id,
                                                              location_tool_id=location_tool_id)
        return InstanceIdOutput(id=instance_id, success=success)
    except Exception as exception:
        logger.error(f"An error occurred: {str(exception)}")
        raise HTTPException(status_code=500, detail="An error occurred while processing your request.")


@router.get("/instance/{instance_id}", response_model=InstanceIdOutput)
async def instance_id(instance_id: int = Path(..., description="The ID of the instance")):
    if get_instance_id(instance_id) == '1':
        return {
            "id": instance_id,
            "success": True
        }
    else:
        return {
            "id": instance_id,
            "success": False
        }
