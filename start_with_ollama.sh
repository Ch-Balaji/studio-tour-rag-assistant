#!/bin/bash

# Start Voice Chat with local Ollama (private, no API needed)

echo "🚀 Starting Voice Chat with local Ollama..."
echo ""

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$SCRIPT_DIR"

# Set environment variables
export OLLAMA_BASE_URL="http://localhost:11434"

# Create logs directory if it doesn't exist
mkdir -p "$PROJECT_ROOT/logs"

# Start backend with Ollama
echo "✅ Starting backend with local Ollama..."
(
    cd "$PROJECT_ROOT"
    export LLM_PROVIDER=ollama
    export OLLAMA_BASE_URL="$OLLAMA_BASE_URL"
    poetry run python backend/run.py 2>&1 | tee logs/backend.log
) &
BACKEND_PID=$!
echo "Backend PID: $BACKEND_PID"
echo $BACKEND_PID > "$PROJECT_ROOT/logs/backend.pid"

sleep 12

# Start frontend
echo ""
echo "✅ Starting frontend..."
(
    cd "$PROJECT_ROOT/frontend"
    npm run dev 2>&1 | tee ../logs/frontend.log
) &
FRONTEND_PID=$!
echo "Frontend PID: $FRONTEND_PID"
echo $FRONTEND_PID > "$PROJECT_ROOT/logs/frontend.pid"

sleep 5

echo ""
echo "🎉 Voice Chat Running!"
echo ""
echo "📱 Open: http://localhost:3000"
echo "🏠 Using: Local Ollama (private, no API costs)"
echo ""
echo "⚠️  Make sure Ollama is running: ollama serve"
echo ""
echo "🛑 To stop: Ctrl+C or run ./stop_voice_chat.sh"
echo ""

# Keep script running
wait

