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


def create_task_image(task):
    """Create a simple, thermal-printer optimized image"""
    # Use conservative width that works - we can scale up gradually
    # Start with 576 pixels which worked before, then adjust
    width = 576  # Conservative width that we know works
    height = 800  # Increased height for larger title font

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

        font = ImageFont.truetype(font_path, 26)
        title_font = ImageFont.truetype(font_path, 52)  # Double size for title

        # New fonts for enhanced Parents section
        try:
            parents_label_font = ImageFont.truetype(
                bold_font_path, 24)  # Bold 24pt for "Parents" label
        except BaseException:
            parents_label_font = ImageFont.truetype(
                font_path, 24)  # Fallback to regular
        parents_text_font = ImageFont.truetype(
            font_path, 30)  # 30pt for parent task names
    except BaseException:
        try:
            # Fallback to system fonts
            font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 26)
            title_font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 52)

            # Try to get bold system font
            try:
                parents_label_font = ImageFont.truetype(
                    "/System/Library/Fonts/Helvetica-Bold.ttc", 24)
            except BaseException:
                parents_label_font = ImageFont.truetype(
                    "/System/Library/Fonts/Helvetica.ttc", 24)
            parents_text_font = ImageFont.truetype(
                "/System/Library/Fonts/Helvetica.ttc", 30)
        except BaseException:
            try:
                font = ImageFont.truetype("/System/Library/Fonts/Arial.ttf", 26)
                title_font = ImageFont.truetype("/System/Library/Fonts/Arial.ttf", 52)

                # Try to get bold Arial
                try:
                    parents_label_font = ImageFont.truetype(
                        "/System/Library/Fonts/Arial-Bold.ttf", 24)
                except BaseException:
                    parents_label_font = ImageFont.truetype(
                        "/System/Library/Fonts/Arial.ttf", 24)
                parents_text_font = ImageFont.truetype(
                    "/System/Library/Fonts/Arial.ttf", 30)
            except BaseException:
                try:
                    # Linux font fallbacks (for Docker containers)
                    font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 26)
                    title_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 52)

                    # Try to get bold DejaVu
                    try:
                        parents_label_font = ImageFont.truetype(
                            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 24)
                    except BaseException:
                        parents_label_font = ImageFont.truetype(
                            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 24)
                    parents_text_font = ImageFont.truetype(
                        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 30)
                except BaseException:
                    try:
                        # Try Liberation fonts (also common in Linux)
                        font = ImageFont.truetype("/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf", 26)
                        title_font = ImageFont.truetype("/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf", 52)

                        try:
                            parents_label_font = ImageFont.truetype(
                                "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf", 24)
                        except BaseException:
                            parents_label_font = ImageFont.truetype(
                                "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf", 24)
                        parents_text_font = ImageFont.truetype(
                            "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf", 30)
                    except BaseException:
                        # Final fallback to default font
                        font = ImageFont.load_default()
                        title_font = font
                        parents_label_font = font
                        parents_text_font = font

    # Layout with larger spacing for 26pt font
    current_y = 30  # More top padding for larger content
    line_spacing = 35  # Larger line spacing for 26pt font
    margin = 28  # Larger margins for better layout

    # Draw a border that fits within the printable area - will be redrawn at the end
    # (Initial border is just for reference, final border will be properly sized)
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

        # Position icon in top right corner with some margin
        icon_x = width - icon.width - 20  # 20px margin from right edge
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
        font_size = 24  # parents_label_font size
        underline_y = current_y + font_size + 2  # Position below the text baseline
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
                    current_y += 38  # Line spacing for 30pt font
            else:
                # Single line - center it
                task_x = (width - task_width) // 2  # Center horizontally
                draw.text((task_x, current_y), parent_task,
                          fill=0, font=parents_text_font)
                current_y += 38  # Line spacing for 30pt font

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
            # Use larger title font
            draw.text((margin, current_y), line, fill=0, font=title_font)
            current_y += 60  # Larger line spacing for 52pt font
    else:
        # Use larger title font
        draw.text((margin, current_y), title, fill=0, font=title_font)
        current_y += 60  # Reduced spacing after title

    # Draw separator
    draw.line([(margin, current_y), (width - margin, current_y)], fill=0, width=1)
    current_y += 8

    # Draw description if exists
    if task.description:
        desc = task.description
        max_chars_per_line = 30  # Characters for 26pt font

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
    border_left = 10
    border_top = 10
    border_right = width - 11
    border_bottom = current_y + 20

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

    # Crop to actual content with proper padding
    final_height = current_y + 25  # Extra padding at bottom for larger content
    final_img = img.crop((0, 0, width, final_height))

    return final_img


def convert_image_to_escp(image):
    """Convert PIL image to ESC/POS commands using simple 8-dot graphics for thermal printers"""
    # Convert to 1-bit (black and white) with better dithering
    bw_image = image.convert('1', dither=Image.FLOYDSTEINBERG)
    width, height = bw_image.size

    # ESC/POS commands for thermal printers
    commands = []

    # Initialize printer (ESC/POS)
    commands.append(b'\x1B\x40')  # ESC @ (Initialize printer)

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

    # Add some space and cut
    commands.append(b'\x0A\x0A')
    commands.append(b'\x1D\x56\x00')  # GS V 0 (Full cut)

    return b''.join(commands)


def convert_image_to_bitmap_escp(image):
    """Alternative: Convert PIL image using GS v 0 bitmap command (more reliable)"""
    # Convert to 1-bit black and white
    bw_image = image.convert('1', dither=Image.FLOYDSTEINBERG)
    width, height = bw_image.size

    # ESC/POS commands
    commands = []

    # Initialize printer
    commands.append(b'\x1B\x40')  # ESC @ (Initialize printer)

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

    # Add more feeding for proper cutting (thermal printers need extra space)
    # 10 line feeds for better cutting space
    commands.append(b'\x0A\x0A\x0A\x0A\x0A\x0A\x0A\x0A\x0A\x0A')

    # Full cut command
    commands.append(b'\x1D\x56\x00')  # GS V 0 (Full cut)

    return b''.join(commands)




def print_task(task, use_graphics=True):

    # Set font to Font A (default)
    commands.append(b'\x1B\x4D\x00')  # ESC M 0 (Font A)

    # Draw border with text characters
    border_line = "=" * 42 + "\n"
    commands.append(border_line.encode('utf-8'))

    # Add urgency indicator in text mode (simple symbols)
    urgency_symbols = {
        'critical': '[!!!]',
        'urgent': '[!!] ',
        'normal': '[!]  ',
        'low': '[ ]  '
    }
    urgency_symbol = urgency_symbols.get(task.urgency, '[?]  ')

    # Position urgency symbol at the end of the top border
    top_line = "=" * 35 + urgency_symbol + "\n"
    commands.pop()  # Remove the previous border line
    commands.append(top_line.encode('utf-8'))

    # Due date without emphasis
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

    commands.append(f"{due_text}\n".encode('utf-8'))

    commands.append(("-" * 42 + "\n").encode('utf-8'))

    # Get task hierarchy
    hierarchy = get_task_hierarchy(task)

    # Print hierarchy path
    if len(hierarchy) > 1:
        # Text mode: Center "Parents" with underline, then list each parent task
        # centered

        # Center and underline "Parents" label
        parents_label = "Parents"
        label_padding = (42 - len(parents_label)) // 2
        centered_label = " " * label_padding + parents_label
        commands.append(f"{centered_label}\n".encode('utf-8'))

        # Add underline using dashes
        underline = " " * label_padding + "-" * len(parents_label)
        commands.append(f"{underline}\n".encode('utf-8'))

        # Add each parent task on its own line, centered
        parent_tasks = hierarchy[:-1]  # All except the current task

        for parent_task in parent_tasks:
            # Check if task name needs wrapping (42 chars is full width, use 40 to be
            # safe)
            if len(parent_task) > 40:
                # Word wrap the task name
                words = parent_task.split()
                lines = []
                current_line = ""

                for word in words:
                    if len(current_line + word + " ") <= 40:
                        current_line += word + " "
                    else:
                        if current_line:
                            lines.append(current_line.strip())
                        current_line = word + " "

                if current_line:
                    lines.append(current_line.strip())

                # Center each line
                for line in lines:
                    line_padding = (42 - len(line)) // 2
                    centered_line = " " * line_padding + line
                    commands.append(f"{centered_line}\n".encode('utf-8'))
            else:
                # Single line - center it
                task_padding = (42 - len(parent_task)) // 2
                centered_task = " " * task_padding + parent_task
                commands.append(f"{centered_task}\n".encode('utf-8'))

        commands.append(("-" * 42 + "\n").encode('utf-8'))

    # Print task title with centering (using ESC/POS alignment commands)
    # Send center alignment command
    commands.append(b'\x1B\x61\x01')  # ESC a 1 (Center align)
    
    # Word wrap title for normal text (42 chars per line, use 40 to be safe)
    title = task.title
    if len(title) > 40:
        words = title.split()
        lines = []
        current_line = ""
        for word in words:
            test_line = current_line + (" " if current_line else "") + word
            if len(test_line) <= 40:
                current_line = test_line
            else:
                if current_line:
                    lines.append(current_line)
                current_line = word
        if current_line:
            lines.append(current_line)

        for line in lines:
            commands.append(f"{line}\n".encode('utf-8'))
    else:
        commands.append(f"{title}\n".encode('utf-8'))
    
    # Reset to left alignment
    commands.append(b'\x1B\x61\x00')  # ESC a 0 (Left align)
    commands.append(("-" * 42 + "\n").encode('utf-8'))

    # Print description
    if task.description:
        desc = task.description
        if len(desc) > 42:
            words = desc.split()
            lines = []
            current_line = ""
            for word in words:
                if len(current_line + word) <= 39:
                    current_line += word + " "
                else:
                    if current_line:
                        lines.append(current_line.strip())
                    current_line = word + " "
            if current_line:
                lines.append(current_line.strip())

            for line in lines:
                commands.append(f"{line}\n".encode('utf-8'))
        else:
            commands.append(f"{desc}\n".encode('utf-8'))
        commands.append(("-" * 42 + "\n").encode('utf-8'))

    # Close border
    commands.append(border_line.encode('utf-8'))

    # Add space and cut (ESC/POS)
    commands.append(b'\x0A\x0A')
    commands.append(b'\x1D\x56\x00')  # GS V 0 (Full cut)

def print_task(task, use_graphics=True):
    """
    Print a task to the configured ESC/POS thermal printer.

    Args:
        task: Django task model instance with urgency, title, description, due_date
        use_graphics (bool): True for graphics mode (default), False for text mode

    Returns:
        tuple: (success: bool, message: str)

    Graphics mode features:
        - Material Design urgency icons (85x85px)
        - Roboto fonts: 52pt for titles, 26pt for other text
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
        # Use bitmap graphics mode only
        image = create_task_image(task)
        print_data = convert_image_to_bitmap_escp(image)

        # Send to printer
        printer_host = getattr(settings, 'PRINTER_HOST', '192.168.1.40')
        printer_port = getattr(settings, 'PRINTER_PORT', 9100)

        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(10)  # 10 second timeout
            sock.connect((printer_host, printer_port))
            sock.sendall(print_data)

        mode_text = "graphics (bitmap)" if use_graphics else "text"
        return True, f"Task printed successfully ({mode_text} mode)"

    except socket.error as e:
        return False, f"Printer connection error: {str(e)}"
    except Exception as e:
        return False, f"Print error: {str(e)}"
