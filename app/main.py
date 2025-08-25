import sys
import os
import traceback

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from app.api_helpers.customer_response_helpers import stream_response, get_menu_system_from_ids, get_menu_chat
from datetime import datetime
from fastapi import FastAPI, HTTPException, Request
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List, Dict, Optional
from app.api_helpers.api_helpers import ApiHelpers
from app.endpoints.frontend import location_tool, category_tool, instance, index_tool, simple_tool
from app.model.db.frontend.client_instance import router as client_instance_router
from app.model.db.frontend.db_end_user import insert_end_user
from app.model.db.frontend.db_message import insert_message, update_message
from app.model.db.frontend.db_system_performance import insert_system_performance
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from app.utilities.openai_helper import get_openai_api_key, get_pinecone_api_key, validate_environment
from app.endpoints.backend import conversation
from app.endpoints.frontend.get_presets import router as presets_router
from app.endpoints.frontend.tts_tool import tts_router
from app.endpoints.frontend.stt_tool import stt_router
import logging

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('app.log')
    ]
)

logger = logging.getLogger(__name__)

app = FastAPI()

# Add startup event
@app.on_event("startup")
async def startup_event():
    try:
        logger.info("Starting application...")
        validate_environment()
        logger.info("Environment variables validated successfully")
        
        # Test API keys
        openai_key = get_openai_api_key()
        pinecone_key = get_pinecone_api_key()
        logger.info("API keys validated successfully")
        
    except Exception as e:
        logger.error(f"Startup error: {str(e)}")
        logger.error(traceback.format_exc())
        raise

# Add shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Shutting down application...")

# Add your routers here
app.include_router(location_tool.router)
app.include_router(category_tool.router)
app.include_router(instance.router)
app.include_router(client_instance_router)
app.include_router(index_tool.router)
app.include_router(simple_tool.router)
app.include_router(conversation.router)
app.include_router(presets_router)
app.include_router(tts_router)
app.include_router(stt_router)

TIME_FORMAT = "%Y-%m-%d %H:%M:%S.%f"
base_dir = os.path.dirname(os.path.abspath(__file__))
templates_dir = os.path.join(base_dir, "../static_files/templates")
static_dir = os.path.join(base_dir, "../static_files/static")

TEMPLATES = Jinja2Templates(directory=templates_dir)
app.mount("/static", StaticFiles(directory=static_dir), name="static")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

class BaseConfig:
    protected_namespaces = ()

class ClientId(BaseModel):
    client_id: str
    
    class Config(BaseConfig):
        pass

class EndUserInput(BaseModel):
    id: str
    ipAddress: str
    
    class Config(BaseConfig):
        pass

class MessageInput(BaseModel):
    content: str
    request_timestamp: str
    response_timestamp: str
    additional: str
    uuid: Optional[str]
    conversation_id: str
    
    class Config(BaseConfig):
        pass

class SystemPerformance(BaseModel):
    message_id: str
    timestamp: str
    response_time: int
    status_code: str
    error_type: Optional[str]
    error_message: Optional[str]
    function_name: str
    request_parameters: str
    response_data: str
    error_data: Optional[str]
    
    class Config(BaseConfig):
        pass

class QueryInput(BaseModel):
    query: str
    history: List[Dict[str, str]]
    credit_transaction_id: int
    type: str
    context: str
    model_type: str
    tool_type_id: int
    instance_id: str
    message_id: str
    conversation_id: str
    
    class Config(BaseConfig):
        pass

class CatalogQueryInput(BaseModel):
    query: str
    history: List
    instance_id: str
    conversation_id: str
    
    class Config(BaseConfig):
        pass

def transform_menu_system(menu_system):
    try:
        output = {}
        for item in menu_system:
            key = item['llm_id']
            new_item = {
                'name': item['title'],
                'description': item['summary'],
                'url': item['url'],
                'image_url': item['img_url'],
            }
            output[key] = new_item
        logger.debug(f"Transformed menu system: {output}")
        return output
    except Exception as e:
        logger.error(f"Error transforming menu system: {str(e)}")
        logger.error(traceback.format_exc())
        raise

@app.post("/catalog_system/")
async def get_catalog_system(catalogQueryInput: CatalogQueryInput):
    try:
        logger.debug("Received catalog system request: %s", catalogQueryInput)
        
        message_id = insert_message(catalogQueryInput.conversation_id)
        logger.debug("Inserted message ID: %s", message_id)

        items = stream_response(
            catalogQueryInput.instance_id,
            catalogQueryInput.query,
            catalogQueryInput.history,
            1,
            message_id,
            catalogQueryInput.conversation_id
        )
        logger.debug("Stream response items: %s", items)

        if not items:
            raise HTTPException(status_code=500, detail="No response from stream_response")

        if items[0] in ["single_call", "end_call"]:
            response = {
                "context": str(items[3]),
                "tool_type_id": items[1],
                "type": items[0],
                "message_id": message_id,
                "model_type": items[2]
            }
            logger.debug("Returning %s response: %s", items[0], response)
            return response
                
        elif items[0] == "filter_and_respond":
            menu_system = get_menu_system_from_ids(items[1], items[2])
            menu_chat = get_menu_chat(items[1], items[2])
            response = {
                "menu_items": items[1],
                "menu_system": menu_system,
                "context": str(menu_chat),
                "tool_type_id": items[2],
                "type": items[0],
                "model_type": items[3],
                "message_id": message_id
            }
            logger.debug("Returning filter_and_respond response: %s", response)
            return response

        elif items[0] == "website_search":
            index_chat = items[3]
            index_system = items[4]
            response = {
                "menu_system": transform_menu_system(index_system),
                "context": str(index_chat),
                "tool_type_id": items[1],
                "type": items[0],
                "model_type": items[2],
                "message_id": message_id
            }
            logger.debug("Returning website_search response: %s", response)
            return response

        else:
            raise HTTPException(status_code=400, detail=f"Unknown response type: {items[0]}")

    except Exception as e:
        logger.error("Error in catalog_system: %s", str(e))
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f'Error processing catalog system request: {str(e)}')

@app.post("/create_end_user/")
async def create_end_user(end_user_input: EndUserInput):
    try:
        logger.debug("Creating end user: %s", end_user_input)
        insert_end_user(end_user_input.id, end_user_input.ipAddress)
        return Response(status_code=200)
    except Exception as e:
        logger.error("Error creating end user: %s", str(e))
        logger.error(traceback.format_exc())
        return Response(status_code=500, content=f"Failed to create end user: {str(e)}")

@app.post("/log_message/")
async def log_message(message_input: MessageInput):
    try:
        logger.debug("Logging message: %s", message_input)
        uuid = message_input.uuid or insert_message(message_input.conversation_id)

        update_message(
            uuid,
            message_input.content,
            datetime.strptime(message_input.request_timestamp, TIME_FORMAT),
            datetime.strptime(message_input.response_timestamp, TIME_FORMAT),
            message_input.conversation_id,
            message_input.additional,
        )
        return Response(status_code=200)
    except Exception as e:
        logger.error("Error logging message: %s", str(e))
        logger.error(traceback.format_exc())
        return Response(status_code=500, content=f"Failed to log message: {str(e)}")

@app.post("/log_system_performance/")
async def log_system_performance(system_performance: SystemPerformance):
    try:
        logger.debug("Logging system performance: %s", system_performance)
        insert_system_performance(
            system_performance.message_id,
            system_performance.timestamp,
            system_performance.response_time,
            system_performance.status_code,
            system_performance.error_type,
            system_performance.error_message,
            system_performance.function_name,
            system_performance.request_parameters,
            system_performance.response_data,
            system_performance.error_data
        )
        return Response(status_code=200)
    except Exception as e:
        logger.error("Error logging system performance: %s", str(e))
        logger.error(traceback.format_exc())
        return Response(status_code=500, content=f"Failed to log system performance: {str(e)}")

@app.post("/create_message/")
async def create_message(query_input: QueryInput):
    try:
        logger.debug("Creating message: %s", query_input)
        response = ApiHelpers.generate_response(
            query_input.query,
            query_input.history,
            query_input.credit_transaction_id,
            query_input.context,
            query_input.type,
            query_input.model_type,
            query_input.tool_type_id,
            query_input.instance_id,
            query_input.message_id,
            query_input.conversation_id,
        )
        return StreamingResponse(response)
    except Exception as e:
        logger.error("Error creating message: %s", str(e))
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Failed to create message: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    
    logger.info("Starting development server...")
    uvicorn.run(
        app,
        host="127.0.0.1",
        port=8081,
        log_level="debug"
    )