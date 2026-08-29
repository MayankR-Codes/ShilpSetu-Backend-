import sys
import os
import io
from PIL import Image

sys.path.insert(0, r'C:\Users\KIIT\Desktop\ShilpSetu')

from services.image_studio.steps.remove_bg import remove_background
from services.image_studio.steps.upscale import upscale_image
from services.image_studio.steps.color_correct import color_correct

input_path = r'C:\Users\KIIT\.gemini\antigravity\brain\2a6b1a9d-3bcc-4246-9609-170251bb44ee\.user_uploaded\media_1787971216647.jpg'
output_path = r'C:\Users\KIIT\.gemini\antigravity\brain\2a6b1a9d-3bcc-4246-9609-170251bb44ee\final_enhanced_image.png'

print('Opening image...')
img = Image.open(input_path).convert('RGBA')

print('Step 1: Removing Background (rembg)...')
img = remove_background(img)

print('Step 2: Upscaling (Real-ESRGAN or Lanczos)...')
img = upscale_image(img)

print('Step 3: Color Correction (CLAHE)...')
img = color_correct(img)

print(f'Saving to {output_path}...')
img.save(output_path, format='PNG')
print('DONE!')
