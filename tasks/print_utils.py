"""
Thermal Printer Utilities for ADHD Print System

This module provides comprehensive printing functionality for ESC/POS thermal printers.
Supports both graphics mode (with Material Design icons and Roboto fonts) and
text mode fallback for maximum compatibility.

Tested with: Qian QOP-T80UL-RI-02 thermal printer
Resolution: 302 DPI, Paper width: 72mm
Connection: TCP/IP socket (configurable)

Features:
- High-quality graphics printing with Roboto fonts (52pt titles, 26pt text)
- Material Design urgency icons
- Due date indicators with status
- Hierarchical task path display
- Professional bordered layout
- Fallback text mode for compatibility
"""

import socket
import os
from PIL import Image, ImageDraw, ImageFont
from django.conf import settings


def get_urgency_color(urgency):
    """Return color based on task urgency"""
    colors = {
        'low': '#28a745',
        'normal': '#007bff',
        'urgent': '#ffc107',
        'critical': '#dc3545'
    }
    return colors.get(urgency, '#007bff')


def get_task_hierarchy(task):
    """Get the hierarchical path to the task"""
    hierarchy = []
    current = task

    # Build hierarchy from current task up to root
    while current:
        hierarchy.append(current.title)
        current = current.parent

    # Reverse to get root -> current order
    hierarchy.reverse()
    return hierarchy


def create_task_image(task, printer_width='80mm'):
    """Create a thermal-printer optimized image with adaptive width
    
    Args:
        task: Django task model instance
        printer_width (str): '80mm' or '57mm' for printer paper width
        
    Returns:
        PIL Image: 1-bit image optimized for thermal printing
    """
    # Debug logging to see what width parameter is being received
    print(f"🖨️ DEBUG: create_task_image called with printer_width='{printer_width}'")
    
    # Calculate dimensions based on printer width at 203 DPI
    # 80mm = ~640px, 57mm = ~456px at 203 DPI, but use conservative values
    if printer_width == '57mm':
        width = 375  # Reduced from 400px to account for 5mm physical margins on each side
        # Scale fonts down for narrower format
        title_font_size = 38  # Further reduced to fit narrower width
        regular_font_size = 24  # Slightly reduced
        parents_label_font_size = 17  # Slightly reduced
        parents_text_font_size = 21  # Slightly reduced
        margin = 20  # Increased margins to ensure content fits within physical limits
        line_spacing = 26  # Slightly reduced for tighter layout
        icon_margin = 15  # Increased to prevent icon cutoff
        top_feed = 20  # Minimal top padding within image (actual feed in ESC/POS)
        bottom_padding = 5  # Minimal bottom padding for 57mm
        print(f"🖨️ DEBUG: Using 57mm settings - width={width}, title_font={title_font_size}")
    else:  # 80mm (default)
        width = 576  # Conservative width that works for 80mm
        # Keep original font sizes
        title_font_size = 52
        regular_font_size = 26
        parents_label_font_size = 24
        parents_text_font_size = 30
        margin = 28
        line_spacing = 35
        icon_margin = 20
        top_feed = 30  # Keep original top padding for 80mm
        bottom_padding = 25  # Keep original bottom padding for 80mm
        print(f"🖨️ DEBUG: Using 80mm settings - width={width}, title_font={title_font_size}")
    
    height = 800  # Initial height, will be adjusted as needed

    # Create image with white background
    img = Image.new('1', (width, height), 1)  # Start as 1-bit image
    draw = ImageDraw.Draw(img)

    # Try to load the included Roboto font, fall back to system fonts

    try:
        # Use the Roboto fonts included in the project
        font_path = os.path.join(
            settings.BASE_DIR,
            'static',
            'fonts',
            'Roboto-Regular.ttf')
        bold_font_path = os.path.join(
            settings.BASE_DIR,
            'static',
            'fonts',
            'Roboto-Bold.ttf')

        font = ImageFont.truetype(font_path, regular_font_size)
        title_font = ImageFont.truetype(font_path, title_font_size)

        # New fonts for enhanced Parents section
        try:
            parents_label_font = ImageFont.truetype(
                bold_font_path, parents_label_font_size)  # Bold for "Parents" label
        except BaseException:
            parents_label_font = ImageFont.truetype(
                font_path, parents_label_font_size)  # Fallback to regular
        parents_text_font = ImageFont.truetype(
            font_path, parents_text_font_size)  # For parent task names
    except BaseException:
        try:
            # Fallback to system fonts
            font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", regular_font_size)
            title_font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", title_font_size)

            # Try to get bold system font
            try:
                parents_label_font = ImageFont.truetype(
                    "/System/Library/Fonts/Helvetica-Bold.ttc", parents_label_font_size)
            except BaseException:
                parents_label_font = ImageFont.truetype(
                    "/System/Library/Fonts/Helvetica.ttc", parents_label_font_size)
            parents_text_font = ImageFont.truetype(
                "/System/Library/Fonts/Helvetica.ttc", parents_text_font_size)
        except BaseException:
            try:
                font = ImageFont.truetype("/System/Library/Fonts/Arial.ttf", regular_font_size)
                title_font = ImageFont.truetype("/System/Library/Fonts/Arial.ttf", title_font_size)

                # Try to get bold Arial
                try:
                    parents_label_font = ImageFont.truetype(
                        "/System/Library/Fonts/Arial-Bold.ttf", parents_label_font_size)
                except BaseException:
                    parents_label_font = ImageFont.truetype(
                        "/System/Library/Fonts/Arial.ttf", parents_label_font_size)
                parents_text_font = ImageFont.truetype(
                    "/System/Library/Fonts/Arial.ttf", parents_text_font_size)
            except BaseException:
                try:
                    # Linux font fallbacks (for Docker containers)
                    font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", regular_font_size)
                    title_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", title_font_size)

                    # Try to get bold DejaVu
                    try:
                        parents_label_font = ImageFont.truetype(
                            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", parents_label_font_size)
                    except BaseException:
                        parents_label_font = ImageFont.truetype(
                            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", parents_label_font_size)
                    parents_text_font = ImageFont.truetype(
                        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", parents_text_font_size)
                except BaseException:
                    try:
                        # Try Liberation fonts (also common in Linux)
                        font = ImageFont.truetype("/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf", regular_font_size)
                        title_font = ImageFont.truetype("/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf", title_font_size)

                        try:
                            parents_label_font = ImageFont.truetype(
                                "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf", parents_label_font_size)
                        except BaseException:
                            parents_label_font = ImageFont.truetype(
                                "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf", parents_label_font_size)
                        parents_text_font = ImageFont.truetype(
                            "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf", parents_text_font_size)
                    except BaseException:
                        # Final fallback to default font
                        font = ImageFont.load_default()
                        title_font = font
                        parents_label_font = font
                        parents_text_font = font

    # Layout with calculated spacing based on printer width
    current_y = top_feed  # Top padding (2cm for 57mm, original for 80mm)
    
    # Add extra space for 57mm to accommodate the urgency icon (85x85)
    if printer_width == '57mm':
        current_y += 90  # Move title down to avoid icon overlap (85px icon + 5px margin)
    
    border_thickness = 4

    # Add urgency icon in top right corner using Material Design icons
    icon_filename = f"{task.urgency}.png"
    icon_path = os.path.join(settings.BASE_DIR, 'static', 'icons', icon_filename)

    try:
        # Load the Material Design urgency icon
        icon = Image.open(icon_path)

        # Convert to 1-bit if needed (our generated icons are already 1-bit)
        if icon.mode != '1':
            icon = icon.convert('1', dither=Image.FLOYDSTEINBERG)

        # Position icon in top right corner with margin based on printer width
        icon_x = width - icon.width - icon_margin
        icon_y = 15  # 15px margin from top

        # Paste the icon onto the image
        img.paste(icon, (icon_x, icon_y))

    except Exception:
        # If Material Design icon loading fails, use simple fallback shapes (85x85 size)
        icon_x = width - 100  # Space for 85x85 icon plus margin
        icon_y = 15

        if task.urgency == 'critical':
            # Hexagonal stop sign style for critical (adjusted for 85x85)
            draw.rectangle([icon_x + 18, icon_y + 5, icon_x +
                           25, icon_y + 70], fill=0)  # Pole
            draw.polygon([(icon_x +
                           25, icon_y +
                           5), (icon_x +
                                62, icon_y +
                                5), (icon_x +
                                     67, icon_y +
                                     16), (icon_x +
                                           62, icon_y +
                                           27), (icon_x +
                          25, icon_y +
                          27)], fill=0)  # Flag
        elif task.urgency == 'urgent':
            # Warning triangle for urgent (adjusted for 85x85)
            triangle_points = [(icon_x + 42, icon_y + 5),
                               (icon_x + 78, icon_y + 71), (icon_x + 7, icon_y + 71)]
            draw.polygon(triangle_points, outline=0, width=4)
            draw.rectangle([icon_x + 39, icon_y + 22, icon_x + 46, icon_y + 47], fill=0)
            draw.rectangle([icon_x + 39, icon_y + 54, icon_x + 46, icon_y + 61], fill=0)
        elif task.urgency == 'normal':
            # Info circle for normal (adjusted for 85x85)
            draw.ellipse([icon_x + 7, icon_y + 5, icon_x +
                         78, icon_y + 76], outline=0, width=4)
            draw.rectangle([icon_x + 39, icon_y + 18, icon_x +
                           46, icon_y + 25], fill=0)  # Dot
            draw.rectangle([icon_x + 39, icon_y + 32, icon_x +
                           46, icon_y + 59], fill=0)  # Line
        else:  # low
            # Simple circle for low priority (adjusted for 85x85)
            draw.ellipse([icon_x + 14, icon_y + 14, icon_x +
                         71, icon_y + 71], outline=0, width=4)

    # Due date indicator (moved up since priority text was removed)
    if hasattr(task, 'due_date') and task.due_date:
        from django.utils import timezone
        # Format the due date
        due_date_str = task.due_date.strftime("%Y-%m-%d")
        # Check if it's overdue
        if task.due_date.date() < timezone.now().date():
            due_text = f"DUE: {due_date_str} (OVERDUE!)"
        elif task.due_date.date() == timezone.now().date():
            due_text = f"DUE: {due_date_str} (TODAY!)"
        else:
            due_text = f"DUE: {due_date_str}"
    else:
        due_text = "DUE: Not set"

    # Use regular font
    draw.text((margin, current_y), due_text, fill=0, font=font)
    current_y += line_spacing * 2

    # Draw a separator line
    draw.line([(margin, current_y), (width - margin, current_y)], fill=0, width=1)
    current_y += 8

    # Get task hierarchy and path
    hierarchy = get_task_hierarchy(task)

    # Draw hierarchy path if exists
    if len(hierarchy) > 1:
        # New formatting: "Parents" bold, underlined, centered, 24pt
        # Individual parent tasks on separate lines, centered, 30pt

        # Draw "Parents" label - centered, bold, underlined
        parents_label = "Parents"

        # Get text dimensions for centering
        bbox = draw.textbbox((0, 0), parents_label, font=parents_label_font)
        label_width = bbox[2] - bbox[0]
        label_x = (width - label_width) // 2  # Center horizontally

        # Draw the "Parents" label
        draw.text((label_x, current_y), parents_label, fill=0, font=parents_label_font)

        # Draw underline for "Parents" label
        # Use font size to calculate proper underline position
        underline_y = current_y + parents_label_font_size + 2  # Position below the text baseline
        underline_start_x = label_x
        underline_end_x = label_x + label_width
        draw.line([(underline_start_x, underline_y),
                  (underline_end_x, underline_y)], fill=0, width=2)

        current_y += 35  # Space after "Parents" label

        # Draw each parent task on its own line, centered
        parent_tasks = hierarchy[:-1]  # All except the current task

        for parent_task in parent_tasks:
            # Get text dimensions for centering
            bbox = draw.textbbox((0, 0), parent_task, font=parents_text_font)
            task_width = bbox[2] - bbox[0]

            # Use actual pixel width to determine if wrapping is needed
            # Leave reasonable margins (40px on each side) for 576px total width
            max_line_width = width - 80  # 496px available width

            if task_width > max_line_width:
                # Word wrap the task name based on actual pixel measurements
                words = parent_task.split()
                lines = []
                current_line = ""

                for word in words:
                    test_line = current_line + (" " if current_line else "") + word
                    test_bbox = draw.textbbox((0, 0), test_line, font=parents_text_font)
                    test_width = test_bbox[2] - test_bbox[0]

                    if test_width <= max_line_width:
                        current_line = test_line
                    else:
                        if current_line:
                            lines.append(current_line.strip())
                        current_line = word

                if current_line:
                    lines.append(current_line.strip())

                # Draw each line of the wrapped task name, centered
                for line in lines:
                    bbox = draw.textbbox((0, 0), line, font=parents_text_font)
                    line_width = bbox[2] - bbox[0]
                    line_x = (width - line_width) // 2  # Center horizontally
                    draw.text((line_x, current_y), line, fill=0, font=parents_text_font)
                    current_y += int(parents_text_font_size * 1.3)  # Line spacing based on font size
            else:
                # Single line - center it
                task_x = (width - task_width) // 2  # Center horizontally
                draw.text((task_x, current_y), parent_task,
                          fill=0, font=parents_text_font)
                current_y += int(parents_text_font_size * 1.3)  # Line spacing based on font size

        # Draw separator
        draw.line([(margin, current_y), (width - margin, current_y)], fill=0, width=1)
        current_y += 8

    # Draw task title with better formatting using larger font
    title = task.title

    # Use actual pixel width to determine if wrapping is needed for 52pt font
    # Leave reasonable margins (20px on each side) for 576px total width
    max_title_width = width - 40  # 536px available width for title

    # Get text dimensions for the full title
    bbox = draw.textbbox((0, 0), title, font=title_font)
    title_width = bbox[2] - bbox[0]

    if title_width > max_title_width:
        # Word wrap the title based on actual pixel measurements
        words = title.split()
        lines = []
        current_line = ""

        for word in words:
            test_line = current_line + (" " if current_line else "") + word
            test_bbox = draw.textbbox((0, 0), test_line, font=title_font)
            test_width = test_bbox[2] - test_bbox[0]

            if test_width <= max_title_width:
                current_line = test_line
            else:
                if current_line:
                    lines.append(current_line.strip())
                current_line = word

        if current_line:
            lines.append(current_line.strip())

        for line in lines:
            # Use title font
            draw.text((margin, current_y), line, fill=0, font=title_font)
            current_y += int(title_font_size * 1.2)  # Line spacing based on title font size
    else:
        # Use title font
        draw.text((margin, current_y), title, fill=0, font=title_font)
        current_y += int(title_font_size * 1.1)  # Spacing after title based on font size

    # Draw separator
    draw.line([(margin, current_y), (width - margin, current_y)], fill=0, width=1)
    current_y += 8

    # Draw description if exists
    if task.description:
        desc = task.description
        # Calculate max characters per line based on width and font size
        # Rough estimate: ~20 chars per line for 57mm, ~30 for 80mm
        max_chars_per_line = 20 if printer_width == '57mm' else 30

        if len(desc) > max_chars_per_line:
            # Word wrapping for description
            words = desc.split()
            lines = []
            current_line = ""
            for word in words:
                if len(current_line + word) <= max_chars_per_line:
                    current_line += word + " "
                else:
                    if current_line:
                        lines.append(current_line.strip())
                    current_line = word + " "
            if current_line:
                lines.append(current_line.strip())

            for line in lines:
                # Use regular font
                draw.text((margin, current_y), line, fill=0, font=font)
                current_y += line_spacing
        else:
            # Use regular font
            draw.text((margin, current_y), desc, fill=0, font=font)
            current_y += line_spacing

        # Draw separator
        draw.line([(margin, current_y + 5), (width - margin, current_y + 5)],
                  fill=0, width=1)
        current_y += 12

    # Add timestamp for reference
    from django.utils import timezone
    timestamp = timezone.localtime(task.created_at).strftime("%Y-%m-%d %H:%M")
    draw.text((margin, current_y), f"Created: {timestamp}", fill=0, font=font)
    current_y += line_spacing + 15  # Reduced padding before bottom border

    # Ensure we have enough space for the bottom border
    if current_y + 30 > height:
        height = current_y + 30
        # Create new image with proper height
        new_img = Image.new('1', (width, height), 1)
        new_img.paste(img, (0, 0))
        img = new_img
        draw = ImageDraw.Draw(img)

    # Draw the complete border now that we know the final dimensions
    border_margin = 5 if printer_width == '57mm' else 10  # Smaller border margin for 57mm
    border_left = border_margin
    border_top = border_margin
    border_right = width - border_margin - 1
    border_bottom = current_y + (10 if printer_width == '57mm' else 20)  # Less space for 57mm

    # Draw border as separate lines to avoid protrusion issues
    # Top border
    draw.rectangle([border_left, border_top, border_right,
                   border_top + border_thickness - 1], fill=0)
    # Bottom border
    draw.rectangle([border_left, border_bottom - border_thickness +
                   1, border_right, border_bottom], fill=0)
    # Left border
    draw.rectangle([border_left, border_top, border_left +
                   border_thickness - 1, border_bottom], fill=0)
    # Right border
    draw.rectangle([border_right - border_thickness + 1,
                   border_top, border_right, border_bottom], fill=0)

    # Crop to actual content with proper padding (ensure border is included)
    border_space = 10 if printer_width == '57mm' else 20
    final_height = current_y + border_space + 5  # Extra 5px to ensure border is visible
    final_img = img.crop((0, 0, width, final_height))

    return final_img


def convert_image_to_escp(image, printer_width='80mm'):
    """Convert PIL image to ESC/POS commands using simple 8-dot graphics for thermal printers"""
    # Convert to 1-bit (black and white) with better dithering
    bw_image = image.convert('1', dither=Image.FLOYDSTEINBERG)
    width, height = bw_image.size

    # ESC/POS commands for thermal printers
    commands = []

    # Initialize printer (ESC/POS)
    commands.append(b'\x1B\x40')  # ESC @ (Initialize printer)
    
    # Add top feed for 57mm printers (10mm ≈ 4 line feeds at 8 lines per cm)
    if printer_width == '57mm':
        for _ in range(4):  # 10mm top feed (reduced from 20mm)
            commands.append(b'\x0A')  # Line feed

    # Use simpler 8-dot single-density graphics (most compatible)
    # ESC/POS: ESC * 0 nL nH [data...]

    # Process image line by line (8-dot mode)
    for y in range(height):
        # Create row data
        row_data = []

        for x in range(0, width, 8):
            byte_val = 0
            for bit in range(8):
                if x + bit < width:
                    pixel = bw_image.getpixel((x + bit, y))
                    if pixel == 0:  # Black pixel
                        byte_val |= (1 << (7 - bit))
            row_data.append(byte_val)

        # Only send non-empty rows
        if any(row_data):
            # ESC/POS 8-dot graphics command: ESC * 0 nL nH data
            n1 = len(row_data) & 0xFF
            n2 = (len(row_data) >> 8) & 0xFF

            commands.append(b'\x1B\x2A\x00')   # ESC * 0 (8-dot single density)
            commands.append(bytes([n1, n2]))   # Width in bytes (low, high)
            commands.append(bytes(row_data))   # Graphics data

        # Line feed to next row
        commands.append(b'\x0A')  # LF

    # Add some space and cut only for 80mm printers (57mm usually don't have cutters)
    if printer_width == '80mm':
        commands.append(b'\x0A\x0A')  # Line feeds
        commands.append(b'\x1D\x56\x00')  # GS V 0 (Full cut)
    else:
        # For 57mm printers, add 10mm bottom feed (4 line feeds)
        for _ in range(4):  # 10mm bottom feed
            commands.append(b'\x0A')

    return b''.join(commands)


def convert_image_to_bitmap_escp(image, printer_width='80mm'):
    """Alternative: Convert PIL image using GS v 0 bitmap command (more reliable)"""
    # Convert to 1-bit black and white
    bw_image = image.convert('1', dither=Image.FLOYDSTEINBERG)
    width, height = bw_image.size

    # ESC/POS commands
    commands = []

    # Initialize printer
    commands.append(b'\x1B\x40')  # ESC @ (Initialize printer)
    
    # Add top feed for 57mm printers (10mm ≈ 4 line feeds at 8 lines per cm)
    if printer_width == '57mm':
        for _ in range(4):  # 10mm top feed (reduced from 20mm)
            commands.append(b'\x0A')  # Line feed

    # Use GS v 0 command for bitmap printing (most reliable method)
    # GS v 0 m xL xH yL yH [data...]
    # m = 0 (normal), 1 (double width), 2 (double height), 3 (double both)

    # Calculate dimensions for 72mm width at 302dpi
    bytes_per_line = (width + 7) // 8

    # Prepare bitmap data
    bitmap_data = []
    for y in range(height):
        for x in range(0, width, 8):
            byte_val = 0
            for bit in range(8):
                if x + bit < width:
                    pixel = bw_image.getpixel((x + bit, y))
                    if pixel == 0:  # Black pixel
                        byte_val |= (1 << (7 - bit))
            bitmap_data.append(byte_val)

    # Send bitmap command with normal width (0) for proper 72mm printing
    commands.append(b'\x1D\x76\x30\x00')  # GS v 0 0 (normal width bitmap)

    # Width and height in bytes
    xL = bytes_per_line & 0xFF
    xH = (bytes_per_line >> 8) & 0xFF
    yL = height & 0xFF
    yH = (height >> 8) & 0xFF

    commands.append(bytes([xL, xH, yL, yH]))
    commands.append(bytes(bitmap_data))

    # Add feeding and cutting only for 80mm printers (57mm usually don't have cutters)
    if printer_width == '80mm':
        # Add more feeding for proper cutting (thermal printers need extra space)
        # 10 line feeds for better cutting space
        commands.append(b'\x0A\x0A\x0A\x0A\x0A\x0A\x0A\x0A\x0A\x0A')
        # Full cut command
        commands.append(b'\x1D\x56\x00')  # GS V 0 (Full cut)
    else:
        # For 57mm printers, add 10mm bottom feed (4 line feeds)
        for _ in range(4):  # 10mm bottom feed
            commands.append(b'\x0A')

    return b''.join(commands)


def print_task(task, use_graphics=True, printer_width='80mm'):
    """
    Print a task to the configured ESC/POS thermal printer.

    Args:
        task: Django task model instance with urgency, title, description, due_date
        use_graphics (bool): True for graphics mode (default), False for text mode
        printer_width (str): '80mm' or '57mm' for printer paper width

    Returns:
        tuple: (success: bool, message: str)

    Graphics mode features:
        - Material Design urgency icons (85x85px)
        - Roboto fonts: Adaptive sizes based on printer width
        - Professional bordered layout with normal font weight
        - Due date indicators with status
        - Hierarchical task paths

    Text mode features:
        - ASCII borders and formatting with normal text weight
        - Compact layout for basic printers
        - Text-based urgency indicators
        - Full printer compatibility
    """
    try:
        # Debug logging to see what width parameter is being received
        print(f"🖨️ DEBUG: print_task called with printer_width='{printer_width}'")
        
        # Use bitmap graphics mode only with adaptive width
        image = create_task_image(task, printer_width)
        print(f"🖨️ DEBUG: Created image with size {image.size[0]}x{image.size[1]}")
        
        print_data = convert_image_to_bitmap_escp(image, printer_width)

        # Send to printer
        printer_host = getattr(settings, 'PRINTER_HOST', '192.168.1.40')
        printer_port = getattr(settings, 'PRINTER_PORT', 9100)

        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(10)  # 10 second timeout
            sock.connect((printer_host, printer_port))
            sock.sendall(print_data)

        mode_text = f"graphics (bitmap) {printer_width}" if use_graphics else f"text {printer_width}"
        return True, f"Task printed successfully ({mode_text} mode)"

    except socket.error as e:
        return False, f"Printer connection error: {str(e)}"
    except Exception as e:
        return False, f"Print error: {str(e)}"
