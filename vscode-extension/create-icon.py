#!/usr/bin/env python3
"""
Create a 128x128 icon for VS Code extension
"""
from PIL import Image, ImageDraw, ImageFont
import os

# Create a new 128x128 image with a purple gradient background
img = Image.new('RGB', (128, 128), color='#7C3AED')
draw = ImageDraw.Draw(img)

# Draw a white rounded rectangle
padding = 20
draw.rounded_rectangle(
    [(padding, padding), (128-padding, 128-padding)],
    radius=15,
    fill='#FFFFFF',
    outline='#7C3AED',
    width=3
)

# Draw the API text
try:
    # Try to use a system font
    font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 36)
except:
    # Fallback to default font
    font = ImageFont.load_default()

# Draw "API" text in purple
text = "API"
bbox = draw.textbbox((0, 0), text, font=font)
text_width = bbox[2] - bbox[0]
text_height = bbox[3] - bbox[1]
text_x = (128 - text_width) // 2
text_y = (128 - text_height) // 2 - 10
draw.text((text_x, text_y), text, fill='#7C3AED', font=font)

# Draw a small lightning bolt or connection symbol
# Simple connection dots
draw.ellipse([54, 80, 64, 90], fill='#7C3AED')
draw.ellipse([64, 80, 74, 90], fill='#7C3AED')

# Save the icon
icon_path = os.path.join(os.path.dirname(__file__), 'media', 'icon-new.png')
img.save(icon_path, 'PNG')
print(f"Icon created at: {icon_path}")
print(f"Size: {img.size}")