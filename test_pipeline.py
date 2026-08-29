import sys
import os
import asyncio

# Ensure imports work
sys.path.insert(0, r'C:\Users\KIIT\Desktop\ShilpSetu')

from services.image_studio.pipeline import ImagePipeline

async def main():
    input_path = r'C:\Users\KIIT\.gemini\antigravity\brain\2a6b1a9d-3bcc-4246-9609-170251bb44ee\.user_uploaded\media_1787971216647.jpg'
    
    with open(input_path, 'rb') as f:
        image_bytes = f.read()

    # Make it save directly to our artifact directory so we can display it!
    os.environ['LOCAL_STORAGE_PATH'] = r'C:\Users\KIIT\.gemini\antigravity\brain\2a6b1a9d-3bcc-4246-9609-170251bb44ee'
    
    pipeline = ImagePipeline()
    print('Starting pipeline...')
    result = await pipeline.run(image_bytes, 'artisan_upload.jpg', 'png')
    
    print(f'QUALITY_SCORE: {result["quality_score"]}')
    print(f'SAVED_URL: {result["url"]}')

if __name__ == '__main__':
    asyncio.run(main())
