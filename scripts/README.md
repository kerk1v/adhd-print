# Development Scripts

This directory contains utility scripts for the ADHD Print project.

## Scripts

### icon_generator.py
Generates Material Design-inspired urgency icons for thermal printing.

**Usage:**
```bash
python scripts/icon_generator.py
```

**Output:**
- Creates 85x85px PNG icons in `static/icons/`
- Icons: critical.png (hexagonal stop sign), urgent.png, normal.png, low.png
- 1-bit format optimized for thermal printers

**Requirements:**
- PIL (Pillow)
- Django environment configured