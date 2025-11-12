"""
Text-to-Speech service using XTTS-v2 model with voice cloning
"""
import os
import base64
import tempfile
from pathlib import Path
from typing import Optional, Dict
import logging
import torch

try:
    from TTS.api import TTS
except ImportError:
    TTS = None

logger = logging.getLogger(__name__)


class TTSService:
    """Service for text-to-speech generation with voice cloning using XTTS-v2"""
    
    def __init__(self, model_name: str = "tts_models/multilingual/multi-dataset/xtts_v2"):
        """
        Initialize TTS service with XTTS-v2 model
        
        Args:
            model_name: TTS model name (default: XTTS-v2)
        """
        if TTS is None:
            raise ImportError("TTS package is required. Install with: pip install TTS")
        
        self.model_name = model_name
        
        # Session storage for voice samples (session_id -> audio_file_path)
        self.voice_samples: Dict[str, str] = {}
        
        # Determine device (GPU if available, otherwise CPU)
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        
        logger.info(f"Loading TTS model '{model_name}' on {self.device}... This may take a moment.")
        
        try:
            # Initialize TTS model
            self.tts = TTS(model_name, gpu=(self.device == "cuda"))
            logger.info(f"TTSService initialized successfully with model '{model_name}'")
            
            # Get supported languages
            if hasattr(self.tts, 'languages'):
                logger.info(f"Supported languages: {self.tts.languages}")
            
            # Create default voice sample directory
            self.default_voice_dir = Path(__file__).parent.parent / "default_voices"
            self.default_voice_dir.mkdir(exist_ok=True)
            
            # Path to default neutral voice (we'll use a generic sample)
            self.default_voice_path = self._get_default_voice()
            
        except Exception as e:
            logger.error(f"Error initializing TTS model: {e}")
            raise
    
    def _get_default_voice(self) -> Optional[str]:
        """
        Get path to default voice sample
        
        Returns:
            Path to default voice sample file, or None if not found
        """
        # Check if default voice exists
        default_voice_file = self.default_voice_dir / "default_voice.wav"
        
        if default_voice_file.exists():
            logger.info(f"Using existing default voice: {default_voice_file}")
            return str(default_voice_file)
        
        logger.info("No default voice sample found. Will use first user-provided sample or generate without cloning.")
        return None
    
    def store_voice_sample(self, audio_data: str, session_id: str, audio_format: str = "webm") -> bool:
        """
        Store voice sample for a session (for voice cloning)
        
        Args:
            audio_data: Base64 encoded audio data
            session_id: Session identifier
            audio_format: Audio format (webm, wav, mp3, etc.)
        
        Returns:
            True if successful, False otherwise
        """
        try:
            # Decode base64 audio
            audio_bytes = base64.b64decode(audio_data)
            
            # Create temporary file with proper extension
            temp_file = tempfile.NamedTemporaryFile(
                suffix=f".{audio_format}",
                delete=False,
                dir=self.default_voice_dir
            )
            
            with temp_file:
                temp_file.write(audio_bytes)
                temp_path = temp_file.name
            
            # If format is not WAV, we might need to convert (XTTS works with various formats)
            # For now, store as-is since XTTS can handle multiple formats
            
            # Store the path
            self.voice_samples[session_id] = temp_path
            
            logger.info(f"Stored voice sample for session {session_id}: {temp_path}")
            return True
        
        except Exception as e:
            logger.error(f"Error storing voice sample: {e}")
            return False
    
    def has_voice_sample(self, session_id: str) -> bool:
        """
        Check if session has a voice sample
        
        Args:
            session_id: Session identifier
        
        Returns:
            True if session has voice sample, False otherwise
        """
        return session_id in self.voice_samples
    
    def generate_speech(
        self,
        text: str,
        session_id: Optional[str] = None,
        language: str = "en"
    ) -> Optional[str]:
        """
        Generate speech from text using voice cloning if available
        
        Args:
            text: Text to convert to speech
            session_id: Session identifier (for voice cloning)
            language: Language code (default: "en")
        
        Returns:
            Base64 encoded audio data (WAV format), or None if failed
        """
        try:
            # Determine which voice sample to use
            speaker_wav = None
            
            if session_id and session_id in self.voice_samples:
                speaker_wav = self.voice_samples[session_id]
                logger.info(f"Using custom voice for session {session_id}")
            elif self.default_voice_path:
                speaker_wav = self.default_voice_path
                logger.info("Using default voice")
            else:
                logger.warning("No voice sample available. Generating with model default.")
            
            # Create temporary output file
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_output:
                output_path = temp_output.name
            
            try:
                # Generate speech
                if speaker_wav:
                    # Use voice cloning
                    self.tts.tts_to_file(
                        text=text,
                        speaker_wav=speaker_wav,
                        language=language,
                        file_path=output_path
                    )
                else:
                    # Generate without cloning (may not work well for XTTS-v2 as it requires speaker reference)
                    # Fall back to a simple neutral generation
                    logger.warning("XTTS-v2 requires a speaker reference. Using default parameters.")
                    self.tts.tts_to_file(
                        text=text,
                        language=language,
                        file_path=output_path
                    )
                
                # Read generated audio and encode to base64
                with open(output_path, 'rb') as audio_file:
                    audio_bytes = audio_file.read()
                    audio_base64 = base64.b64encode(audio_bytes).decode('utf-8')
                
                logger.info(f"Successfully generated speech ({len(text)} chars -> {len(audio_bytes)} bytes)")
                return audio_base64
            
            finally:
                # Clean up temporary output file
                if os.path.exists(output_path):
                    os.unlink(output_path)
        
        except Exception as e:
            logger.error(f"Error generating speech: {e}")
            return None
    
    def cleanup_session(self, session_id: str) -> None:
        """
        Clean up voice sample for a session
        
        Args:
            session_id: Session identifier
        """
        if session_id in self.voice_samples:
            voice_path = self.voice_samples[session_id]
            
            try:
                if os.path.exists(voice_path):
                    os.unlink(voice_path)
                    logger.info(f"Cleaned up voice sample for session {session_id}")
            except Exception as e:
                logger.error(f"Error cleaning up voice sample: {e}")
            
            del self.voice_samples[session_id]
    
    def cleanup_all(self) -> None:
        """Clean up all voice samples"""
        for session_id in list(self.voice_samples.keys()):
            self.cleanup_session(session_id)
        
        logger.info("Cleaned up all voice samples")

