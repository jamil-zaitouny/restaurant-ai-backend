import traceback

from fastapi import APIRouter
from fastapi.openapi.models import Response
from pydantic import BaseModel

from app.model.db.frontend.db_conversation import insert_conversation

router = APIRouter()


class ConversationInput(BaseModel):
    instance_id: int
    end_user_id: str


@router.post("/conversation/")
async def create_conversation(request: ConversationInput):
    try:
        id = insert_conversation(request.end_user_id, request.instance_id)
        return {
            "id": id
        }
    except Exception as e:
        traceback.print_exc()
        return Response(status_code=500, content=f"failed to create end_user due to {e}")
