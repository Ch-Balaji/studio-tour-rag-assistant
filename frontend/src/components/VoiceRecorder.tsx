/**
 * Voice Recorder Component with Waveform Visualization
 */

'use client';

import { useEffect, useRef } from 'react';
import { motion } from 'framer-motion';

interface VoiceRecorderProps {
  isRecording: boolean;
  onStartRecording: () => void;
  onStopRecording: () => void;
  audioStream: MediaStream | null;
  disabled?: boolean;
}

export default function VoiceRecorder({
  isRecording,
  onStartRecording,
  onStopRecording,
  audioStream,
  disabled = false,
}: VoiceRecorderProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const animationFrameRef = useRef<number>();
  const analyserRef = useRef<AnalyserNode | null>(null);
  const audioContextRef = useRef<AudioContext | null>(null);

  useEffect(() => {
    if (isRecording && audioStream && canvasRef.current) {
      // Create audio context and analyser
      const audioContext = new AudioContext();
      const analyser = audioContext.createAnalyser();
      const source = audioContext.createMediaStreamSource(audioStream);
      
      analyser.fftSize = 128;
      analyser.smoothingTimeConstant = 0.8;
      source.connect(analyser);
      
      audioContextRef.current = audioContext;
      analyserRef.current = analyser;
      
      // Start visualization
      visualize();
    }

    return () => {
      if (animationFrameRef.current) {
        cancelAnimationFrame(animationFrameRef.current);
      }
      if (audioContextRef.current && audioContextRef.current.state !== 'closed') {
        audioContextRef.current.close();
      }
    };
  }, [isRecording, audioStream]);

  const visualize = () => {
    const canvas = canvasRef.current;
    const analyser = analyserRef.current;
    
    if (!canvas || !analyser) return;
    
    const ctx = canvas.getContext('2d');
    if (!ctx) return;
    
    const bufferLength = analyser.frequencyBinCount;
    const dataArray = new Uint8Array(bufferLength);
    
    // Detect system theme
    const isDarkMode = window.matchMedia('(prefers-color-scheme: dark)').matches;
    
    const draw = () => {
      animationFrameRef.current = requestAnimationFrame(draw);
      
      analyser.getByteFrequencyData(dataArray);
      
      // Clear canvas with magical dark background
      ctx.fillStyle = 'rgb(18, 18, 26)';
      ctx.fillRect(0, 0, canvas.width, canvas.height);
      
      const barWidth = (canvas.width / bufferLength) * 2.5;
      let barHeight;
      let x = 0;
      
      for (let i = 0; i < bufferLength; i++) {
        barHeight = (dataArray[i] / 255) * canvas.height * 0.8;
        
        // Create magical gradient for bars (indigo/purple)
        const gradient = ctx.createLinearGradient(0, canvas.height - barHeight, 0, canvas.height);
        gradient.addColorStop(0, 'rgb(129, 140, 248)'); // Indigo
        gradient.addColorStop(1, 'rgb(147, 51, 234)');  // Purple
        
        ctx.fillStyle = gradient;
        ctx.fillRect(x, canvas.height - barHeight, barWidth, barHeight);
        
        x += barWidth + 1;
      }
    };
    
    draw();
  };

  const handleClick = () => {
    if (disabled) return;
    
    if (isRecording) {
      onStopRecording();
    } else {
      onStartRecording();
    }
  };

  return (
    <div className="flex items-center gap-2">
      <motion.button
        onClick={handleClick}
        disabled={disabled}
        className={`p-3 rounded-full transition-all ${
          isRecording
            ? 'bg-red-500 hover:bg-red-600 magical-glow'
            : 'bg-secondary hover:bg-card border border-border hover:border-primary/50'
        } ${disabled ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}`}
        whileTap={{ scale: 0.95 }}
        whileHover={{ scale: 1.05 }}
        animate={isRecording ? { scale: [1, 1.05, 1] } : {}}
        transition={isRecording ? { repeat: Infinity, duration: 1.5 } : {}}
      >
        {isRecording ? (
          <svg
            className="w-5 h-5 text-white"
            fill="currentColor"
            viewBox="0 0 20 20"
          >
            <rect x="6" y="6" width="8" height="8" />
          </svg>
        ) : (
          <svg
            className="w-5 h-5 text-foreground"
            fill="currentColor"
            viewBox="0 0 20 20"
          >
            <path
              fillRule="evenodd"
              d="M7 4a3 3 0 016 0v4a3 3 0 11-6 0V4zm4 10.93A7.001 7.001 0 0017 8a1 1 0 10-2 0A5 5 0 015 8a1 1 0 00-2 0 7.001 7.001 0 006 6.93V17H6a1 1 0 100 2h8a1 1 0 100-2h-3v-2.07z"
              clipRule="evenodd"
            />
          </svg>
        )}
      </motion.button>
      
      {isRecording && (
        <motion.div
          initial={{ opacity: 0, width: 0 }}
          animate={{ opacity: 1, width: 150 }}
          exit={{ opacity: 0, width: 0 }}
          className="overflow-hidden"
        >
          <canvas
            ref={canvasRef}
            width="150"
            height="40"
            className="rounded border border-primary/30 bg-card"
          />
        </motion.div>
      )}
    </div>
  );
}

