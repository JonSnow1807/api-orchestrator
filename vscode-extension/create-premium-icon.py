#!/usr/bin/env python3
"""
Create a premium, professional icon like top VS Code extensions
(Similar style to Prettier, GitHub Copilot, etc.)
"""
from PIL import Image, ImageDraw, ImageFont
import math

# Create high quality image
img = Image.new('RGB', (128, 128), color='#1e1e1e')
draw = ImageDraw.Draw(img)

# Premium gradient background (like GitHub's gradient)
for y in range(128):
    for x in range(128):
        # Radial gradient from center
        dx = x - 64
        dy = y - 64
        distance = math.sqrt(dx*dx + dy*dy) / 90
        
        # GitHub-style gradient: dark purple to bright purple/pink
        if distance < 1:
            ratio = distance
            r = int(13 + (139 - 13) * ratio)   # Dark to bright purple
            g = int(17 + (92 - 17) * ratio)
            b = int(23 + (246 - 23) * ratio)
        else:
            r, g, b = 139, 92, 246
        
        draw.point((x, y), fill=(r, g, b))

# Draw elegant infinity symbol (representing continuous API flow)
def draw_infinity(cx, cy, size, color, width=3):
    """Draw an infinity symbol"""
    points = []
    for t in range(0, 360, 5):
        angle = math.radians(t)
        # Lemniscate formula
        x = cx + size * math.cos(angle) / (1 + math.sin(angle)**2)
        y = cy + size * math.sin(angle) * math.cos(angle) / (1 + math.sin(angle)**2)
        points.append((x, y))
    
    # Draw the curve
    for i in range(len(points) - 1):
        draw.line([points[i], points[i+1]], fill=color, width=width)

# Draw large elegant infinity in center
draw_infinity(64, 64, 35, (255, 255, 255), width=4)

# Add glow effect
for i in range(3):
    opacity = 100 - i * 30
    draw_infinity(64, 64, 35 + i * 2, (255, 255, 255, opacity), width=2)

# Draw minimalist "API" text below
try:
    # Use San Francisco or Helvetica for Apple-like quality
    fonts = [
        "/System/Library/Fonts/SFNS.ttf",
        "/System/Library/Fonts/Helvetica.ttc",
        "/Library/Fonts/Arial.ttf"
    ]
    font = None
    for f in fonts:
        try:
            font = ImageFont.truetype(f, 14)
            break
        except:
            continue
    if not font:
        font = ImageFont.load_default()
except:
    font = ImageFont.load_default()

# Simple, elegant text
text = "API"
bbox = draw.textbbox((0, 0), text, font=font)
text_width = bbox[2] - bbox[0]
text_x = (128 - text_width) // 2
text_y = 95

# Text with subtle shadow
draw.text((text_x+1, text_y+1), text, fill=(0, 0, 0, 128), font=font)
draw.text((text_x, text_y), text, fill=(255, 255, 255), font=font)

# Add 4 corner dots (representing API endpoints)
corners = [(20, 20), (108, 20), (20, 108), (108, 108)]
for x, y in corners:
    # Outer glow
    draw.ellipse([x-5, y-5, x+5, y+5], fill=(255, 255, 255, 30))
    # Inner dot
    draw.ellipse([x-2, y-2, x+2, y+2], fill=(255, 255, 255))

# Save
img.save('/Users/chinmayshrivastava/Api Orchestrator/api-orchestrator/vscode-extension/media/icon-premium.png', 'PNG')
print("Premium icon created!")