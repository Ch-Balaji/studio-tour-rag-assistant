/**
 * Main Chat Interface Component
 */

'use client';

import { useState, useEffect, useRef, useCallback } from 'react';
import { Message, ChatSettings, Source, TTSSettings } from '@/types';
import { useWebSocket } from '@/hooks/useWebSocket';
import { useVoiceRecorder } from '@/hooks/useVoiceRecorder';
import { transcribeAudio, checkHealth, getSettings, generateSpeech, checkVoiceStatus } from '@/services/api';
import MessageBubble from './MessageBubble';
import SettingsPanel from './SettingsPanel';
import VoiceUploadModal from './VoiceUploadModal';
import { motion } from 'framer-motion';

export default function ChatInterface() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputValue, setInputValue] = useState('');
  const [settings, setSettings] = useState<ChatSettings>({
    use_reranking: true,
    initial_top_k: 25,
    final_top_n: 5,
    similarity_threshold: 0.3,
    use_hybrid_search: true,
    hybrid_alpha: 0.5,
    use_query_enhancement: true,
    citation_style: 'clean',
  });
  const [showSettings, setShowSettings] = useState(false);
  const [isHealthy, setIsHealthy] = useState(true);
  const [llmProvider, setLlmProvider] = useState<string>('ollama');
  const [isTranscribing, setIsTranscribing] = useState(false);
  const [isSearching, setIsSearching] = useState(false);
  
  // TTS State
  const [ttsSettings, setTtsSettings] = useState<TTSSettings>({
    enabled: false,
    hasVoiceSample: false,
  });
  const [showVoiceUpload, setShowVoiceUpload] = useState(false);
  const [sessionId, setSessionId] = useState<string>('');
  const [generatingAudioForIndex, setGeneratingAudioForIndex] = useState<number | null>(null);
  
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const animationFrameRef = useRef<number>();
  const analyserRef = useRef<AnalyserNode | null>(null);
  const audioContextRef = useRef<AudioContext | null>(null);

  // WebSocket hook
  const handleMessageComplete = useCallback(async (response: string, sources: Source[], enhancedQuery?: string, suggestedQuestions?: string[]) => {
    // Hide searching indicator when complete
    setIsSearching(false);
    
    setMessages((prev) => {
      const lastIdx = prev.length - 1;
      
      if (lastIdx >= 0 && prev[lastIdx].role === 'assistant') {
        // Create new object (don't mutate!)
        return [
          ...prev.slice(0, lastIdx),
          {
            ...prev[lastIdx],
            content: response,
            sources: sources,
            enhanced_query: enhancedQuery || prev[lastIdx].enhanced_query,
            suggested_questions: suggestedQuestions,
          },
        ];
      }
      
      return prev;
    });

    // Generate audio if TTS is enabled
    if (ttsSettings.enabled && response) {
      setMessages((prev) => {
        const lastIdx = prev.length - 1;
        setGeneratingAudioForIndex(lastIdx);
        return prev;
      });

      try {
        const audioResult = await generateSpeech(response, sessionId);
        if (audioResult.success && audioResult.audio) {
          setMessages((prev) => {
            const lastIdx = prev.length - 1;
            if (lastIdx >= 0 && prev[lastIdx].role === 'assistant') {
              return [
                ...prev.slice(0, lastIdx),
                {
                  ...prev[lastIdx],
                  audio: audioResult.audio,
                },
              ];
            }
            return prev;
          });
        }
      } catch (error) {
        console.error('Error generating audio:', error);
      } finally {
        setGeneratingAudioForIndex(null);
      }
    }
  }, [ttsSettings.enabled, sessionId]);

  const {
    sendMessage,
    isConnected,
    isStreaming,
    currentResponse,
    currentSources,
    enhancedQuery,
    error: wsError,
  } = useWebSocket(handleMessageComplete);

  // Voice recorder hook
  const {
    isRecording,
    startRecording,
    stopRecording,
    audioStream,
    error: recorderError,
  } = useVoiceRecorder();

  // Initialize session ID on mount
  useEffect(() => {
    // Generate or retrieve session ID
    let sid = sessionStorage.getItem('tts_session_id');
    if (!sid) {
      sid = `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
      sessionStorage.setItem('tts_session_id', sid);
    }
    setSessionId(sid);
  }, []);

  // Load settings on mount
  useEffect(() => {
    const loadSettings = async () => {
      const settingsData = await getSettings();
      if (settingsData) {
        setSettings(settingsData.defaults);
      }
    };
    
    const checkBackendHealth = async () => {
      const health = await checkHealth();
      setIsHealthy(health.llm_connected && health.services_loaded);
      setLlmProvider(health.llm_provider || 'ollama');
    };

    loadSettings();
    checkBackendHealth();
    
    // Check health every 30 seconds
    const interval = setInterval(checkBackendHealth, 30000);
    return () => clearInterval(interval);
  }, []);

  // Check voice status when session ID is available
  useEffect(() => {
    if (sessionId) {
      const checkVoice = async () => {
        const status = await checkVoiceStatus(sessionId);
        setTtsSettings(prev => ({ ...prev, hasVoiceSample: status.has_voice }));
      };
      checkVoice();
    }
  }, [sessionId]);

  // Auto-scroll to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, currentResponse]);

  // Waveform visualization for voice recording
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
      const visualize = () => {
        const canvas = canvasRef.current;
        const analyserNode = analyserRef.current;
        
        if (!canvas || !analyserNode) return;
        
        const ctx = canvas.getContext('2d');
        if (!ctx) return;
        
        const bufferLength = analyserNode.frequencyBinCount;
        const dataArray = new Uint8Array(bufferLength);
        
        const draw = () => {
          animationFrameRef.current = requestAnimationFrame(draw);
          
          analyserNode.getByteFrequencyData(dataArray);
          
          // Clear canvas with dark slate background
          ctx.fillStyle = 'rgb(30, 41, 59)';
          ctx.fillRect(0, 0, canvas.width, canvas.height);
          
          const barWidth = (canvas.width / bufferLength) * 2.5;
          let barHeight;
          let x = 0;
          
          for (let i = 0; i < bufferLength; i++) {
            barHeight = (dataArray[i] / 255) * canvas.height * 0.8;
            
            // Create blue gradient for bars
            const gradient = ctx.createLinearGradient(0, canvas.height - barHeight, 0, canvas.height);
            gradient.addColorStop(0, 'rgb(59, 130, 246)'); // Blue-500
            gradient.addColorStop(1, 'rgb(37, 99, 235)');   // Blue-600
            
            ctx.fillStyle = gradient;
            ctx.fillRect(x, canvas.height - barHeight, barWidth, barHeight);
            
            x += barWidth + 1;
          }
        };
        
        draw();
      };
      
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

  // Update streaming message
  useEffect(() => {
    if (isStreaming && currentResponse) {
      // Hide searching indicator
      if (isSearching) {
        setIsSearching(false);
      }
      
      setMessages((prev) => {
        const lastIdx = prev.length - 1;
        
        // Check if last message is an assistant message
        if (lastIdx >= 0 && prev[lastIdx].role === 'assistant') {
          // Update existing assistant message (create new object!)
          return [
            ...prev.slice(0, lastIdx),
            {
              ...prev[lastIdx],
              content: currentResponse,
              sources: currentSources,
              enhanced_query: enhancedQuery || prev[lastIdx].enhanced_query,
            },
          ];
        } else {
          // Create new assistant message
          return [
            ...prev,
            {
              role: 'assistant',
              content: currentResponse,
              sources: currentSources,
              enhanced_query: enhancedQuery || undefined,
            },
          ];
        }
      });
    }
  }, [isStreaming, currentResponse, currentSources, enhancedQuery, isSearching]);

  const handleSendMessage = useCallback((overrideQuery?: string) => {
    // Ensure we have a string value before calling trim()
    const rawQuery = overrideQuery || inputValue;
    const query = typeof rawQuery === 'string' ? rawQuery.trim() : String(rawQuery || '').trim();
    if (!query || isStreaming || !isConnected) return;

    // Add user message
    const userMessage: Message = {
      role: 'user',
      content: query,
    };
    setMessages((prev) => [...prev, userMessage]);

    // Show searching indicator (no placeholder message needed - loading indicator handles it)
    setIsSearching(true);

    // Send via WebSocket
    sendMessage(query, settings);
    setInputValue('');
  }, [inputValue, isStreaming, isConnected, sendMessage, settings]);

  const handleKeyPress = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  const handleVoiceStop = async () => {
    setIsTranscribing(true);
    const audioBlob = await stopRecording();
    
    if (audioBlob) {
      const result = await transcribeAudio(audioBlob);
      if (result.success && result.text) {
        setInputValue(result.text);
        inputRef.current?.focus();
      } else {
        console.error('Transcription failed:', result.error);
      }
    }
    
    setIsTranscribing(false);
  };

  const clearChat = () => {
    setMessages([]);
  };

  const handleVoiceUploaded = async () => {
    // Refresh voice status
    if (sessionId) {
      const status = await checkVoiceStatus(sessionId);
      setTtsSettings(prev => ({ ...prev, hasVoiceSample: status.has_voice }));
    }
  };

  const toggleTTS = () => {
    setTtsSettings(prev => ({ ...prev, enabled: !prev.enabled }));
  };

  return (
    <div className="flex flex-col h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950 relative overflow-hidden">
      {/* Floating Orb Decorations - Soft Blue Theme */}
      <div className="fixed inset-0 -z-10 overflow-hidden pointer-events-none">
        <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-blue-500/10 rounded-full blur-3xl" />
        <div className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-slate-700/10 rounded-full blur-3xl" />
      </div>

      {/* Header */}
      <motion.div 
        initial={{ y: -20, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        className="flex items-center justify-between px-3 sm:px-6 py-3 sm:py-4 border-b border-border/50 frosted-glass"
      >
        {/* Mobile: Simple layout, Desktop: Centered with spacers */}
        <div className="hidden sm:flex flex-1"></div>
        
        {/* Centered Title and Status */}
        <div className="flex flex-col items-center gap-1 flex-1 sm:flex-1 min-w-0">
          <h1 className="text-base sm:text-xl font-bold text-foreground magical-text text-center whitespace-nowrap">
            <span className="sm:hidden">⚡ Voice Chat</span>
            <span className="hidden sm:inline">⚡ Silverlight Studios Voice Chat</span>
          </h1>
          <div className="flex items-center gap-2">
            <div
              className={`w-2 h-2 rounded-full flex-shrink-0 ${
                isConnected && isHealthy ? 'bg-green-500' : 'bg-red-500'
              }`}
            />
            <span className="text-xs text-foreground-muted whitespace-nowrap">
              {isConnected
                ? isHealthy
                  ? `Connected (${llmProvider.toUpperCase()})`
                  : `${llmProvider === 'groq' ? 'Groq API' : 'LLM'} Disconnected`
                : 'Connecting...'}
            </span>
          </div>
        </div>
        
        {/* Right side buttons */}
        <div className="flex items-center gap-2 flex-shrink-0 sm:flex-1 sm:justify-end">
          {/* TTS Toggle */}
          <motion.button
            onClick={toggleTTS}
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            className={`p-2 rounded-lg transition-colors ${
              ttsSettings.enabled 
                ? 'bg-primary/20 text-primary' 
                : 'hover:bg-primary/10 hover:text-primary'
            }`}
            title={ttsSettings.enabled ? "Disable text-to-speech" : "Enable text-to-speech"}
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15.536 8.464a5 5 0 010 7.072m2.828-9.9a9 9 0 010 12.728M5.586 15.586A2 2 0 014 14.586V9.414a2 2 0 011.586-1.586l3.828-3.828a1 1 0 011.707.707v15.172a1 1 0 01-1.707.707l-3.828-3.828z" />
            </svg>
          </motion.button>

          {/* Voice Upload Button (only show when TTS enabled) */}
          {ttsSettings.enabled && (
            <motion.button
              initial={{ scale: 0, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              onClick={() => setShowVoiceUpload(true)}
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              className={`p-2 rounded-lg transition-colors ${
                ttsSettings.hasVoiceSample
                  ? 'bg-primary/20 text-primary'
                  : 'bg-primary/10 text-primary hover:bg-primary/20'
              }`}
              title={ttsSettings.hasVoiceSample ? "Voice sample uploaded" : "Upload voice for cloning"}
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z" />
              </svg>
            </motion.button>
          )}

          <motion.button
            onClick={clearChat}
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            className="p-2 hover:bg-primary/10 hover:text-primary rounded-lg transition-colors"
            title="Clear chat"
          >
            <svg
              className="w-5 h-5 text-foreground"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"
              />
            </svg>
          </motion.button>
          <motion.button
            onClick={() => setShowSettings(true)}
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            className="p-2 hover:bg-primary/10 hover:text-primary rounded-lg transition-colors"
            title="Settings"
          >
            <svg
              className="w-5 h-5 text-foreground"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z"
              />
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"
              />
            </svg>
          </motion.button>
        </div>
      </motion.div>

      {/* Messages Area */}
      <div className="flex-1 overflow-y-auto px-3 sm:px-6 py-3 sm:py-4">
        {messages.length === 0 && !currentResponse ? (
          <motion.div 
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="flex flex-col items-center justify-center h-full text-center"
          >
            <div className="text-6xl mb-4">⚡</div>
            <h2 className="text-2xl font-bold text-foreground magical-text mb-2">
              Welcome to Silverlight Studios Voice Chat
            </h2>
            <p className="text-foreground-muted max-w-md px-4 text-sm sm:text-base">
              Ask me anything about Silverlight Studios! You can type your question or use
              the microphone to speak.
            </p>
          </motion.div>
        ) : (
          <div className="max-w-4xl mx-auto">
            {messages.map((message, idx) => {
              // Show streaming content for last assistant message
              const isLastMessage = idx === messages.length - 1;
              const shouldStream = isLastMessage && message.role === 'assistant' && isStreaming;
              const isGeneratingAudio = generatingAudioForIndex === idx;
              
              return (
                <div key={`${idx}-${message.content.length}`}>
                  <MessageBubble
                    message={message}
                    isStreaming={shouldStream}
                    isGeneratingAudio={isGeneratingAudio}
                  />
                  
                  {/* Suggested Questions */}
                  {message.role === 'assistant' && 
                   message.suggested_questions && 
                   message.suggested_questions.length > 0 &&
                   !shouldStream && (
                    <motion.div 
                      initial={{ opacity: 0, y: 5 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ delay: 0.3 }}
                      className="mt-4 mb-4 max-w-4xl"
                    >
                      <div className="ml-14">
                        {/* Simple minimal header */}
                        <p className="text-xs text-foreground-muted/70 mb-2 flex items-center gap-1">
                          <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8.228 9c.549-1.165 2.03-2 3.772-2 2.21 0 4 1.343 4 3 0 1.4-1.278 2.575-3.006 2.907-.542.104-.994.54-.994 1.093m0 3h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                          </svg>
                          Suggested questions
                        </p>
                        
                        {/* Simple question buttons */}
                        <div className="space-y-1.5">
                          {message.suggested_questions.map((question, qIdx) => (
                            <motion.button
                              key={qIdx}
                              initial={{ opacity: 0 }}
                              animate={{ opacity: 1 }}
                              transition={{ delay: 0.4 + qIdx * 0.05 }}
                              onClick={() => {
                                setInputValue(question);
                                handleSendMessage(question);
                              }}
                              className="group w-full text-left p-3 rounded-xl border border-border/30 hover:border-primary/50 bg-card/30 hover:bg-card/50 transition-all duration-200 text-sm"
                            >
                              <div className="flex items-center gap-2">
                                <svg 
                                  className="w-3.5 h-3.5 text-foreground-muted/50 group-hover:text-primary transition-colors flex-shrink-0" 
                                  fill="none" 
                                  viewBox="0 0 24 24" 
                                  stroke="currentColor"
                                >
                                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                                </svg>
                                <span className="text-foreground-muted group-hover:text-foreground transition-colors">
                                  {question}
                                </span>
                              </div>
                            </motion.button>
                          ))}
                        </div>
                      </div>
                    </motion.div>
                  )}
                </div>
              );
            })}
            
            {/* Loading indicator while searching */}
            {isSearching && (
              <motion.div 
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                className="flex gap-3 max-w-4xl mb-4"
              >
                <div className="flex-shrink-0 w-10 h-10 rounded-full flex items-center justify-center bg-gradient-to-br from-blue-600 to-blue-800 border-2 border-blue-500/30">
                  <span className="text-white text-xl">✨</span>
                </div>
                <div className="flex flex-col gap-2 flex-1">
                  <div className="rounded-3xl px-4 py-3 bg-assistant-message backdrop-blur-sm border border-border/50">
                    <div className="flex items-center gap-2 text-foreground-muted">
                      <div className="flex gap-1">
                        <div className="w-2 h-2 bg-primary rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></div>
                        <div className="w-2 h-2 bg-primary rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></div>
                        <div className="w-2 h-2 bg-primary rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></div>
                      </div>
                      <span className="text-sm italic">Searching knowledge base and thinking...</span>
                    </div>
                  </div>
                </div>
              </motion.div>
            )}
            
            <div ref={messagesEndRef} />
          </div>
        )}
      </div>

      {/* Input Area */}
      <div className="px-3 sm:px-6 py-3 sm:py-4 border-t border-border/50 frosted-glass">
        <div className="max-w-4xl mx-auto">
          {(wsError || recorderError) && (
            <motion.div 
              initial={{ opacity: 0, y: -10 }}
              animate={{ opacity: 1, y: 0 }}
              className="mb-2 p-3 bg-red-900/20 border border-red-500/50 rounded-lg text-red-400 text-sm backdrop-blur-sm"
            >
              {wsError || recorderError}
            </motion.div>
          )}
          
          {!isHealthy && (
            <motion.div 
              initial={{ opacity: 0, y: -10 }}
              animate={{ opacity: 1, y: 0 }}
              className="mb-2 p-3 bg-yellow-900/20 border border-yellow-500/50 rounded-lg text-yellow-400 text-sm backdrop-blur-sm"
            >
              ⚠️ {llmProvider === 'groq' 
                ? 'Groq API is not connected. Check your API key and internet connection.' 
                : 'Ollama is not connected. Make sure it\'s running: '
              }
              {llmProvider !== 'groq' && <code className="bg-card px-2 py-1 rounded">ollama serve</code>}
            </motion.div>
          )}
          
          {/* Unified Input Bar */}
          <div className="relative flex items-end gap-2 sm:gap-3 bg-secondary/80 border border-border/50 rounded-2xl p-2 sm:p-3 focus-within:border-primary focus-within:ring-2 focus-within:ring-primary/30 transition-all backdrop-blur-sm">
            {/* Voice Recording Button */}
            <div className="flex-shrink-0 flex items-center pb-1">
              <motion.button
                onClick={isRecording ? handleVoiceStop : startRecording}
                disabled={isStreaming || isTranscribing}
                className={`p-2.5 rounded-xl transition-all ${
                  isRecording
                    ? 'bg-red-500 hover:bg-red-600 shadow-md'
                    : 'hover:bg-card border border-transparent hover:border-primary/30'
                } ${isStreaming || isTranscribing ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}`}
                whileTap={{ scale: 0.95 }}
                whileHover={{ scale: 1.05 }}
                animate={isRecording ? { scale: [1, 1.05, 1] } : {}}
                transition={isRecording ? { repeat: Infinity, duration: 1.5 } : {}}
                title={isRecording ? "Stop recording" : "Start voice recording"}
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
            </div>

            {/* Recording Waveform Visualization */}
            {isRecording && audioStream && (
              <motion.div
                initial={{ opacity: 0, width: 0 }}
                animate={{ opacity: 1, width: 200 }}
                exit={{ opacity: 0, width: 0 }}
                className="flex-shrink-0 flex items-center pb-1 overflow-hidden"
              >
                <canvas
                  ref={canvasRef}
                  width="200"
                  height="40"
                  className="rounded-lg border border-primary/30 bg-card/50"
                />
              </motion.div>
            )}

            {/* Text Input */}
            <div className="flex-1 min-w-0">
              <textarea
                ref={inputRef}
                value={inputValue}
                onChange={(e) => setInputValue(e.target.value)}
                onKeyPress={handleKeyPress}
                placeholder={
                  isTranscribing
                    ? 'Transcribing...'
                    : 'What is on your mind?'
                }
                disabled={isStreaming || isTranscribing}
                className="w-full px-2 py-2.5 bg-transparent text-foreground resize-none focus:outline-none disabled:opacity-50 placeholder-foreground-muted/70 min-h-[40px] max-h-[150px] transition-smooth"
                rows={1}
                style={{ 
                  lineHeight: '1.5',
                  scrollbarWidth: 'thin',
                  scrollbarColor: 'rgba(99, 102, 241, 0.3) transparent'
                }}
              />
            </div>

            {/* Send Button */}
            <div className="flex-shrink-0 flex items-center pb-1">
              <motion.button
                onClick={() => handleSendMessage()}
                disabled={!inputValue.trim() || isStreaming || !isConnected}
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                className="p-2.5 bg-user-message hover:bg-green-500 disabled:bg-secondary/50 disabled:cursor-not-allowed rounded-xl transition-colors shadow-md disabled:shadow-none"
                title="Send message"
              >
                <svg
                  className="w-5 h-5 text-black"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8"
                  />
                </svg>
              </motion.button>
            </div>
          </div>
        </div>
      </div>

      {/* Settings Panel */}
      <SettingsPanel
        isOpen={showSettings}
        onClose={() => setShowSettings(false)}
        settings={settings}
        onSettingsChange={setSettings}
      />

      {/* Voice Upload Modal */}
      <VoiceUploadModal
        isOpen={showVoiceUpload}
        onClose={() => setShowVoiceUpload(false)}
        sessionId={sessionId}
        onVoiceUploaded={handleVoiceUploaded}
      />
    </div>
  );
}

