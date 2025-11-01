"""
Material Design Icon Generator for ADHD Print System

Generates 85x85 pixel Material Design-inspired urgency icons for thermal printing.
Icons are created as 1-bit PNG files optimized for ESC/POS thermal printers.

Icons generated:
- critical.png: Report flag style for critical urgency
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

    # Critical - Material Design "report" icon style (flag with exclamation)
    critical_img = Image.new('1', (icon_size, icon_size), 1)  # White background
    draw = ImageDraw.Draw(critical_img)

    # Flag pole (adjusted for 85x85)
    draw.rectangle([18, 10, 25, 75], fill=0)
    # Flag body (adjusted for 85x85)
    draw.polygon([(25, 10), (67, 10), (74, 21), (67, 32), (25, 32)], fill=0)
    # Exclamation in flag (adjusted for 85x85)
    draw.rectangle([39, 16, 42, 26], fill=1)  # White on black

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
