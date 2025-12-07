#!/bin/bash
# 
# Local Development Environment Manager for Linux/macOS
# 
# Make this script executable:
#   chmod +x scripts/run-local.sh
# 
# Run the script:
#   ./scripts/run-local.sh
#

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

cd "$(dirname "$0")/.."

# Create logs directory if it doesn't exist
mkdir -p logs

# Function to find an available port
find_available_port() {
    local start_port=$1
    local port=$start_port
    while [ $port -lt $((start_port + 100)) ]; do
        if ! netstat -tuln 2>/dev/null | grep -q ":$port " && ! lsof -i:$port >/dev/null 2>&1; then
            echo $port
            return
        fi
        port=$((port + 1))
    done
    echo $start_port
}

echo "========================================"
echo "Local Development Environment Manager"
echo "========================================"
echo ""

# Activate Python environment if it exists
if [ -f "/app/pyenv/bin/activate" ]; then
    echo "Activating Python environment..."
    source /app/pyenv/bin/activate
    echo -e "${GREEN}✓ Python environment activated${NC}"
elif [ -f "$HOME/pyenv/bin/activate" ]; then
    echo "Activating Python environment..."
    source $HOME/pyenv/bin/activate
    echo -e "${GREEN}✓ Python environment activated${NC}"
elif [ -f "venv/bin/activate" ]; then
    echo "Activating Python environment..."
    source venv/bin/activate
    echo -e "${GREEN}✓ Python environment activated${NC}"
else
    echo -e "${YELLOW}No Python virtual environment found at /app/pyenv, ~/pyenv, or venv${NC}"
    echo "Continuing with system Python..."
fi

# Set PYTHONPATH
export PYTHONPATH=.
echo "PYTHONPATH set to current directory"
echo ""

# Check if this is first-time setup
FIRST_TIME_SETUP=false
if [ ! -f "backend/.env" ] || [ ! -d "frontend/node_modules" ] || [ ! -f ".setup_done" ]; then
    FIRST_TIME_SETUP=true
fi

if [ "$FIRST_TIME_SETUP" = true ]; then
    echo "=========================================="
    echo "First-Time Setup Detection"
    echo "=========================================="
    echo ""
    echo "It appears this is the first time running the application."
    echo "Would you like to install dependencies?"
    echo ""
    read -p "Install Python requirements and Node modules? (y/n): " INSTALL_DEPS
    
    if [[ "$INSTALL_DEPS" =~ ^[Yy]$ ]]; then
        echo ""
        echo "Installing dependencies..."
        echo ""
        
        # Install Python requirements for backend
        if [ -f "backend/requirements.txt" ]; then
            echo "Installing Python requirements for backend..."
            pip install -r backend/requirements.txt
            if [ $? -eq 0 ]; then
                echo -e "${GREEN}✓ Backend requirements installed${NC}"
            else
                echo -e "${RED}✗ Failed to install backend requirements${NC}"
            fi
            echo ""
        fi
        
        # Install Python requirements for mock_alm
        if [ -f "mock_alm/requirements.txt" ]; then
            echo "Installing Python requirements for mock_alm..."
            pip install -r mock_alm/requirements.txt
            if [ $? -eq 0 ]; then
                echo -e "${GREEN}✓ Mock ALM requirements installed${NC}"
            else
                echo -e "${RED}✗ Failed to install mock_alm requirements${NC}"
            fi
            echo ""
        fi
        
        # Install Node modules for frontend
        if [ -f "frontend/package.json" ]; then
            echo "Installing Node modules for frontend..."
            cd frontend
            npm install
            if [ $? -eq 0 ]; then
                echo -e "${GREEN}✓ Frontend dependencies installed${NC}"
            else
                echo -e "${RED}✗ Failed to install frontend dependencies${NC}"
            fi
            cd ..
            echo ""
        fi
        
        # Mark setup as done
        touch .setup_done
        echo -e "${GREEN}✓ Initial setup completed!${NC}"
        echo ""
    else
        echo "Skipping dependency installation."
        echo "Note: You may need to install dependencies manually."
        echo ""
    fi
fi

# Step 1: Choose MongoDB connection
echo "Step 1: Choose MongoDB Connection"
echo "--------------------------------"
echo ""
echo "Which MongoDB do you want to connect to?"
echo ""
echo "1. Local MongoDB (workspace installation - localhost:27017)"
echo "2. Docker MongoDB (Docker container - localhost:27017)"
echo "3. MongoDB Atlas (cloud hosted)"
echo "4. Custom MongoDB connection string"
echo ""
read -p "Enter your choice (1-4): " MONGO_CHOICE

# Determine Python command early (before MongoDB operations)
if command -v python3 &> /dev/null; then
    PYTHON_CMD="python3"
elif [ -f "$HOME/pyenv/bin/python" ]; then
    PYTHON_CMD="$HOME/pyenv/bin/python"
elif command -v python &> /dev/null; then
    PYTHON_CMD="python"
else
    echo -e "${RED}Error: Python not found. Please install Python 3.${NC}"
    exit 1
fi

MONGO_URI=""
START_MONGO_LOCAL=0
case $MONGO_CHOICE in
    1)
        MONGO_URI="mongodb://localhost:27017/almdb"
        START_MONGO_LOCAL=1
        echo "Selected: Local MongoDB (workspace/mongodb)"
        echo "Note: Will attempt to start MongoDB if not running"
        ;;
    2)
        MONGO_URI="mongodb://localhost:27017/almdb"
        echo "Selected: Docker MongoDB (localhost:27017)"
        echo "Note: Make sure Docker MongoDB container is running"
        ;;
    3)
        read -p "Enter MongoDB Atlas connection string: " MONGO_URI
        echo "Selected: MongoDB Atlas - $MONGO_URI"
        ;;
    4)
        read -p "Enter custom MongoDB connection string: " MONGO_URI
        echo "Selected: Custom MongoDB - $MONGO_URI"
        ;;
    *)
        echo "Invalid choice. Defaulting to Local MongoDB."
        MONGO_URI="mongodb://localhost:27017/almdb"
        ;;
esac
echo ""

# Step 2: Show MongoDB status
echo "Step 2: MongoDB Status"
echo "----------------------"
echo ""

# Only check localhost MongoDB for options 1 and 2
if [ "$MONGO_CHOICE" = "1" ] || [ "$MONGO_CHOICE" = "2" ]; then
    echo "Checking if MongoDB is running on localhost:27017..."
    
    if timeout 2 bash -c "echo > /dev/tcp/localhost/27017" 2>/dev/null; then
        echo -e "${GREEN}✓ Connected to MongoDB successfully on localhost:27017${NC}"
        echo "Database: almdb"
    else
        echo -e "${YELLOW}MongoDB is not running on localhost:27017${NC}"
        
        if [ $START_MONGO_LOCAL -eq 1 ]; then
            echo "Attempting to start local MongoDB..."
            
            # Check if mongod exists in workspace
            if [ -f "mongodb/bin/mongod" ]; then
                echo "Starting MongoDB from workspace/mongodb..."
                mkdir -p mongodb_data
                mongodb/bin/mongod --dbpath mongodb_data --port 27017 --logpath logs/mongodb.log --fork
                sleep 3
                
                # Verify MongoDB started
                if timeout 2 bash -c "echo > /dev/tcp/localhost/27017" 2>/dev/null; then
                    echo -e "${GREEN}✓ MongoDB started successfully${NC}"
                else
                    echo -e "${RED}✗ Failed to start MongoDB${NC}"
                    echo "Please start MongoDB manually and try again."
                    exit 1
                fi
            elif command -v mongod &> /dev/null; then
                echo "Starting system MongoDB..."
                sudo systemctl start mongod || sudo service mongod start
                sleep 3
                
                # Verify MongoDB started
                if timeout 2 bash -c "echo > /dev/tcp/localhost/27017" 2>/dev/null; then
                    echo -e "${GREEN}✓ MongoDB started successfully${NC}"
                else
                    echo -e "${RED}✗ Failed to start MongoDB${NC}"
                    echo "Please start MongoDB manually and try again."
                    exit 1
            fi
        else
            echo -e "${RED}✗ MongoDB not found${NC}"
            echo "Please install MongoDB or start it manually."
            exit 1
        fi
    else
        echo "Please make sure MongoDB is running at $MONGO_URI"
        exit 1
    fi
    fi
else
    # For Atlas or Custom MongoDB (options 3 and 4), skip localhost check
    echo "Using remote MongoDB connection"
    echo "Connection: $MONGO_URI"
fi
echo ""

# Step 3: Ask to clean MongoDB
echo "Step 3: Clean MongoDB Database"
echo "-------------------------------"
echo ""
read -p "Do you want to clean the MongoDB database? (y/n): " CLEAN_CHOICE

if [[ "$CLEAN_CHOICE" =~ ^[Yy]$ ]]; then
    echo ""
    echo -e "${YELLOW}WARNING: This will delete ALL data from the almdb database!${NC}"
    read -p "Are you sure? Type YES to confirm: " CONFIRM
    
    if [ "$CONFIRM" = "YES" ]; then
        echo ""
        echo "Cleaning MongoDB database using Python..."
        $PYTHON_CMD -c "from pymongo import MongoClient; client = MongoClient('$MONGO_URI'); db = client.get_database(); [db.drop_collection(col) for col in db.list_collection_names()]; print('Database cleaned successfully.')"
        
        if [ $? -eq 0 ]; then
            echo -e "${GREEN}Database cleaned successfully!${NC}"
        else
            echo "Warning: Database cleaning may have failed. Continuing anyway..."
        fi
    else
        echo "Database cleaning cancelled."
    fi
else
    echo "Skipping database cleaning."
fi
echo ""

# Step 4: Update backend .env with all local URLs
echo "Step 4: Configure Backend"
echo "-------------------------"
echo ""
echo "Updating backend/.env with MongoDB connection and local URLs..."

if [ -f "backend/.env" ]; then
    # Update existing .env file
    sed -i "s|^MONGO_URI=.*|MONGO_URI=$MONGO_URI|" backend/.env
    sed -i "s|^ALM_URL=.*|ALM_URL=http://localhost:8001|" backend/.env
else
    # Create new .env file
    cat > backend/.env <<EOF
MONGO_URI=$MONGO_URI
ALM_URL=http://localhost:8001
USE_MOCK_ALM=true
CORS_ORIGINS=http://localhost:5173
SECRET_KEY=your-secret-key-change-in-production
EOF
fi
echo "Backend configuration updated."
echo ""

# Find available ports
echo "Finding available ports..."
MOCK_ALM_PORT=$(find_available_port 8001)
BACKEND_PORT=$(find_available_port 8000)
FRONTEND_PORT=$(find_available_port 5173)
echo "Ports assigned: Mock ALM=$MOCK_ALM_PORT, Backend=$BACKEND_PORT, Frontend=$FRONTEND_PORT"
echo ""

# Update backend .env with actual ports
sed -i "s|^ALM_URL=.*|ALM_URL=http://localhost:$MOCK_ALM_PORT|" backend/.env
sed -i "s|^CORS_ORIGINS=.*|CORS_ORIGINS=http://localhost:$FRONTEND_PORT|" backend/.env

# Initialize admin user in MongoDB
echo "Initializing admin user..."
cd backend
$PYTHON_CMD init_admin.py
if [ $? -ne 0 ]; then
    echo "Warning: Failed to initialize admin user"
fi
cd ..
echo ""

# Step 5: Start Mock ALM Server
echo "Step 5: Start Mock ALM Server"
echo "------------------------------"
echo ""
echo "Starting Mock ALM server on http://localhost:$MOCK_ALM_PORT..."
cd mock_alm
$PYTHON_CMD main.py --port $MOCK_ALM_PORT > ../logs/mock-alm.log 2>&1 &
MOCK_ALM_PID=$!
echo $MOCK_ALM_PID > ../logs/mock-alm.pid
cd ..
sleep 2
echo -e "${GREEN}Mock ALM server started (PID: $MOCK_ALM_PID)${NC}"
echo ""

# Step 6: Start Backend Server
echo "Step 6: Start Backend Server"
echo "-----------------------------"
echo ""
echo "Starting Backend server on http://localhost:$BACKEND_PORT..."
cd backend
$PYTHON_CMD -m uvicorn app.main:app --host 0.0.0.0 --port $BACKEND_PORT --reload > ../logs/backend.log 2>&1 &
BACKEND_PID=$!
echo $BACKEND_PID > ../logs/backend.pid
cd ..
sleep 3
echo -e "${GREEN}Backend server started (PID: $BACKEND_PID)${NC}"
echo ""

# Step 7: Start Frontend Server
echo "Step 7: Start Frontend Server"
echo "------------------------------"
echo ""
echo "Starting Frontend development server on http://localhost:$FRONTEND_PORT..."
cd frontend
PORT=$FRONTEND_PORT npm run dev > ../logs/frontend.log 2>&1 &
FRONTEND_PID=$!
echo $FRONTEND_PID > ../logs/frontend.pid
cd ..
sleep 2
echo -e "${GREEN}Frontend server started (PID: $FRONTEND_PID)${NC}"
echo ""

# Write startup info to startup.log
cat > logs/startup.log <<EOF
======================================
ReleaseCraft - Startup Information
======================================
Date: $(date)

Services Running:
- Mock ALM:  http://localhost:$MOCK_ALM_PORT (PID: $MOCK_ALM_PID)
- Backend:   http://localhost:$BACKEND_PORT (PID: $BACKEND_PID)
- Frontend:  http://localhost:$FRONTEND_PORT (PID: $FRONTEND_PID)
- MongoDB:   $MONGO_URI

API Documentation: http://localhost:$BACKEND_PORT/docs

Process IDs:
- Mock ALM PID: $MOCK_ALM_PID
- Backend PID:  $BACKEND_PID
- Frontend PID: $FRONTEND_PID

Logs:
- Mock ALM:  logs/mock-alm.log
- Backend:   logs/backend.log
- Frontend:  logs/frontend.log
- MongoDB:   logs/mongodb.log (if local)

To stop services: ./scripts/stop-all.sh
======================================
EOF

echo "========================================"
echo "All Services Started Successfully!"
echo "========================================"
echo ""
echo "Services running:"
echo "  - Mock ALM:  http://localhost:$MOCK_ALM_PORT"
echo "  - Backend:   http://localhost:$BACKEND_PORT (API Docs: /docs)"
echo "  - Frontend:  http://localhost:$FRONTEND_PORT"
echo "  - MongoDB:   $MONGO_URI"
echo ""
echo "Process IDs saved in logs/ directory"
echo "Logs available in logs/ directory"
echo "Startup info saved to logs/startup.log"
echo ""
echo "API Documentation: http://localhost:$BACKEND_PORT/docs"
echo ""
echo "To stop all services, run: ./scripts/stop-all.sh"
echo ""
echo "Press Enter to open the application in your browser..."
read

# Open browser
if command -v xdg-open &> /dev/null; then
    xdg-open http://localhost:$FRONTEND_PORT
elif command -v open &> /dev/null; then
    open http://localhost:$FRONTEND_PORT
else
    echo "Please open http://localhost:$FRONTEND_PORT in your browser"
fi

echo ""
echo "Application opened in browser."
echo "Services are running in the background."
echo ""
