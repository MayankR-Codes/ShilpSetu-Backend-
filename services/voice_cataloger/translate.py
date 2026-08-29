from deep_translator import GoogleTranslator
from fastapi import HTTPException
from api_gateway.logger import get_logger

logger = get_logger(__name__)

def translate_catalog_text(regional_text: str) -> dict:
    """
    Translates the transcribed regional text into English and Hindi.
    """
    if not regional_text.strip():
        return {"english": "", "hindi": ""}
        
    try:
        en_text = GoogleTranslator(source='auto', target='en').translate(regional_text)
        hi_text = GoogleTranslator(source='auto', target='hi').translate(regional_text)
        return {"english": en_text, "hindi": hi_text}
    except Exception as e:
        logger.error(f"Translation failed: {e}")
        # Graceful fallback: just return the original text if API rate limited
        return {"english": regional_text, "hindi": regional_text}
