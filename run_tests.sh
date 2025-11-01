#!/bin/bash

# Test Runner Script for ADHD Print Task Management System
# This script provides convenient test execution with various options

set -e

# Configuration
TEST_SETTINGS="adhd_print_project.test_settings"
TEST_MODULES="tasks.tests tasks.tests.test_views tasks.tests.test_ui_integration tasks.tests.test_periodic tasks.tests.test_background_jobs"
COVERAGE_THRESHOLD=80

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Functions
print_header() {
    echo -e "${BLUE}======================================${NC}"
    echo -e "${BLUE} ADHD Print Test Runner${NC}"
    echo -e "${BLUE}======================================${NC}"
    echo ""
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

# Check if coverage is installed
check_coverage() {
    if ! command -v coverage &> /dev/null; then
        print_warning "Coverage not installed. Install with: pip install coverage"
        return 1
    fi
    return 0
}

# Run basic tests
run_basic_tests() {
    print_info "Running basic test suite..."
    
    if python manage.py test $TEST_MODULES --settings=$TEST_SETTINGS; then
        print_success "All tests passed!"
        return 0
    else
        print_error "Some tests failed!"
        return 1
    fi
}

# Run tests with coverage
run_coverage_tests() {
    if ! check_coverage; then
        print_error "Cannot run coverage tests without coverage package"
        return 1
    fi
    
    print_info "Running tests with coverage analysis..."
    
    # Run tests with coverage
    if coverage run --source='.' manage.py test $TEST_MODULES --settings=$TEST_SETTINGS; then
        print_success "Tests completed successfully"
        
        # Generate coverage report
        echo ""
        print_info "Coverage Report:"
        coverage report
        
        # Check coverage threshold
        COVERAGE_PERCENT=$(coverage report | tail -1 | awk '{print $4}' | sed 's/%//')
        if [ "${COVERAGE_PERCENT%.*}" -ge "$COVERAGE_THRESHOLD" ]; then
            print_success "Coverage threshold ($COVERAGE_THRESHOLD%) met: $COVERAGE_PERCENT%"
        else
            print_warning "Coverage below threshold: $COVERAGE_PERCENT% < $COVERAGE_THRESHOLD%"
        fi
        
        return 0
    else
        print_error "Tests failed!"
        return 1
    fi
}

# Run specific test module
run_specific_tests() {
    local test_pattern="$1"
    print_info "Running specific tests: $test_pattern"
    
    if python manage.py test "$test_pattern" --settings=$TEST_SETTINGS; then
        print_success "Specific tests passed!"
        return 0
    else
        print_error "Specific tests failed!"
        return 1
    fi
}

# Run tests in parallel
run_parallel_tests() {
    print_info "Running tests in parallel..."
    
    if python manage.py test --parallel --settings=$TEST_SETTINGS; then
        print_success "Parallel tests completed successfully!"
        return 0
    else
        print_error "Parallel tests failed!"
        return 1
    fi
}

# Generate HTML coverage report
generate_html_coverage() {
    if ! check_coverage; then
        return 1
    fi
    
    print_info "Generating HTML coverage report..."
    
    # Run tests with coverage if coverage data doesn't exist
    if [ ! -f ".coverage" ]; then
        print_info "No coverage data found, running tests first..."
        coverage run --source='.' manage.py test $TEST_MODULES --settings=$TEST_SETTINGS
    fi
    
    # Generate HTML report
    coverage html
    
    if [ -d "htmlcov" ]; then
        print_success "HTML coverage report generated in htmlcov/"
        print_info "Open htmlcov/index.html in your browser to view the report"
        
        # Try to open the report automatically
        if command -v open &> /dev/null; then
            open htmlcov/index.html
        elif command -v xdg-open &> /dev/null; then
            xdg-open htmlcov/index.html
        fi
    else
        print_error "Failed to generate HTML coverage report"
        return 1
    fi
}

# Clean test artifacts
clean_test_artifacts() {
    print_info "Cleaning test artifacts..."
    
    # Remove coverage files
    rm -f .coverage
    rm -rf htmlcov/
    rm -f coverage.xml
    
    # Remove test database files
    rm -f test_*.db
    
    # Remove Python cache
    find . -name "*.pyc" -delete
    find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
    
    print_success "Test artifacts cleaned"
}

# Lint and test
run_quality_checks() {
    print_info "Running quality checks..."
    
    # Check for Python syntax errors
    print_info "Checking Python syntax..."
    if python -m py_compile tasks/tests.py; then
        print_success "Python syntax check passed"
    else
        print_error "Python syntax errors found"
        return 1
    fi
    
    # Run tests
    if run_coverage_tests; then
        print_success "All quality checks passed"
        return 0
    else
        print_error "Quality checks failed"
        return 1
    fi
}

# Watch mode (requires entr or similar)
run_watch_mode() {
    if ! command -v entr &> /dev/null; then
        print_error "Watch mode requires 'entr'. Install with: brew install entr (macOS) or apt-get install entr (Ubuntu)"
        return 1
    fi
    
    print_info "Starting watch mode (tests will run on file changes)..."
    print_info "Press Ctrl+C to stop"
    
    find . -name "*.py" | entr -c python manage.py test $TEST_MODULES --settings=$TEST_SETTINGS
}

# Show help
show_help() {
    print_header
    echo "Usage: $0 [OPTION]"
    echo ""
    echo "Options:"
    echo "  basic       Run basic test suite (default)"
    echo "  coverage    Run tests with coverage analysis"
    echo "  html        Generate HTML coverage report"
    echo "  parallel    Run tests in parallel"
    echo "  specific    Run specific test pattern (requires pattern argument)"
    echo "  quality     Run quality checks (syntax + coverage tests)"
    echo "  watch       Run tests in watch mode (requires entr)"
    echo "  clean       Clean test artifacts"
    echo "  help        Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0                                    # Run basic tests"
    echo "  $0 coverage                          # Run with coverage"
    echo "  $0 specific tasks.tests.TaskModelTests # Run specific tests"
    echo "  $0 html                              # Generate HTML coverage report"
    echo "  $0 parallel                          # Run tests in parallel"
    echo ""
}

# Main script logic
main() {
    # Check if we're in the correct directory
    if [ ! -f "manage.py" ]; then
        print_error "Please run this script from the Django project root directory"
        exit 1
    fi
    
    # Parse command line arguments
    case "${1:-basic}" in
        "basic")
            print_header
            run_basic_tests
            ;;
        "coverage")
            print_header
            run_coverage_tests
            ;;
        "html")
            print_header
            generate_html_coverage
            ;;
        "parallel")
            print_header
            run_parallel_tests
            ;;
        "specific")
            if [ -z "$2" ]; then
                print_error "Specific test pattern required"
                echo "Example: $0 specific tasks.tests.TaskModelTests"
                exit 1
            fi
            print_header
            run_specific_tests "$2"
            ;;
        "quality")
            print_header
            run_quality_checks
            ;;
        "watch")
            print_header
            run_watch_mode
            ;;
        "clean")
            print_header
            clean_test_artifacts
            ;;
        "help"|"-h"|"--help")
            show_help
            ;;
        *)
            print_error "Unknown option: $1"
            show_help
            exit 1
            ;;
    esac
}

# Run main function with all arguments
main "$@"