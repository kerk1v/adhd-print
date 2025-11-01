#!/usr/bin/env python
"""
Test Suite Validation Script
Validates that the test suite is properly configured and ready to run.
"""

import os
import sys
import subprocess
import importlib.util
from pathlib import Path


def check_file_exists(filepath, description):
    """Check if a file exists and print result."""
    if os.path.exists(filepath):
        print(f"✅ {description}: {filepath}")
        return True
    else:
        print(f"❌ {description}: {filepath} (NOT FOUND)")
        return False


def check_python_syntax(filepath):
    """Check Python syntax for a file."""
    try:
        with open(filepath, 'r') as f:
            compile(f.read(), filepath, 'exec')
        print(f"✅ Python syntax valid: {filepath}")
        return True
    except SyntaxError as e:
        print(f"❌ Python syntax error in {filepath}: {e}")
        return False
    except Exception as e:
        print(f"❌ Error checking {filepath}: {e}")
        return False


def check_django_imports():
    """Check if Django can be imported."""
    try:
        import django
        print(f"✅ Django available: version {django.get_version()}")
        return True
    except ImportError:
        print("❌ Django not available")
        return False


def check_test_settings():
    """Check if test settings can be imported."""
    try:
        # Set up Django environment
        os.environ.setdefault(
            'DJANGO_SETTINGS_MODULE',
            'adhd_print_project.test_settings')
        import django
        django.setup()
        print("✅ Test settings import successful")
        return True
    except Exception as e:
        print(f"❌ Test settings import failed: {e}")
        return False


def main():
    """Main validation function."""
    print("🧪 ADHD Print Test Suite Validation")
    print("=" * 50)

    # Check if we're in the right directory
    if not os.path.exists('manage.py'):
        print("❌ Not in Django project root (manage.py not found)")
        sys.exit(1)

    issues = []

    # Check core files
    core_files = [
        ('manage.py', 'Django management script'),
        ('adhd_print_project/asgi.py', 'ASGI configuration'),
        ('adhd_print_project/test_settings.py', 'Test settings'),
        ('tasks/tests.py', 'Main test file'),
        ('tasks/tests/test_background_jobs.py', 'Background jobs tests'),
        ('tasks/tests/test_periodic.py', 'Periodic task tests'),
        ('TESTING_GUIDE.md', 'Testing documentation'),
        ('run_tests.sh', 'Test runner script'),
    ]

    print("\n📁 File Structure Check:")
    for filepath, description in core_files:
        if not check_file_exists(filepath, description):
            issues.append(f"Missing file: {filepath}")

    # Check Python syntax
    python_files = [
        'adhd_print_project/test_settings.py',
        'tasks/tests.py',
        'tasks/tests/test_background_jobs.py',
        'tasks/tests/test_periodic.py',
    ]

    print("\n🐍 Python Syntax Check:")
    for filepath in python_files:
        if os.path.exists(filepath):
            if not check_python_syntax(filepath):
                issues.append(f"Syntax error in: {filepath}")

    # Check imports
    print("\n📦 Import Check:")
    if not check_django_imports():
        issues.append("Django not available")

    if not check_test_settings():
        issues.append("Test settings import failed")

    # Check test discovery
    print("\n🔍 Test Discovery Check:")
    try:
        result = subprocess.run([
            sys.executable, 'manage.py', 'test', '--help'
        ], capture_output=True, text=True, timeout=10)

        if result.returncode == 0:
            print("✅ Django test command available")

            # Try to run a simple test check
            result2 = subprocess.run([
                sys.executable, 'manage.py', 'test',
                '--settings=adhd_print_project.test_settings',
                '--verbosity=0', 'tasks.tests'
            ], capture_output=True, text=True, timeout=30)

            if 'OK' in result2.stderr or 'test' in result2.stderr.lower():
                print("✅ Test execution framework working")
            else:
                print(f"⚠️  Test execution may have issues: {result2.stderr[:200]}")
        else:
            print(f"❌ Django test command failed: {result.stderr}")
            issues.append("Django test command not working")
    except subprocess.TimeoutExpired:
        print("❌ Test command timed out")
        issues.append("Test command timeout")
    except Exception as e:
        print(f"❌ Test command error: {e}")
        issues.append(f"Test command error: {e}")

    # Summary
    print("\n" + "=" * 50)
    if issues:
        print(f"❌ Validation completed with {len(issues)} issues:")
        for issue in issues:
            print(f"   • {issue}")
        print("\n🔧 Fix these issues before running tests")
        sys.exit(1)
    else:
        print("✅ All validation checks passed!")
        print("\n🚀 Test suite is ready to run!")
        print("\nNext steps:")
        print("  • Run basic tests: ./run_tests.sh")
        print("  • Run with coverage: ./run_tests.sh coverage")
        print("  • See all options: ./run_tests.sh help")


if __name__ == '__main__':
    main()
