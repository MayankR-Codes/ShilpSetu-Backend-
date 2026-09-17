import sys
import json
from services.voice_cataloger.translate import translate_catalog_text

def test_translation():
    results = {}
    
    # Test 1: Telugu
    telugu_text = "ఇది మట్టితో చేసిన అందమైన ఏనుగు బొమ్మ."
    results["Telugu_Input"] = telugu_text
    results["Telugu_Result"] = translate_catalog_text(telugu_text)

    # Test 2: Hindi
    hindi_text = "यह घर की सजावट के लिए एकदम सही है।"
    results["Hindi_Input"] = hindi_text
    results["Hindi_Result"] = translate_catalog_text(hindi_text)
    
    with open("translation_output.json", "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    test_translation()
