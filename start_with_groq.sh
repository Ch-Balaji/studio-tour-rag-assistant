#!/bin/bash

# Start Voice Chat with Groq API (fast inference)

echo "🚀 Starting Voice Chat with Groq API..."
echo ""

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$SCRIPT_DIR"

# Get conda base
CONDA_BASE=$(conda info --base)

# Create logs directory if it doesn't exist
mkdir -p "$PROJECT_ROOT/logs"

# Start backend with Groq
echo "✅ Starting backend with Groq API..."
(
    source "$CONDA_BASE/etc/profile.d/conda.sh"
    conda activate hp_rag_voice
    cd "$PROJECT_ROOT"
    export LLM_PROVIDER=groq
    # Set your Groq API key here or in your environment
    export GROQ_API_KEY=${GROQ_API_KEY:-"your_groq_api_key_here"}
    python backend/run.py
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
    npm run dev
) &
FRONTEND_PID=$!
echo "Frontend PID: $FRONTEND_PID"
echo $FRONTEND_PID > "$PROJECT_ROOT/logs/frontend.pid"

sleep 5

echo ""
echo "🎉 Voice Chat Running!"
echo ""
echo "📱 Open: http://localhost:3000"
echo "⚡ Using: Groq API (ultra-fast responses!)"
echo ""
echo "🛑 To stop: Ctrl+C or run ./stop_voice_chat.sh"
echo ""

# Keep script running
wait

