#!/usr/bin/env python3
"""
Create a professional, attractive 128x128 icon for VS Code extension
"""
from PIL import Image, ImageDraw, ImageFont
import math

def create_gradient(draw, width, height, color1, color2):
    """Create a diagonal gradient"""
    for i in range(width):
        for j in range(height):
            # Calculate the gradient ratio
            ratio = (i + j) / (width + height)
            
            # Interpolate between colors
            r = int(color1[0] * (1 - ratio) + color2[0] * ratio)
            g = int(color1[1] * (1 - ratio) + color2[1] * ratio)
            b = int(color1[2] * (1 - ratio) + color2[2] * ratio)
            
            draw.point((i, j), fill=(r, g, b))

# Create a new 128x128 image
img = Image.new('RGB', (128, 128), color='white')
draw = ImageDraw.Draw(img)

# Define colors
purple_light = (139, 92, 246)  # #8B5CF6
purple_dark = (109, 40, 217)   # #6D28D9
accent = (236, 72, 153)        # #EC4899 (pink accent)
white = (255, 255, 255)

# Create gradient background
create_gradient(draw, 128, 128, purple_light, purple_dark)

# Draw modern geometric shapes

# Main hexagon shape (representing API connectivity)
center_x, center_y = 64, 64
size = 35

# Calculate hexagon points
angles = [i * 60 for i in range(6)]
hex_points = []
for angle in angles:
    rad = math.radians(angle)
    x = center_x + size * math.cos(rad)
    y = center_y + size * math.sin(rad)
    hex_points.append((x, y))

# Draw hexagon with white fill
draw.polygon(hex_points, fill=white, outline=purple_dark, width=2)

# Draw connection dots around (representing API endpoints)
orbit_radius = 50
for i in range(6):
    angle = math.radians(i * 60)
    x = center_x + orbit_radius * math.cos(angle)
    y = center_y + orbit_radius * math.sin(angle)
    
    # Draw small circles
    if i % 2 == 0:
        draw.ellipse([x-4, y-4, x+4, y+4], fill=white, outline=None)
    else:
        draw.ellipse([x-3, y-3, x+3, y+3], fill=accent, outline=None)
    
    # Draw connection lines
    if i % 2 == 0:
        draw.line([(center_x, center_y), (x, y)], fill=white, width=1)

# Draw API text in the center
text = "API"
try:
    # Try multiple font options
    fonts_to_try = [
        "/System/Library/Fonts/Helvetica.ttc",
        "/System/Library/Fonts/Avenir.ttc",
        "/Library/Fonts/Arial Bold.ttf",
        "/System/Library/Fonts/Futura.ttc"
    ]
    font = None
    for font_path in fonts_to_try:
        try:
            font = ImageFont.truetype(font_path, 20)
            break
        except:
            continue
    
    if not font:
        font = ImageFont.load_default()
except:
    font = ImageFont.load_default()

# Draw text with better positioning
bbox = draw.textbbox((0, 0), text, font=font)
text_width = bbox[2] - bbox[0]
text_height = bbox[3] - bbox[1]
text_x = center_x - text_width // 2
text_y = center_y - text_height // 2 - 2

# Draw text
draw.text((text_x, text_y), text, fill=purple_dark, font=font)

# Add subtle glow effect around the hexagon
for i in range(3, 0, -1):
    alpha = 30 * (4 - i)
    glow_img = Image.new('RGBA', (128, 128), (255, 255, 255, 0))
    glow_draw = ImageDraw.Draw(glow_img)
    
    # Create larger hexagon for glow
    glow_points = []
    for angle in angles:
        rad = math.radians(angle)
        x = center_x + (size + i * 3) * math.cos(rad)
        y = center_y + (size + i * 3) * math.sin(rad)
        glow_points.append((x, y))
    
    glow_draw.polygon(glow_points, fill=(255, 255, 255, alpha))
    img = Image.alpha_composite(img.convert('RGBA'), glow_img).convert('RGB')

# Save the icon
img.save('/Users/chinmayshrivastava/Api Orchestrator/api-orchestrator/vscode-extension/media/icon-professional.png', 'PNG')
print("Professional icon created successfully!")