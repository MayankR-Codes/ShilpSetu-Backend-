import os
import json
from gtts import gTTS
from fastapi.testclient import TestClient
from api_gateway.main import app
from dotenv import load_dotenv

# Ensure env vars are loaded
load_dotenv()

print('Generating Hindi voice note...')
text = "यह एक सुंदर हाथ से बना टेराकोटा हाथी है। यह घर की सजावट के लिए एकदम सही है। इसे प्राकृतिक मिट्टी से बनाया गया है।"
tts = gTTS(text, lang='hi')
tts.save('test_audio.mp3')

print('Sending to /api/v1/catalog/voice...')
client = TestClient(app)
with open('test_audio.mp3', 'rb') as f:
    response = client.post(
        '/api/v1/catalog/voice',
        files={'audio': ('test_audio.mp3', f, 'audio/mpeg')}
    )

print(f'\nSTATUS: {response.status_code}')
if response.status_code == 200:
    print('\nSUCCESS! Generated Catalog JSON:')
    print(json.dumps(response.json(), indent=2, ensure_ascii=False))
else:
    print('ERROR:')
    print(response.text)
