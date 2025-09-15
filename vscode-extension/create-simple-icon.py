#!/usr/bin/env python3
"""
Create a simple 128x128 icon for VS Code extension
"""
from PIL import Image, ImageDraw, ImageFont

# Create a new 128x128 image with gradient background
img = Image.new('RGB', (128, 128))
draw = ImageDraw.Draw(img)

# Create gradient background (purple to dark purple)
for i in range(128):
    color_value = int(124 - (i * 0.3))  # Gradient from 124 to darker
    color = (color_value, 58, 237)  # #7C3AED base color
    draw.rectangle([(0, i), (128, i+1)], fill=color)

# Draw white circle background
draw.ellipse([24, 24, 104, 104], fill='white')

# Draw API text
text = "API"
try:
    font = ImageFont.truetype("/System/Library/Fonts/Avenir.ttc", 32)
except:
    try:
        font = ImageFont.truetype("/Library/Fonts/Arial.ttf", 32)
    except:
        # Create a basic font representation
        font = ImageFont.load_default()

# Get text size and center it
bbox = draw.textbbox((0, 0), text, font=font)
text_width = bbox[2] - bbox[0]
text_height = bbox[3] - bbox[1]
x = (128 - text_width) // 2
y = (128 - text_height) // 2 - 5

# Draw text with shadow effect
draw.text((x+2, y+2), text, fill='#5A2FB8', font=font)  # Shadow
draw.text((x, y), text, fill='#7C3AED', font=font)  # Main text

# Save the icon
img.save('/Users/chinmayshrivastava/Api Orchestrator/api-orchestrator/vscode-extension/media/icon-simple.png', 'PNG')
print("Simple icon created at: media/icon-simple.png")