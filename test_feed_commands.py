#!/usr/bin/env python3
"""
Test script to verify the paper feed commands in ESC/POS data.
"""

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'adhd_print_project.settings')
django.setup()

from tasks.models import Task
from tasks.print_utils import create_task_image, convert_image_to_bitmap_escp

def test_feed_commands():
    print("🧪 Testing Paper Feed Commands in ESC/POS Data")
    print("=" * 60)
    
    # Get a task to test with
    task = Task.objects.first()
    if not task:
        print("❌ No tasks found")
        return
    
    print(f"✅ Using task: {task.title}")
    
    # Test 57mm with feed commands
    print("\n🔄 Testing 57mm with paper feed commands...")
    image_57mm = create_task_image(task, '57mm')
    escpos_57mm = convert_image_to_bitmap_escp(image_57mm, '57mm')
    
    # Count line feeds in ESC/POS data
    line_feeds_57mm = escpos_57mm.count(b'\x0A')
    
    print(f"📏 57mm image size: {image_57mm.size}")
    print(f"📄 57mm ESC/POS data length: {len(escpos_57mm)} bytes")
    print(f"📋 57mm line feeds count: {line_feeds_57mm}")
    
    # Test 80mm for comparison
    print("\n🔄 Testing 80mm for comparison...")
    image_80mm = create_task_image(task, '80mm')
    escpos_80mm = convert_image_to_bitmap_escp(image_80mm, '80mm')
    
    # Count line feeds in ESC/POS data
    line_feeds_80mm = escpos_80mm.count(b'\x0A')
    
    print(f"📏 80mm image size: {image_80mm.size}")
    print(f"📄 80mm ESC/POS data length: {len(escpos_80mm)} bytes")
    print(f"📋 80mm line feeds count: {line_feeds_80mm}")
    
    # Check for cut commands
    cut_commands_57mm = escpos_57mm.count(b'\x1D\x56\x00')
    cut_commands_80mm = escpos_80mm.count(b'\x1D\x56\x00')
    
    print(f"\n✂️  Cut commands: 57mm={cut_commands_57mm}, 80mm={cut_commands_80mm}")
    
    print("\n" + "=" * 60)
    print("🏁 Paper feed command analysis complete!")
    print("📊 Expected: 57mm should have ~36 line feeds (24 top + 12 bottom + image lines)")
    print("📊 Expected: 80mm should have ~10+ line feeds (mostly for cutting)")
    print("📊 Expected: Only 80mm should have cut commands")

if __name__ == '__main__':
    test_feed_commands()