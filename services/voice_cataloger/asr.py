import os
import tempfile
import whisper
from fastapi import HTTPException

# Load the base model (145MB) to keep things lightweight!
# It will auto-download on the very first run.
WHISPER_MODEL = os.getenv("WHISPER_MODEL", "base")
print(f"Loading Whisper '{WHISPER_MODEL}' model...")
model = whisper.load_model(WHISPER_MODEL)

def transcribe_audio(audio_bytes: bytes, language_hint: str = None) -> dict:
    """
    Transcribes audio bytes to text using Whisper.
    
    Args:
        audio_bytes: Raw bytes from the uploaded audio file.
        language_hint: Optional ISO-639-1 language code (e.g., 'hi' for Hindi).
    
    Returns:
        dict: {"text": "Transcribed text", "language": "detected_or_hinted_language"}
    """
    if len(audio_bytes) < 1000:
        raise HTTPException(status_code=422, detail="Audio file is too short or empty.")

    # Whisper requires a physical file path or numpy array. 
    # The easiest and most robust way is a temporary file.
    with tempfile.NamedTemporaryFile(delete=False, suffix=".m4a") as tmp_file:
        tmp_file.write(audio_bytes)
        tmp_file_path = tmp_file.name

    try:
        # Prepare decode options
        options = {}
        if language_hint:
            options["language"] = language_hint
            
        # Transcribe!
        result = model.transcribe(tmp_file_path, **options)
        
        return {
            "text": result["text"].strip(),
            "language": result.get("language", language_hint)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Transcription failed: {str(e)}")
    finally:
        # Always clean up the temp file
        if os.path.exists(tmp_file_path):
            os.remove(tmp_file_path)
