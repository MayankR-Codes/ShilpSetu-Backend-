import os
import json
import google.generativeai as genai
from fastapi import HTTPException
from api_gateway.logger import get_logger

logger = get_logger(__name__)

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

def generate_catalog_listing(english_transcript: str) -> dict:
    """
    Uses Gemini 1.5 Flash to convert raw transcribed text into a structured e-commerce listing.
    """
    if not GEMINI_API_KEY:
        raise HTTPException(status_code=500, detail="GEMINI_API_KEY is not set in the environment.")

    model = genai.GenerativeModel("gemini-3.6-flash")
    
    prompt = f"""
    You are an expert e-commerce copywriter for an Indian artisan platform called ShilpSetu.
    Based on the following artisan's voice note, create a high-converting product listing. 
    Return ONLY a valid JSON object. Do not wrap it in markdown blockquotes like `json`.
    
    Required JSON Format:
    {{
        "title_en": "Catchy Product Title",
        "title_hi": "उत्पाद का शीर्षक",
        "description_en": "A beautiful description...",
        "description_hi": "एक सुंदर विवरण...",
        "features": ["feature 1", "feature 2", "feature 3"],
        "seo_tags": ["tag1", "tag2"]
    }}
    
    Artisan's description (translated to English):
    "{english_transcript}"
    """

    try:
        response = model.generate_content(prompt)
        text = response.text.strip()
        
        # Cleanup potential markdown formatting from LLM
        if text.startswith("```json"):
            text = text[7:]
        if text.startswith("```"):
            text = text[3:]
        if text.endswith("```"):
            text = text[:-3]
            
        return json.loads(text.strip())
    except Exception as e:
        logger.error(f"Gemini generation failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate product description from AI.")
