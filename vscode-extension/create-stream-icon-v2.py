#!/usr/bin/env python3
"""
Create a modern STREAM API branded 128x128 icon for VS Code extension
"""
from PIL import Image, ImageDraw, ImageFont

# Create new image with gradient background
img = Image.new('RGB', (128, 128), color='white')
draw = ImageDraw.Draw(img)

# Create electric blue to purple gradient (modern streaming vibe)
for y in range(128):
    ratio = y / 128
    # Electric blue to purple gradient
    r = int(0 + (147 * ratio))    # 0 -> 147
    g = int(191 + (51 - 191) * ratio)   # 191 -> 51  
    b = int(255 + (234 - 255) * ratio)  # 255 -> 234
    draw.rectangle([(0, y), (128, y+1)], fill=(r, g, b))

# Draw flowing stream lines (representing data streams)
stream_lines = [
    [(10, 30), (40, 35), (70, 25), (100, 30), (118, 28)],
    [(10, 50), (35, 45), (65, 55), (95, 48), (118, 52)],
    [(10, 70), (45, 75), (75, 65), (105, 72), (118, 68)],
    [(10, 90), (38, 85), (68, 95), (98, 88), (118, 92)],
]

# Draw smooth flowing lines
for points in stream_lines:
    # Draw with varying opacity for depth
    for i in range(len(points) - 1):
        draw.line([points[i], points[i+1]], fill=(255, 255, 255, 180), width=2)

# Create central card for text
card_margin = 20
card_top = 38
card_bottom = 90
card_height = card_bottom - card_top

# Draw semi-transparent white card
for y in range(card_top, card_bottom):
    alpha_ratio = 1 - abs((y - (card_top + card_bottom)/2) / (card_height/2)) * 0.3
    white_value = int(255 * 0.95)
    draw.rectangle(
        [(card_margin, y), (128 - card_margin, y+1)], 
        fill=(white_value, white_value, white_value)
    )

# Add border to card
draw.rounded_rectangle(
    [(card_margin, card_top), (128 - card_margin, card_bottom)],
    radius=8,
    fill=None,
    outline=(147, 51, 234),  # Purple outline
    width=2
)

# Load fonts
try:
    # Bold font for STREAM
    font_stream = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 20)
    # Regular font for API
    font_api = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 16)
except:
    try:
        font_stream = ImageFont.truetype("/Library/Fonts/Arial Bold.ttf", 20)
        font_api = ImageFont.truetype("/Library/Fonts/Arial.ttf", 16)
    except:
        font_stream = ImageFont.load_default()
        font_api = ImageFont.load_default()

# Draw STREAM text
text_stream = "STREAM"
bbox = draw.textbbox((0, 0), text_stream, font=font_stream)
text_width = bbox[2] - bbox[0]
text_x = (128 - text_width) // 2
text_y = card_top + 10

# Draw with shadow for depth
draw.text((text_x + 1, text_y + 1), text_stream, fill=(100, 100, 100), font=font_stream)
draw.text((text_x, text_y), text_stream, fill=(30, 30, 30), font=font_stream)

# Draw API text
text_api = "API"
bbox = draw.textbbox((0, 0), text_api, font=font_api)
text_width = bbox[2] - bbox[0]
text_x = (128 - text_width) // 2
text_y = card_top + 32

draw.text((text_x, text_y), text_api, fill=(147, 51, 234), font=font_api)  # Purple

# Add small accent elements
# Top left indicator
draw.ellipse([8, 8, 14, 14], fill=(0, 191, 255))  # Cyan
# Top right indicator
draw.ellipse([114, 8, 120, 14], fill=(255, 0, 128))  # Pink
# Bottom indicators
draw.ellipse([8, 114, 14, 120], fill=(147, 51, 234))  # Purple
draw.ellipse([114, 114, 120, 120], fill=(0, 255, 128))  # Green

# Add connection lines from indicators to center
center_x, center_y = 64, 64
indicators = [(11, 11), (117, 11), (11, 117), (117, 117)]
for x, y in indicators:
    # Draw thin connection line
    draw.line([(x, y), (center_x, center_y)], fill=(255, 255, 255, 100), width=1)

# Save the icon
img.save('/Users/chinmayshrivastava/Api Orchestrator/api-orchestrator/vscode-extension/media/icon-stream-api.png', 'PNG')
print("STREAM API icon created successfully!")