#!/usr/bin/env python3
"""
Create a bold, eye-catching STREAM API icon
"""
from PIL import Image, ImageDraw, ImageFont

# Create image
img = Image.new('RGB', (128, 128), color='white')
draw = ImageDraw.Draw(img)

# Bold gradient background - vibrant colors
for x in range(128):
    for y in range(128):
        # Diagonal gradient from hot pink to electric blue
        ratio = (x + y) / 256
        r = int(255 - (255 - 59) * ratio)   # 255 -> 59 (pink to blue)
        g = int(20 + (130 - 20) * ratio)    # 20 -> 130
        b = int(147 + (246 - 147) * ratio)  # 147 -> 246
        draw.point((x, y), fill=(r, g, b))

# Draw large bold rectangle frame
frame_margin = 12
draw.rectangle(
    [(frame_margin, frame_margin), (128-frame_margin, 128-frame_margin)],
    fill=None,
    outline=(255, 255, 255),
    width=3
)

# Create dark overlay for text visibility
overlay_top = 35
overlay_bottom = 93
for y in range(overlay_top, overlay_bottom):
    for x in range(frame_margin + 3, 128 - frame_margin - 3):
        # Semi-transparent dark overlay
        current = img.getpixel((x, y))
        new_color = tuple(int(c * 0.3) for c in current)
        draw.point((x, y), fill=new_color)

# Load fonts - go for BOLD
try:
    font_stream = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 24)
    font_api = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 18)
    font_small = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 10)
except:
    font_stream = ImageFont.load_default()
    font_api = ImageFont.load_default()
    font_small = ImageFont.load_default()

# STREAM text - large and bold
text = "STREAM"
bbox = draw.textbbox((0, 0), text, font=font_stream)
text_width = bbox[2] - bbox[0]
text_x = (128 - text_width) // 2
text_y = 42

# Draw with glow effect
for offset in [(2, 2), (-2, -2), (2, -2), (-2, 2)]:
    draw.text((text_x + offset[0], text_y + offset[1]), text, 
              fill=(255, 255, 255, 50), font=font_stream)
draw.text((text_x, text_y), text, fill=(255, 255, 255), font=font_stream)

# API text - also bold
text = "API"
bbox = draw.textbbox((0, 0), text, font=font_api)
text_width = bbox[2] - bbox[0]
text_x = (128 - text_width) // 2
text_y = 68

draw.text((text_x, text_y), text, fill=(255, 255, 200), font=font_api)

# Add "lightning" streaks for dynamic feel
streak_points = [
    [(30, 20), (35, 25), (32, 30), (37, 35)],
    [(91, 20), (96, 25), (93, 30), (98, 35)],
    [(30, 93), (35, 98), (32, 103), (37, 108)],
    [(91, 93), (96, 98), (93, 103), (98, 108)],
]

for points in streak_points:
    for i in range(len(points) - 1):
        draw.line([points[i], points[i+1]], fill=(255, 255, 255), width=2)

# Add corner badges with dots
corners = [
    (frame_margin + 5, frame_margin + 5),
    (128 - frame_margin - 5, frame_margin + 5),
    (frame_margin + 5, 128 - frame_margin - 5),
    (128 - frame_margin - 5, 128 - frame_margin - 5)
]

for x, y in corners:
    draw.ellipse([x-3, y-3, x+3, y+3], fill=(255, 255, 255))

# Add tagline at bottom
tagline = "POSTMAN KILLER"
bbox = draw.textbbox((0, 0), tagline, font=font_small)
text_width = bbox[2] - bbox[0]
text_x = (128 - text_width) // 2
text_y = 108

draw.text((text_x, text_y), tagline, fill=(255, 255, 255, 200), font=font_small)

# Save
img.save('/Users/chinmayshrivastava/Api Orchestrator/api-orchestrator/vscode-extension/media/icon-stream-bold.png', 'PNG')
print("Bold STREAM API icon created!")