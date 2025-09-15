#!/usr/bin/env python3
"""
Create a modern, minimalist 128x128 icon for VS Code extension
Similar to popular extensions like Prettier, ESLint, etc.
"""
from PIL import Image, ImageDraw, ImageFont

# Create a new 128x128 image
img = Image.new('RGB', (128, 128), color='white')
draw = ImageDraw.Draw(img)

# Modern gradient background (Purple to Pink - very trendy)
for y in range(128):
    # Gradient from purple to pink
    ratio = y / 128
    r = int(124 + (236 - 124) * ratio)  # 124 -> 236
    g = int(58 + (72 - 58) * ratio)     # 58 -> 72
    b = int(237 + (153 - 237) * ratio)  # 237 -> 153
    draw.rectangle([(0, y), (128, y+1)], fill=(r, g, b))

# Draw a modern rounded rectangle card
card_margin = 24
corner_radius = 12
draw.rounded_rectangle(
    [(card_margin, card_margin), (128-card_margin, 128-card_margin)],
    radius=corner_radius,
    fill=(255, 255, 255, 240),  # Slightly transparent white
    outline=None
)

# Draw modern brackets { } to represent API/JSON
bracket_color = (124, 58, 237)  # Purple
try:
    font = ImageFont.truetype("/System/Library/Fonts/Courier.ttc", 48)
except:
    try:
        font = ImageFont.truetype("/Library/Fonts/Courier New.ttf", 48)
    except:
        font = ImageFont.load_default()

# Draw curly brackets
left_bracket = "{"
right_bracket = "}"

# Position brackets
draw.text((35, 38), left_bracket, fill=bracket_color, font=font)
draw.text((78, 38), right_bracket, fill=bracket_color, font=font)

# Draw forward slash in between (representing routes/endpoints)
try:
    slash_font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 36)
except:
    slash_font = font

draw.text((54, 45), "/", fill=(236, 72, 153), font=slash_font)  # Pink accent

# Save the icon
img.save('/Users/chinmayshrivastava/Api Orchestrator/api-orchestrator/vscode-extension/media/icon-modern.png', 'PNG')
print("Modern minimalist icon created!")