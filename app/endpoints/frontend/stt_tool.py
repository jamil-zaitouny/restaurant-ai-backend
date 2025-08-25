from fastapi import APIRouter, HTTPException, UploadFile, File, Query
import openai
from deepgram import DeepgramClient, PrerecordedOptions, FileSource
import shutil
import os
from dotenv import load_dotenv
import json

load_dotenv()  # Load environment variables from .env file

# Initialize OpenAI with API key
openai.api_key = os.getenv('OPENAI_API_KEY')

# Initialize your Deepgram client
deepgram_api_key = os.environ.get("DEEPGRAM_API_KEY")
deepgram_client = DeepgramClient(deepgram_api_key)

stt_router = APIRouter()

@stt_router.post("/convert_speech_to_text/")
async def convert_speech_to_text(
    audio_file: UploadFile = File(...),
    provider: str = Query("deepgram", enum=["deepgram", "openai"])
):
    temp_file_path = f"temp_{audio_file.filename}"
    try:
        with open(temp_file_path, "wb") as buffer:
            shutil.copyfileobj(audio_file.file, buffer)

        if provider == "deepgram":
            with open(temp_file_path, "rb") as file:
                buffer_data = file.read()

            payload: FileSource = {
                "buffer": buffer_data,
            }

            options = PrerecordedOptions(
                model="nova-2",
                smart_format=True,
            )

            response = deepgram_client.listen.prerecorded.v("1").transcribe_file(payload, options)
            response_content = response.to_json(indent=4)

            # Log the response for debugging
            print(response_content)

            # Directly parse the JSON string to avoid an extra conversion step
            response_json = json.loads(response_content)

            # Correct path based on your provided structure
            transcription_text = response_json['results']['channels'][0]['alternatives'][0]['transcript']

            # Handle empty transcriptions
            if not transcription_text.strip():
                transcription_text = "- Transcription wasnt able to detect speach -"
        else:  # provider == "openai"
            with open(temp_file_path, "rb") as f:
                transcript = openai.Audio.transcriptions.create(
                    model="whisper-1",
                    file=f
                )
            transcription_text = transcript.text  # Changed to access .text property directly

            # Handle empty transcriptions
            if not transcription_text.strip():
                transcription_text = "- Transcription wasnt able to detect speach -"

        return {"text": transcription_text}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        # Delete the temporary file
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)