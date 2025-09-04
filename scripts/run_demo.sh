#!/bin/bash

# Tokenized Weather API Demo Runner
# This script starts all components needed for the demo

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo -e "${BLUE}🚀 Starting Tokenized Weather API Demo${NC}"
echo "Project root: $PROJECT_ROOT"

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

# Function to check if a process is running on a port
check_port() {
    local port=$1
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
        return 0  # Port is in use
    else
        return 1  # Port is free
    fi
}

# Function to wait for service to be ready
wait_for_service() {
    local url=$1
    local name=$2
    local max_attempts=30
    local attempt=1
    
    echo "Waiting for $name to be ready..."
    while [ $attempt -le $max_attempts ]; do
        if curl -s "$url" > /dev/null 2>&1; then
            print_status "$name is ready"
            return 0
        fi
        echo "  Attempt $attempt/$max_attempts..."
        sleep 2
        ((attempt++))
    done
    
    print_error "$name failed to start"
    return 1
}

# Check if LocalNet is running
echo "Checking Algorand LocalNet status..."
if ! algokit localnet status | grep -q "running"; then
    echo "Starting LocalNet..."
    algokit localnet start
    sleep 5
fi
print_status "LocalNet is running"

# Check if backend is already running
if check_port 8000; then
    print_warning "Backend already running on port 8000"
else
    echo "Starting backend server..."
    cd "$PROJECT_ROOT/backend"
    
    # Check if virtual environment exists
    if [ ! -d "venv" ]; then
        print_error "Backend virtual environment not found. Run setup_demo.py first."
        exit 1
    fi
    
    # Start backend in background
    ./venv/bin/python main.py > backend.log 2>&1 &
    BACKEND_PID=$!
    
    # Wait for backend to be ready
    if wait_for_service "http://localhost:8000/health" "Backend server"; then
        print_status "Backend server started (PID: $BACKEND_PID)"
        echo "Backend logs: $PROJECT_ROOT/backend/backend.log"
    else
        kill $BACKEND_PID 2>/dev/null || true
        exit 1
    fi
fi

# Function to cleanup on exit
cleanup() {
    echo -e "\n${YELLOW}Cleaning up...${NC}"
    if [ ! -z "$BACKEND_PID" ]; then
        kill $BACKEND_PID 2>/dev/null || true
        print_status "Backend server stopped"
    fi
}

# Set trap to cleanup on exit
trap cleanup EXIT

# Start the AI agent
echo -e "\n${BLUE}Starting AI Agent Demo${NC}"
cd "$PROJECT_ROOT/agent"

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    print_error "Agent virtual environment not found. Run setup_demo.py first."
    exit 1
fi

# Check if .env exists
if [ ! -f ".env" ]; then
    print_warning "Agent .env file not found. Using default configuration."
fi

echo -e "\n${BLUE}🤖 Running AI Agent${NC}"
echo "The agent will:"
echo "1. Try to get weather data (will be denied initially)"
echo "2. Automatically purchase access tokens"
echo "3. Retry and succeed with valid tokens"
echo "4. Display statistics"
echo -e "\n${YELLOW}Press Ctrl+C to stop the demo${NC}\n"

# Run the agent
./venv/bin/python agent.py

echo -e "\n${GREEN}🎉 Demo completed!${NC}"