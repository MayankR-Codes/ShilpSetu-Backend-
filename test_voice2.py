import os
import json
from gtts import gTTS
from fastapi.testclient import TestClient
from api_gateway.main import app
from dotenv import load_dotenv

load_dotenv()

text = "यह एक सुंदर हाथ से बना टेराकोटा हाथी है। यह घर की सजावट के लिए एकदम सही है। इसे प्राकृतिक मिट्टी से बनाया गया है।"
tts = gTTS(text, lang='hi')
tts.save('test_audio.mp3')

client = TestClient(app)
with open('test_audio.mp3', 'rb') as f:
    response = client.post(
        '/api/v1/catalog/voice',
        files={'audio': ('test_audio.mp3', f, 'audio/mpeg')}
    )

if response.status_code == 200:
    with open('test_output.json', 'w', encoding='utf-8') as out:
        json.dump(response.json(), out, indent=2, ensure_ascii=False)
