from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.model.db.tool.db_instance_tool import insert_or_update_instance_tool
from app.model.db.tool.db_tool import get_tool_by_id
from app.model.db.wordpress.db_llmcall_tool import insert_llm_call_tool
from fastapi.responses import Response

# Import other necessary modules and classes


router = APIRouter()


class LLMCallToolInput(BaseModel):
    # Define the fields required for LLMCallTool
    response_primer_before: str
    response_primer_after: str
    agent_system_prompt_title: str
    agent_system_prompt_description: str
    llm_model: str
    context: str
    description: str
    instance_id: int
    tool_id: int


@router.post("/simple_tool")
async def simple_tool(llmcall_tool_input: LLMCallToolInput):
    tool_id, _, _, tool_type = get_tool_by_id(llmcall_tool_input.tool_id)
    if tool_type != 'single_call':
        raise HTTPException(status_code=500, detail="You can only send tools with the type single call!")

    instance_tool_id, _ = insert_or_update_instance_tool(
        llmcall_tool_input.instance_id,
        tool_id,
        llmcall_tool_input.agent_system_prompt_title,
        llmcall_tool_input.agent_system_prompt_description,
        True,
        "Initial state of instance tool is on",
        llmcall_tool_input.llm_model
    )

    insert_llm_call_tool(llmcall_tool_input.response_primer_before,
                         llmcall_tool_input.response_primer_after,
                         llmcall_tool_input.context,
                         instance_tool_id)

    return Response(status_code=200)
