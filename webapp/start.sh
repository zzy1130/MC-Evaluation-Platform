#!/bin/bash

# Invariant Subset Analyzer - Startup Script
# ===========================================

echo "🚀 Starting Invariant Subset Analyzer..."
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Get the directory where the script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to kill ALL processes on a specific port (with retry)
kill_port() {
    local port=$1
    local max_attempts=3
    local attempt=1
    
    while [ $attempt -le $max_attempts ]; do
        local pids=$(lsof -ti:$port 2>/dev/null | tr '\n' ' ')
        if [ -z "$pids" ]; then
            return 0
        fi
        
        echo -e "${YELLOW}⚠ Port $port is in use (PIDs: $pids), killing (attempt $attempt)...${NC}"
        for pid in $pids; do
            kill -9 $pid 2>/dev/null
        done
        sleep 1
        attempt=$((attempt + 1))
    done
    
    # Final check
    if lsof -ti:$port >/dev/null 2>&1; then
        echo -e "${RED}❌ Could not free port $port${NC}"
        return 1
    fi
    echo -e "${GREEN}✓ Port $port is now free${NC}"
}

# Check prerequisites
echo -e "${CYAN}🔍 Checking prerequisites...${NC}"

# Check Python
if ! command_exists python3; then
    echo -e "${RED}❌ Python3 is not installed. Please install Python 3.8+ first.${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Python3 found${NC}"

# Check npm (optional for frontend)
HAS_NPM=false
if command_exists npm; then
    HAS_NPM=true
    echo -e "${GREEN}✓ npm found${NC}"
else
    echo -e "${YELLOW}⚠ npm not found - will use standalone HTML version${NC}"
fi

echo ""

# Setup Python virtual environment
if [ ! -d "backend/venv" ]; then
    echo -e "${CYAN}📦 Creating Python virtual environment...${NC}"
    python3 -m venv backend/venv
    if [ $? -ne 0 ]; then
        echo -e "${RED}❌ Failed to create virtual environment${NC}"
        exit 1
    fi
fi

# Activate virtual environment
source backend/venv/bin/activate

# Install Python dependencies with SSL workaround
echo -e "${CYAN}📦 Installing Python dependencies...${NC}"
pip install --upgrade pip -q 2>/dev/null

# Try normal install first, if fails try with trusted hosts
pip install -q -r backend/requirements.txt 2>/dev/null
if [ $? -ne 0 ]; then
    echo -e "${YELLOW}⚠ Standard pip install failed, trying with trusted hosts...${NC}"
    pip install --trusted-host pypi.org --trusted-host pypi.python.org --trusted-host files.pythonhosted.org -r backend/requirements.txt
    if [ $? -ne 0 ]; then
        echo -e "${RED}❌ Failed to install Python dependencies${NC}"
        echo -e "${YELLOW}💡 Try running manually:${NC}"
        echo -e "   pip install flask flask-cors pyvis beautifulsoup4"
        exit 1
    fi
fi
echo -e "${GREEN}✓ Python dependencies installed${NC}"

# Kill any existing processes on required ports
echo ""
echo -e "${CYAN}🔌 Checking and clearing ports...${NC}"
kill_port 5001
kill_port 8080
kill_port 3000

# Double-check port 5001 is really free
sleep 1
if lsof -ti:5001 >/dev/null 2>&1; then
    echo -e "${YELLOW}⚠ Port 5001 still occupied, force killing all...${NC}"
    lsof -ti:5001 | xargs kill -9 2>/dev/null
    sleep 2
fi

# Start backend
echo ""
echo -e "${GREEN}🐍 Starting Flask backend on port 5001...${NC}"
cd backend
python app.py &
BACKEND_PID=$!
cd ..

# Wait for backend to start
sleep 2

# Check if backend started successfully
if ! kill -0 $BACKEND_PID 2>/dev/null; then
    echo -e "${RED}❌ Backend failed to start${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Backend started on port 5001 (PID: $BACKEND_PID)${NC}"

# Handle frontend
if [ "$HAS_NPM" = true ]; then
    # Setup and start React frontend
    if [ ! -d "frontend/node_modules" ]; then
        echo -e "${CYAN}📦 Installing Node.js dependencies...${NC}"
        cd frontend
        npm install
        cd ..
    fi
    
    echo -e "${GREEN}⚛️  Starting React frontend on port 3000...${NC}"
    cd frontend
    npm run dev &
    FRONTEND_PID=$!
    cd ..
    
    echo ""
    echo -e "${GREEN}✅ Application started!${NC}"
    echo ""
    echo -e "${BLUE}🌐 Open your browser at: ${CYAN}http://localhost:3000${NC}"
else
    # Use standalone HTML version
    echo ""
    echo -e "${GREEN}✅ Backend started!${NC}"
    echo ""
    echo -e "${BLUE}🌐 Open this file in your browser:${NC}"
    echo -e "${CYAN}   file://${SCRIPT_DIR}/index.html${NC}"
    echo ""
    echo -e "${YELLOW}Or use Python's built-in server:${NC}"
    python3 -m http.server 8080 &
    HTTP_PID=$!
    echo -e "${BLUE}🌐 Open your browser at: ${CYAN}http://localhost:8080${NC}"
fi

echo ""
echo -e "Press ${RED}Ctrl+C${NC} to stop all services"

# Trap Ctrl+C to cleanup
cleanup() {
    echo ""
    echo -e "${RED}🛑 Shutting down...${NC}"
    kill $BACKEND_PID 2>/dev/null
    [ -n "$FRONTEND_PID" ] && kill $FRONTEND_PID 2>/dev/null
    [ -n "$HTTP_PID" ] && kill $HTTP_PID 2>/dev/null
    deactivate 2>/dev/null
    exit 0
}

trap cleanup INT TERM

# Wait for processes
wait
