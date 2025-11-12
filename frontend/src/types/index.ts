/**
 * TypeScript types and interfaces
 */

export interface Message {
  role: 'user' | 'assistant' | 'system';
  content: string;
  sources?: Source[];
  enhanced_query?: string;
  audio?: string; // Base64 encoded audio
  suggested_questions?: string[];
}

export interface Source {
  text: string;
  metadata: {
    source_file?: string;
    page_num?: number;
    characters?: string[];
    locations?: string[];
    spells?: string[];
  };
  similarity?: number;
  rerank_score?: number;
  retrieval_method?: string;
  bm25_score?: number;
}

export interface ChatSettings {
  use_reranking: boolean;
  initial_top_k: number;
  final_top_n: number;
  similarity_threshold: number;
  use_hybrid_search: boolean;
  hybrid_alpha: number;
  use_query_enhancement: boolean;
  citation_style: 'clean' | 'none';
}

export interface TranscriptionResponse {
  text: string;
  success: boolean;
  error?: string;
}

export interface WebSocketMessage {
  type: 'chunk' | 'sources' | 'enhanced_query' | 'suggested_questions' | 'done' | 'error';
  content: any;
}

export interface HealthStatus {
  status: string;
  llm_connected: boolean;
  llm_provider: string;
  services_loaded: boolean;
}

export interface SettingsResponse {
  defaults: ChatSettings;
  ranges: {
    initial_top_k: { min: number; max: number; step: number };
    final_top_n: { min: number; max: number; step: number };
    similarity_threshold: { min: number; max: number; step: number };
    hybrid_alpha: { min: number; max: number; step: number };
  };
}

// TTS Types
export interface TTSSettings {
  enabled: boolean;
  hasVoiceSample: boolean;
}

export interface VoiceSampleResponse {
  success: boolean;
  message: string;
  error?: string;
}

export interface TTSResponse {
  audio?: string;
  success: boolean;
  error?: string;
}

export interface VoiceStatusResponse {
  has_voice: boolean;
  session_id: string;
}

