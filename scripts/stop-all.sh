#!/bin/bash

cd "$(dirname "$0")/.."

echo "Stopping all services..."

# Create logs directory if it doesn't exist
mkdir -p logs

# Stop Frontend
if [ -f logs/frontend.pid ]; then
    FRONTEND_PID=$(cat logs/frontend.pid)
    if ps -p $FRONTEND_PID > /dev/null 2>&1; then
        kill $FRONTEND_PID
        echo "✓ Frontend server stopped (PID: $FRONTEND_PID)"
    fi
    rm logs/frontend.pid
fi

# Stop Backend
if [ -f logs/backend.pid ]; then
    BACKEND_PID=$(cat logs/backend.pid)
    if ps -p $BACKEND_PID > /dev/null 2>&1; then
        kill $BACKEND_PID
        echo "✓ Backend server stopped (PID: $BACKEND_PID)"
    fi
    rm logs/backend.pid
fi

# Stop Mock ALM
if [ -f logs/mock-alm.pid ]; then
    MOCK_ALM_PID=$(cat logs/mock-alm.pid)
    if ps -p $MOCK_ALM_PID > /dev/null 2>&1; then
        kill $MOCK_ALM_PID
        echo "✓ Mock ALM server stopped (PID: $MOCK_ALM_PID)"
    fi
    rm logs/mock-alm.pid
fi

# Kill any remaining processes on the ports
lsof -ti:8001 | xargs kill -9 2>/dev/null
lsof -ti:8000 | xargs kill -9 2>/dev/null
lsof -ti:5173 | xargs kill -9 2>/dev/null

echo ""
echo "All services stopped."
