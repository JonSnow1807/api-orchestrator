#!/usr/bin/env python3
"""
Create a truly professional, eye-catching icon
Similar to successful brands like Notion, Linear, Figma
"""
from PIL import Image, ImageDraw, ImageFont
import math

# Create high-quality image
img = Image.new('RGB', (128, 128))
draw = ImageDraw.Draw(img)

# Professional gradient background (subtle, not too loud)
# Using a sophisticated blue to purple gradient (trustworthy and modern)
for y in range(128):
    for x in range(128):
        # Radial gradient from center
        dx = x - 64
        dy = y - 64
        distance = math.sqrt(dx*dx + dy*dy) / 90
        distance = min(1.0, distance)
        
        # Sophisticated gradient: deep blue to purple
        r = int(37 + (99 - 37) * distance)    # 37 -> 99
        g = int(99 + (102 - 99) * distance)   # 99 -> 102  
        b = int(235 + (241 - 235) * distance) # 235 -> 241
        
        draw.point((x, y), fill=(r, g, b))

# Draw a clean, modern icon shape (network/API nodes)
center_x, center_y = 64, 64

# Central circle (main node)
main_radius = 20
draw.ellipse(
    [center_x - main_radius, center_y - main_radius,
     center_x + main_radius, center_y + main_radius],
    fill=(255, 255, 255),
    outline=None
)

# Surrounding nodes (representing API endpoints)
node_positions = []
num_nodes = 6
for i in range(num_nodes):
    angle = (i * 360 / num_nodes) - 90  # Start from top
    rad = math.radians(angle)
    
    # Position nodes in a circle
    node_x = center_x + 40 * math.cos(rad)
    node_y = center_y + 40 * math.sin(rad)
    node_positions.append((node_x, node_y))
    
    # Draw connection lines first (behind nodes)
    draw.line(
        [(center_x, center_y), (node_x, node_y)],
        fill=(255, 255, 255, 180),
        width=2
    )

# Draw the outer nodes
for x, y in node_positions:
    node_radius = 8
    draw.ellipse(
        [x - node_radius, y - node_radius,
         x + node_radius, y + node_radius],
        fill=(255, 255, 255),
        outline=None
    )

# Add elegant text in the center
try:
    # Professional font
    fonts_to_try = [
        ("/System/Library/Fonts/SFNS.ttf", 18),
        ("/System/Library/Fonts/Helvetica.ttc", 18),
        ("/Library/Fonts/Arial.ttf", 18),
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

# Draw "API" text in the center circle
text = "API"
bbox = draw.textbbox((0, 0), text, font=font)
text_width = bbox[2] - bbox[0]
text_height = bbox[3] - bbox[1]
text_x = center_x - text_width // 2
text_y = center_y - text_height // 2 - 2

draw.text((text_x, text_y), text, fill=(37, 99, 235), font=font)

# Add subtle glow effect around the main elements
img_glow = Image.new('RGBA', (128, 128), (0, 0, 0, 0))
draw_glow = ImageDraw.Draw(img_glow)

# Glow for center
for i in range(3):
    glow_radius = main_radius + 3 + (i * 2)
    alpha = 80 - (i * 20)
    draw_glow.ellipse(
        [center_x - glow_radius, center_y - glow_radius,
         center_x + glow_radius, center_y + glow_radius],
        fill=(255, 255, 255, alpha)
    )

# Convert and save
img_final = Image.new('RGB', (128, 128))
img_final.paste(img)
img_final = Image.alpha_composite(img.convert('RGBA'), img_glow).convert('RGB')

img_final.save('/Users/chinmayshrivastava/Api Orchestrator/api-orchestrator/vscode-extension/media/icon-professional-final.png', 'PNG')
print("Professional final icon created!")