#!/bin/bash

# ISO 20022 Mapper - Podman Setup Script
# This script sets up and runs the ISO 20022 GenAI Migration Platform using Podman

set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Functions
print_header() {
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}========================================${NC}"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

check_podman() {
    print_header "Checking Podman Installation"
    
    if ! command -v podman &> /dev/null; then
        print_error "Podman is not installed. Please install Podman from https://podman.io/docs/installation"
        exit 1
    fi
    
    if ! command -v podman-compose &> /dev/null; then
        print_error "podman-compose is not installed. Please install it:"
        echo "  pip install podman-compose"
        exit 1
    fi
    
    print_success "Podman $(podman --version | cut -d' ' -f3)"
    print_success "podman-compose $(podman-compose --version | cut -d' ' -f4)"
}

setup_env() {
    print_header "Setting Up Environment"
    
    if [ ! -f ".env" ]; then
        if [ -f ".env.example" ]; then
            cp .env.example .env
            print_success "Created .env from .env.example"
            print_warning "Please update .env with your configuration (especially Azure credentials if needed)"
        else
            print_error ".env.example not found"
            exit 1
        fi
    else
        print_success ".env file already exists"
    fi
}

build_images() {
    print_header "Building Container Images"
    
    print_warning "This may take a few minutes..."
    podman-compose -f docker-compose.yml build
    
    print_success "Container images built successfully"
}

start_services() {
    print_header "Starting Services"
    
    podman-compose -f docker-compose.yml up -d
    
    print_success "Services started"
    
    # Wait for backend to be ready
    print_warning "Waiting for services to be ready (this may take 30-60 seconds)..."
    
    local max_attempts=60
    local attempt=0
    
    while [ $attempt -lt $max_attempts ]; do
        if podman-compose -f docker-compose.yml exec backend curl -f http://localhost:8000/health &>/dev/null; then
            print_success "Backend is ready"
            break
        fi
        
        attempt=$((attempt + 1))
        sleep 1
    done
    
    if [ $attempt -eq $max_attempts ]; then
        print_warning "Services may still be starting up. Check logs with: make logs"
    fi
}

show_endpoints() {
    print_header "Service Endpoints"
    
    echo -e "${GREEN}Backend API:${NC}"
    echo "  Main:      http://localhost:8000"
    echo "  Health:    http://localhost:8000/health"
    echo "  Docs:      http://localhost:8000/docs"
    echo "  ReDoc:     http://localhost:8000/redoc"
    echo ""
    echo -e "${GREEN}Frontend:${NC}"
    echo "  UI:        http://localhost:5173"
    echo ""
    echo -e "${GREEN}Services:${NC}"
    echo "  Database:  localhost:5432 (postgres:postgres)"
    echo "  Redis:     localhost:6379"
    echo "  Phoenix:   http://localhost:6006"
    echo ""
}

show_quick_commands() {
    print_header "Quick Commands"
    
    echo "View logs:"
    echo "  make logs"
    echo "  make logs-backend"
    echo "  make logs-frontend"
    echo ""
    echo "Stop services:"
    echo "  make down"
    echo ""
    echo "Clean up everything:"
    echo "  make clean"
    echo ""
    echo "Open shells:"
    echo "  make backend-shell"
    echo "  make frontend-shell"
    echo "  make db-shell"
    echo ""
    echo "For all commands: make help"
}

main() {
    print_header "ISO 20022 GenAI Migration Platform - Podman Setup"
    
    local action="${1:-setup}"
    
    case $action in
        setup)
            check_podman
            setup_env
            build_images
            start_services
            show_endpoints
            show_quick_commands
            ;;
        start)
            check_podman
            start_services
            show_endpoints
            ;;
        stop)
            print_header "Stopping Services"
            podman-compose -f docker-compose.yml down
            print_success "Services stopped"
            ;;
        rebuild)
            print_header "Rebuilding Images"
            podman-compose -f docker-compose.yml down -v
            build_images
            start_services
            show_endpoints
            ;;
        logs)
            podman-compose -f docker-compose.yml logs -f
            ;;
        *)
            echo "Usage: $0 {setup|start|stop|rebuild|logs}"
            echo ""
            echo "Commands:"
            echo "  setup    - Initial setup, build images, and start services"
            echo "  start    - Start existing services"
            echo "  stop     - Stop running services"
            echo "  rebuild  - Rebuild images from scratch"
            echo "  logs     - View live logs from all services"
            exit 1
            ;;
    esac
}

main "$@"
