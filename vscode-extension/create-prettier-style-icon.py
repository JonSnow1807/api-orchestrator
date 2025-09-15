#!/usr/bin/env python3
"""
Create an icon in the style of Prettier - simple, clean, memorable
Prettier uses: Colorful background with simple "P" letter
We'll use: Gradient background with clean "A" for API
"""
from PIL import Image, ImageDraw, ImageFont

# Create image
img = Image.new('RGB', (128, 128))
draw = ImageDraw.Draw(img)

# Create a vibrant gradient like Prettier (but our own colors)
# Prettier uses teal/orange, we'll use purple/pink (more modern)
for y in range(128):
    for x in range(128):
        # Diagonal gradient
        progress = (x + y) / 256
        
        # From vibrant purple to hot pink
        r = int(99 + (255 - 99) * progress)   # 99 -> 255
        g = int(102 + (20 - 102) * progress)  # 102 -> 20
        b = int(241 + (147 - 241) * progress) # 241 -> 147
        
        draw.point((x, y), fill=(r, g, b))

# Draw a large, bold "A" in the center (like Prettier's "P")
try:
    # Try to get a nice bold font
    fonts_to_try = [
        ("/System/Library/Fonts/Helvetica.ttc", 72),
        ("/Library/Fonts/Arial Bold.ttf", 72),
        ("/System/Library/Fonts/Avenir Next.ttc", 72),
    ]
    
    font = None
    for font_path, size in fonts_to_try:
        try:
            font = ImageFont.truetype(font_path, size)
            break
        except:
            continue
    
    if not font:
        font = ImageFont.load_default()
except:
    font = ImageFont.load_default()

# Draw the "A" 
text = "A"
bbox = draw.textbbox((0, 0), text, font=font)
text_width = bbox[2] - bbox[0]
text_height = bbox[3] - bbox[1]
text_x = (128 - text_width) // 2
text_y = (128 - text_height) // 2 - 5

# White text with subtle shadow (like Prettier)
draw.text((text_x + 2, text_y + 2), text, fill=(0, 0, 0, 50), font=font)
draw.text((text_x, text_y), text, fill=(255, 255, 255), font=font)

# Save
img.save('/Users/chinmayshrivastava/Api Orchestrator/api-orchestrator/vscode-extension/media/icon-prettier-style.png', 'PNG')
print("Prettier-style icon created!")