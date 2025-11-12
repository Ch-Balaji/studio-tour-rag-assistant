/**
 * Voice Upload Modal for TTS Voice Cloning
 */

'use client';

import { useState, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useVoiceRecorder } from '@/hooks/useVoiceRecorder';
import { uploadVoiceSample } from '@/services/api';

interface VoiceUploadModalProps {
  isOpen: boolean;
  onClose: () => void;
  sessionId: string;
  onVoiceUploaded: () => void;
}

export default function VoiceUploadModal({
  isOpen,
  onClose,
  sessionId,
  onVoiceUploaded,
}: VoiceUploadModalProps) {
  const [uploadMode, setUploadMode] = useState<'record' | 'upload'>('record');
  const [isUploading, setIsUploading] = useState(false);
  const [recordedBlob, setRecordedBlob] = useState<Blob | null>(null);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [recordingTime, setRecordingTime] = useState(0);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const timerRef = useRef<NodeJS.Timeout | null>(null);

  const {
    isRecording,
    startRecording,
    stopRecording,
    audioStream,
    error: recorderError,
  } = useVoiceRecorder();

  const handleStartRecording = async () => {
    setRecordedBlob(null);
    setUploadError(null);
    setRecordingTime(0);
    
    await startRecording();
    
    // Start timer
    timerRef.current = setInterval(() => {
      setRecordingTime((prev) => prev + 1);
    }, 1000);
  };

  const handleStopRecording = async () => {
    if (timerRef.current) {
      clearInterval(timerRef.current);
      timerRef.current = null;
    }

    const blob = await stopRecording();
    if (blob) {
      setRecordedBlob(blob);
    }
  };

  const handleFileUpload = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      setRecordedBlob(file);
      setUploadError(null);
    }
  };

  const handleSubmit = async () => {
    if (!recordedBlob) return;

    setIsUploading(true);
    setUploadError(null);

    try {
      const result = await uploadVoiceSample(recordedBlob, sessionId);
      
      if (result.success) {
        onVoiceUploaded();
        handleClose();
      } else {
        setUploadError(result.error || 'Failed to upload voice sample');
      }
    } catch (error) {
      setUploadError(error instanceof Error ? error.message : 'Unknown error');
    } finally {
      setIsUploading(false);
    }
  };

  const handleClose = () => {
    if (timerRef.current) {
      clearInterval(timerRef.current);
      timerRef.current = null;
    }
    setRecordedBlob(null);
    setUploadError(null);
    setRecordingTime(0);
    onClose();
  };

  const formatRecordingTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  return (
    <AnimatePresence>
      {isOpen && (
        <>
          {/* Backdrop */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black/50 backdrop-blur-sm z-40"
            onClick={handleClose}
          />

          {/* Modal */}
          <motion.div
            initial={{ opacity: 0, scale: 0.95, y: 20 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.95, y: 20 }}
            className="fixed left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 w-full max-w-2xl bg-card border border-primary/20 rounded-2xl shadow-2xl z-50 p-6"
          >
            {/* Header */}
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-2xl font-bold text-foreground magical-text">
                🎤 Voice Clone Setup
              </h2>
              <button
                onClick={handleClose}
                className="p-2 hover:bg-primary/10 rounded-lg transition-colors"
              >
                <svg className="w-6 h-6 text-foreground" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>

            {/* Instructions */}
            <div className="mb-6 p-4 bg-primary/10 border border-primary/20 rounded-lg">
              <h3 className="font-semibold text-foreground mb-2">📝 Recording Tips for Best Results:</h3>
              <ul className="text-sm text-foreground-muted space-y-1.5">
                <li>• <strong>Duration:</strong> Record 10-15 seconds of clear speech</li>
                <li>• <strong>Environment:</strong> Find a quiet location with minimal background noise</li>
                <li>• <strong>Content:</strong> Read naturally - try a paragraph from a book or article</li>
                <li>• <strong>Tone:</strong> Speak in your natural voice, not too fast or too slow</li>
                <li>• <strong>Distance:</strong> Keep consistent distance from microphone (6-12 inches)</li>
                <li>• <strong>Quality:</strong> The better your recording, the better the voice clone!</li>
              </ul>
            </div>

            {/* Mode Selection */}
            <div className="flex gap-2 mb-6">
              <button
                onClick={() => setUploadMode('record')}
                className={`flex-1 py-3 px-4 rounded-lg font-medium transition-all ${
                  uploadMode === 'record'
                    ? 'bg-primary text-white magical-glow'
                    : 'bg-secondary text-foreground-muted hover:bg-secondary/80'
                }`}
              >
                🎙️ Record Now
              </button>
              <button
                onClick={() => setUploadMode('upload')}
                className={`flex-1 py-3 px-4 rounded-lg font-medium transition-all ${
                  uploadMode === 'upload'
                    ? 'bg-primary text-white magical-glow'
                    : 'bg-secondary text-foreground-muted hover:bg-secondary/80'
                }`}
              >
                📁 Upload File
              </button>
            </div>

            {/* Content Area */}
            <div className="mb-6">
              {uploadMode === 'record' ? (
                <div className="flex flex-col items-center gap-4 py-8">
                  {isRecording && (
                    <div className="text-4xl font-bold text-primary magical-text">
                      {formatRecordingTime(recordingTime)}
                    </div>
                  )}
                  
                  <motion.button
                    onClick={isRecording ? handleStopRecording : handleStartRecording}
                    whileHover={{ scale: 1.05 }}
                    whileTap={{ scale: 0.95 }}
                    className={`w-20 h-20 rounded-full flex items-center justify-center text-3xl transition-all ${
                      isRecording
                        ? 'bg-red-500 hover:bg-red-600 magical-glow animate-pulse'
                        : 'bg-primary hover:bg-primary-hover magical-glow'
                    }`}
                  >
                    {isRecording ? '⏹️' : '🎤'}
                  </motion.button>

                  <p className="text-sm text-foreground-muted">
                    {isRecording
                      ? 'Click to stop recording (aim for 10-15 seconds)'
                      : recordedBlob
                      ? '✓ Recording saved! Click Submit below or record again'
                      : 'Click the microphone to start recording'}
                  </p>

                  {recordedBlob && !isRecording && (
                    <audio
                      controls
                      src={URL.createObjectURL(recordedBlob)}
                      className="w-full max-w-md"
                    />
                  )}

                  {audioStream && (
                    <div className="w-full max-w-md h-2 bg-secondary rounded-full overflow-hidden">
                      <div className="h-full bg-primary animate-pulse" style={{ width: '50%' }}></div>
                    </div>
                  )}
                </div>
              ) : (
                <div className="flex flex-col items-center gap-4 py-8">
                  <input
                    ref={fileInputRef}
                    type="file"
                    accept="audio/*"
                    onChange={handleFileUpload}
                    className="hidden"
                  />
                  
                  <motion.button
                    onClick={() => fileInputRef.current?.click()}
                    whileHover={{ scale: 1.05 }}
                    whileTap={{ scale: 0.95 }}
                    className="w-32 h-32 rounded-2xl bg-primary/10 hover:bg-primary/20 border-2 border-dashed border-primary flex flex-col items-center justify-center gap-2 transition-all"
                  >
                    <span className="text-4xl">📁</span>
                    <span className="text-sm text-foreground-muted">Choose File</span>
                  </motion.button>

                  {recordedBlob && (
                    <div className="text-center">
                      <p className="text-sm text-foreground mb-2">
                        ✓ File selected: {(recordedBlob as File).name || 'Audio file'}
                      </p>
                      <audio
                        controls
                        src={URL.createObjectURL(recordedBlob)}
                        className="w-full max-w-md"
                      />
                    </div>
                  )}
                </div>
              )}
            </div>

            {/* Errors */}
            {(uploadError || recorderError) && (
              <div className="mb-4 p-3 bg-red-900/20 border border-red-500/50 rounded-lg text-red-400 text-sm">
                {uploadError || recorderError}
              </div>
            )}

            {/* Actions */}
            <div className="flex gap-3">
              <button
                onClick={handleClose}
                className="flex-1 py-3 px-4 bg-secondary hover:bg-secondary/80 text-foreground rounded-lg font-medium transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={handleSubmit}
                disabled={!recordedBlob || isUploading || isRecording}
                className="flex-1 py-3 px-4 bg-primary hover:bg-primary-hover text-white rounded-lg font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed magical-glow disabled:shadow-none"
              >
                {isUploading ? 'Uploading...' : 'Submit Voice Sample'}
              </button>
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
}

