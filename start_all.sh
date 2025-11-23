#!/bin/bash
# Alfa Ofertas - Start All Services
# This script starts both the WhatsApp service and the Python bot

echo "🚀 Starting Alfa Ofertas Bot Services..."
echo "========================================"

# Get script directory
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$DIR"

# Kill any existing instances
echo "🧹 Cleaning up old processes..."
pkill -f "whatsapp-service/index.js" 2>/dev/null
pkill -f "src.main" 2>/dev/null
pkill -f "chromium.*alfa-ofertas" 2>/dev/null
pkill -f "chrome.*alfa-ofertas" 2>/dev/null
# Also kill by port to be sure
lsof -ti:3000 | xargs kill -9 2>/dev/null
lsof -ti:3001 | xargs kill -9 2>/dev/null
sleep 3

# Clear database for fresh start
echo "🗑️  Clearing deals database for fresh start..."
if [ -f "deals.db" ]; then
    mv deals.db "deals.db.backup.$(date +%Y%m%d_%H%M%S)" 2>/dev/null
    echo "   ✅ Old database backed up"
else
    echo "   ℹ️  No database to clear"
fi

# Start WhatsApp service in background
echo ""
echo "📱 Starting WhatsApp Service (port 3001)..."
cd whatsapp-service
node index.js > ../logs/whatsapp.log 2>&1 &
WHATSAPP_PID=$!
cd ..

# Wait for WhatsApp service to start
echo "⏳ Waiting for WhatsApp service to initialize..."
sleep 8

# Check if process is still running
if ! ps -p $WHATSAPP_PID > /dev/null; then
    echo "❌ WhatsApp service crashed on startup!"
    echo "Check logs: tail logs/whatsapp.log"
    exit 1
fi

# Try to ping the service
if curl -s -m 5 http://localhost:3001/send-deal -X POST -H "Content-Type: application/json" -d '{}' 2>&1 | grep -q "error\|Missing"; then
    echo "✅ WhatsApp service is responding (PID: $WHATSAPP_PID)"
else
    echo "⚠️  WhatsApp service may not be ready yet, but process is running"
fi

# Start Python bot
echo ""
echo "🤖 Starting Python Bot (port 3000)..."
./venv/bin/python3 -m src.main > logs/bot.log 2>&1 &
BOT_PID=$!

# Wait a moment
sleep 3

# Check if bot is running
if ps -p $BOT_PID > /dev/null; then
    echo "✅ Python bot is running (PID: $BOT_PID)"
else
    echo "❌ Python bot failed to start!"
    exit 1
fi

echo ""
echo "========================================"
echo "✅ All services started successfully!"
echo ""
echo "📊 Dashboard: http://localhost:3000"
echo "📱 WhatsApp Service: http://localhost:3001"
echo ""
echo "📝 Logs:"
echo "   - Bot: tail -f logs/bot.log"
echo "   - WhatsApp: tail -f logs/whatsapp.log"
echo ""
echo "🛑 To stop: pkill -f 'whatsapp-service' && pkill -f 'src/main.py'"
echo "========================================"
