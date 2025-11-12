#!/bin/bash
# Run performance metrics tracking with Groq API

echo "🔍 Starting Performance Metrics Collection..."
echo "Using Groq API (llama-3.1-8b-instant)"
echo ""

cd "$(dirname "$0")/.."

# Activate conda environment
source ~/.zshrc
conda activate hp_rag_voice

# Set Groq API key from environment variable
# Make sure to set GROQ_API_KEY in your environment before running this script
export GROQ_API_KEY=${GROQ_API_KEY:-""}

# Run the performance tracker
python metrics/performance_tracker.py

echo ""
echo "✅ Metrics collection complete! Check the metrics/ folder for results."

