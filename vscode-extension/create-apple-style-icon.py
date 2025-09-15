#!/usr/bin/env python3
"""
Create an Apple-style icon - ultra clean, minimalist, premium
"""
from PIL import Image, ImageDraw, ImageFont
import math

# Create image with clean white background
img = Image.new('RGB', (128, 128), color='#FFFFFF')
draw = ImageDraw.Draw(img)

# Draw a perfect gradient circle (like Apple's app icons)
for y in range(128):
    for x in range(128):
        # Distance from center
        dx = x - 64
        dy = y - 64
        distance = math.sqrt(dx*dx + dy*dy)
        
        # Only draw within circle
        if distance <= 50:
            # Gradient from blue to purple (Apple-like colors)
            ratio = distance / 50
            
            # Beautiful blue to purple gradient
            r = int(0 + (147 * ratio))      # 0 -> 147
            g = int(122 + (51 - 122) * ratio)   # 122 -> 51
            b = int(255 + (234 - 255) * ratio)  # 255 -> 234
            
            draw.point((x, y), fill=(r, g, b))

# Draw clean white API symbol in center
# Using interconnected circles to represent API connections
positions = [
    (64, 50),    # Top
    (50, 64),    # Left
    (78, 64),    # Right
    (64, 78),    # Bottom
]

# Draw connection lines (thin and elegant)
for i, pos1 in enumerate(positions):
    for pos2 in positions[i+1:]:
        draw.line([pos1, pos2], fill=(255, 255, 255, 200), width=1)

# Draw nodes
for x, y in positions:
    draw.ellipse([x-4, y-4, x+4, y+4], fill=(255, 255, 255))

# Center node (slightly larger)
draw.ellipse([64-6, 64-6, 64+6, 64+6], fill=(255, 255, 255))

# Save with smooth edges
img.save('/Users/chinmayshrivastava/Api Orchestrator/api-orchestrator/vscode-extension/media/icon-apple-style.png', 'PNG')
print("Apple-style icon created!")