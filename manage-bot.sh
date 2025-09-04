#!/bin/bash
# 🤖 Twitter Bot Management Script
# Comprehensive start/stop script with nohup background processes
# Usage: ./manage-bot.sh [start|stop|restart|status|logs]

set -e

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="/home/ubuntu/audiopod-apps/tweety"
LOGS_DIR="$PROJECT_DIR/logs"
PID_DIR="$PROJECT_DIR/pids"

# Service definitions
declare -A SERVICES=(
    ["oauth"]="OAuth Server"
    ["email"]="Email Pipeline"
    ["twitter"]="Twitter Bot"
    ["full"]="Full Automation (Email + Twitter)"
)

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Helper functions
log() {
    echo -e "${GREEN}[$(date '+%Y-%m-%d %H:%M:%S')]${NC} $1"
}

warn() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

# Initialize directories
init_dirs() {
    mkdir -p "$LOGS_DIR" "$PID_DIR"
    cd "$PROJECT_DIR"
}

# Environment setup
setup_environment() {
    log "Setting up environment..."
    
    # Add Poetry to PATH
    export PATH="/home/ubuntu/.local/bin:$PATH"
    
    # Set Python path
    export PYTHONPATH="$PROJECT_DIR"
    
    # Activate conda if available
    if [ -f "/home/ubuntu/miniconda3/etc/profile.d/conda.sh" ]; then
        source /home/ubuntu/miniconda3/etc/profile.d/conda.sh
        conda activate base
        info "Conda environment activated"
    fi
    
    # Load environment variables
    if [ -f "$PROJECT_DIR/production.env" ]; then
        set -o allexport
        source "$PROJECT_DIR/production.env"
        set +o allexport
        info "Production environment loaded"
    elif [ -f "$PROJECT_DIR/.env" ]; then
        set -o allexport
        source "$PROJECT_DIR/.env"
        set +o allexport
        info "Development environment loaded"
    else
        warn "No environment file found"
    fi
    
    # Set production environment
    export ENVIRONMENT=production
}

# Check if service is running
is_running() {
    local service=$1
    local pid_file="$PID_DIR/${service}.pid"
    
    if [ -f "$pid_file" ]; then
        local pid=$(cat "$pid_file")
        if kill -0 "$pid" 2>/dev/null; then
            return 0
        else
            # Remove stale PID file
            rm -f "$pid_file"
            return 1
        fi
    fi
    return 1
}

# Kill process and cleanup
kill_service() {
    local service=$1
    local pid_file="$PID_DIR/${service}.pid"
    
    if [ -f "$pid_file" ]; then
        local pid=$(cat "$pid_file")
        if kill -0 "$pid" 2>/dev/null; then
            log "Stopping $service (PID: $pid)..."
            kill -TERM "$pid" 2>/dev/null || true
            
            # Wait for graceful shutdown
            for i in {1..10}; do
                if ! kill -0 "$pid" 2>/dev/null; then
                    break
                fi
                sleep 1
            done
            
            # Force kill if still running
            if kill -0 "$pid" 2>/dev/null; then
                warn "Force killing $service..."
                kill -KILL "$pid" 2>/dev/null || true
            fi
        fi
        rm -f "$pid_file"
    fi
}

# Stop all existing processes
stop_all_processes() {
    log "Stopping all existing processes..."
    
    # Stop PID-tracked services
    for service in "${!SERVICES[@]}"; do
        if is_running "$service"; then
            kill_service "$service"
        fi
    done
    
    # Kill any remaining related processes
    pkill -f "python.*background.scheduler" 2>/dev/null || true
    pkill -f "python.*oauth_server" 2>/dev/null || true
    pkill -f "email_pipeline" 2>/dev/null || true
    
    # Wait a bit for cleanup
    sleep 2
    
    log "All processes stopped"
}

# Start OAuth server
start_oauth() {
    local service="oauth"
    
    if is_running "$service"; then
        warn "OAuth server already running"
        return 0
    fi
    
    log "Starting OAuth server..."
    
    nohup poetry run python integrations/oauth_server.py \
        > "$LOGS_DIR/oauth_server.log" 2>&1 &
    
    echo $! > "$PID_DIR/${service}.pid"
    sleep 2
    
    if is_running "$service"; then
        log "✅ OAuth server started (PID: $(cat "$PID_DIR/${service}.pid"))"
    else
        error "❌ Failed to start OAuth server"
        return 1
    fi
}

# Start email pipeline only
start_email() {
    local service="email"
    
    if is_running "$service"; then
        warn "Email pipeline already running"
        return 0
    fi
    
    log "Starting email pipeline..."
    
    nohup poetry run python -m background.scheduler --no-twitter \
        > "$LOGS_DIR/email_pipeline.log" 2>&1 &
    
    echo $! > "$PID_DIR/${service}.pid"
    sleep 3
    
    if is_running "$service"; then
        log "✅ Email pipeline started (PID: $(cat "$PID_DIR/${service}.pid"))"
    else
        error "❌ Failed to start email pipeline"
        return 1
    fi
}

# Start Twitter bot only
start_twitter() {
    local service="twitter"
    
    if is_running "$service"; then
        warn "Twitter bot already running"
        return 0
    fi
    
    log "Starting Twitter bot..."
    
    nohup poetry run python -m background.scheduler --no-email \
        > "$LOGS_DIR/twitter_bot.log" 2>&1 &
    
    echo $! > "$PID_DIR/${service}.pid"
    sleep 3
    
    if is_running "$service"; then
        log "✅ Twitter bot started (PID: $(cat "$PID_DIR/${service}.pid"))"
    else
        error "❌ Failed to start Twitter bot"
        return 1
    fi
}

# Start full automation (email + Twitter)
start_full() {
    local service="full"
    
    if is_running "$service"; then
        warn "Full automation already running"
        return 0
    fi
    
    log "Starting full automation (Email + Twitter)..."
    
    nohup poetry run python -m background.scheduler \
        > "$LOGS_DIR/full_automation.log" 2>&1 &
    
    echo $! > "$PID_DIR/${service}.pid"
    sleep 3
    
    if is_running "$service"; then
        log "✅ Full automation started (PID: $(cat "$PID_DIR/${service}.pid"))"
    else
        error "❌ Failed to start full automation"
        return 1
    fi
}

# Start all services
start_all() {
    log "🚀 Starting Twitter Bot Platform..."
    
    init_dirs
    setup_environment
    stop_all_processes
    
    # Start OAuth server first
    start_oauth
    
    # Start full automation (email + Twitter)
    start_full
    
    log "🎉 All services started successfully!"
    show_status
}

# Show service status
show_status() {
    echo
    log "📊 Service Status:"
    echo "----------------------------------------"
    
    for service in "${!SERVICES[@]}"; do
        local name="${SERVICES[$service]}"
        if is_running "$service"; then
            local pid=$(cat "$PID_DIR/${service}.pid")
            echo -e "${GREEN}✅ $name${NC} - Running (PID: $pid)"
        else
            echo -e "${RED}❌ $name${NC} - Stopped"
        fi
    done
    echo
    
    # Show listening ports
    echo "🔗 Listening Services:"
    ss -tlnp 2>/dev/null | grep -E ":(8000|8080)" | while read line; do
        echo "  $line"
    done || echo "  No services detected on expected ports"
    echo
}

# Show logs
show_logs() {
    local service=${1:-"full"}
    local log_file="$LOGS_DIR/${service}_automation.log"
    
    if [ "$service" = "oauth" ]; then
        log_file="$LOGS_DIR/oauth_server.log"
    elif [ "$service" = "email" ]; then
        log_file="$LOGS_DIR/email_pipeline.log"
    elif [ "$service" = "twitter" ]; then
        log_file="$LOGS_DIR/twitter_bot.log"
    fi
    
    if [ -f "$log_file" ]; then
        log "📋 Showing logs for $service service..."
        tail -f "$log_file"
    else
        error "Log file not found: $log_file"
        echo "Available log files:"
        ls -la "$LOGS_DIR"/*.log 2>/dev/null || echo "No log files found"
    fi
}

# Validate configuration
validate_config() {
    log "🔍 Validating configuration..."
    
    # Check if required files exist
    local required_files=(
        "production.env"
        "core/config.py"
        "background/scheduler.py"
        "integrations/oauth_server.py"
    )
    
    for file in "${required_files[@]}"; do
        if [ ! -f "$PROJECT_DIR/$file" ]; then
            error "Required file missing: $file"
            return 1
        fi
    done
    
    # Test configuration loading
    if poetry run python -c "from core.config import get_config; c = get_config(); print('✅ Configuration valid')" 2>/dev/null; then
        log "✅ Configuration validation passed"
    else
        error "❌ Configuration validation failed"
        return 1
    fi
}

# Main command handler
case "${1:-start}" in
    start)
        validate_config
        start_all
        ;;
    stop)
        log "🛑 Stopping all services..."
        init_dirs
        stop_all_processes
        log "✅ All services stopped"
        ;;
    restart)
        log "🔄 Restarting services..."
        $0 stop
        sleep 3
        $0 start
        ;;
    status)
        init_dirs
        show_status
        ;;
    logs)
        show_logs "$2"
        ;;
    oauth)
        validate_config
        init_dirs
        setup_environment
        start_oauth
        ;;
    email)
        validate_config
        init_dirs
        setup_environment
        start_email
        ;;
    twitter)
        validate_config
        init_dirs
        setup_environment
        start_twitter
        ;;
    test)
        validate_config
        init_dirs
        setup_environment
        log "🧪 Running test email..."
        poetry run python -m background.scheduler --test
        ;;
    *)
        echo "🤖 Twitter Bot Management Script"
        echo
        echo "Usage: $0 [command]"
        echo
        echo "Commands:"
        echo "  start     - Start all services (OAuth + Full Automation)"
        echo "  stop      - Stop all services"
        echo "  restart   - Restart all services"
        echo "  status    - Show service status"
        echo "  logs [service] - Show logs (full, oauth, email, twitter)"
        echo "  oauth     - Start OAuth server only"
        echo "  email     - Start email pipeline only"
        echo "  twitter   - Start Twitter bot only"
        echo "  test      - Send test email"
        echo
        echo "Examples:"
        echo "  $0 start          # Start all services"
        echo "  $0 logs full      # Show full automation logs"
        echo "  $0 status         # Check service status"
        echo
        exit 1
        ;;
esac
