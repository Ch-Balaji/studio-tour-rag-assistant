# Studio Tours AI Assistant - Voice-Enabled RAG System

## 🎬 Overview

An intelligent AI assistant designed to support **studio tours and visitor experiences** by providing instant, accurate answers about tour operations, facilities, production history, and interactive experiences. Built with 100% open-source models and local inference for complete data privacy.

### ✨ Key Features

- 🎙️ **Voice-First Interface** - Natural conversation with real-time speech-to-text
- 💬 **Streaming Responses** - Real-time answer generation with inline citations
- 🤖 **Intelligent Suggestions** - AI-generated follow-up questions based on context
- 📚 **Hybrid RAG Pipeline** - BM25 + vector search + cross-encoder reranking
- 🌍 **Multi-Language Support** - Ask questions in 90+ languages
- 🔒 **100% Local & Private** - All models run on your hardware, zero external APIs
- 📖 **Comprehensive Knowledge Base** - Studio tour guides, FAQs, production history, and facilities

### 🎯 Use Cases

- **Tour Guides**: Quick answers during tours
- **Visitor Services**: Instant FAQ responses
- **Training**: New staff onboarding with interactive Q&A
- **Operations**: Access production history and technical specifications
- **Multi-lingual Support**: Serve international visitors in their language

## Prerequisites

Before starting, ensure you have:
- **Python 3.9+** installed
- **Poetry** for dependency management ([Install Poetry](https://python-poetry.org/docs/#installation))
- **Node.js 18+** and npm installed
- **Git** installed
- **Ollama** for local LLM inference ([Install Ollama](https://ollama.ai))
- At least **8GB of RAM**
- ~10GB free disk space (for models and vector database)
- (Optional) GPU for faster inference

## Step-by-Step Installation Guide

### 1. Clone the Repository

```bash
# Clone the repository
git clone https://github.com/Ch-Balaji/studio-tour-rag-assistant.git
cd studio-tour-rag-assistant
```

### 2. Set Up Python Environment with Poetry

```bash
# Install dependencies using Poetry
poetry install

# This will:
# - Create a virtual environment automatically
# - Install all required packages from pyproject.toml
# - Set up the project in development mode

# Activate the virtual environment (optional, Poetry handles this)
poetry shell
```

**Note**: Poetry automatically manages your virtual environment. All subsequent commands should be run with `poetry run` prefix, or inside `poetry shell`.

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

### 4. Install and Configure Ollama (Local LLM)

Ollama provides completely local LLM inference - no data leaves your machine.

```bash
# Install Ollama
# macOS
brew install ollama

# Linux
curl https://ollama.ai/install.sh | sh

# Windows - Download from https://ollama.ai

# Start Ollama service (keep this running in a terminal)
ollama serve

# In a new terminal, download the Llama 3.1 model (~4GB)
ollama pull llama3.1
```

**Verify Ollama is running:**
```bash
ollama list  # Should show llama3.1
curl http://localhost:11434  # Should return "Ollama is running"
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

### 6. Ingest the Studio Tour Knowledge Base

The project includes comprehensive PDF documents about Warner Bros Studio Tours:

```bash
# Run the data ingestion script with recursive chunking strategy
poetry run python scripts/ingest_data.py --data-dir data/pdfs --chunking-strategy recursive

# This will:
# - Process all studio tour PDF documents in data/pdfs/ directory
# - Extract information about tours, facilities, production history, and FAQs
# - Use recursive chunking for better document segmentation
# - Generate embeddings using sentence-transformers (local)
# - Store vectors in ChromaDB for semantic search
# - Build BM25 index for keyword search (hybrid retrieval)
```

**Included Knowledge Base (Sample Data):**
- Comprehensive Tour Guides and FAQs
- Studio Facilities and Technical Specifications
- Production History Database
- Interactive Experiences Guide
- Backlot Environments Details
- Special Effects and Production Techniques

> **Note:** The included PDFs contain sample/generated data for demonstration purposes.

### 7. Run the Application

Start both backend and frontend services with a single command:

```bash
# Make the script executable
chmod +x start_with_ollama.sh

# Run the application (starts backend + frontend)
./start_with_ollama.sh
```

The script will:
1. Start the FastAPI backend on port 8000
2. Start the Next.js frontend on port 3000
3. Connect to your local Ollama instance
4. Display logs in real-time

### 8. Access the Application

Once running, you can access:
- **🎙️ Voice Chat Interface**: http://localhost:3000
- **📚 Backend API**: http://localhost:8000
- **📖 API Documentation**: http://localhost:8000/docs (Interactive Swagger UI)

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

## 🎯 How to Use the AI Assistant

### 🎙️ Voice Interaction (Recommended)

1. **Click the microphone button** to start recording
2. **Speak your question** naturally (e.g., "What are the safety requirements for studio tours?")
3. **Click stop** to process your voice
4. **Watch the AI**:
   - Transcribes your speech using local Whisper
   - Searches the knowledge base with hybrid retrieval
   - Streams the answer in real-time with citations
5. **Click suggested questions** for instant follow-up answers

### 💬 Text Chat

- Type questions directly in the chat interface
- Press Enter to send (Shift+Enter for new line)
- View source citations for each answer
- Copy and reference specific responses

### 🤖 Intelligent Suggested Questions

After each answer, the AI generates 3 contextually relevant follow-up questions:
- **One-tap interaction** - Click any suggested question to get instant answers
- **Contextually aware** - Questions are based on the current conversation
- **Exploration mode** - Discover related topics you didn't know to ask about

### 🌍 Multi-Language Support

Ask questions in your preferred language:
- English, Spanish, French, German, Italian
- Mandarin, Japanese, Korean, Arabic, Portuguese
- And 80+ more languages supported by Whisper

### ⚙️ Settings Panel

- Adjust retrieval parameters (top-k, similarity threshold)
- Toggle hybrid search (semantic + keyword)
- Enable/disable query enhancement
- Customize citation style

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
# Check Python packages (use poetry run if not in poetry shell)
poetry run python -c "import fastapi; import whisper; import chromadb; print('✅ Core packages OK')"

# Check Ollama
ollama list  # Should show llama3.1

# Check Node/npm
node --version  # Should be 18+
npm --version

# Check FFmpeg
ffmpeg -version

# Check if ports are available
lsof -i :3000  # Should be empty
lsof -i :8000  # Should be empty
```

## Stop the Application

```bash
# Use the provided script
./stop_voice_chat.sh

# Or manually stop with Ctrl+C in the terminal
```

## 💡 Example Questions to Try

### Tour Operations
- "What are the safety requirements for studio tours?"
- "How long does the standard studio tour last?"
- "What age restrictions apply to studio tours?"
- "Can I book a private or VIP tour experience?"

### Facilities & Productions
- "What special effects technologies are used in productions?"
- "Tell me about the backlot environments available"
- "What are the technical specifications of the sound stages?"
- "How does the green screen technology work?"

### Visitor Information
- "What accessibility accommodations are available?"
- "Are photography and videography allowed during tours?"
- "What interactive experiences can visitors participate in?"
- "Where can I find gift shops and dining options?"

### Production History
- "What famous movies were filmed at this studio?"
- "Tell me about the history of Warner Bros productions"
- "What production techniques have evolved over the years?"

### Multi-Language Examples
- **Spanish**: "¿Cuáles son los requisitos de seguridad para los tours del estudio?"
- **French**: "Quelles sont les installations disponibles pour les productions?"
- **Mandarin**: "工作室导览需要多长时间？"

## 🏗️ Project Structure
```
studio-tour-rag-assistant/
├── backend/                    # FastAPI backend
│   ├── main.py                # API endpoints and WebSocket handlers
│   ├── config.py              # Configuration management
│   ├── services/              # Business logic services
│   │   ├── rag_service.py    # RAG orchestration
│   │   └── transcription_service.py  # Whisper integration
│   └── models/                # Pydantic schemas
│
├── frontend/                  # Next.js React application
│   ├── src/
│   │   ├── components/       # UI components
│   │   │   ├── ChatInterface.tsx      # Main chat UI
│   │   │   ├── VoiceRecorder.tsx      # Voice input
│   │   │   ├── MessageBubble.tsx      # Chat messages
│   │   │   └── SettingsPanel.tsx      # Configuration UI
│   │   ├── hooks/            # React hooks
│   │   ├── services/         # API clients
│   │   └── types/            # TypeScript types
│   └── package.json          # Node dependencies
│
├── src/                       # Core RAG engine
│   ├── embeddings/           # Sentence transformer embeddings
│   ├── vector_store/         # ChromaDB integration
│   ├── retrieval/            # Hybrid search (BM25 + semantic)
│   ├── llm/                  # LLM clients (Ollama)
│   ├── chunking/             # Document chunking strategies
│   ├── chat/                 # Conversation memory
│   └── query/                # Query enhancement
│
├── data/                     # Studio tour knowledge base
│   └── pdfs/                 # Source documents
│
├── config/                   # Configuration files
│   └── config.yaml          # Main configuration
│
├── scripts/                  # Utility scripts
│   └── ingest_data.py       # Data ingestion pipeline
│
├── chroma_db/               # Vector database (generated)
├── bm25_index/              # BM25 index (generated)
├── logs/                    # Application logs
├── pyproject.toml           # Poetry dependencies
└── start_with_ollama.sh     # Startup script
```

## 🔧 Technology Stack

### 100% Open-Source Components

**Backend:**
- **FastAPI** - Modern Python web framework with async support
- **Poetry** - Dependency management and packaging
- **OpenAI Whisper** - Local speech-to-text (90+ languages)
- **ChromaDB** - Vector database for semantic search
- **Sentence Transformers** - Local embedding generation
- **Rank-BM25** - Keyword-based retrieval
- **Cross-Encoder** - Result reranking

**Frontend:**
- **Next.js 14** - React framework with App Router
- **TypeScript** - Type-safe development
- **Tailwind CSS** - Utility-first styling
- **Framer Motion** - Smooth animations
- **WebSocket** - Real-time streaming communication

**AI Models (All Local):**
- **Llama 3.1** (via Ollama) - 8B parameter LLM
- **all-MiniLM-L6-v2** - Embedding model (384 dimensions)
- **ms-marco-MiniLM-L-6-v2** - Cross-encoder for reranking
- **Whisper Base** - Speech recognition model

**No External APIs Required** - Everything runs on your hardware!

## 🎓 Key Technical Features

### Hybrid RAG Architecture
- **Semantic Search**: Vector embeddings for meaning-based retrieval
- **Keyword Search**: BM25 for exact term matching  
- **Reciprocal Rank Fusion**: Combines both search methods
- **Cross-Encoder Reranking**: Refines results for accuracy

### Conversation Intelligence
- **Context Memory**: Maintains conversation history (last 5 turns)
- **Query Enhancement**: Expands queries with context
- **Suggested Questions**: AI-generated follow-ups based on retrieved context
- **Citation Tracking**: Every answer links to source documents

### Voice Processing
- **Real-time Transcription**: Local Whisper processing
- **Multi-language**: 90+ languages automatically detected
- **Waveform Visualization**: Visual feedback during recording
- **Error Handling**: Graceful fallbacks for audio issues

## 📊 Performance

- **Response Time**: < 3 seconds for typical queries
- **Concurrent Users**: Supports multiple WebSocket connections
- **Knowledge Base**: 2000+ document chunks indexed
- **Accuracy**: High relevance through hybrid search + reranking

## Support

If you encounter issues:
1. Check the `logs/` directory for detailed error messages
2. Verify Ollama is running: `ollama list`
3. Ensure ports 3000 and 8000 are available
4. Check Poetry environment: `poetry env info`
5. Review configuration in `config/config.yaml`

## 📝 Notes

- **First run** will download models (~5-7GB total):
  - Whisper base model (~140MB)
  - Llama 3.1 model (~4GB)
  - Sentence transformer models (~80MB)
  - Cross-encoder model (~80MB)
- **Models are cached** in `~/.cache/` and `~/.ollama/`
- **Fully offline** after initial setup - no internet required
- **Privacy-first** - All processing happens on your machine
- **Extensible** - Easy to add new documents to knowledge base