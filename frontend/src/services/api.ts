/**
 * API service for backend communication
 */

import { 
  TranscriptionResponse, 
  HealthStatus, 
  SettingsResponse,
  VoiceSampleResponse,
  TTSResponse,
  VoiceStatusResponse
} from '@/types';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

/**
 * Transcribe audio using OpenAI Whisper
 */
export async function transcribeAudio(
  audioBlob: Blob
): Promise<TranscriptionResponse> {
  try {
    // Convert blob to base64
    const base64Audio = await blobToBase64(audioBlob);
    
    const response = await fetch(`${API_URL}/api/transcribe`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        audio: base64Audio,
        format: 'webm',
      }),
    });

    if (!response.ok) {
      throw new Error(`Transcription failed: ${response.statusText}`);
    }

    return await response.json();
  } catch (error) {
    console.error('Transcription error:', error);
    return {
      text: '',
      success: false,
      error: error instanceof Error ? error.message : 'Unknown error',
    };
  }
}

/**
 * Check backend health status
 */
export async function checkHealth(): Promise<HealthStatus> {
  try {
    const response = await fetch(`${API_URL}/api/health`);
    return await response.json();
  } catch (error) {
    console.error('Health check error:', error);
    return {
      status: 'unhealthy',
      ollama_connected: false,
      services_loaded: false,
    };
  }
}

/**
 * Get available settings and ranges
 */
export async function getSettings(): Promise<SettingsResponse | null> {
  try {
    const response = await fetch(`${API_URL}/api/settings`);
    return await response.json();
  } catch (error) {
    console.error('Get settings error:', error);
    return null;
  }
}

/**
 * Convert Blob to base64 string
 */
function blobToBase64(blob: Blob): Promise<string> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onloadend = () => {
      const base64String = (reader.result as string).split(',')[1];
      resolve(base64String);
    };
    reader.onerror = reject;
    reader.readAsDataURL(blob);
  });
}

/**
 * Upload voice sample for TTS voice cloning
 */
export async function uploadVoiceSample(
  audioBlob: Blob,
  sessionId: string
): Promise<VoiceSampleResponse> {
  try {
    // Convert blob to base64
    const base64Audio = await blobToBase64(audioBlob);
    
    const response = await fetch(`${API_URL}/api/tts/upload-voice`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        audio: base64Audio,
        format: 'webm',
        session_id: sessionId,
      }),
    });

    if (!response.ok) {
      throw new Error(`Voice upload failed: ${response.statusText}`);
    }

    return await response.json();
  } catch (error) {
    console.error('Voice upload error:', error);
    return {
      success: false,
      message: 'Failed to upload voice sample',
      error: error instanceof Error ? error.message : 'Unknown error',
    };
  }
}

/**
 * Generate speech from text using TTS
 */
export async function generateSpeech(
  text: string,
  sessionId?: string
): Promise<TTSResponse> {
  try {
    const response = await fetch(`${API_URL}/api/tts/generate`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        text,
        session_id: sessionId || null,
        language: 'en',
      }),
    });

    if (!response.ok) {
      throw new Error(`TTS generation failed: ${response.statusText}`);
    }

    return await response.json();
  } catch (error) {
    console.error('TTS generation error:', error);
    return {
      success: false,
      error: error instanceof Error ? error.message : 'Unknown error',
    };
  }
}

/**
 * Check if session has a voice sample
 */
export async function checkVoiceStatus(
  sessionId: string
): Promise<VoiceStatusResponse> {
  try {
    const response = await fetch(`${API_URL}/api/tts/has-voice/${sessionId}`);
    return await response.json();
  } catch (error) {
    console.error('Voice status check error:', error);
    return {
      has_voice: false,
      session_id: sessionId,
    };
  }
}

