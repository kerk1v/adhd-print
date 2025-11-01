#!/bin/bash
# ADHD Print Task Management System - Docker Setup Script

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if Docker is installed
check_docker() {
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed. Please install Docker first."
        exit 1
    fi
    
    if ! command -v docker-compose &> /dev/null; then
        print_error "Docker Compose is not installed. Please install Docker Compose first."
        exit 1
    fi
    
    print_success "Docker and Docker Compose are installed"
}

# Function to setup development environment
setup_development() {
    print_status "Setting up development environment..."
    
    # Build and start services
    docker-compose build
    docker-compose up -d
    
    print_success "Development environment is running!"
    print_status "Access the application at: http://localhost:8000"
    print_status "To view logs: docker-compose logs -f"
    print_status "To stop: docker-compose down"
}

# Function to setup production environment
setup_production() {
    print_status "Setting up production environment..."
    
    # Check for required environment variables
    if [ ! -f .env.production ]; then
        print_warning "Creating .env.production template..."
        cat > .env.production << EOF
DB_PASSWORD=change_this_secure_password
DJANGO_SECRET_KEY=change_this_secret_key
DJANGO_DEBUG=False
ALLOWED_HOSTS=your-domain.com,www.your-domain.com
EOF
        print_warning "Please edit .env.production with your production settings!"
        return 1
    fi
    
    # Build and start production services
    docker-compose -f docker-compose.prod.yml --env-file .env.production build
    docker-compose -f docker-compose.prod.yml --env-file .env.production up -d
    
    print_success "Production environment is running!"
    print_status "Access the application at: http://localhost"
    print_status "To view logs: docker-compose -f docker-compose.prod.yml logs -f"
    print_status "To stop: docker-compose -f docker-compose.prod.yml down"
}

# Function to clean up Docker resources
cleanup() {
    print_status "Cleaning up Docker resources..."
    
    docker-compose down -v --remove-orphans 2>/dev/null || true
    docker-compose -f docker-compose.prod.yml down -v --remove-orphans 2>/dev/null || true
    
    print_status "Removing unused Docker images..."
    docker image prune -f
    
    print_success "Cleanup completed!"
}

# Function to show status
show_status() {
    print_status "Docker containers status:"
    docker ps --filter "name=adhd-print" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
    
    echo ""
    print_status "Docker volumes:"
    docker volume ls --filter "name=adhd" --format "table {{.Name}}\t{{.Driver}}"
}

# Function to backup data
backup_data() {
    print_status "Creating data backup..."
    
    timestamp=$(date +%Y%m%d_%H%M%S)
    backup_file="adhd_print_backup_${timestamp}.tar.gz"
    
    docker run --rm -v adhd-print_adhd_data:/data -v $(pwd):/backup alpine tar czf /backup/${backup_file} -C /data .
    
    print_success "Backup created: ${backup_file}"
}

# Function to restore data
restore_data() {
    if [ -z "$1" ]; then
        print_error "Please specify backup file: ./docker_setup.sh restore backup_file.tar.gz"
        exit 1
    fi
    
    if [ ! -f "$1" ]; then
        print_error "Backup file not found: $1"
        exit 1
    fi
    
    print_status "Restoring data from: $1"
    
    docker run --rm -v adhd-print_adhd_data:/data -v $(pwd):/backup alpine tar xzf /backup/$1 -C /data
    
    print_success "Data restored from: $1"
}

# Main script logic
case "${1:-}" in
    "dev"|"development")
        check_docker
        setup_development
        ;;
    "prod"|"production")
        check_docker
        setup_production
        ;;
    "clean"|"cleanup")
        cleanup
        ;;
    "status")
        show_status
        ;;
    "backup")
        backup_data
        ;;
    "restore")
        restore_data "$2"
        ;;
    "help"|"--help"|"-h")
        echo "ADHD Print Task Management System - Docker Setup"
        echo ""
        echo "Usage: $0 [command]"
        echo ""
        echo "Commands:"
        echo "  dev, development    Setup development environment"
        echo "  prod, production    Setup production environment"
        echo "  status              Show container and volume status"
        echo "  backup              Create data backup"
        echo "  restore [file]      Restore data from backup"
        echo "  clean, cleanup      Clean up Docker resources"
        echo "  help                Show this help message"
        echo ""
        echo "Examples:"
        echo "  $0 dev              # Start development environment"
        echo "  $0 prod             # Start production environment"
        echo "  $0 backup           # Create backup"
        echo "  $0 restore backup.tar.gz # Restore from backup"
        ;;
    "")
        print_warning "No command specified. Use '$0 help' for usage information."
        setup_development
        ;;
    *)
        print_error "Unknown command: $1"
        print_status "Use '$0 help' for usage information."
        exit 1
        ;;
esac