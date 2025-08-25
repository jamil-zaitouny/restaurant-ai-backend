from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()


class ToolStreamingResponseInput(BaseModel):
    tool_id: int
    query: str
    client_id: str
