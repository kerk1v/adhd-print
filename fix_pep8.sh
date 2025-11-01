#!/bin/bash
# PEP 8 Automated Fixes for ADHD Print Project

echo "🔧 Starting PEP 8 automated fixes..."

# Install autopep8 for automatic fixing
pip install autopep8

# Fix the most common issues automatically
echo "📝 Fixing whitespace and formatting issues..."

# Remove trailing whitespace and fix basic formatting
autopep8 --in-place --aggressive --aggressive \
    --max-line-length=88 \
    --exclude=venv,migrations,__pycache__,static,staticfiles \
    --recursive .

echo "🧹 Removing whitespace from blank lines..."
find . -name "*.py" \
    -not -path "./venv/*" \
    -not -path "./migrations/*" \
    -not -path "./__pycache__/*" \
    -not -path "./static/*" \
    -not -path "./staticfiles/*" \
    -exec sed -i '' 's/^[ \t]*$//' {} \;

echo "📄 Adding missing newlines at end of files..."
find . -name "*.py" \
    -not -path "./venv/*" \
    -not -path "./migrations/*" \
    -not -path "./__pycache__/*" \
    -not -path "./static/*" \
    -not -path "./staticfiles/*" \
    -exec sh -c 'if [ -s "$1" ] && [ "$(tail -c1 "$1")" != "" ]; then echo "" >> "$1"; fi' _ {} \;

echo "✅ Automated fixes completed!"
echo "🔍 Run 'python -m flake8 --max-line-length=88 --exclude=venv,migrations,__pycache__,static,staticfiles .' to check remaining issues"