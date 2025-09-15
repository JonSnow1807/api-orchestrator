#!/usr/bin/env python3
"""
Create a super minimal, clean icon (Vercel/Linear style)
"""
from PIL import Image, ImageDraw, ImageFont

# Pure black background (like Vercel)
img = Image.new('RGB', (128, 128), color='#000000')
draw = ImageDraw.Draw(img)

# Single accent color - electric blue
accent = (0, 112, 243)  # Electric blue like Vercel

# Draw a simple, bold lightning bolt (representing fast APIs)
lightning_points = [
    (64, 20),    # Top
    (45, 55),    # Left middle
    (58, 55),    # 
    (48, 108),   # Bottom point
    (68, 55),    # Right side
    (55, 55),    #
    (74, 20),    # Back to near top
]

# Fill the lightning bolt
draw.polygon(lightning_points[:-1], fill=accent)

# Add a subtle glow
for i in range(1, 4):
    glow_points = []
    for x, y in lightning_points[:-1]:
        # Expand points slightly for glow
        dx = (x - 64) * (1 + i * 0.05)
        dy = (y - 64) * (1 + i * 0.05)
        glow_points.append((64 + dx, 64 + dy))
    
    alpha = 60 - i * 15
    color = (*accent, alpha)
    try:
        draw.polygon(glow_points, outline=accent, width=1)
    except:
        pass

# Save
img.save('/Users/chinmayshrivastava/Api Orchestrator/api-orchestrator/vscode-extension/media/icon-minimal.png', 'PNG')
print("Minimal icon created!")