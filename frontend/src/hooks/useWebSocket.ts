/**
 * WebSocket hook for streaming chat
 */

import { useState, useEffect, useCallback, useRef } from 'react';
import { ChatSettings, WebSocketMessage, Source } from '@/types';

const WS_URL = process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000';

interface UseWebSocketReturn {
  sendMessage: (query: string, settings: ChatSettings) => void;
  isConnected: boolean;
  isStreaming: boolean;
  currentResponse: string;
  currentSources: Source[];
  enhancedQuery: string | null;
  suggestedQuestions: string[];
  error: string | null;
}

export function useWebSocket(
  onMessageComplete: (response: string, sources: Source[], enhancedQuery?: string, suggestedQuestions?: string[]) => void
): UseWebSocketReturn {
  const [isConnected, setIsConnected] = useState(false);
  const [isStreaming, setIsStreaming] = useState(false);
  const [currentResponse, setCurrentResponse] = useState('');
  const [currentSources, setCurrentSources] = useState<Source[]>([]);
  const [enhancedQuery, setEnhancedQuery] = useState<string | null>(null);
  const [suggestedQuestions, setSuggestedQuestions] = useState<string[]>([]);
  const [error, setError] = useState<string | null>(null);
  
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const reconnectAttempts = useRef(0);
  
  // Use refs to avoid stale closure issues
  const currentResponseRef = useRef('');
  const currentSourcesRef = useRef<Source[]>([]);
  const enhancedQueryRef = useRef<string | null>(null);
  const suggestedQuestionsRef = useRef<string[]>([]);

  // Store callback in ref to avoid recreating connect function
  const onMessageCompleteRef = useRef(onMessageComplete);
  
  // Throttle state updates for better performance
  const updateThrottleRef = useRef<NodeJS.Timeout | null>(null);
  const pendingUpdateRef = useRef(false);
  
  useEffect(() => {
    onMessageCompleteRef.current = onMessageComplete;
  }, [onMessageComplete]);

  const connect = useCallback(() => {
    try {
      const ws = new WebSocket(`${WS_URL}/ws/chat`);
      
      ws.onopen = () => {
        console.log('WebSocket connected');
        setIsConnected(true);
        setError(null);
        reconnectAttempts.current = 0;
      };

      ws.onmessage = (event) => {
        try {
          const message: WebSocketMessage = JSON.parse(event.data);
          
          switch (message.type) {
            case 'chunk':
              currentResponseRef.current += message.content;
              
              // Throttle updates using requestAnimationFrame for smooth 60fps rendering
              if (!pendingUpdateRef.current) {
                pendingUpdateRef.current = true;
                requestAnimationFrame(() => {
                  setCurrentResponse(currentResponseRef.current);
                  pendingUpdateRef.current = false;
                });
              }
              break;
            
            case 'sources':
              currentSourcesRef.current = message.content;
              setCurrentSources(message.content);
              break;
            
            case 'enhanced_query':
              enhancedQueryRef.current = message.content;
              setEnhancedQuery(message.content);
              break;
            
            case 'suggested_questions':
              suggestedQuestionsRef.current = message.content;
              setSuggestedQuestions(message.content);
              break;
            
            case 'done':
              // Force final state update FIRST
              setCurrentResponse(currentResponseRef.current);
              
              // Wait for state update to complete, THEN stop streaming
              setTimeout(() => {
                setIsStreaming(false);
                
                onMessageCompleteRef.current(
                  currentResponseRef.current, 
                  currentSourcesRef.current, 
                  enhancedQueryRef.current || undefined,
                  suggestedQuestionsRef.current.length > 0 ? suggestedQuestionsRef.current : undefined
                );
                
                // Reset refs for next message
                currentResponseRef.current = '';
                currentSourcesRef.current = [];
                enhancedQueryRef.current = null;
                suggestedQuestionsRef.current = [];
              }, 200);
              break;
            
            case 'error':
              console.error('Server error:', message.content);
              setError(message.content);
              setIsStreaming(false);
              break;
          }
        } catch (err) {
          console.error('Error parsing WebSocket message:', err);
        }
      };

      ws.onerror = (event) => {
        console.error('WebSocket error:', event);
        setError('WebSocket connection error');
      };

      ws.onclose = () => {
        console.log('WebSocket disconnected');
        setIsConnected(false);
        
        // Attempt to reconnect with exponential backoff
        if (reconnectAttempts.current < 5) {
          const delay = Math.min(1000 * Math.pow(2, reconnectAttempts.current), 10000);
          console.log(`Reconnecting in ${delay}ms...`);
          
          reconnectTimeoutRef.current = setTimeout(() => {
            reconnectAttempts.current++;
            connect();
          }, delay);
        }
      };

      wsRef.current = ws;
    } catch (err) {
      console.error('Error creating WebSocket:', err);
      setError('Failed to create WebSocket connection');
    }
  }, []); // Empty dependency array - stable function

  useEffect(() => {
    connect();

    return () => {
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, [connect]);

  const sendMessage = useCallback((query: string, settings: ChatSettings) => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      setIsStreaming(true);
      currentResponseRef.current = '';
      currentSourcesRef.current = [];
      enhancedQueryRef.current = null;
      suggestedQuestionsRef.current = [];
      setCurrentResponse('');
      setCurrentSources([]);
      setEnhancedQuery(null);
      setSuggestedQuestions([]);
      setError(null);
      
      wsRef.current.send(JSON.stringify({
        query,
        settings,
      }));
    } else {
      setError('WebSocket is not connected');
      console.error('WebSocket is not connected');
    }
  }, []);

  return {
    sendMessage,
    isConnected,
    isStreaming,
    currentResponse,
    currentSources,
    enhancedQuery,
    suggestedQuestions,
    error,
  };
}

