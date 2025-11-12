# Installation Guide

## Requirements Files

This project includes several requirements files for different use cases:

### 1. `requirements.txt` (Main)
The primary requirements file with pinned versions for production use.
```bash
pip install -r requirements.txt
```

### 2. `requirements-minimal.txt`
Minimal requirements without version pinning for flexible installations.
```bash
pip install -r requirements-minimal.txt
```

### 3. `requirements-dev.txt`
Development dependencies including testing and code quality tools.
```bash
pip install -r requirements-dev.txt
```

### 4. `requirements-cpu.txt`
CPU-only version for systems without GPU/CUDA support.
```bash
pip install -r requirements-cpu.txt --index-url https://download.pytorch.org/whl/cpu
```

### 5. `requirements_voice.txt`
Original voice-specific requirements (kept for compatibility).

## Installation Methods

### Method 1: Using Conda (Recommended)
```bash
# Create conda environment from environment.yml
conda env create -f environment.yml

# Activate the environment
conda activate hp_rag_voice

# Install additional packages if needed
pip install -r requirements.txt
```

### Method 2: Using pip with Virtual Environment
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

### Method 3: CPU-only Installation
```bash
# For systems without GPU
pip install -r requirements-cpu.txt --index-url https://download.pytorch.org/whl/cpu
```

## Post-Installation

1. **Install Ollama** (if using local LLM):
   ```bash
   # macOS
   brew install ollama
   
   # Linux
   curl https://ollama.ai/install.sh | sh
   ```

2. **Download Ollama Models**:
   ```bash
   ollama pull llama2
   ollama pull mistral
   ```

3. **Install FFmpeg** (for audio processing):
   ```bash
   # macOS
   brew install ffmpeg
   
   # Ubuntu/Debian
   sudo apt-get install ffmpeg
   
   # Windows
   # Download from https://ffmpeg.org/download.html
   ```

## Troubleshooting

### Common Issues

1. **PyTorch Installation Issues**:
   - For GPU support: Visit https://pytorch.org/get-started/locally/
   - For CPU-only: Use requirements-cpu.txt

2. **Whisper Model Download**:
   - Models download automatically on first use
   - Requires internet connection
   - Default location: ~/.cache/whisper/

3. **TTS Model Issues**:
   - Models download on first use (~2GB)
   - Ensure sufficient disk space
   - Default location: ~/Library/Application Support/tts/ (macOS)

4. **ChromaDB Conflicts**:
   ```bash
   # If you encounter sqlite3 issues
   pip install pysqlite3-binary
   ```

## Verifying Installation

Run these commands to verify your installation:

```bash
# Check Python packages
python -c "import fastapi; print('FastAPI OK')"
python -c "import whisper; print('Whisper OK')"
python -c "import chromadb; print('ChromaDB OK')"
python -c "import langchain; print('LangChain OK')"

# Check Ollama
ollama list

# Check FFmpeg
ffmpeg -version
```
