# app/endpoints/frontend/tts_tool.py

from fastapi import APIRouter, HTTPException
from openai import OpenAI
from starlette.responses import StreamingResponse, Response
from pydantic import BaseModel
import io
import requests
from dotenv import load_dotenv
import os
import logging
import traceback
from typing import Optional

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

class TextToSpeechRequest(BaseModel):
    text: str
    voice: Optional[str] = None
    provider: Optional[str] = "openai"  # Default to OpenAI
    model: Optional[str] = "tts-1"      # Default model

class AudioResponse(BaseModel):
    audio_content: bytes
    content_type: str
    error: Optional[str] = None

tts_router = APIRouter()

def convert_with_openai(text: str, voice: str = "shimmer", model: str = "tts-1") -> tuple[bytes, str]:
    """Convert text to speech using OpenAI's API"""
    try:
        logger.debug(f"Converting text with OpenAI: {text[:100]}...")
        
        response = client.audio.speech.create(
            model=model,
            voice=voice,
            input=text,
            response_format="mp3"
        )
        
        # Get the binary audio data
        audio_data = response.content
        
        if not audio_data:
            raise ValueError("No audio content received from OpenAI")
            
        logger.debug(f"Successfully received audio from OpenAI, content length: {len(audio_data)}")
        return audio_data, "audio/mpeg"
        
    except Exception as e:
        logger.error(f"OpenAI conversion error: {str(e)}")
        logger.error(traceback.format_exc())
        raise

def convert_with_deepgram(text: str, voice: str = "aura-luna-en") -> tuple[bytes, str]:
    """Convert text to speech using Deepgram's API"""
    try:
        logger.debug(f"Converting text with Deepgram: {text[:100]}...")
        url = "https://api.deepgram.com/v1/speak"
        
        headers = {
            "Authorization": f"Token {os.getenv('DEEPGRAM_API_KEY')}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "text": text,
            "voice": voice,
            "encoding": "mp3"
        }
        
        response = requests.post(url, headers=headers, json=payload)
        
        if response.status_code != 200:
            logger.error(f"Deepgram API error: {response.status_code} - {response.text}")
            raise ValueError(f"Deepgram API error: {response.status_code} - {response.text}")
            
        if not response.content:
            raise ValueError("No audio content received from Deepgram")
            
        logger.debug(f"Successfully received audio from Deepgram, content length: {len(response.content)}")
        return response.content, "audio/mpeg"
        
    except Exception as e:
        logger.error(f"Deepgram conversion error: {str(e)}")
        logger.error(traceback.format_exc())
        raise

@tts_router.post("/convert_text_to_speech/")
async def convert_text_to_speech(request: TextToSpeechRequest):
    """
    Convert text to speech and return audio stream
    """
    try:
        if not request.text:
            raise HTTPException(status_code=400, detail="Text cannot be empty")
            
        logger.info(f"Processing TTS request: provider={request.provider}, voice={request.voice}")
        logger.debug(f"Text content: {request.text[:100]}...")

        # First try OpenAI
        try:
            if request.provider.lower() == "openai":
                audio_content, content_type = convert_with_openai(
                    request.text,
                    voice=request.voice or "shimmer",
                    model=request.model
                )
            else:
                raise ValueError("Falling back to Deepgram")
                
        except Exception as e:
            logger.warning(f"OpenAI TTS failed, falling back to Deepgram: {str(e)}")
            # Fallback to Deepgram
            audio_content, content_type = convert_with_deepgram(
                request.text,
                voice=request.voice or "aura-luna-en"
            )

        # Verify audio content
        if not audio_content:
            raise HTTPException(
                status_code=500,
                detail="No audio content generated"
            )

        # Create audio stream
        audio_stream = io.BytesIO(audio_content)
        audio_stream.seek(0)

        logger.info(f"Successfully generated audio, size: {len(audio_content)} bytes")
        
        # Return streaming response with appropriate headers
        return StreamingResponse(
            audio_stream,
            media_type=content_type,
            headers={
                "Content-Disposition": "attachment; filename=audio.mp3",
                "Accept-Ranges": "bytes",
                "Cache-Control": "no-cache",
                "Content-Length": str(len(audio_content))
            }
        )

    except Exception as e:
        logger.error(f"Error in convert_text_to_speech: {str(e)}")
        logger.error(traceback.format_exc())
        
        # Return detailed error response
        return Response(
            content=str(e),
            status_code=500,
            media_type="text/plain"
        )

# Health check endpoint
@tts_router.get("/tts_health")
async def tts_health():
    """Health check endpoint for TTS service"""
    try:
        # Test OpenAI credentials
        if not os.getenv('OPENAI_API_KEY'):
            raise ValueError("OpenAI API key not configured")

        # Test Deepgram credentials
        if not os.getenv('DEEPGRAM_API_KEY'):
            raise ValueError("Deepgram API key not configured")

        # Test actual TTS conversion
        test_text = "Test."
        try:
            audio_content, _ = convert_with_openai(test_text)
            openai_status = "working" if audio_content else "not working"
        except Exception as e:
            openai_status = f"error: {str(e)}"

        try:
            audio_content, _ = convert_with_deepgram(test_text)
            deepgram_status = "working" if audio_content else "not working"
        except Exception as e:
            deepgram_status = f"error: {str(e)}"

        return {
            "status": "healthy",
            "providers": {
                "openai": openai_status,
                "deepgram": deepgram_status
            }
        }
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return {
            "status": "unhealthy",
            "error": str(e)
        }

if __name__ == "__main__":
    # Test the TTS functionality
    from fastapi import FastAPI
    import uvicorn
    
    app = FastAPI()
    app.include_router(tts_router)
    uvicorn.run(app, host="0.0.0.0", port=8000)