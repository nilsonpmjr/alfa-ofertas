#!/bin/bash
# Stop all Alfa Ofertas services

echo "🛑 Stopping Alfa Ofertas Services..."
echo "========================================"

# Kill by process name
echo "Killing processes by name..."
pkill -9 -f "whatsapp-service/index.js" 2>/dev/null
pkill -9 -f "node index.js" 2>/dev/null
pkill -9 -f "src.main" 2>/dev/null
pkill -9 -f "chromium.*alfa-ofertas" 2>/dev/null
pkill -9 -f "chrome.*alfa-ofertas" 2>/dev/null

# Kill by port
echo "Killing processes on ports 3000, 3001..."
lsof -ti:3000 | xargs kill -9 2>/dev/null
lsof -ti:3001 | xargs kill -9 2>/dev/null

sleep 2

# Verify
REMAINING=$(ps aux | grep -E "node index|src.main" | grep -v grep | wc -l)
if [ $REMAINING -eq 0 ]; then
    echo "✅ All services stopped successfully"
else
    echo "⚠️  Some processes may still be running:"
    ps aux | grep -E "node index|src.main" | grep -v grep
fi

echo "========================================"
