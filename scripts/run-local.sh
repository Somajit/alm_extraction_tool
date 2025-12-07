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

echo "========================================"
echo "Local Development Environment Manager"
echo "========================================"
echo ""

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
        MONGO_URI="mongodb://localhost:27017/releasecraftdb"
        START_MONGO_LOCAL=1
        echo "Selected: Local MongoDB (workspace/mongodb)"
        echo "Note: Will attempt to start MongoDB if not running"
        ;;
    2)
        MONGO_URI="mongodb://localhost:27017/releasecraftdb"
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
        MONGO_URI="mongodb://localhost:27017/releasecraftdb"
        ;;
esac
echo ""

# Step 2: Show MongoDB status
echo "Step 2: MongoDB Status"
echo "----------------------"
echo ""
echo "Checking if MongoDB is running..."

if timeout 2 bash -c "echo > /dev/tcp/localhost/27017" 2>/dev/null; then
    echo -e "${GREEN}✓ Connected to MongoDB successfully on localhost:27017${NC}"
    echo "Database: releasecraftdb"
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
echo ""

# Step 3: Ask to clean MongoDB
echo "Step 3: Clean MongoDB Database"
echo "-------------------------------"
echo ""
read -p "Do you want to clean the MongoDB database? (y/n): " CLEAN_CHOICE

if [[ "$CLEAN_CHOICE" =~ ^[Yy]$ ]]; then
    echo ""
    echo -e "${YELLOW}WARNING: This will delete ALL data from the releasecraftdb database!${NC}"
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
    sed -i "s|^MOCK_ALM_URL=.*|MOCK_ALM_URL=http://localhost:8001|" backend/.env
    
    # Add MOCK_ALM_URL if it doesn't exist
    if ! grep -q "^MOCK_ALM_URL=" backend/.env; then
        echo "MOCK_ALM_URL=http://localhost:8001" >> backend/.env
    fi
else
    # Create new .env file
    cat > backend/.env <<EOF
MONGO_URI=$MONGO_URI
ALM_URL=http://localhost:8001
MOCK_ALM_URL=http://localhost:8001
USE_MOCK_ALM=true
CORS_ORIGINS=http://localhost:5173
SECRET_KEY=your-secret-key-change-in-production
EOF
fi
echo "Backend configuration updated."
echo ""

# Step 5: Start Mock ALM Server
echo "Step 5: Start Mock ALM Server"
echo "------------------------------"
echo ""
echo "Starting Mock ALM server on http://localhost:8001..."
cd mock_alm
$PYTHON_CMD main.py > ../logs/mock-alm.log 2>&1 &
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
echo "Starting Backend server on http://localhost:8000..."
cd backend
$PYTHON_CMD -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload > ../logs/backend.log 2>&1 &
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
echo "Starting Frontend development server on http://localhost:5173..."
cd frontend
npm run dev > ../logs/frontend.log 2>&1 &
FRONTEND_PID=$!
echo $FRONTEND_PID > ../logs/frontend.pid
cd ..
sleep 2
echo -e "${GREEN}Frontend server started (PID: $FRONTEND_PID)${NC}"
echo ""

echo "========================================"
echo "All Services Started Successfully!"
echo "========================================"
echo ""
echo "Services running:"
echo "  - Mock ALM:  http://localhost:8001"
echo "  - Backend:   http://localhost:8000 (API Docs: /docs)"
echo "  - Frontend:  http://localhost:5173"
echo "  - MongoDB:   $MONGO_URI"
echo ""
echo "Process IDs saved in logs/ directory"
echo "Logs available in logs/ directory"
echo ""
echo "API Documentation: http://localhost:8000/docs"
echo ""
echo "To stop all services, run: ./scripts/stop-all.sh"
echo ""
echo "Press Enter to open the application in your browser..."
read

# Open browser
if command -v xdg-open &> /dev/null; then
    xdg-open http://localhost:5173
elif command -v open &> /dev/null; then
    open http://localhost:5173
else
    echo "Please open http://localhost:5173 in your browser"
fi

echo ""
echo "Application opened in browser."
echo "Services are running in the background."
echo ""
