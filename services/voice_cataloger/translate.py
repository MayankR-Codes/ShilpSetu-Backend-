import time
from deep_translator import GoogleTranslator
from api_gateway.logger import get_logger

logger = get_logger(__name__)

def translate_catalog_text(regional_text: str) -> dict:
    """
    Translates the transcribed regional text into English and Hindi.
    Includes rate-limit resilience with retry and fallback.
    """
    if not regional_text or not regional_text.strip():
        return {"english": "", "hindi": ""}
        
    en_text = None
    hi_text = None

    # Attempt English translation
    for attempt in range(2):
        try:
            en_text = GoogleTranslator(source='auto', target='en').translate(regional_text)
            break
        except Exception as e:
            if attempt == 0:
                time.sleep(0.4)
            else:
                logger.warning(f"EN translation warning: {e}. Falling back to original text.")
                en_text = regional_text

    # Attempt Hindi translation
    for attempt in range(2):
        try:
            hi_text = GoogleTranslator(source='auto', target='hi').translate(regional_text)
            break
        except Exception as e:
            if attempt == 0:
                time.sleep(0.4)
            else:
                logger.warning(f"HI translation warning: {e}. Falling back to original text.")
                hi_text = regional_text

    return {
        "english": en_text or regional_text,
        "hindi": hi_text or regional_text,
    }

