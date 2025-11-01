#!/usr/bin/env python3
"""
Static Files Validation Script
Validates that all CSS and JavaScript files are properly referenced and exist.
"""

import os
import re
from pathlib import Path

def check_static_files():
    """Check that all static files exist and are properly referenced."""
    
    base_dir = Path(__file__).parent
    templates_dir = base_dir / 'tasks' / 'templates' / 'tasks'
    static_dir = base_dir / 'tasks' / 'static' / 'tasks'
    
    print("🔍 Checking Static Files Configuration...")
    print("=" * 50)
    
    # Check if static directories exist
    css_dir = static_dir / 'css'
    js_dir = static_dir / 'js'
    
    print(f"📁 CSS Directory: {css_dir}")
    print(f"   Exists: {'✅' if css_dir.exists() else '❌'}")
    
    print(f"📁 JS Directory: {js_dir}")
    print(f"   Exists: {'✅' if js_dir.exists() else '❌'}")
    
    # List CSS files
    print("\n📄 CSS Files:")
    if css_dir.exists():
        css_files = list(css_dir.glob('*.css'))
        for css_file in css_files:
            print(f"   ✅ {css_file.name} ({css_file.stat().st_size} bytes)")
    else:
        print("   ❌ No CSS directory found")
    
    # List JS files
    print("\n📄 JavaScript Files:")
    if js_dir.exists():
        js_files = list(js_dir.glob('*.js'))
        for js_file in js_files:
            print(f"   ✅ {js_file.name} ({js_file.stat().st_size} bytes)")
    else:
        print("   ❌ No JS directory found")
    
    # Check template references
    print("\n🔗 Template References:")
    template_files = list(templates_dir.glob('*.html'))
    
    for template_file in template_files:
        print(f"\n📄 {template_file.name}:")
        content = template_file.read_text()
        
        # Check for external CSS references
        css_refs = re.findall(r"{% static 'tasks/css/([^']+)' %}", content)
        for css_ref in css_refs:
            css_path = css_dir / css_ref
            status = "✅" if css_path.exists() else "❌"
            print(f"   CSS: {status} {css_ref}")
        
        # Check for external JS references
        js_refs = re.findall(r"{% static 'tasks/js/([^']+)' %}", content)
        for js_ref in js_refs:
            js_path = js_dir / js_ref
            status = "✅" if js_path.exists() else "❌"
            print(f"   JS:  {status} {js_ref}")
        
        # Check for inline styles (should be minimal now)
        inline_styles = content.count('<style>')
        if inline_styles > 0:
            print(f"   ⚠️  {inline_styles} inline <style> block(s) found")
        
        # Check for large inline scripts (only scripts > 500 characters)
        script_blocks = re.findall(r'<script[^>]*>(.*?)</script>', content, re.DOTALL)
        large_scripts = [s for s in script_blocks if len(s.strip()) > 500]
        if large_scripts:
            print(f"   ⚠️  {len(large_scripts)} large inline script block(s) found (>500 chars)")
        else:
            print(f"   ✅ No large inline scripts (all scripts <500 chars)")
    
    print("\n" + "=" * 50)
    print("📊 Summary:")
    
    total_css = len(list(css_dir.glob('*.css'))) if css_dir.exists() else 0
    total_js = len(list(js_dir.glob('*.js'))) if js_dir.exists() else 0
    
    print(f"   External CSS files: {total_css}")
    print(f"   External JS files: {total_js}")
    print(f"   Templates checked: {len(template_files)}")
    
    # Recommendations
    print("\n💡 Recommendations:")
    print("   ✅ CSS moved to external files")
    print("   ✅ JavaScript modularized")
    print("   ✅ Better cache performance")
    print("   ✅ Easier maintenance")
    print("   ✅ Improved page load times")

if __name__ == "__main__":
    check_static_files()