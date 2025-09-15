#!/usr/bin/env python3
"""
Create a high-quality, professional icon with anti-aliasing
"""
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import math

# Create a larger image first for better quality (will resize down)
size = 512
final_size = 128
img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
draw = ImageDraw.Draw(img, 'RGBA')

# Create smooth gradient background
center_x, center_y = size // 2, size // 2

for y in range(size):
    for x in range(size):
        # Radial gradient
        dx = x - center_x
        dy = y - center_y
        distance = math.sqrt(dx*dx + dy*dy)
        max_distance = size // 2
        
        if distance <= max_distance:
            ratio = distance / max_distance
            
            # Premium gradient: Electric blue to deep purple
            if ratio < 0.5:
                # Inner: bright blue
                factor = ratio * 2
                r = int(56 + (99 - 56) * factor)
                g = int(189 + (102 - 189) * factor)
                b = int(248 + (241 - 248) * factor)
            else:
                # Outer: purple
                factor = (ratio - 0.5) * 2
                r = int(99 + (88 - 99) * factor)
                g = int(102 + (28 - 102) * factor)
                b = int(241 + (171 - 241) * factor)
            
            # Add subtle noise for texture
            import random
            random.seed(x * y)
            noise = random.randint(-5, 5)
            r = max(0, min(255, r + noise))
            g = max(0, min(255, g + noise))
            b = max(0, min(255, b + noise))
            
            alpha = 255
            if distance > max_distance * 0.95:
                # Soft edges
                alpha = int(255 * (1 - (distance - max_distance * 0.95) / (max_distance * 0.05)))
            
            draw.point((x, y), fill=(r, g, b, alpha))

# Draw high-quality API symbol
# Using bezier curves for smooth lines

# Draw lightning bolt (representing fast APIs)
bolt_width = size // 8
bolt_points = [
    (center_x - bolt_width//2, center_y - size//4),  # Top left
    (center_x + bolt_width//4, center_y - size//8),  # Mid right
    (center_x - bolt_width//4, center_y + size//8),  # Mid left
    (center_x + bolt_width//2, center_y + size//4),  # Bottom right
]

# Draw with smooth edges
for i in range(len(bolt_points) - 1):
    x1, y1 = bolt_points[i]
    x2, y2 = bolt_points[i + 1]
    draw.line([(x1, y1), (x2, y2)], fill=(255, 255, 255, 255), width=size//16)

# Draw center circle
circle_radius = size // 6
draw.ellipse(
    [center_x - circle_radius, center_y - circle_radius,
     center_x + circle_radius, center_y + circle_radius],
    fill=(255, 255, 255, 240)
)

# Add "API" text with proper font
try:
    # Try to get a high-quality font
    font_size = size // 8
    font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", font_size)
except:
    font = ImageFont.load_default()

text = "API"
bbox = draw.textbbox((0, 0), text, font=font)
text_width = bbox[2] - bbox[0]
text_height = bbox[3] - bbox[1]
text_x = center_x - text_width // 2
text_y = center_y - text_height // 2

# Draw text with shadow for depth
shadow_offset = size // 100
draw.text((text_x + shadow_offset, text_y + shadow_offset), text, 
          fill=(0, 0, 0, 100), font=font)
draw.text((text_x, text_y), text, fill=(56, 189, 248), font=font)

# Apply slight blur for smoothness
img = img.filter(ImageFilter.SMOOTH_MORE)

# Resize to final size with high-quality resampling
img_final = img.resize((final_size, final_size), Image.Resampling.LANCZOS)

# Convert to RGB for saving
img_rgb = Image.new('RGB', (final_size, final_size), (255, 255, 255))
img_rgb.paste(img_final, (0, 0), img_final)

# Save with maximum quality
img_rgb.save('/Users/chinmayshrivastava/Api Orchestrator/api-orchestrator/vscode-extension/media/icon-hq.png', 
             'PNG', quality=100, optimize=False)
print("High-quality icon created!")