#!/usr/bin/env python3
"""
Test script to generate and save 57mm vs 80mm layout images for visual comparison.
"""

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'adhd_print_project.settings')
django.setup()

from tasks.models import Task
from tasks.print_utils import create_task_image

def test_layout_comparison():
    print("🧪 Testing Layout Comparison: 57mm vs 80mm")
    print("=" * 60)
    
    # Get a task to test with
    task = Task.objects.first()
    if not task:
        print("❌ No tasks found")
        return
    
    print(f"✅ Using task: {task.title}")
    
    # Test 57mm layout
    print("\n🔄 Generating 57mm layout...")
    image_57mm = create_task_image(task, '57mm')
    print(f"📏 57mm image size: {image_57mm.size} (width x height)")
    
    # Save 57mm image
    image_57mm.save('/Users/volker/adhd-print/test_57mm_layout.png')
    print("💾 Saved as: test_57mm_layout.png")
    
    # Test 80mm layout
    print("\n🔄 Generating 80mm layout...")
    image_80mm = create_task_image(task, '80mm')
    print(f"📏 80mm image size: {image_80mm.size} (width x height)")
    
    # Save 80mm image
    image_80mm.save('/Users/volker/adhd-print/test_80mm_layout.png')
    print("💾 Saved as: test_80mm_layout.png")
    
    print("\n" + "=" * 60)
    print("🏁 Layout comparison complete!")
    print("📂 Check the generated PNG files to see the layout differences:")
    print("   - test_57mm_layout.png (400px wide, 2cm top feed, 1cm bottom feed)")
    print("   - test_80mm_layout.png (576px wide, original margins)")

if __name__ == '__main__':
    test_layout_comparison()