from fastapi import APIRouter
from pydantic import BaseModel
from app.model.db.db_base import fetch_sql_query, execute_sql_query_and_get_id

router = APIRouter()

class EmbedInput(BaseModel):
    embed_id: str
    chat_history: str = ""
    menu_system: str = ""



# The bellow is a sample payload for the /presets/ endpoint
# This should be sent in json
# payload = {
#     'embed_id': 'example_embed_id',
# }


@router.post("/presets/")
async def get_presets(embedInput: EmbedInput):
    query = "SELECT chat_history, menu_system FROM presets WHERE embed_id=%s"
    result = fetch_sql_query(query, (embedInput.embed_id,))

    if result is None or len(result) == 0:
        return {"detail": f"No preset found for embed_id: {embedInput.embed_id}"}

    return {"chat_history": result[0][0], "menu_system": result[0][1]}



# The bellow is a sample payload for the /create-preset/ endpoint
# This should be sent in json
# payload = {
#     'embed_id': 'example_embed_id',
#     'chat_history': 'example_chat_history',
#     'menu_system': 'example_menu_system',
# }

@router.post("/create-preset/")
async def create_preset(embedInput: EmbedInput):
    query = "INSERT INTO presets (embed_id, chat_history, menu_system) VALUES (%s, %s, %s)"
    id = execute_sql_query_and_get_id(query, (embedInput.embed_id, embedInput.chat_history, embedInput.menu_system))

    if id is None:
        return {"detail": "Failed to create preset in the database."}

    return {"id": id, "embed_id": embedInput.embed_id, "chat_history": embedInput.chat_history, "menu_system": embedInput.menu_system}
