#!/usr/bin/env python3
"""
Create a modern STREAM API branded 128x128 icon for VS Code extension
"""
from PIL import Image, ImageDraw, ImageFont
import math

def create_wave_pattern(draw, y_offset, amplitude, color, width=128):
    """Create flowing wave pattern to represent streaming"""
    points = []
    for x in range(width + 1):
        y = y_offset + amplitude * math.sin(x * 0.05)
        points.append((x, y))
    
    # Create filled area below wave
    for i in range(len(points) - 1):
        x1, y1 = points[i]
        x2, y2 = points[i + 1]
        for y in range(int(max(y1, y2)), 128):
            alpha = max(0, 255 - (y - max(y1, y2)) * 3)
            if alpha > 0:
                draw.point((x1, y), fill=(*color, alpha))

# Create image with dark modern background
img = Image.new('RGBA', (128, 128), color=(25, 26, 36, 255))  # Dark blue-gray
draw = ImageDraw.Draw(img)

# Create gradient background (dark blue to purple)
for y in range(128):
    ratio = y / 128
    r = int(25 + (49 * ratio))   # 25 -> 74
    g = int(26 + (32 * ratio))   # 26 -> 58
    b = int(36 + (201 * ratio))  # 36 -> 237
    draw.rectangle([(0, y), (128, y+1)], fill=(r, g, b, 255))

# Draw streaming waves (representing data flow)
wave_colors = [
    (124, 58, 237),   # Purple
    (236, 72, 153),   # Pink
    (59, 130, 246),   # Blue
]

# Draw multiple wave layers
for i, color in enumerate(wave_colors):
    y_offset = 40 + (i * 15)
    amplitude = 8 - (i * 2)
    create_wave_pattern(draw, y_offset, amplitude, color)

# Create central badge/card for text
card_width = 100
card_height = 50
card_x = (128 - card_width) // 2
card_y = (128 - card_height) // 2 - 5

# Draw card with glass morphism effect
glass_img = Image.new('RGBA', (128, 128), (0, 0, 0, 0))
glass_draw = ImageDraw.Draw(glass_img)

# Card background with transparency
glass_draw.rounded_rectangle(
    [(card_x, card_y), (card_x + card_width, card_y + card_height)],
    radius=10,
    fill=(255, 255, 255, 200)  # Semi-transparent white
)

# Merge glass effect
img = Image.alpha_composite(img, glass_img)
draw = ImageDraw.Draw(img)

# Draw STREAM text
try:
    # Try to get a bold, modern font
    fonts_to_try = [
        ("/System/Library/Fonts/Helvetica.ttc", 18),
        ("/Library/Fonts/Arial Bold.ttf", 18),
        ("/System/Library/Fonts/Avenir Next.ttc", 18),
    ]
    
    font_stream = None
    for font_path, size in fonts_to_try:
        try:
            font_stream = ImageFont.truetype(font_path, size)
            break
        except:
            continue
    
    if not font_stream:
        font_stream = ImageFont.load_default()
    
    # Smaller font for API
    font_api = None
    for font_path, _ in fonts_to_try:
        try:
            font_api = ImageFont.truetype(font_path, 14)
            break
        except:
            continue
    
    if not font_api:
        font_api = ImageFont.load_default()
        
except:
    font_stream = ImageFont.load_default()
    font_api = ImageFont.load_default()

# Draw STREAM text
text_stream = "STREAM"
bbox = draw.textbbox((0, 0), text_stream, font=font_stream)
text_width = bbox[2] - bbox[0]
text_x = 64 - text_width // 2
text_y = card_y + 8

# Draw with gradient effect
draw.text((text_x, text_y), text_stream, fill=(49, 46, 129), font=font_stream)  # Dark purple

# Draw API text below
text_api = "API"
bbox = draw.textbbox((0, 0), text_api, font=font_api)
text_width = bbox[2] - bbox[0]
text_x = 64 - text_width // 2
text_y = card_y + 28

draw.text((text_x, text_y), text_api, fill=(124, 58, 237), font=font_api)  # Purple

# Add connection dots around (representing endpoints)
dot_positions = [
    (20, 20),
    (108, 20),
    (20, 108),
    (108, 108),
]

for x, y in dot_positions:
    # Outer glow
    draw.ellipse([x-4, y-4, x+4, y+4], fill=(236, 72, 153, 100))
    # Inner dot
    draw.ellipse([x-2, y-2, x+2, y+2], fill=(255, 255, 255))

# Convert to RGB for saving
img_rgb = Image.new('RGB', (128, 128), (255, 255, 255))
img_rgb.paste(img, (0, 0), img)

# Save
img_rgb.save('/Users/chinmayshrivastava/Api Orchestrator/api-orchestrator/vscode-extension/media/icon-stream-api.png', 'PNG')
print("STREAM API icon created successfully!")