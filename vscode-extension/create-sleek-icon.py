#!/usr/bin/env python3
"""
Create a sleek, tech-style 128x128 icon for VS Code extension
"""
from PIL import Image, ImageDraw, ImageFont

# Create image with dark background
img = Image.new('RGB', (128, 128), color='#1e1e1e')
draw = ImageDraw.Draw(img)

# Draw dark gradient background
for y in range(128):
    gray_value = 30 + int(20 * (y / 128))  # Subtle gradient from dark gray
    draw.rectangle([(0, y), (128, y+1)], fill=(gray_value, gray_value, gray_value))

# Draw glowing purple accent square in center
center_size = 72
margin = (128 - center_size) // 2

# Glow effect layers
for i in range(5, 0, -1):
    glow_size = center_size + (i * 4)
    glow_margin = (128 - glow_size) // 2
    opacity = 20 + (5 - i) * 10
    color = (124 + opacity//2, 58 + opacity//2, 237)
    draw.rounded_rectangle(
        [(glow_margin, glow_margin), (glow_margin + glow_size, glow_margin + glow_size)],
        radius=8 + i,
        fill=None,
        outline=color,
        width=1
    )

# Main square with gradient
for y in range(margin, margin + center_size):
    # Purple to pink gradient
    ratio = (y - margin) / center_size
    r = int(139 + (236 - 139) * ratio)
    g = int(92 + (72 - 92) * ratio)  
    b = int(246 + (153 - 246) * ratio)
    draw.rectangle([(margin, y), (margin + center_size, y+1)], fill=(r, g, b))

# Draw API text in white
try:
    font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 28)
except:
    font = ImageFont.load_default()

text = "API"
bbox = draw.textbbox((0, 0), text, font=font)
text_width = bbox[2] - bbox[0]
text_height = bbox[3] - bbox[1]
text_x = (128 - text_width) // 2
text_y = (128 - text_height) // 2 - 2

# Draw text with shadow
draw.text((text_x+2, text_y+2), text, fill=(0, 0, 0), font=font)  # Shadow
draw.text((text_x, text_y), text, fill=(255, 255, 255), font=font)  # White text

# Add small connection dots (representing endpoints)
dot_positions = [
    (margin - 10, 64),
    (margin + center_size + 10, 64),
    (64, margin - 10),
    (64, margin + center_size + 10)
]

for x, y in dot_positions:
    draw.ellipse([x-3, y-3, x+3, y+3], fill=(236, 72, 153))  # Pink dots
    # Draw thin lines to center
    draw.line([(x, y), (64, 64)], fill=(124, 58, 237, 128), width=1)

# Save
img.save('/Users/chinmayshrivastava/Api Orchestrator/api-orchestrator/vscode-extension/media/icon-sleek.png', 'PNG')
print("Sleek tech icon created!")