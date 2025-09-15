#!/usr/bin/env python3
"""
Create a rocket icon - representing fast API development
"""
from PIL import Image, ImageDraw, ImageFont
import math

# Create image with gradient
img = Image.new('RGB', (128, 128))
draw = ImageDraw.Draw(img)

# Space-like gradient background (dark blue to purple)
for y in range(128):
    ratio = y / 128
    r = int(25 + (88 * ratio))   # 25 -> 113
    g = int(25 + (28 * ratio))   # 25 -> 53  
    b = int(112 + (119 * ratio))  # 112 -> 231
    draw.rectangle([(0, y), (128, y+1)], fill=(r, g, b))

# Add stars in background
import random
random.seed(42)
for _ in range(20):
    x = random.randint(0, 128)
    y = random.randint(0, 128)
    brightness = random.randint(150, 255)
    size = random.choice([0, 0, 1])
    draw.ellipse([x-size, y-size, x+size, y+size], fill=(brightness, brightness, brightness))

# Draw rocket body
rocket_x = 64
rocket_y = 50
rocket_width = 24
rocket_height = 40

# Rocket body (triangle + rectangle)
body_points = [
    (rocket_x, rocket_y - 20),  # Tip
    (rocket_x - rocket_width//2, rocket_y),  # Left
    (rocket_x - rocket_width//2, rocket_y + rocket_height),  # Left bottom
    (rocket_x + rocket_width//2, rocket_y + rocket_height),  # Right bottom
    (rocket_x + rocket_width//2, rocket_y),  # Right
]

# Draw rocket with gradient
draw.polygon(body_points, fill=(240, 240, 240))

# Add window
window_y = rocket_y + 5
draw.ellipse(
    [rocket_x - 6, window_y - 6, rocket_x + 6, window_y + 6],
    fill=(100, 200, 255)
)

# Draw fins
fin_color = (200, 200, 200)
# Left fin
left_fin = [
    (rocket_x - rocket_width//2, rocket_y + 20),
    (rocket_x - rocket_width//2 - 8, rocket_y + 35),
    (rocket_x - rocket_width//2, rocket_y + 35),
]
draw.polygon(left_fin, fill=fin_color)

# Right fin
right_fin = [
    (rocket_x + rocket_width//2, rocket_y + 20),
    (rocket_x + rocket_width//2 + 8, rocket_y + 35),
    (rocket_x + rocket_width//2, rocket_y + 35),
]
draw.polygon(right_fin, fill=fin_color)

# Draw flame/thrust
flame_colors = [(255, 100, 0), (255, 200, 0), (255, 255, 100)]
for i, color in enumerate(flame_colors):
    flame_y = rocket_y + rocket_height + (i * 5)
    flame_width = rocket_width - (i * 4)
    if flame_width > 0:
        flame_points = [
            (rocket_x - flame_width//2, flame_y),
            (rocket_x, flame_y + 15 - (i * 3)),
            (rocket_x + flame_width//2, flame_y),
        ]
        draw.polygon(flame_points, fill=color)

# Add "API" text on the rocket body
try:
    font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 10)
except:
    font = ImageFont.load_default()

text = "API"
bbox = draw.textbbox((0, 0), text, font=font)
text_width = bbox[2] - bbox[0]
text_x = rocket_x - text_width // 2
text_y = rocket_y + 15

draw.text((text_x, text_y), text, fill=(50, 50, 50), font=font)

# Add motion lines
for i in range(3):
    y = rocket_y - 25 - (i * 8)
    draw.line([(15, y), (35, y)], fill=(255, 255, 255, 150 - i * 40), width=2)
    draw.line([(93, y), (113, y)], fill=(255, 255, 255, 150 - i * 40), width=2)

# Save
img.save('/Users/chinmayshrivastava/Api Orchestrator/api-orchestrator/vscode-extension/media/icon-rocket.png', 'PNG')
print("Rocket icon created!")