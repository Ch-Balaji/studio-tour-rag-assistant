# GitHub Push Authentication Guide

Since you got a "could not read Username" error, here are your options:

## Option 1: Using Personal Access Token (Recommended)

1. Go to GitHub.com → Settings → Developer settings → Personal access tokens → Tokens (classic)
2. Click "Generate new token (classic)"
3. Give it a name like "FF918-push"
4. Select scopes: at minimum check `repo` (all sub-items)
5. Generate token and COPY IT (you won't see it again!)

Then push with:
```bash
cd /Users/bchippada/Documents/hackathon_new_project
git push https://<your-github-username>:<your-token>@github.com/WarnerBrosDiscovery/FF918.git main
```

## Option 2: Using GitHub CLI

```bash
# Install GitHub CLI
brew install gh

# Authenticate
gh auth login

# Push
git push -u origin main
```

## Option 3: Using SSH

```bash
# Change remote to SSH
git remote set-url origin git@github.com:WarnerBrosDiscovery/FF918.git

# Generate SSH key if you don't have one
ssh-keygen -t ed25519 -C "balaji.chippada@wbd.com"

# Add to GitHub: Settings → SSH and GPG keys → New SSH key
# Copy your public key:
cat ~/.ssh/id_ed25519.pub

# Then push
git push -u origin main
```

## Option 4: Configure Git Credentials

```bash
# Set username
git config --global user.name "your-github-username"

# Use credential helper
git config --global credential.helper osxkeychain

# Then push (it will prompt for username/password)
git push -u origin main




```

For the password, use your Personal Access Token, NOT your GitHub password!

---

# How to Clone and Run the RAG Voice Chat System

## Overview
This is a comprehensive RAG (Retrieval Augmented Generation) chatbot with voice capabilities. It features:
- 🎙️ Voice input/output with real-time transcription
- 💬 Interactive chat interface with streaming responses
- 📚 Advanced RAG pipeline with hybrid search
- 🔊 Multiple voice options for text-to-speech
- 🌐 Local LLM support via Ollama

## Prerequisites

Before starting, ensure you have:
- Python 3.9+ installed
- Node.js 16+ and npm installed
- Git installed
- At least 8GB of RAM
- ~10GB free disk space (for models)
- (Optional) GPU for faster processing

## Step-by-Step Installation Guide

### 1. Clone the Repository

```bash
# Clone the repository
git clone https://github.com/WarnerBrosDiscovery/FF918.git
cd FF918
```

### 2. Set Up Python Environment

You have several options for setting up the Python environment:

#### Option A: Using Conda (Recommended)
```bash
# Create conda environment from the provided file
conda env create -f environment.yml

# Activate the environment
conda activate hp_rag_voice
```

#### Option B: Using Python venv
```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On macOS/Linux:
source venv/bin/activate
# On Windows:
venv\Scripts\activate

# Install requirements
pip install -r requirements.txt
```

#### Option C: CPU-only Installation (if no GPU)
```bash
# Install CPU-only versions
pip install -r requirements-cpu.txt --index-url https://download.pytorch.org/whl/cpu
```

### 3. Install System Dependencies

#### FFmpeg (Required for audio processing)
```bash
# macOS
brew install ffmpeg

# Ubuntu/Debian
sudo apt-get update && sudo apt-get install ffmpeg

# Windows
# Download from https://ffmpeg.org/download.html and add to PATH
```

### 4. Install and Configure LLM Provider

#### Ollama (Local LLM - Recommended for privacy)
```bash
# Install Ollama
# macOS
brew install ollama

# Linux
curl https://ollama.ai/install.sh | sh

# Start Ollama service
ollama serve

# In a new terminal, download required models
ollama pull llama3.1 # Alternative model
```


### 5. Set Up the Frontend

```bash
# Navigate to frontend directory
cd frontend

# Install Node dependencies
npm install

# Return to project root
cd ..
```

### 6. Ingest the Data

The project includes PDF documents that need to be processed:

```bash
# Run the data ingestion script with recursive chunking strategy
python scripts/ingest_data.py --data-dir data/pdfs --chunking-strategy recursive

# This will:
# - Process all PDF documents in data/pdfs/ directory
# - Use recursive chunking strategy for better document segmentation
# - Create vector embeddings
# - Store in ChromaDB
# - Generate BM25 index
```

### 7. Run the Application

#### Using Ollama (Local)
```bash
# Make the script executable
chmod +x start_with_ollama.sh

# Run the application
./start_with_ollama.sh
```


### 8. Access the Application

Once running, access the application at:
- **Frontend (Voice Chat)**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs

## Configuration

### Modify Settings
Edit `config/config.yaml` to customize:
- LLM provider and model
- Embedding models
- Chunking strategies
- Retrieval parameters
- Voice settings

### Environment Variables
Create a `.env` file if needed:
```bash
OLLAMA_BASE_URL=http://localhost:11434
```

## Features Usage

### Voice Chat
1. Click the microphone button to start recording
2. Speak your question
3. Click stop to send the message
4. Listen to the AI response

### Text Chat
- Type questions in the chat interface
- Supports markdown formatting
- Shows source citations

### Voice Selection
- Click settings to choose different voices
- Options include various accents and styles

## Troubleshooting

### Common Issues

1. **"Ollama not running" error**
   ```bash
   # Start Ollama service
   ollama serve
   ```

2. **Audio not working**
   ```bash
   # Check FFmpeg installation
   ffmpeg -version
   ```

3. **Models not downloading**
   ```bash
   # Manual model download
   cd ~/.cache/whisper
   wget https://openaipublic.azureedge.net/main/whisper/models/[model-file]
   ```

4. **Port already in use**
   ```bash
   # Kill existing processes
   ./stop_voice_chat.sh
   # Or manually:
   lsof -i :3000  # Find process using port
   kill -9 [PID]  # Kill the process
   ```

### Verify Installation

Run these commands to verify everything is set up:

```bash
# Check Python packages
python -c "import fastapi; import whisper; import chromadb; print('✅ Core packages OK')"

# Check Ollama (if using)
ollama list

# Check Node/npm
node --version
npm --version

# Check FFmpeg
ffmpeg -version
```

## Stop the Application

```bash
# Use the provided script
./stop_voice_chat.sh

# Or manually stop with Ctrl+C in the terminal
```

## Project Structure
```
FF918/
├── app/                 # Streamlit app (alternative UI)
├── backend/            # FastAPI backend with voice/RAG services
├── frontend/           # Next.js frontend with voice interface
├── data/              # PDF documents for RAG
├── scripts/           # Utility scripts for data processing
├── src/               # Core RAG implementation
├── config/            # Configuration files
└── metrics/           # Performance tracking tools
```

## Support

If you encounter issues:
1. Check the logs in `logs/` directory
2. Ensure all prerequisites are installed
3. Verify your Python and Node versions
4. Check that required ports (3000, 8000) are free

## Notes

- The first run will download several models (~2-5GB)
- Voice models are cached in `~/.cache/`
- The system works offline after initial setup (with Ollama)
- For production use, consider setting up proper authentication
