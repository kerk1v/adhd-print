"""
Material Design Icon Generator for ADHD Print System

Generates 85x85 pixel Material Design-inspired urgency icons for thermal printing.
Icons are created as 1-bit PNG files optimized for ESC/POS thermal printers.

Icons generated:
- critical.png: Hexagonal stop sign with exclamation for critical urgency
- urgent.png: Warning triangle for urgent tasks
- normal.png: Info circle for normal priority
- low.png: Simple circle for low priority

Usage:
    python scripts/icon_generator.py

Requirements:
    - PIL (Pillow)
    - Django settings configured
"""
from PIL import Image, ImageDraw
import os
from django.conf import settings


def create_material_design_icons():
    """Create Material Design inspired urgency icons using PIL"""
    icon_size = 85  # 85x85 pixels

    icons_dir = os.path.join(settings.BASE_DIR, 'static', 'icons')
    os.makedirs(icons_dir, exist_ok=True)

    # Critical - Hexagonal stop sign with exclamation (like traffic stop sign)
    critical_img = Image.new('1', (icon_size, icon_size), 1)  # White background
    draw = ImageDraw.Draw(critical_img)

    # Calculate hexagon points for 85x85 image (centered, with good border)
    center_x, center_y = icon_size // 2, icon_size // 2
    radius = 32  # Radius to fit nicely in 85x85 with border
    
    # Hexagon points (6 sides, starting from top and going clockwise)
    import math
    hexagon_points = []
    for i in range(6):
        angle = math.pi / 3 * i - math.pi / 2  # Start from top (-90 degrees)
        x = center_x + radius * math.cos(angle)
        y = center_y + radius * math.sin(angle)
        hexagon_points.append((x, y))
    
    # Draw filled hexagon (black on white)
    draw.polygon(hexagon_points, fill=0, outline=0)
    
    # Draw hexagon border to make it more prominent
    border_radius = radius + 2
    border_points = []
    for i in range(6):
        angle = math.pi / 3 * i - math.pi / 2
        x = center_x + border_radius * math.cos(angle)
        y = center_y + border_radius * math.sin(angle)
        border_points.append((x, y))
    draw.polygon(border_points, outline=0, width=2)
    
    # Exclamation mark inside hexagon (white on black background)
    # Exclamation line (vertical bar)
    line_width = 4
    line_height = 16
    line_x = center_x - line_width // 2
    line_y = center_y - 12
    draw.rectangle([line_x, line_y, line_x + line_width, line_y + line_height], fill=1)
    
    # Exclamation dot
    dot_size = 4
    dot_x = center_x - dot_size // 2
    dot_y = center_y + 8
    draw.rectangle([dot_x, dot_y, dot_x + dot_size, dot_y + dot_size], fill=1)

    critical_img.save(os.path.join(icons_dir, 'critical.png'))

    # Urgent - Material Design "warning" icon style (triangle with exclamation)
    urgent_img = Image.new('1', (icon_size, icon_size), 1)
    draw = ImageDraw.Draw(urgent_img)

    # Triangle outline (adjusted for 85x85)
    triangle_points = [(42, 7), (78, 71), (7, 71)]
    draw.polygon(triangle_points, outline=0, width=4)
    # Exclamation mark inside (adjusted for 85x85)
    draw.rectangle([39, 25, 46, 50], fill=0)  # Line
    draw.rectangle([39, 57, 46, 64], fill=0)  # Dot

    urgent_img.save(os.path.join(icons_dir, 'urgent.png'))

    # Normal - Material Design "info" icon style (circle with 'i')
    normal_img = Image.new('1', (icon_size, icon_size), 1)
    draw = ImageDraw.Draw(normal_img)

    # Circle outline (adjusted for 85x85)
    draw.ellipse([7, 7, 78, 78], outline=0, width=4)
    # Info 'i' - dot and line (adjusted for 85x85)
    draw.rectangle([39, 21, 46, 28], fill=0)  # Top dot
    draw.rectangle([39, 35, 46, 64], fill=0)  # Line

    normal_img.save(os.path.join(icons_dir, 'normal.png'))

    # Low - Material Design "radio_button_unchecked" style (simple circle)
    low_img = Image.new('1', (icon_size, icon_size), 1)
    draw = ImageDraw.Draw(low_img)

    # Simple circle outline (radio button style) (adjusted for 85x85)
    draw.ellipse([14, 14, 71, 71], outline=0, width=4)

    low_img.save(os.path.join(icons_dir, 'low.png'))


if __name__ == "__main__":
    import django
    import sys
    import os

    # Add the project directory to Python path
    sys.path.append('/Users/volker/adhd-print')
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'adhd_print_project.settings')
    django.setup()

    create_material_design_icons()
    print("Material Design inspired urgency icons created successfully!")
