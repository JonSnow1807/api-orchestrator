#!/usr/bin/env python3
"""
Create a simple, clean icon that actually looks good
"""
from PIL import Image, ImageDraw, ImageFont

# Create image
img = Image.new('RGB', (128, 128))
draw = ImageDraw.Draw(img)

# Simple two-color gradient background
for y in range(128):
    # Purple to pink gradient
    ratio = y / 128
    r = int(139 + (236 - 139) * ratio)  # Purple to pink
    g = int(92 + (72 - 92) * ratio)
    b = int(246 + (153 - 246) * ratio)
    draw.rectangle([(0, y), (128, y+1)], fill=(r, g, b))

# Draw simple </> brackets in white (common for API/code tools)
try:
    font = ImageFont.truetype("/System/Library/Fonts/Courier.ttc", 48)
except:
    try:
        font = ImageFont.truetype("/Library/Fonts/Courier New.ttf", 48)
    except:
        font = ImageFont.load_default()

# Draw the brackets
text = "</>"
bbox = draw.textbbox((0, 0), text, font=font)
text_width = bbox[2] - bbox[0]
text_height = bbox[3] - bbox[1]
text_x = (128 - text_width) // 2
text_y = (128 - text_height) // 2

# White text
draw.text((text_x, text_y), text, fill=(255, 255, 255), font=font)

# Save
img.save('/Users/chinmayshrivastava/Api Orchestrator/api-orchestrator/vscode-extension/media/icon.png', 'PNG')
print("Simple clean icon created!")