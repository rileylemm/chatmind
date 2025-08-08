#!/bin/bash

# ChatMind Database Management Script
# Manages Neo4j and Qdrant Docker containers (root-level compose)

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
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

# Function to check if Docker is running
check_docker() {
    if ! docker info > /dev/null 2>&1; then
        print_error "Docker is not running. Please start Docker and try again."
        exit 1
    fi
}

# Detect docker compose command
compose_cmd() {
    if command -v docker-compose >/dev/null 2>&1; then
        echo "docker-compose"
    else
        echo "docker compose"
    fi
}

# Function to show usage
show_usage() {
    echo "ChatMind Database Management Script"
    echo "=================================="
    echo ""
    echo "Usage: $0 [COMMAND]"
    echo ""
    echo "Commands:"
    echo "  start     - Start Neo4j and Qdrant"
    echo "  stop      - Stop Neo4j and Qdrant"
    echo "  restart   - Restart Neo4j and Qdrant"
    echo "  status    - Show status of services"
    echo "  logs      - Show logs (follow)"
    echo "  clean     - Stop and remove containers (data preserved)"
    echo "  reset     - Stop, remove containers and volumes (data lost)"
    echo "  backup    - Create backup of database volumes"
    echo "  restore   - Restore from backup (requires backup file)"
    echo "  health    - Check service health"
    echo ""
    echo "Examples:"
    echo "  $0 start"
    echo "  $0 status"
    echo "  $0 logs"
}

# Function to start databases
start_databases() {
    print_info "Starting ChatMind databases (root compose)..."
    cd "$REPO_ROOT"
    $(compose_cmd) up -d neo4j qdrant
    print_status "Databases started successfully!"
    print_info "Neo4j: http://localhost:7474"
    print_info "Qdrant: http://localhost:6335"
}

# Function to stop databases
stop_databases() {
    print_info "Stopping ChatMind databases..."
    cd "$REPO_ROOT"
    $(compose_cmd) stop neo4j qdrant
    print_status "Databases stopped successfully!"
}

# Function to restart databases
restart_databases() {
    print_info "Restarting ChatMind databases..."
    cd "$REPO_ROOT"
    $(compose_cmd) restart neo4j qdrant
    print_status "Databases restarted successfully!"
}

# Function to show status
show_status() {
    print_info "Database Status:"
    echo ""
    cd "$REPO_ROOT"
    $(compose_cmd) ps
    echo ""
    
    # Check if services are responding
    print_info "Health Checks:"
    
    # Check Neo4j
    if curl -s http://localhost:7474 > /dev/null 2>&1; then
        print_status "Neo4j is responding"
    else
        print_warning "Neo4j is not responding"
    fi
    
    # Check Qdrant
    if curl -s http://localhost:6335/collections > /dev/null 2>&1; then
        print_status "Qdrant is responding"
    else
        print_warning "Qdrant is not responding"
    fi
}

# Function to show logs
show_logs() {
    print_info "Database Logs:"
    cd "$REPO_ROOT"
    $(compose_cmd) logs -f neo4j qdrant
}

# Function to clean containers
clean_containers() {
    print_warning "This will stop and remove containers but preserve data volumes."
    read -p "Are you sure? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        cd "$REPO_ROOT"
        $(compose_cmd) rm -sf neo4j qdrant
        print_status "Containers cleaned successfully!"
    else
        print_info "Operation cancelled."
    fi
}

# Function to reset everything
reset_databases() {
    print_error "This will stop containers and REMOVE ALL DATA!"
    read -p "Are you absolutely sure? This cannot be undone! (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        cd "$REPO_ROOT"
        $(compose_cmd) down -v
        print_status "Databases reset successfully!"
        print_warning "All data has been removed."
    else
        print_info "Operation cancelled."
    fi
}

# Function to create backup
create_backup() {
    print_info "Creating database backup..."
    BACKUP_DIR="$REPO_ROOT/chatmind/pipeline/backups"
    BACKUP_FILE="chatmind_backup_$(date +%Y%m%d_%H%M%S).tar.gz"
    
    mkdir -p "$BACKUP_DIR"
    cd "$REPO_ROOT"
    
    # Create backup of volumes
    docker run --rm -v "$(pwd)":/backup -v neo4j_data:/neo4j_data -v qdrant_storage:/qdrant_storage alpine tar czf /backup/chatmind/pipeline/backups/"$BACKUP_FILE" neo4j_data qdrant_storage
    
    print_status "Backup created: $BACKUP_DIR/$BACKUP_FILE"
}

# Function to restore from backup
restore_backup() {
    if [ -z "$1" ]; then
        print_error "Please specify a backup file to restore from."
        echo "Usage: $0 restore <backup_file>"
        exit 1
    fi
    
    BACKUP_FILE="$1"
    if [ ! -f "$BACKUP_FILE" ]; then
        print_error "Backup file not found: $BACKUP_FILE"
        exit 1
    fi
    
    print_warning "This will overwrite existing data!"
    read -p "Are you sure? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        print_info "Restoring from backup: $BACKUP_FILE"
        cd "$REPO_ROOT"
        
        # Stop containers first
        $(compose_cmd) stop neo4j qdrant
        
        # Restore volumes
        docker run --rm -v "$(pwd)":/backup -v neo4j_data:/neo4j_data -v qdrant_storage:/qdrant_storage alpine sh -c "cd / && tar xzf /backup/$BACKUP_FILE"
        
        # Start containers
        $(compose_cmd) up -d neo4j qdrant
        
        print_status "Backup restored successfully!"
    else
        print_info "Operation cancelled."
    fi
}

# Function to check health
check_health() {
    print_info "Health Check Results:"
    echo ""
    
    # Check Neo4j health
    print_info "Neo4j Health:"
    if curl -s http://localhost:7474 > /dev/null 2>&1; then
        print_status "✅ Neo4j is healthy"
    else
        print_error "❌ Neo4j is not responding"
    fi
    
    # Check Qdrant health
    print_info "Qdrant Health:"
    if curl -s http://localhost:6335/health > /dev/null 2>&1; then
        print_status "✅ Qdrant is healthy"
    else
        print_error "❌ Qdrant is not responding"
    fi
    
    # Show container status
    echo ""
    print_info "Container Status:"
    cd "$REPO_ROOT"
    $(compose_cmd) ps
}

# Main script logic
main() {
    check_docker
    case "${1:-}" in
        start)
            start_databases
            ;;
        stop)
            stop_databases
            ;;
        restart)
            restart_databases
            ;;
        status)
            show_status
            ;;
        logs)
            show_logs
            ;;
        clean)
            clean_containers
            ;;
        reset)
            reset_databases
            ;;
        backup)
            create_backup
            ;;
        restore)
            restore_backup "$2"
            ;;
        health)
            check_health
            ;;
        *)
            show_usage
            exit 1
            ;;
    esac
}

# Run main function with all arguments
main "$@" 