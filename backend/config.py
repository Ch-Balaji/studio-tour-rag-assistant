"""
Backend configuration management
"""
import os
import yaml
from pathlib import Path
from typing import Any, Dict
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class Config:
    """Configuration class for backend"""
    
    def __init__(self):
        self.config_path = Path(__file__).parent.parent / "config" / "config.yaml"
        self.config_data = self._load_config()
        
        # API Configuration
        self.backend_port = int(os.getenv("BACKEND_PORT", "8000"))
        self.frontend_url = os.getenv("FRONTEND_URL", "http://localhost:3000")
        
        # Whisper model configuration
        self.whisper_model_size = os.getenv("WHISPER_MODEL_SIZE", "base")
        
        # LLM provider configuration
        self.llm_provider = os.getenv("LLM_PROVIDER", "ollama")  # 'ollama' or 'groq'
        self.groq_api_key = os.getenv("GROQ_API_KEY")
        
        # Paths
        self.project_root = Path(__file__).parent.parent
        self.chroma_db_path = self.project_root / "chroma_db"
        self.bm25_index_path = self.project_root / "bm25_index"
        
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from YAML file"""
        with open(self.config_path, 'r') as f:
            return yaml.safe_load(f)
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value"""
        keys = key.split('.')
        value = self.config_data
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
            else:
                return default
        return value if value is not None else default
    
    @property
    def vector_db_config(self) -> dict:
        """Get vector database configuration"""
        return self.config_data.get('vector_db', {})
    
    @property
    def embeddings_config(self) -> dict:
        """Get embeddings configuration"""
        return self.config_data.get('embeddings', {})
    
    @property
    def retrieval_config(self) -> dict:
        """Get retrieval configuration"""
        return self.config_data.get('retrieval', {})
    
    @property
    def llm_config(self) -> dict:
        """Get LLM configuration"""
        return self.config_data.get('llm', {})
    
    @property
    def memory_config(self) -> dict:
        """Get memory configuration"""
        return self.config_data.get('memory', {})


# Global config instance
config = Config()

