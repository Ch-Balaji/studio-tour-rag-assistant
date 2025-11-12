"""
Audio transcription service using local open-source Whisper model
"""
import os
import base64
import tempfile
from pathlib import Path
from typing import Optional
import logging

try:
    import whisper
except ImportError:
    whisper = None

from pydub import AudioSegment

logger = logging.getLogger(__name__)


class TranscriptionService:
    """Service for transcribing audio using local Whisper model"""
    
    def __init__(self, model_size: str = "base"):
        """
        Initialize transcription service with local Whisper model
        
        Args:
            model_size: Whisper model size ('tiny', 'base', 'small', 'medium', 'large')
                       'base' is recommended for balanced speed and accuracy
        """
        if whisper is None:
            raise ImportError("whisper package is required. Install with: pip install openai-whisper")
        
        self.model_size = model_size
        logger.info(f"Loading Whisper model '{model_size}'... This may take a moment on first run.")
        self.model = whisper.load_model(model_size)
        logger.info(f"TranscriptionService initialized with local Whisper model '{model_size}'")
    
    def convert_webm_to_wav(self, webm_path: str, wav_path: str) -> None:
        """
        Convert WebM audio to WAV format
        
        Args:
            webm_path: Path to WebM file
            wav_path: Output path for WAV file
        """
        try:
            audio = AudioSegment.from_file(webm_path, format="webm")
            audio.export(wav_path, format="wav")
            logger.info(f"Converted {webm_path} to {wav_path}")
        except Exception as e:
            logger.error(f"Error converting audio: {e}")
            raise
    
    def transcribe_audio(self, audio_data: str, audio_format: str = "webm") -> str:
        """
        Transcribe audio data using local Whisper model
        
        Args:
            audio_data: Base64 encoded audio data
            audio_format: Audio format (webm, wav, mp3, etc.)
        
        Returns:
            Transcribed text
        """
        try:
            # Decode base64 audio
            audio_bytes = base64.b64decode(audio_data)
            
            # Create temporary files
            with tempfile.NamedTemporaryFile(suffix=f".{audio_format}", delete=False) as temp_input:
                temp_input.write(audio_bytes)
                temp_input_path = temp_input.name
            
            try:
                # Convert to WAV if necessary (Whisper works better with WAV)
                if audio_format.lower() == "webm":
                    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_wav:
                        temp_wav_path = temp_wav.name
                    
                    self.convert_webm_to_wav(temp_input_path, temp_wav_path)
                    audio_file_path = temp_wav_path
                else:
                    audio_file_path = temp_input_path
                
                # Transcribe using local Whisper model
                logger.info("Transcribing audio with local Whisper model...")
                result = self.model.transcribe(audio_file_path)
                transcript = result["text"].strip()
                
                logger.info(f"Transcribed audio: {transcript[:50]}...")
                return transcript
            
            finally:
                # Clean up temporary files
                if os.path.exists(temp_input_path):
                    os.unlink(temp_input_path)
                if audio_format.lower() == "webm" and os.path.exists(audio_file_path):
                    os.unlink(audio_file_path)
        
        except Exception as e:
            logger.error(f"Error transcribing audio: {e}")
            raise

